"""LLM-agnostic conversational shopping agent with LangGraph multi-agent support."""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator
from app.config import LLM_PROVIDER
from app.graph import ShoppingGraph
from app.tools import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger(__name__)

# Initialize graph (lazy initialization)
_graph_instance = None

SYSTEM_PROMPT = """You are a friendly and knowledgeable e-commerce shopping assistant. You help users discover products, compare items, and manage their shopping cart through natural conversation.

## Your Capabilities
- Search and filter products by keyword, category, and price range
- Show detailed product information
- Compare products side by side
- Add/remove items from the shopping cart
- Show cart contents and totals

## Available Categories
- electronics
- jewelery
- men's clothing
- women's clothing

## Response Guidelines
1. When showing products, present them in a clear, structured format with key details (name, price, rating).
2. When comparing products, create a structured comparison highlighting differences.
3. When modifying the cart, always confirm the action and show the updated state.
4. Keep responses concise but informative.
5. If the user's request is ambiguous, ask for clarification.
6. Use the tools available to you — always call the appropriate tool rather than guessing product data.
7. When referencing products from previous results, use the correct product IDs.
8. After showing a list or comparison, you may suggest short follow-ups (e.g. "You can say 'Add the cheaper one to my cart' or 'Compare the first two'") to make the next step obvious.

## Formatting
- Use markdown for formatting responses
- Format prices as $XX.XX
- Use bullet points for lists
- Use bold for product names and important info
- When displaying multiple products, use a consistent card-like format
"""

from app.conversation_store import get_messages as store_get_messages, append_messages as store_append_messages


def _get_graph() -> ShoppingGraph:
    """Get or create graph instance."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = ShoppingGraph(llm_provider=LLM_PROVIDER)
    return _graph_instance


async def stream_response(session_id: str, user_message: str) -> AsyncGenerator[str, None]:
    """Stream the agent's response using LangGraph multi-agent system."""
    logger.info("[agent] stream_response called session_id=%s user_message=%r", session_id, user_message[:60] if len(user_message) > 60 else user_message)
    messages = await store_get_messages(session_id)
    logger.info("[agent] conversation history length=%d", len(messages))

    # Get graph instance
    graph = _get_graph()
    logger.info("[agent] got graph, calling graph.stream_response")

    # Convert messages to LLMMessage format for graph
    conversation_history = []
    for msg in messages:
        from app.llm.base import LLMMessage
        conversation_history.append(LLMMessage(
            role=msg.get("role", "user"),
            content=msg.get("content", "")
        ))

    # Stream response and accumulate for conversation history
    response_text = ""
    product_ids_from_search = []
    async for chunk in graph.stream_response(session_id, user_message, conversation_history):
        yield chunk
        # Parse chunk to persist context for follow-up (e.g. "compare the first two")
        try:
            line = chunk.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get("type") == "text":
                response_text += obj.get("content", "")
            elif obj.get("type") == "tool_result" and obj.get("name") == "search_products":
                data = obj.get("data") or {}
                products = data.get("products") or []
                product_ids_from_search = [p.get("id") for p in products if p.get("id") is not None]
        except (json.JSONDecodeError, TypeError):
            pass

    logger.info("[agent] graph.stream_response finished, updating conversation history")
    assistant_content = response_text
    if product_ids_from_search:
        ids_ctx = ", ".join(f"ID {pid}" for pid in product_ids_from_search)
        assistant_content = response_text + f"\n\n[Products listed above, in order: {ids_ctx}]"
    messages = await store_append_messages(session_id, [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": assistant_content},
    ])
    logger.info("[agent] stream_response done messages_count=%d", len(messages))
