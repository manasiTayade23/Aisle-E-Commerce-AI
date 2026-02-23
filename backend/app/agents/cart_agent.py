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
        """Get cart-related tools plus search/get_product_details to resolve product by name."""
        cart_tool_names = [
            "search_products",
            "get_product_details",
            "add_to_cart",
            "get_cart",
            "remove_from_cart",
            "update_cart_quantity",
            "clear_cart",
        ]
        return [
            tool for tool in TOOL_DEFINITIONS
            if tool["name"] in cart_tool_names
        ]

    def _user_message_with_context(self, state: Dict[str, Any]) -> str:
        """Inject recent product IDs so the agent can resolve 'the first one', 'the cheaper one', etc."""
        user_message = state.get("user_message", "")
        recent_ids = state.get("recent_product_ids") or []
        if not recent_ids:
            return user_message
        ids_str = ", ".join(str(pid) for pid in recent_ids)
        return (
            f"Context: The user was recently shown these product IDs in order: {ids_str}. "
            "When they say 'the first one', 'the second product', 'add the cheaper one', 'remove the last one', etc., "
            "use these IDs: first = index 0, second = index 1, and so on. You must pass the numeric product_id to add_to_cart/remove_from_cart.\n\n"
            f"User request: {user_message}"
        )

    def get_system_prompt(self) -> str:
        base = super().get_system_prompt()
        return f"""{base}

## Your Responsibilities:
- Add products to cart with correct quantities (resolve product by name or position when needed)
- Remove specific items or clear the entire cart when requested
- Update quantities accurately
- Always show cart total after modifications
- Confirm all cart actions clearly

## Adding a product:
- **Quantity: use 1 unless the user explicitly says otherwise.** For "add X to the cart", "add the hard drive", "add Samsung TV" use quantity=1. Only use quantity 2 or more when the user explicitly says so (e.g. "add 2", "add three", "add 5 of these"). Do NOT call add_to_cart twice for the same product—call it once with the correct quantity.
- If the user names a product (e.g. "add Samsung TV", "add the wireless mouse"): first call search_products with that name/query, get the product id from the results, then call add_to_cart(product_id=..., quantity=1) unless they said "add 2" or similar.
- If the user says "add the first one", "the second one", "the cheaper one": use the Context above (recent product IDs in order). First = first ID, second = second ID. For "cheaper one", call get_product_details on the relevant IDs to compare prices, then add_to_cart with the lower-priced product_id and quantity=1 unless they asked for more.
- Never guess or invent product_id. Always resolve via search_products + results, or from Context recent IDs, or get_product_details.

## Reducing quantity by one (NOT removing the item entirely):
- If the user says "remove only one quantity", "remove one quantity", "reduce by one", "take one off", "minus one", "reduce quantity by 1": they want to DECREASE the quantity by 1, not remove the product from the cart. First call get_cart to get current items and their quantities. Then for the product they mean (or the only product if there's one), call update_cart_quantity(product_id=..., quantity=current_quantity - 1). Example: if WD drive has quantity 2, set quantity to 1. Only if they say "remove it" or "remove the product" (entirely) do you use remove_from_cart.

## Removing items (entire product from cart):
- When the user says "remove X from my cart", "remove the [name]" (e.g. "remove acer tv", "remove the WD drive"): (1) call get_cart to get items (each has product_id and title). (2) Find the item whose title matches or contains the user's words (e.g. "acer" or "acer tv" matches "Acer SB220Q bi 21.5 inches Full HD..."). (3) Call remove_from_cart(product_id=...) with that item's product_id. You MUST perform both steps: get_cart then remove_from_cart. Do not reply with only the cart—always complete the removal.
- Match by partial name: "acer tv", "acer", "WD drive", "hard drive" match cart items whose title contains those words (case-insensitive).
- If the user says "remove the first item", "remove the second" (entirely): use get_cart to get items in order, then remove_from_cart with the corresponding product_id.
- If the user says "clear cart", "empty cart", "remove everything", "clear my cart": call clear_cart() with no parameters. Do not call remove_from_cart for each item.

## Updating quantity:
- If the user says "change quantity of the laptop to 2" or "update the [product name] to N": first call get_cart to get items (product_id and title), match by name, then update_cart_quantity(product_id=..., quantity=N).

## Showing the cart in your response:
- add_to_cart, remove_from_cart, update_cart_quantity, and clear_cart return a "cart" object with "items" (each has title, quantity, item_total) and "total". When you show "Updated Cart" or any cart summary, use this cart data exactly. Show each item's quantity and item_total as returned—this is the full cart state after the action, not just what you added. Example: if the user had 1x WD drive and added 1 more, the cart will show quantity 2 and item_total $128; do not show "Quantity: 1" or "Total $64".

## Cart guidelines:
- Default quantity is 1 if not specified
- Handle errors (e.g. missing product_id): if a tool returns an error, call get_cart or search_products as needed to resolve, then retry.
"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process cart management request. Loops: execute tool calls, feed results back, until LLM returns no more tools."""
        import json
        from app.tools import execute_tool

        user_message = self._user_message_with_context(state)
        messages = state.get("messages", [])
        session_id = state.get("session_id", "")
        user_id = state.get("user_id")

        messages.append(LLMMessage(role="user", content=user_message))

        all_tool_calls = []
        all_tool_results = []  # for graph to stream without re-executing (avoids double add_to_cart)
        response_text = ""
        max_rounds = 5  # prevent infinite loops

        for _ in range(max_rounds):
            tool_calls = []
            assistant_content = []
            response_text = ""

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

            if not tool_calls:
                break

            all_tool_calls.extend(tool_calls)
            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                tool_input = tool_call.get("input", {})
                result = await execute_tool(tool_name, tool_input, session_id, user_id=user_id)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.get("id"),
                    "name": tool_name,
                    "content": result,
                })
                try:
                    all_tool_results.append({"name": tool_name, "data": json.loads(result)})
                except (json.JSONDecodeError, TypeError):
                    all_tool_results.append({"name": tool_name, "data": {"raw": result}})

            messages.append(LLMMessage(role="assistant", content=assistant_content))
            messages.append(LLMMessage(role="user", content=tool_results))

        if not (response_text or "").strip():
            tool_names = [tc.get("name") for tc in all_tool_calls if tc.get("name")]
            if "add_to_cart" in tool_names:
                response_text = "Added to your cart."
            elif "get_cart" in tool_names:
                response_text = "Here's your cart."
            elif "remove_from_cart" in tool_names:
                response_text = "Removed from your cart."
            elif "clear_cart" in tool_names:
                response_text = "Your cart has been cleared."
            elif "update_cart_quantity" in tool_names:
                response_text = "Cart updated."
            else:
                response_text = "Done."

        messages.append(LLMMessage(role="assistant", content=response_text))

        return {
            **state,
            "messages": messages,
            "response": response_text,
            "tool_calls": all_tool_calls,
            "tool_results": all_tool_results,
            "agent": self.name,
        }
