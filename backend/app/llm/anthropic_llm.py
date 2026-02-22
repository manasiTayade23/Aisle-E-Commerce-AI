"""Anthropic Claude LLM implementation."""

from typing import AsyncGenerator, List, Optional, Dict, Any
from anthropic import AsyncAnthropic
from app.llm.base import BaseLLM, LLMMessage, ToolCall, StreamEvent
from app.config import LLM_MAX_TOKENS


class AnthropicLLM(BaseLLM):
    """Anthropic Claude implementation."""
    
    def __init__(self, api_key: str, model: str):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
    
    async def stream_chat(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat with Claude."""
        # Convert messages to Anthropic format
        anthropic_messages = []
        for msg in messages:
            if isinstance(msg.content, list):
                # Handle tool results
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        current_tool_call = None
        tool_input_buffer = ""
        
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", LLM_MAX_TOKENS),
            system=system_prompt,
            tools=tools or [],
            messages=anthropic_messages,
        ) as stream:
            async for event in stream:
                if event.type == "content_block_start":
                    if hasattr(event, 'content_block'):
                        if event.content_block.type == "text":
                            pass  # Text will come as deltas
                        elif event.content_block.type == "tool_use":
                            current_tool_call = {
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                                "input": "",
                            }
                            yield {
                                "type": StreamEvent.TOOL_CALL_START,
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                            }
                
                elif event.type == "content_block_delta":
                    if hasattr(event, 'delta'):
                        if event.delta.type == "text_delta":
                            yield {
                                "type": StreamEvent.TEXT_DELTA,
                                "content": event.delta.text,
                            }
                        elif event.delta.type == "input_json_delta":
                            if current_tool_call:
                                tool_input_buffer += event.delta.partial_json
                                yield {
                                    "type": StreamEvent.TOOL_CALL_DELTA,
                                    "id": current_tool_call["id"],
                                    "delta": event.delta.partial_json,
                                }
                
                elif event.type == "content_block_stop":
                    if current_tool_call:
                        import json
                        try:
                            parsed_input = json.loads(tool_input_buffer) if tool_input_buffer else {}
                        except json.JSONDecodeError:
                            parsed_input = {}
                        
                        yield {
                            "type": StreamEvent.TOOL_CALL_END,
                            "id": current_tool_call["id"],
                            "name": current_tool_call["name"],
                            "input": parsed_input,
                        }
                        current_tool_call = None
                        tool_input_buffer = ""
        
        yield {"type": StreamEvent.DONE}
    
    def get_tool_calls_from_message(self, message: Any) -> List[ToolCall]:
        """Extract tool calls from Anthropic message."""
        tool_calls = []
        if isinstance(message, dict) and "content" in message:
            content = message["content"]
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_calls.append(ToolCall(
                            id=block["id"],
                            name=block["name"],
                            input=block.get("input", {})
                        ))
        return tool_calls
    
    def format_tool_result(self, tool_call_id: str, result: str) -> Dict[str, Any]:
        """Format tool result for Anthropic."""
        import json
        try:
            result_data = json.loads(result)
        except json.JSONDecodeError:
            result_data = {"content": result}
        
        return {
            "type": "tool_result",
            "tool_use_id": tool_call_id,
            "content": json.dumps(result_data) if isinstance(result_data, dict) else result,
        }
