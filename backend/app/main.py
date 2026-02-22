"""FastAPI application entry point."""

import json
import logging
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from app.agent import stream_response
from app.config import ANTHROPIC_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="E-Commerce Shopping Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


@app.get("/health")
async def health():
    has_key = bool(ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your-anthropic-api-key-here")
    return {"status": "ok", "api_key_configured": has_key}


@app.post("/chat")
async def chat(req: ChatRequest):
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your-anthropic-api-key-here":
        return JSONResponse(
            status_code=503,
            content={"error": "ANTHROPIC_API_KEY is not configured. Please add your API key to the .env file."},
        )

    session_id = req.session_id or str(uuid.uuid4())

    async def event_stream():
        yield json.dumps({"type": "session", "session_id": session_id}) + "\n"
        try:
            async for chunk in stream_response(session_id, req.message):
                yield chunk
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Stream error: {error_msg}")
            if "authentication" in error_msg.lower() or "401" in error_msg:
                yield json.dumps({"type": "error", "content": "Invalid API key. Please check your ANTHROPIC_API_KEY in the .env file."}) + "\n"
            elif "rate" in error_msg.lower() and "limit" in error_msg.lower():
                yield json.dumps({"type": "error", "content": "Rate limit reached. Please wait a moment and try again."}) + "\n"
            elif "overloaded" in error_msg.lower() or "529" in error_msg:
                yield json.dumps({"type": "error", "content": "The AI service is temporarily overloaded. Please try again shortly."}) + "\n"
            else:
                yield json.dumps({"type": "error", "content": f"Something went wrong: {error_msg}"}) + "\n"
            yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
