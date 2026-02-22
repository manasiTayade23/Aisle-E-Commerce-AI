"""Per-session conversation persistence. Uses Redis when REDIS_URL is set, else in-memory."""

from __future__ import annotations

import json
import logging
from typing import List

from app.config import REDIS_URL, CONVERSATION_TTL_SECONDS

logger = logging.getLogger(__name__)

# In-memory fallback when Redis is not configured
_memory: dict[str, list[dict]] = {}

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not REDIS_URL:
        return None
    try:
        import redis.asyncio as redis
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        return _redis_client
    except Exception as e:
        logger.warning("Redis not available, using in-memory store: %s", e)
        return None


def _key(session_id: str) -> str:
    return f"shopai:conv:{session_id}"


async def get_messages(session_id: str) -> List[dict]:
    """Get conversation messages for a session."""
    r = _get_redis()
    if r is None:
        return _memory.get(session_id, []).copy()
    try:
        raw = await r.get(_key(session_id))
        if not raw:
            return []
        return json.loads(raw)
    except Exception as e:
        logger.warning("Redis get_messages failed: %s", e)
        return _memory.get(session_id, []).copy()


async def set_messages(session_id: str, messages: List[dict]) -> None:
    """Store conversation messages for a session."""
    r = _get_redis()
    if r is None:
        _memory[session_id] = messages[-40:] if len(messages) > 40 else messages.copy()
        return
    try:
        to_store = messages[-40:] if len(messages) > 40 else messages
        await r.setex(
            _key(session_id),
            CONVERSATION_TTL_SECONDS,
            json.dumps(to_store),
        )
    except Exception as e:
        logger.warning("Redis set_messages failed: %s", e)
        _memory[session_id] = messages[-40:] if len(messages) > 40 else messages.copy()


async def append_messages(session_id: str, new_messages: List[dict]) -> List[dict]:
    """Append messages and trim to last 40. Returns the updated list."""
    messages = await get_messages(session_id)
    messages.extend(new_messages)
    if len(messages) > 40:
        messages = messages[-40:]
    await set_messages(session_id, messages)
    return messages
