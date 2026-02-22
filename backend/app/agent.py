"""Claude-based conversational shopping agent with streaming support."""

from __future__ import annotations

import json
from typing import AsyncGenerator
from anthropic import AsyncAnthropic
from app.config import ANTHROPIC_API_KEY, MODEL_NAME
from app.tools import TOOL_DEFINITIONS, execute_tool

client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

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

## Formatting
- Use markdown for formatting responses
- Format prices as $XX.XX
- Use bullet points for lists
- Use bold for product names and important info
- When displaying multiple products, use a consistent card-like format
"""

# Store conversation history per session
_conversations: dict[str, list[dict]] = {}


def _get_messages(session_id: str) -> list[dict]:
    return _conversations.setdefault(session_id, [])


async def stream_response(session_id: str, user_message: str) -> AsyncGenerator[str, None]:
    """Stream the agent's response, handling tool calls in a loop."""
    messages = _get_messages(session_id)
    messages.append({"role": "user", "content": user_message})

    while True:
        # Stream from Claude
        collected_content = []
        current_text = ""
        tool_uses = []

        async with client.messages.stream(
            model=MODEL_NAME,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        ) as stream:
            async for event in stream:
                if event.type == "content_block_start":
                    if event.content_block.type == "text":
                        current_text = ""
                    elif event.content_block.type == "tool_use":
                        tool_uses.append({
                            "id": event.content_block.id,
                            "name": event.content_block.name,
                            "input_json": "",
                        })
                elif event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        current_text += event.delta.text
                        yield json.dumps({"type": "text", "content": event.delta.text}) + "\n"
                    elif event.delta.type == "input_json_delta":
                        if tool_uses:
                            tool_uses[-1]["input_json"] += event.delta.partial_json
                elif event.type == "content_block_stop":
                    if current_text:
                        collected_content.append({"type": "text", "text": current_text})
                        current_text = ""

            final_message = await stream.get_final_message()

        # Build assistant message content
        assistant_content = []
        for block in collected_content:
            assistant_content.append(block)
        for tu in tool_uses:
            try:
                parsed_input = json.loads(tu["input_json"]) if tu["input_json"] else {}
            except json.JSONDecodeError:
                parsed_input = {}
            assistant_content.append({
                "type": "tool_use",
                "id": tu["id"],
                "name": tu["name"],
                "input": parsed_input,
            })

        messages.append({"role": "assistant", "content": assistant_content})

        # If there are no tool uses, we're done
        if not tool_uses:
            break

        # Execute tools and add results
        tool_results = []
        for tu in tool_uses:
            try:
                parsed_input = json.loads(tu["input_json"]) if tu["input_json"] else {}
            except json.JSONDecodeError:
                parsed_input = {}

            yield json.dumps({"type": "tool_call", "name": tu["name"], "input": parsed_input}) + "\n"

            result = await execute_tool(tu["name"], parsed_input, session_id)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu["id"],
                "content": result,
            })

            # Send tool result data to frontend for rendering
            try:
                result_data = json.loads(result)
                yield json.dumps({"type": "tool_result", "name": tu["name"], "data": result_data}) + "\n"
            except json.JSONDecodeError:
                pass

        messages.append({"role": "user", "content": tool_results})

    # Trim conversation history to last 40 messages to avoid token overflow
    if len(messages) > 40:
        _conversations[session_id] = messages[-40:]

    yield json.dumps({"type": "done"}) + "\n"
