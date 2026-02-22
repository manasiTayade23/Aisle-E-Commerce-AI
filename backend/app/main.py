"""FastAPI application entry point."""

# Use pysqlite3 for ChromaDB when system sqlite is < 3.35 (required by Chroma)
import sys
import types
try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    pass

# Stub langchain.debug so LangGraph/langchain-core don't raise (we use LangGraph only, no full langchain)
_lc = types.ModuleType("langchain")
_lc.debug = False
sys.modules["langchain"] = _lc

import json
import logging
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from app.agent import stream_response
from app.config import get_default_llm_config
from app.database import init_db
from app import fake_store
from app.tools import get_cart_payload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Silence Chroma PostHog telemetry errors (anonymized_telemetry=False still triggers buggy capture() calls)
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)

app = FastAPI(title="E-Commerce Shopping Assistant API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    logger.info("Database initialized")


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


# ----- FakeStoreAPI proxy (for testing connectivity without LLM) -----

@app.get("/api/fakestore/products")
async def fakestore_all_products():
    """Get all products from FakeStoreAPI via backend."""
    try:
        data = await fake_store.get_all_products()
        return {"ok": True, "count": len(data), "products": data}
    except Exception as e:
        logger.exception("FakeStoreAPI get_all_products failed")
        return JSONResponse(status_code=502, content={"ok": False, "error": str(e)})


@app.get("/api/fakestore/products/{product_id:int}")
async def fakestore_product(product_id: int):
    """Get one product by ID from FakeStoreAPI via backend."""
    try:
        data = await fake_store.get_product(product_id)
        return {"ok": True, "product": data}
    except Exception as e:
        logger.exception("FakeStoreAPI get_product failed")
        return JSONResponse(status_code=502, content={"ok": False, "error": str(e)})


@app.get("/api/fakestore/categories")
async def fakestore_categories():
    """Get all categories from FakeStoreAPI via backend."""
    try:
        data = await fake_store.get_categories()
        return {"ok": True, "categories": data}
    except Exception as e:
        logger.exception("FakeStoreAPI get_categories failed")
        return JSONResponse(status_code=502, content={"ok": False, "error": str(e)})


@app.get("/api/fakestore/products/category/{category:path}")
async def fakestore_products_by_category(category: str):
    """Get products in a category from FakeStoreAPI via backend."""
    try:
        data = await fake_store.get_products_by_category(category)
        return {"ok": True, "count": len(data), "category": category, "products": data}
    except Exception as e:
        logger.exception("FakeStoreAPI get_products_by_category failed")
        return JSONResponse(status_code=502, content={"ok": False, "error": str(e)})


@app.get("/api/cart")
async def get_cart(session_id: str | None = None):
    """Get cart contents for a session. Returns same shape as get_cart tool: { items, total }."""
    if not session_id:
        return {"items": [], "total": 0}
    try:
        payload = await get_cart_payload(session_id)
        return payload
    except Exception as e:
        logger.exception("get_cart failed")
        return JSONResponse(status_code=500, content={"error": str(e), "items": [], "total": 0})


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        llm_config = get_default_llm_config()
        has_key = bool(llm_config.get("api_key") and llm_config.get("api_key") != "your-api-key-here")
        return {
            "status": "ok",
            "llm_provider": llm_config.get("provider"),
            "api_key_configured": has_key,
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/chat")
async def chat(req: ChatRequest):
    """Chat endpoint with LangGraph multi-agent system."""
    try:
        llm_config = get_default_llm_config()
        if not llm_config.get("api_key") or llm_config.get("api_key") == "your-api-key-here":
            return JSONResponse(
                status_code=503,
                content={
                    "error": f"{llm_config.get('provider', 'LLM')} API key is not configured. "
                             f"Please add your {llm_config.get('provider', 'LLM')}_API_KEY to the .env file."
                },
            )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"error": f"LLM configuration error: {str(e)}"},
        )

    session_id = req.session_id or str(uuid.uuid4())
    logger.info("[chat] POST /chat received message=%r session_id=%s", req.message[:80] if len(req.message) > 80 else req.message, session_id)

    async def event_stream():
        logger.info("[chat] event_stream: yielding session chunk")
        yield json.dumps({"type": "session", "session_id": session_id}) + "\n"
        try:
            chunk_count = 0
            async for chunk in stream_response(session_id, req.message):
                chunk_count += 1
                yield chunk
            logger.info("[chat] event_stream: finished stream_response chunk_count=%d", chunk_count)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Stream error: {error_msg}")
            if "authentication" in error_msg.lower() or "401" in error_msg:
                llm_config = get_default_llm_config()
                provider = llm_config.get("provider", "LLM")
                yield json.dumps({"type": "error", "content": f"Invalid API key. Please check your {provider.upper()}_API_KEY in the .env file."}) + "\n"
            elif "rate" in error_msg.lower() and "limit" in error_msg.lower():
                yield json.dumps({"type": "error", "content": "Rate limit reached. Please wait a moment and try again."}) + "\n"
            elif "overloaded" in error_msg.lower() or "529" in error_msg:
                yield json.dumps({"type": "error", "content": "The AI service is temporarily overloaded. Please try again shortly."}) + "\n"
            else:
                yield json.dumps({"type": "error", "content": f"Something went wrong: {error_msg}"}) + "\n"
            yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
