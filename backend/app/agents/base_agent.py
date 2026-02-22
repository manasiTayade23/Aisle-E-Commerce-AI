"""Base agent class for LangGraph agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.llm.base import BaseLLM, LLMMessage


class BaseAgent(ABC):
    """Base class for specialized agents."""
    
    def __init__(self, llm: BaseLLM, name: str, description: str):
        self.llm = llm
        self.name = name
        self.description = description
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the current state and return updated state."""
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get tools available to this agent."""
        pass
    
    def get_system_prompt(self) -> str:
        """Get system prompt for this agent."""
        return f"You are {self.name}. {self.description}"
