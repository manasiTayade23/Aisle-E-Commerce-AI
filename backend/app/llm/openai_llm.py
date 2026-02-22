"""OpenAI LLM implementation."""

from typing import AsyncGenerator, List, Optional, Dict, Any
import httpx
from openai import AsyncOpenAI
from app.llm.base import BaseLLM, LLMMessage, ToolCall, StreamEvent


def _openai_http_client() -> httpx.AsyncClient:
    """Return an httpx.AsyncClient that does not use 'proxies' (avoids SDK/httpx incompatibility)."""
    return httpx.AsyncClient(timeout=60.0)


class OpenAILLM(BaseLLM):
    """OpenAI implementation."""
    
    def __init__(self, api_key: str, model: str):
        # Pass explicit http_client so the SDK does not pass 'proxies' to httpx.AsyncClient
        # (httpx expects 'proxy', not 'proxies'; SDK's wrapper causes AttributeError on aclose)
        self.client = AsyncOpenAI(
            api_key=api_key,
            http_client=_openai_http_client(),
        )
        self.model = model
    
    async def stream_chat(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat with OpenAI."""
        # Convert messages to OpenAI format
        openai_messages = []
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})
        
        import json as _json
        for msg in messages:
            if isinstance(msg.content, list):
                # OpenAI expects assistant message with top-level tool_calls, then separate "tool" messages.
                # content[] cannot contain type "tool_call" or "tool_result".
                text_parts = []
                tool_calls_for_assistant = []
                tool_results = []
                for item in msg.content:
                    if isinstance(item, dict):
                        if item.get("type") == "tool_use":
                            inp = item.get("input", {})
                            tool_calls_for_assistant.append({
                                "id": item.get("id", ""),
                                "type": "function",
                                "function": {
                                    "name": item.get("name", ""),
                                    "arguments": _json.dumps(inp) if isinstance(inp, dict) else str(inp),
                                },
                            })
                        elif item.get("type") == "tool_result":
                            tool_results.append({
                                "tool_call_id": item.get("tool_use_id", ""),
                                "content": item.get("content", ""),
                            })
                    else:
                        text_parts.append(str(item))
                assistant_content = " ".join(text_parts) if text_parts else ""
                if tool_calls_for_assistant:
                    openai_messages.append({
                        "role": "assistant",
                        "content": assistant_content or None,
                        "tool_calls": tool_calls_for_assistant,
                    })
                    for tr in tool_results:
                        openai_messages.append({
                            "role": "tool",
                            "tool_call_id": tr["tool_call_id"],
                            "content": tr["content"],
                        })
                elif tool_results:
                    # Message is tool results only (e.g. user message with list of tool_result)
                    for tr in tool_results:
                        openai_messages.append({
                            "role": "tool",
                            "tool_call_id": tr["tool_call_id"],
                            "content": tr["content"],
                        })
                else:
                    openai_messages.append({"role": msg.role, "content": assistant_content or ""})
            else:
                openai_messages.append({"role": msg.role, "content": str(msg.content)})
        
        # Convert tools format
        openai_tools = None
        if tools:
            openai_tools = []
            for tool in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("input_schema", {})
                    }
                })
        
        # Track multiple tool calls by index (OpenAI streams one delta per index)
        tool_calls_by_index: Dict[int, Dict[str, Any]] = {}
        
        async for chunk in await self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            tools=openai_tools,
            stream=True,
            **kwargs
        ):
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue
            
            if delta.content:
                yield {
                    "type": StreamEvent.TEXT_DELTA,
                    "content": delta.content,
                }
            
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index if tc.index is not None else 0
                    if idx not in tool_calls_by_index and (tc.id or (tc.function and tc.function.name)):
                        tool_calls_by_index[idx] = {
                            "id": tc.id or "",
                            "name": tc.function.name if tc.function and tc.function.name else "",
                            "input": "",
                        }
                        yield {
                            "type": StreamEvent.TOOL_CALL_START,
                            "id": tool_calls_by_index[idx]["id"],
                            "name": tool_calls_by_index[idx]["name"],
                        }
                    if idx in tool_calls_by_index:
                        if tc.id:
                            tool_calls_by_index[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls_by_index[idx]["name"] = tc.function.name
                            if tc.function.arguments:
                                tool_calls_by_index[idx]["input"] += tc.function.arguments
                                yield {
                                    "type": StreamEvent.TOOL_CALL_DELTA,
                                    "id": tool_calls_by_index[idx]["id"],
                                    "delta": tc.function.arguments,
                                }
            
            # When done, yield TOOL_CALL_END for each tool call in index order
            if chunk.choices and chunk.choices[0].finish_reason == "tool_calls":
                import json
                for idx in sorted(tool_calls_by_index.keys()):
                    cur = tool_calls_by_index[idx]
                    try:
                        parsed_input = json.loads(cur["input"]) if cur["input"] else {}
                    except json.JSONDecodeError:
                        parsed_input = {}
                    yield {
                        "type": StreamEvent.TOOL_CALL_END,
                        "id": cur["id"],
                        "name": cur["name"],
                        "input": parsed_input,
                    }
                tool_calls_by_index.clear()
        
        yield {"type": StreamEvent.DONE}
    
    def get_tool_calls_from_message(self, message: Any) -> List[ToolCall]:
        """Extract tool calls from OpenAI message."""
        tool_calls = []
        if hasattr(message, 'tool_calls'):
            for tc in message.tool_calls:
                import json
                try:
                    args = json.loads(tc.function.arguments) if hasattr(tc.function, 'arguments') else {}
                except json.JSONDecodeError:
                    args = {}
                
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name if hasattr(tc.function, 'name') else "",
                    input=args
                ))
        return tool_calls
    
    def format_tool_result(self, tool_call_id: str, result: str) -> Dict[str, Any]:
        """Format tool result for OpenAI."""
        import json
        try:
            result_data = json.loads(result)
        except json.JSONDecodeError:
            result_data = {"content": result}
        
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": json.dumps(result_data) if isinstance(result_data, dict) else result,
        }
