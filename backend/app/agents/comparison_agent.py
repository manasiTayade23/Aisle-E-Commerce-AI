"""Product comparison agent."""

import json
import logging
from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.llm.base import BaseLLM, LLMMessage
from app.tools import TOOL_DEFINITIONS

logger = logging.getLogger(__name__)


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
    
    def get_system_prompt(self, state: Dict[str, Any] = None) -> str:
        base = super().get_system_prompt()
        prompt = f"""{base}

## Your Responsibilities:
- Compare multiple products side by side (e.g. "compare the first two", "compare these")
- Highlight key differences (price, features, ratings)
- Identify pros and cons for each product
- Provide recommendations based on user needs
- Present comparisons in a structured, easy-to-read format

## Comparison Guidelines:
- When the user says "compare the first two", "compare these", "compare items 1 and 2", or similar, use the product IDs from the PREVIOUS assistant message or from the context below. The previous message may end with "[Products listed above, in order: ID X, ID Y, ...]". Use those IDs.
- Call get_product_details(product_id) for EACH product you need to compare (e.g. get_product_details(9) and get_product_details(10)), then write a comparison. Do NOT call search_products when the user wants to compare items already shown. You MUST pass a numeric product_id to every get_product_details call.
- Always fetch full product details for accurate comparison
- Compare on multiple dimensions: price, rating, category, features
- Use tables or structured lists for clarity
- Provide actionable insights, not just data
- You must ALWAYS respond with a clear, helpful message to the user. If a tool returns an error (e.g. missing product_id), explain what went wrong and suggest next steps (e.g. "Please search for products first, then say 'compare the last two'").
"""
        recent_ids = (state or {}).get("recent_product_ids") or []
        if recent_ids:
            ids_str = ", ".join(str(pid) for pid in recent_ids)
            prompt += f"""

## CRITICAL — Recent product IDs (use these for "last N" or "first two"):
The user was recently shown these product IDs in order: {ids_str}.
"""
            if len(recent_ids) >= 2:
                prompt += f"- For \"compare last 2 products\" you MUST call get_product_details with product_id={recent_ids[-2]} and get_product_details with product_id={recent_ids[-1]} (the last two in the list).\n"
            prompt += "- Never call get_product_details without one of these numeric product_id values.\n"
        return prompt

    def _user_message_with_context(self, state: Dict[str, Any]) -> str:
        """Build user message, prefixing recent product IDs context when available."""
        user_message = state.get("user_message", "")
        recent_ids = state.get("recent_product_ids") or []
        if not recent_ids:
            return user_message
        ids_str = ", ".join(str(pid) for pid in recent_ids)
        return (
            f"Context: The user was recently shown these product IDs in order: {ids_str}. "
            "When they say 'last N products', 'the first two', 'compare the last two', etc., "
            "call get_product_details(product_id) for each product you need (e.g. the last 2 = these IDs). "
            "You must pass the numeric product_id for each call.\n\n"
            f"User request: {user_message}"
        )

    async def _prefetch_last_two_and_inject(self, state: Dict[str, Any]) -> str:
        """When user wants 'compare last 2', fetch those two products and return enriched user message so LLM can respond with text only."""
        user_message = (state.get("user_message") or "").strip().lower()
        recent_ids = state.get("recent_product_ids") or []
        if len(recent_ids) < 2:
            return self._user_message_with_context(state)
        if "compare" not in user_message or ("last 2" not in user_message and "last two" not in user_message):
            return self._user_message_with_context(state)
        from app.tools import execute_tool
        import json
        session_id = state.get("session_id", "")
        id1, id2 = recent_ids[-2], recent_ids[-1]
        try:
            r1 = await execute_tool("get_product_details", {"product_id": id1}, session_id)
            r2 = await execute_tool("get_product_details", {"product_id": id2}, session_id)
            d1 = json.loads(r1) if isinstance(r1, str) else r1
            d2 = json.loads(r2) if isinstance(r2, str) else r2
            if d1.get("error") or d2.get("error"):
                return self._user_message_with_context(state)
        except Exception as e:
            logger.warning("[comparison_agent] pre-fetch failed: %s", e)
            return self._user_message_with_context(state)
        # Inject full details so the model can write the comparison without calling tools
        base = state.get("user_message", "")
        return (
            "The following two products have already been fetched. Write a clear comparison for the user. Do not call any tools.\n\n"
            f"**Product 1 (ID {id1}):** {json.dumps(d1, indent=2)}\n\n"
            f"**Product 2 (ID {id2}):** {json.dumps(d2, indent=2)}\n\n"
            f"User request: {base}"
        )

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process comparison request."""
        import json
        from app.tools import execute_tool
        
        user_message = await self._prefetch_last_two_and_inject(state)
        messages = state.get("messages", [])
        session_id = state.get("session_id", "")
        
        messages.append(LLMMessage(role="user", content=user_message))
        
        response_text = ""
        tool_calls = []
        assistant_content = []
        
        system_prompt = self.get_system_prompt(state)
        # When we pre-fetched product details, no tools so model only writes comparison text
        use_tools = None if user_message.startswith("The following two products have already been fetched.") else self.get_tools()
        async for event in self.llm.stream_chat(
            messages=messages,
            system_prompt=system_prompt,
            tools=use_tools,
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
        tool_results_for_graph = []
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
                try:
                    tool_results_for_graph.append({"name": tool_name, "data": json.loads(result)})
                except (TypeError, json.JSONDecodeError):
                    tool_results_for_graph.append({"name": tool_name, "data": {"raw": result}})
            
            messages.append(LLMMessage(role="assistant", content=assistant_content))
            messages.append(LLMMessage(role="user", content=tool_results))
            
            # Get final response (must always get a helpful reply, especially after tool errors)
            final_response = ""
            async for event in self.llm.stream_chat(
                messages=messages,
                system_prompt=system_prompt,
                tools=use_tools,
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
            "tool_results": tool_results_for_graph,
            "agent": self.name,
        }
