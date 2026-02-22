"""Google Gemini LLM implementation."""

import logging
from typing import AsyncGenerator, List, Optional, Dict, Any
import google.generativeai as genai
from app.llm.base import BaseLLM, LLMMessage, ToolCall, StreamEvent

logger = logging.getLogger(__name__)

# User-friendly message when Gemini free-tier quota is exceeded (429).
# Note: API key from AI Studio uses free tier; GCP $300 credit applies to Vertex AI, not this API.
GEMINI_QUOTA_MESSAGE = (
    "Gemini rate limit or quota exceeded (free tier). "
    "Try: (1) Use GEMINI_MODEL=gemini-1.5-flash in .env (often has quota), "
    "(2) wait a minute and retry, or (3) use another provider (LLM_PROVIDER=anthropic or openai). "
    "GCP free credit applies when using Vertex AI, not the AI Studio API key."
)


def _is_quota_exhausted(e: Exception) -> bool:
    """True if this is a 429 / quota exceeded error from Gemini."""
    msg = str(e).lower()
    if "429" in msg or "quota" in msg or "resourceexhausted" in msg or "rate limit" in msg:
        return True
    try:
        from google.api_core.exceptions import ResourceExhausted
        return type(e).__name__ == "ResourceExhausted" or isinstance(e, ResourceExhausted)
    except ImportError:
        return False


def _schema_for_gemini(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Remove fields Gemini does not accept (e.g. default) from JSON schema."""
    if not schema:
        return {"type": "object", "properties": {}}
    out = {"type": schema.get("type", "object"), "properties": {}}
    for k, v in (schema.get("properties") or {}).items():
        if isinstance(v, dict):
            v = {kk: vv for kk, vv in v.items() if kk not in ("default",)}
            out["properties"][k] = v
    if schema.get("required"):
        out["required"] = schema["required"]
    return out


def _tools_to_gemini_format(tools: Optional[List[Dict[str, Any]]]) -> Optional[Any]:
    """Convert our tool definitions (name, description, input_schema) to Gemini Tool with FunctionDeclarations."""
    if not tools:
        return None
    declarations = []
    for t in tools:
        params = _schema_for_gemini(t.get("input_schema") or {})
        decl = genai.types.FunctionDeclaration(
            name=t.get("name", ""),
            description=t.get("description", ""),
            parameters=params,
        )
        declarations.append(decl)
    return [genai.types.Tool(function_declarations=declarations)]


class GeminiLLM(BaseLLM):
    """Google Gemini implementation."""
    
    def __init__(self, api_key: str, model: str):
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)
    
    async def stream_chat(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat with Gemini."""
        # Convert messages to Gemini format
        chat_history = []
        for msg in messages:
            if msg.role == "user":
                chat_history.append({"role": "user", "parts": [str(msg.content)]})
            elif msg.role == "assistant":
                if isinstance(msg.content, list):
                    # Handle tool results
                    parts = []
                    for item in msg.content:
                        if isinstance(item, dict):
                            if item.get("type") == "tool_use":
                                parts.append({
                                    "function_call": {
                                        "name": item["name"],
                                        "args": item.get("input") or {}
                                    }
                                })
                            elif item.get("type") == "tool_result":
                                # Gemini expects function_response with name and response (dict or string)
                                content = item.get("content", "")
                                if isinstance(content, str):
                                    try:
                                        import json
                                        content = json.loads(content)
                                    except Exception:
                                        content = {"result": content}
                                parts.append({
                                    "function_response": {
                                        "name": item.get("name", item.get("tool_use_id", "")),
                                        "response": content
                                    }
                                })
                        else:
                            parts.append(str(item))
                    chat_history.append({"role": "model", "parts": parts})
                else:
                    chat_history.append({"role": "model", "parts": [str(msg.content)]})
        
        # Start chat session
        chat = self.model.start_chat(history=chat_history)
        
        # Prepare prompt
        user_message = messages[-1].content if messages else ""
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{user_message}"
        else:
            full_prompt = user_message
        
        # Convert tools to Gemini format (FunctionDeclaration + Tool)
        gemini_tools = _tools_to_gemini_format(tools)

        # With tools, use non-streaming: Gemini returns function_call reliably in full response only
        try:
            if gemini_tools:
                response = await chat.send_message_async(
                    full_prompt,
                    stream=False,
                    tools=gemini_tools,
                )
                # Single response: parse candidates[0].content.parts
                if response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, "content") and candidate.content:
                        parts = getattr(candidate.content, "parts", None) or []
                        for i, part in enumerate(parts):
                            if hasattr(part, "text") and part.text:
                                yield {"type": StreamEvent.TEXT_DELTA, "content": part.text}
                            elif hasattr(part, "function_call") and part.function_call:
                                fc = part.function_call
                                args = getattr(fc, "args", None)
                                if not isinstance(args, dict):
                                    args = dict(args) if args else {}
                                else:
                                    args = args or {}
                                call_id = f"call_{getattr(fc, 'name', '')}_{i}"
                                name = getattr(fc, "name", "")
                                yield {"type": StreamEvent.TOOL_CALL_START, "id": call_id, "name": name}
                                yield {"type": StreamEvent.TOOL_CALL_END, "id": call_id, "name": name, "input": args}
            else:
                # No tools: stream normally
                response = await chat.send_message_async(full_prompt, stream=True)
                async for chunk in response:
                    if not chunk.candidates:
                        continue
                    candidate = chunk.candidates[0]
                    if not hasattr(candidate, "content") or not candidate.content:
                        continue
                    for part in (getattr(candidate.content, "parts", None) or []):
                        if hasattr(part, "text") and part.text:
                            yield {"type": StreamEvent.TEXT_DELTA, "content": part.text}
                        elif hasattr(part, "function_call") and part.function_call:
                            fc = part.function_call
                            args = getattr(fc, "args", None) or {}
                            if not isinstance(args, dict):
                                args = dict(args) if args else {}
                            call_id = f"call_{getattr(fc, 'name', '')}_0"
                            name = getattr(fc, "name", "")
                            yield {"type": StreamEvent.TOOL_CALL_START, "id": call_id, "name": name}
                            yield {"type": StreamEvent.TOOL_CALL_END, "id": call_id, "name": name, "input": args}
        except Exception as e:
            if _is_quota_exhausted(e):
                logger.warning("[gemini] quota exceeded (429): %s", e)
                yield {"type": StreamEvent.ERROR, "content": GEMINI_QUOTA_MESSAGE}
            else:
                logger.exception("[gemini] stream_chat error")
                yield {"type": StreamEvent.ERROR, "content": str(e)}

        yield {"type": StreamEvent.DONE}
    
    def get_tool_calls_from_message(self, message: Any) -> List[ToolCall]:
        """Extract tool calls from Gemini message."""
        tool_calls = []
        if hasattr(message, 'candidates'):
            for candidate in message.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call'):
                            tool_calls.append(ToolCall(
                                id=f"call_{len(tool_calls)}",
                                name=part.function_call.name,
                                input=dict(part.function_call.args) if hasattr(part.function_call, 'args') else {}
                            ))
        return tool_calls
    
    def format_tool_result(self, tool_call_id: str, result: str) -> Dict[str, Any]:
        """Format tool result for Gemini."""
        import json
        try:
            result_data = json.loads(result)
        except json.JSONDecodeError:
            result_data = {"content": result}
        
        return {
            "type": "function_response",
            "name": tool_call_id,
            "response": result_data,
        }
