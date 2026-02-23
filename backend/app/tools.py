"""Tool definitions and execution for the AI agent."""

from __future__ import annotations

import json
import logging
from typing import Optional

from app import fake_store, cart

logger = logging.getLogger(__name__)

# ---------- Claude tool schemas ----------

TOOL_DEFINITIONS = [
    {
        "name": "search_products",
        "description": (
            "Search and filter products from the store. "
            "You can filter by keyword query, category, and/or price range. "
            "Returns a list of matching products with id, title, price, category, image, and rating."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Optional keyword to search in product titles and descriptions.",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter. Valid: electronics, jewelery, men's clothing, women's clothing. Use 'tv' or 'electronics' for TV/monitor requests; backend maps tv→electronics.",
                },
                "min_price": {
                    "type": "number",
                    "description": "Optional minimum price filter.",
                },
                "max_price": {
                    "type": "number",
                    "description": "Optional maximum price filter.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_product_details",
        "description": "Get full details for a single product by its ID, including title, price, description, category, image URL, and rating.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "The product ID to look up.",
                }
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "add_to_cart",
        "description": "Add a product to the user's shopping cart. Use quantity=1 unless the user explicitly asks for more (e.g. 'add 2', 'add three'). Do not call this tool twice for the same product in one request.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "The product ID to add.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "Number to add. Default 1. Use 2 or more only when the user explicitly says so (e.g. 'add 2', 'add three').",
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "get_cart",
        "description": "Get the current contents of the user's shopping cart, including product details and total price.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "remove_from_cart",
        "description": "Remove a product entirely from the cart (all of its quantity). Do NOT use for 'remove one quantity' or 'reduce by one' — use update_cart_quantity with new quantity = current - 1 instead.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "The product ID to remove.",
                }
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "update_cart_quantity",
        "description": "Set the new quantity for a product in the cart. Use for 'remove one quantity', 'reduce by one', 'take one off' (call get_cart first to get current quantity, then pass quantity = current - 1). Also use to set an exact quantity (e.g. change to 2). Set quantity to 0 to remove the line.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "The product ID (from get_cart).",
                },
                "quantity": {
                    "type": "integer",
                    "description": "New quantity. Use current_quantity - 1 to reduce by one. Set to 0 to remove.",
                },
            },
            "required": ["product_id", "quantity"],
        },
    },
    {
        "name": "clear_cart",
        "description": "Remove all items from the user's shopping cart. Use when the user says 'clear cart', 'empty cart', 'remove everything', 'clear my cart', etc.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


async def get_cart_payload(session_id: str, user_id: Optional[int] = None) -> dict:
    """Return cart as { items: [...], total: float } for a session or user. Used by get_cart tool and GET /api/cart."""
    cart_data = cart.get_cart(session_id, user_id=user_id)
    if not cart_data:
        return {"items": [], "total": 0}
    items = []
    total = 0.0
    for pid, qty in cart_data.items():
        try:
            product = await fake_store.get_product(pid)
            item_total = product["price"] * qty
            total += item_total
            items.append({
                "product_id": pid,
                "title": product["title"],
                "price": product["price"],
                "quantity": qty,
                "item_total": round(item_total, 2),
                "image": product["image"],
            })
        except Exception:
            continue
    return {"items": items, "total": round(total, 2)}


async def execute_tool(
    name: str, input_data: dict, session_id: str, user_id: Optional[int] = None
) -> str:
    """Execute a tool and return the JSON string result. user_id used for cart when authenticated."""
    logger.info("[tools] execute_tool name=%s input=%s session_id=%s user_id=%s", name, input_data, session_id, user_id)

    if name == "search_products":
        query = (input_data.get("query") or "").strip().lower()
        raw_category = (input_data.get("category") or "").strip().lower()
        min_price = input_data.get("min_price")
        max_price = input_data.get("max_price")

        # Intent: map TV / television (and similar) to electronics; API has no "tv" category
        CATEGORY_ALIASES = {
            "tv": "electronics",
            "tvs": "electronics",
            "television": "electronics",
            "televisions": "electronics",
            "monitor": "electronics",
            "monitors": "electronics",
        }
        category = CATEGORY_ALIASES.get(raw_category, raw_category) if raw_category else ""

        if category:
            products = await fake_store.get_products_by_category(category)
        else:
            products = await fake_store.get_all_products()

        # Match: exact phrase OR all query words present in title/description (so "hard drive 3.0" matches)
        def _matches_query(p: dict, q: str) -> bool:
            if not q:
                return True
            title_lower = p["title"].lower()
            desc_lower = (p.get("description") or "").lower()
            if q in title_lower or q in desc_lower:
                return True
            words = [w for w in q.split() if len(w) > 0]
            if len(words) > 1:
                if all(w in title_lower or w in desc_lower for w in words):
                    return True
            if q in ("tv", "tvs", "television", "televisions"):
                if any(kw in title_lower or kw in desc_lower for kw in ("monitor", "display", "screen", "inch", "led", "qled")):
                    return True
            return False

        results = []
        for p in products:
            if query and not _matches_query(p, query):
                continue
            if min_price is not None and p["price"] < min_price:
                continue
            if max_price is not None and p["price"] > max_price:
                continue
            results.append({
                "id": p["id"],
                "title": p["title"],
                "price": p["price"],
                "category": p["category"],
                "image": p["image"],
                "rating": p["rating"],
                "description": p.get("description", ""),
            })
        out = json.dumps({"products": results, "count": len(results)})
        logger.info("[tools] search_products done count=%d", len(results))
        return out

    elif name == "get_product_details":
        product_id = input_data.get("product_id")
        if product_id is None:
            return json.dumps({"error": "Missing required parameter: product_id. You must call get_product_details with a numeric product_id (e.g. from the context of recently shown products)."})
        try:
            product_id = int(product_id)
        except (TypeError, ValueError):
            return json.dumps({"error": "product_id must be a number."})
        product = await fake_store.get_product(product_id)
        logger.info("[tools] get_product_details done product_id=%s", product_id)
        return json.dumps(product)

    elif name == "add_to_cart":
        product_id = input_data.get("product_id")
        if product_id is None:
            return json.dumps({"error": "Missing product_id. To add by product name (e.g. 'add Samsung TV'), first call search_products with that name, then use the product id from the results to call add_to_cart(product_id=...). For 'add the first one', use the first ID from the conversation context (recent product IDs)."})
        try:
            product_id = int(product_id)
        except (TypeError, ValueError):
            return json.dumps({"error": "product_id must be a number."})
        quantity = input_data.get("quantity", 1)
        cart.add_item(session_id, product_id, quantity, user_id=user_id)
        payload = await get_cart_payload(session_id, user_id=user_id)
        logger.info("[tools] add_to_cart done product_id=%s", product_id)
        return json.dumps({"success": True, "cart": payload})

    elif name == "get_cart":
        payload = await get_cart_payload(session_id, user_id=user_id)
        logger.info("[tools] get_cart done items=%d total=%s", len(payload["items"]), payload["total"])
        return json.dumps(payload)

    elif name == "remove_from_cart":
        product_id = input_data.get("product_id")
        if product_id is None:
            return json.dumps({"error": "Missing product_id. When the user asks to remove a specific item by name (e.g. 'remove the laptop'), first call get_cart to see current cart items (each has product_id and title), then call remove_from_cart with the matching product_id."})
        try:
            product_id = int(product_id)
        except (TypeError, ValueError):
            return json.dumps({"error": "product_id must be a number."})
        cart.remove_item(session_id, product_id, user_id=user_id)
        payload = await get_cart_payload(session_id, user_id=user_id)
        logger.info("[tools] remove_from_cart done product_id=%s", product_id)
        return json.dumps({"success": True, "cart": payload})

    elif name == "update_cart_quantity":
        cart.update_quantity(
            session_id, input_data["product_id"], input_data["quantity"], user_id=user_id
        )
        payload = await get_cart_payload(session_id, user_id=user_id)
        return json.dumps({"success": True, "cart": payload})

    elif name == "clear_cart":
        cart.clear_cart(session_id, user_id=user_id)
        payload = await get_cart_payload(session_id, user_id=user_id)
        logger.info("[tools] clear_cart done")
        return json.dumps({"success": True, "cart": payload})

    logger.warning("[tools] unknown tool name=%s", name)
    return json.dumps({"error": f"Unknown tool: {name}"})
