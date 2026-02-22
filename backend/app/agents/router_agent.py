"""Router agent that decides which specialized agent to use."""

import logging
from typing import Dict, Any
from app.agents.base_agent import BaseAgent
from app.llm.base import BaseLLM, LLMMessage

logger = logging.getLogger(__name__)


class RouterAgent(BaseAgent):
    """Router agent that routes requests to appropriate specialized agents."""
    
    def __init__(self, llm: BaseLLM):
        super().__init__(
            llm=llm,
            name="Router Agent",
            description=(
                "You analyze user requests and determine which specialized agent "
                "should handle the request. You route to: search, cart, comparison, "
                "or recommendation agents."
            )
        )
    
    def get_tools(self) -> list:
        """Router doesn't need tools."""
        return []
    
    def get_system_prompt(self) -> str:
        base = super().get_system_prompt()
        return f"""{base}

## Your Task:
Analyze the user's request and determine which agent should handle it.

## Available Agents:
1. **search** - For finding products, browsing, searching by keyword/category/price
2. **cart** - For adding/removing items, updating quantities, viewing cart
3. **comparison** - For comparing multiple products side by side
4. **recommendation** - For personalized product recommendations

## Routing Rules:
- Search: "find", "search", "show", "browse", "look for", "what products"
- Cart: "add to cart", "remove", "cart", "checkout", "quantity"
- Comparison: "compare", "difference", "which is better", "vs", "versus"
- Recommendation: "recommend", "suggest", "what should I buy", "similar to"

Respond with ONLY the agent name: search, cart, comparison, or recommendation.
"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate agent."""
        user_message = state.get("user_message", "")
        logger.info("[router] process user_message=%r", user_message[:80] if len(user_message) > 80 else user_message)

        # Simple routing logic - can be enhanced with LLM
        message_lower = user_message.lower().strip()

        if any(word in message_lower for word in ["cart", "add", "remove", "quantity", "checkout"]):
            next_agent = "cart"
        elif any(word in message_lower for word in ["compare", "comparison", "difference", "vs", "versus", "better"]) or "comapre" in message_lower or "compair" in message_lower:
            next_agent = "comparison"
        elif any(word in message_lower for word in ["recommend", "suggest", "similar", "like"]):
            next_agent = "recommendation"
        else:
            next_agent = "search"
        logger.info("[router] next_agent=%s", next_agent)
        return {**state, "next_agent": next_agent}
