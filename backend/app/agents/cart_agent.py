"""Cart management agent."""

from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.llm.base import BaseLLM, LLMMessage
from app.tools import TOOL_DEFINITIONS


class CartAgent(BaseAgent):
    """Agent specialized in shopping cart management."""
    
    def __init__(self, llm: BaseLLM):
        super().__init__(
            llm=llm,
            name="Cart Management Agent",
            description=(
                "You specialize in managing shopping carts. "
                "You help users add items, remove items, update quantities, "
                "and view their cart contents. You always confirm actions and "
                "show updated cart totals."
            )
        )
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get cart-related tools."""
        return [
            tool for tool in TOOL_DEFINITIONS 
            if tool["name"] in ["add_to_cart", "get_cart", "remove_from_cart", "update_cart_quantity"]
        ]
    
    def get_system_prompt(self) -> str:
        base = super().get_system_prompt()
        return f"""{base}

## Your Responsibilities:
- Add products to cart with correct quantities
- Remove items when requested
- Update quantities accurately
- Always show cart total after modifications
- Confirm all cart actions clearly

## Cart Guidelines:
- Always verify product IDs before adding/removing
- Default quantity is 1 if not specified
- Show itemized breakdown of cart contents
- Calculate and display total price
- Handle edge cases (removing non-existent items, etc.)

## Resolving references from conversation:
- If the user says "add the cheaper one", "the first one", "the second product", etc., use the **previous assistant message** in this conversation. It may end with "[Products listed above, in order: ID X, ID Y, ...]" — use that order (first = first ID, second = second ID). For "cheaper one", use the product with the lower price from the comparison or list (you may call get_product_details to confirm prices if needed).
- Always call add_to_cart with the resolved numeric product_id (and optional quantity). Never guess IDs; use conversation context or get_product_details.
"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process cart management request."""
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
