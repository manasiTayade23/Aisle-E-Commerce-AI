"""OpenAI LLM implementation."""

from typing import AsyncGenerator, List, Optional, Dict, Any
from openai import AsyncOpenAI
from app.llm.base import BaseLLM, LLMMessage, ToolCall, StreamEvent


class OpenAILLM(BaseLLM):
    """OpenAI implementation."""
    
    def __init__(self, api_key: str, model: str):
        self.client = AsyncOpenAI(api_key=api_key)
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
        
        for msg in messages:
            if isinstance(msg.content, list):
                # Handle tool results
                content = []
                for item in msg.content:
                    if isinstance(item, dict):
                        if item.get("type") == "tool_use":
                            content.append({
                                "type": "tool_call",
                                "id": item.get("id", ""),
                                "name": item.get("name", ""),
                                "arguments": str(item.get("input", {}))
                            })
                        elif item.get("type") == "tool_result":
                            content.append({
                                "type": "tool_result",
                                "tool_call_id": item.get("tool_use_id", ""),
                                "content": item.get("content", "")
                            })
                    else:
                        content.append({"type": "text", "text": str(item)})
                openai_messages.append({"role": msg.role, "content": content})
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
        
        current_tool_call = None
        
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
                for tool_call in delta.tool_calls:
                    if tool_call.index is not None:
                        if tool_call.id and not current_tool_call:
                            current_tool_call = {
                                "id": tool_call.id,
                                "name": tool_call.function.name if tool_call.function else "",
                                "input": "",
                            }
                            yield {
                                "type": StreamEvent.TOOL_CALL_START,
                                "id": tool_call.id,
                                "name": tool_call.function.name if tool_call.function else "",
                            }
                        
                        if tool_call.function:
                            if tool_call.function.arguments:
                                if current_tool_call:
                                    current_tool_call["input"] += tool_call.function.arguments
                                    yield {
                                        "type": StreamEvent.TOOL_CALL_DELTA,
                                        "id": current_tool_call["id"],
                                        "delta": tool_call.function.arguments,
                                    }
            
            # Check if tool call is complete
            if current_tool_call and chunk.choices and chunk.choices[0].finish_reason == "tool_calls":
                import json
                try:
                    parsed_input = json.loads(current_tool_call["input"])
                except json.JSONDecodeError:
                    parsed_input = {}
                
                yield {
                    "type": StreamEvent.TOOL_CALL_END,
                    "id": current_tool_call["id"],
                    "name": current_tool_call["name"],
                    "input": parsed_input,
                }
                current_tool_call = None
        
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
