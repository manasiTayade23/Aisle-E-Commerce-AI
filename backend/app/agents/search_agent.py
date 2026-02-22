"""Search agent for product discovery and search."""

import logging
from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.llm.base import BaseLLM, LLMMessage
from app.tools import TOOL_DEFINITIONS

logger = logging.getLogger(__name__)


class SearchAgent(BaseAgent):
    """Agent specialized in product search and discovery."""
    
    def __init__(self, llm: BaseLLM):
        super().__init__(
            llm=llm,
            name="Product Search Agent",
            description=(
                "You specialize in helping users find products. "
                "You understand natural language queries and can search by keywords, "
                "categories, price ranges, and other filters. "
                "You provide clear, organized product listings with key information."
            )
        )
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get search-related tools."""
        return [
            tool for tool in TOOL_DEFINITIONS 
            if tool["name"] in ["search_products", "get_product_details"]
        ]
    
    def get_system_prompt(self) -> str:
        base = super().get_system_prompt()
        return f"""{base}

## Your Responsibilities:
- Understand user search intent from natural language
- Use search_products tool with appropriate filters
- Present results in a clear, organized manner
- Highlight key product features (price, rating, category)
- Suggest refinements if results are too broad or narrow

## Search Guidelines:
- Extract keywords, categories, and price ranges from user queries
- Use fuzzy matching for product names
- Group similar products together
- Always show product IDs for reference
"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process search request."""
        import json
        from app.tools import execute_tool
        
        user_message = state.get("user_message", "")
        messages = state.get("messages", [])
        session_id = state.get("session_id", "")
        
        # Add user message
        messages.append(LLMMessage(role="user", content=user_message))
        
        # Stream response with tool calls
        response_text = ""
        tool_calls = []
        assistant_content = []
        
        # First LLM call - may include tool calls
        async for event in self.llm.stream_chat(
            messages=messages,
            system_prompt=self.get_system_prompt(),
            tools=self.get_tools(),
        ):
            if event.get("type") == "text_delta":
                response_text += event.get("content", "")
            elif event.get("type") == "tool_call_end":
                tool_calls.append(event)
                assistant_content.append({
                    "type": "tool_use",
                    "id": event.get("id"),
                    "name": event.get("name"),
                    "input": event.get("input", {}),
                })

        logger.info("[search_agent] first LLM call done response_text_len=%d tool_calls_count=%d", len(response_text), len(tool_calls))

        # Execute tools if any
        if tool_calls:
            tool_results = []
            for idx, tool_call in enumerate(tool_calls):
                tool_name = tool_call.get("name")
                tool_input = tool_call.get("input", {})
                logger.info("[search_agent] executing tool[%d] name=%s input=%s", idx, tool_name, tool_input)
                # Execute tool
                result = await execute_tool(tool_name, tool_input, session_id)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.get("id"),
                    "name": tool_name,
                    "content": result,
                })
            
            # Add tool results to messages
            messages.append(LLMMessage(role="assistant", content=assistant_content))
            messages.append(LLMMessage(role="user", content=tool_results))

            logger.info("[search_agent] second LLM call (with tool results)")
            # Second LLM call with tool results
            final_response = ""
            async for event in self.llm.stream_chat(
                messages=messages,
                system_prompt=self.get_system_prompt(),
                tools=self.get_tools(),
            ):
                if event.get("type") == "text_delta":
                    final_response += event.get("content", "")

            response_text = final_response if final_response else response_text
            logger.info("[search_agent] second LLM call done final_response_len=%d response_text_len=%d", len(final_response), len(response_text))

        messages.append(LLMMessage(role="assistant", content=response_text))

        logger.info("[search_agent] returning state agent=%s response_len=%d tool_calls_count=%d", self.name, len(response_text), len(tool_calls))
        return {
            **state,
            "messages": messages,
            "response": response_text,
            "tool_calls": tool_calls,
            "agent": self.name,
        }
