"""Product comparison agent."""

from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.llm.base import BaseLLM, LLMMessage
from app.tools import TOOL_DEFINITIONS


class ComparisonAgent(BaseAgent):
    """Agent specialized in product comparison."""
    
    def __init__(self, llm: BaseLLM):
        super().__init__(
            llm=llm,
            name="Product Comparison Agent",
            description=(
                "You specialize in comparing products side by side. "
                "You help users understand differences between products, "
                "highlight pros and cons, and make informed decisions."
            )
        )
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get comparison-related tools."""
        return [
            tool for tool in TOOL_DEFINITIONS 
            if tool["name"] in ["get_product_details", "search_products"]
        ]
    
    def get_system_prompt(self) -> str:
        base = super().get_system_prompt()
        return f"""{base}

## Your Responsibilities:
- Compare multiple products side by side (e.g. "compare the first two", "compare these")
- Highlight key differences (price, features, ratings)
- Identify pros and cons for each product
- Provide recommendations based on user needs
- Present comparisons in a structured, easy-to-read format

## Comparison Guidelines:
- When the user says "compare the first two", "compare these", "compare items 1 and 2", or similar, use the product IDs from the PREVIOUS assistant message. The previous message may end with "[Products listed above, in order: ID X, ID Y, ...]". Use those IDs.
- Call get_product_details(product_id) for EACH product you need to compare (e.g. get_product_details for ID 9 and get_product_details for ID 10), then write a comparison. Do NOT call search_products when the user wants to compare items already shown.
- Always fetch full product details for accurate comparison
- Compare on multiple dimensions: price, rating, category, features
- Use tables or structured lists for clarity
- Provide actionable insights, not just data
"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process comparison request."""
        import json
        from app.tools import execute_tool
        
        user_message = state.get("user_message", "")
        messages = state.get("messages", [])
        session_id = state.get("session_id", "")
        
        messages.append(LLMMessage(role="user", content=user_message))
        
        response_text = ""
        tool_calls = []
        assistant_content = []
        
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
        
        # Execute tools
        if tool_calls:
            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                tool_input = tool_call.get("input", {})
                result = await execute_tool(tool_name, tool_input, session_id)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.get("id"),
                    "name": tool_name,
                    "content": result,
                })
            
            messages.append(LLMMessage(role="assistant", content=assistant_content))
            messages.append(LLMMessage(role="user", content=tool_results))
            
            # Get final response
            final_response = ""
            async for event in self.llm.stream_chat(
                messages=messages,
                system_prompt=self.get_system_prompt(),
                tools=self.get_tools(),
            ):
                if event.get("type") == "text_delta":
                    final_response += event.get("content", "")
            
            response_text = final_response if final_response else response_text
        
        messages.append(LLMMessage(role="assistant", content=response_text))
        
        return {
            **state,
            "messages": messages,
            "response": response_text,
            "tool_calls": tool_calls,
            "agent": self.name,
        }
