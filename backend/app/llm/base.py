"""Base LLM interface for LLM-agnostic agent framework."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any, Dict, List, Optional
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENAI = "openai"


class LLMMessage:
    """Standardized message format."""
    def __init__(self, role: str, content: Any):
        self.role = role
        self.content = content
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {"role": self.role, "content": self.content}


class ToolCall:
    """Standardized tool call format."""
    def __init__(self, id: str, name: str, input: Dict[str, Any]):
        self.id = id
        self.name = name
        self.input = input


class StreamEvent:
    """Streaming event types."""
    TEXT_DELTA = "text_delta"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_DELTA = "tool_call_delta"
    TOOL_CALL_END = "tool_call_end"
    DONE = "done"
    ERROR = "error"


class BaseLLM(ABC):
    """Base class for LLM implementations."""
    
    @abstractmethod
    async def stream_chat(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream chat completion with tool support.
        
        Yields events with structure:
        - {"type": "text_delta", "content": str}
        - {"type": "tool_call_start", "id": str, "name": str}
        - {"type": "tool_call_delta", "id": str, "delta": str}
        - {"type": "tool_call_end", "id": str, "name": str, "input": dict}
        - {"type": "done"}
        """
        pass
    
    @abstractmethod
    def get_tool_calls_from_message(self, message: Any) -> List[ToolCall]:
        """Extract tool calls from a message object."""
        pass
    
    @abstractmethod
    def format_tool_result(self, tool_call_id: str, result: str) -> Any:
        """Format tool result for the LLM."""
        pass
