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
- Use search_products to find products, then use get_product_details when the user asks about a single product.
- Return only ONE short title line (e.g. "Here are some electronics.", "Here’s the product you asked about.", "Laptops under $500:") — no product lists in your text; the product list or product detail is shown below.

## Search Guidelines:
- Extract keywords, categories, and price ranges from user queries (e.g. \"hard drive 3.0\", \"WD 2TB\", \"USB drive\").
- When the user asks about a SPECIFIC product (by name, e.g. \"hard drive 3.0\", \"the WD drive\", \"show me the SanDisk SSD\") you MUST: (1) call search_products with the relevant query to find it, then (2) call get_product_details(product_id) with the id of the matching product so the user sees full details. Always call get_product_details when the user is asking about one product or when search returns exactly one result.
- When search_products returns one or a few results and the user asked for a single product, call get_product_details for the first/best matching product id.
- Keep your reply to a single streaming title. Do not list products, prices, or IDs in your message.
- For TV, television, or monitors: use category \"electronics\" (or \"tv\") and query \"tv\" or \"monitor\"; backend maps tv→electronics. Never say \"no such data\" for TV.
"""

    def _user_message_with_context(self, state: Dict[str, Any]) -> str:
        """Build user message, prefixing recent product IDs context when available."""
        user_message = state.get("user_message", "")
        recent_ids = state.get("recent_product_ids") or []
        if not recent_ids:
            return user_message
        ids_str = ", ".join(str(pid) for pid in recent_ids)
        return (
            f"Context: The user was recently shown these product IDs in order: {ids_str}. "
            "When they say 'last N products', 'the first one', 'the second product', 'compare the last two', etc., "
            "use these IDs. For get_product_details you must pass the numeric product_id for each product.\n\n"
            f"User request: {user_message}"
        )

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process search request."""
        import json
        from app.tools import execute_tool
        
        user_message = self._user_message_with_context(state)
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
        user_id = state.get("user_id")
        tool_results_for_graph = []
        if tool_calls:
            tool_results = []
            for idx, tool_call in enumerate(tool_calls):
                tool_name = tool_call.get("name")
                tool_input = tool_call.get("input", {})
                logger.info("[search_agent] executing tool[%d] name=%s input=%s", idx, tool_name, tool_input)
                result = await execute_tool(tool_name, tool_input, session_id, user_id=user_id)
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

            # When search returned exactly one product, add get_product_details so the UI shows it
            search_tool_calls = [tc for tc in tool_calls if tc.get("name") == "search_products"]
            if search_tool_calls:
                last_search_result = None
                for tr in tool_results:
                    if tr.get("name") == "search_products":
                        try:
                            last_search_result = json.loads(tr.get("content", "{}"))
                        except (TypeError, json.JSONDecodeError):
                            pass
                if last_search_result and isinstance(last_search_result, dict):
                    products = last_search_result.get("products") or []
                    if len(products) == 1 and isinstance(products[0], dict) and products[0].get("id") is not None:
                        pid = products[0]["id"]
                        if not any(tc.get("name") == "get_product_details" and tc.get("input", {}).get("product_id") == pid for tc in tool_calls):
                            tool_calls = list(tool_calls) + [
                                {"name": "get_product_details", "input": {"product_id": pid}, "id": f"single-product-{pid}"}
                            ]
                            logger.info("[search_agent] added get_product_details(product_id=%s) for single search result", pid)
                            extra_result = await execute_tool("get_product_details", {"product_id": pid}, session_id, user_id=user_id)
                            try:
                                tool_results_for_graph.append({"name": "get_product_details", "data": json.loads(extra_result)})
                            except (TypeError, json.JSONDecodeError):
                                tool_results_for_graph.append({"name": "get_product_details", "data": {"raw": extra_result}})
            
            # Add tool results to messages
            messages.append(LLMMessage(role="assistant", content=assistant_content))
            messages.append(LLMMessage(role="user", content=tool_results))

            logger.info("[search_agent] second LLM call (with tool results)")
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
            "tool_results": tool_results_for_graph,
            "agent": self.name,
        }
