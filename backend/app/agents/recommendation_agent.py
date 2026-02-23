"""Product recommendation agent using RAG."""

import json
from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.llm.base import BaseLLM, LLMMessage
from app.tools import TOOL_DEFINITIONS
from app.rag.retriever import RAGRetriever


class RecommendationAgent(BaseAgent):
    """Agent specialized in product recommendations using RAG."""
    
    def __init__(self, llm: BaseLLM, rag_retriever: RAGRetriever):
        super().__init__(
            llm=llm,
            name="Recommendation Agent",
            description=(
                "You specialize in recommending products based on user preferences, "
                "purchase history, and semantic similarity. You use advanced RAG "
                "to find the most relevant products."
            )
        )
        self.rag_retriever = rag_retriever
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get recommendation-related tools."""
        return [
            tool for tool in TOOL_DEFINITIONS 
            if tool["name"] in ["search_products", "get_product_details"]
        ]
    
    def get_system_prompt(self) -> str:
        base = super().get_system_prompt()
        return f"""{base}

## Your Responsibilities:
- Understand user preferences and needs
- Use semantic search to find relevant products
- Provide personalized recommendations
- Explain why products are recommended
- Consider user's cart and browsing history

## Recommendation Guidelines:
- Use semantic similarity for better matches
- Consider multiple factors: price, rating, category, features
- Provide diverse recommendations (not just similar items)
- Explain the reasoning behind each recommendation
- Ask clarifying questions if preferences are unclear
"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process recommendation request."""
        import json
        from app.tools import execute_tool
        
        user_message = state.get("user_message", "")
        messages = state.get("messages", [])
        session_id = state.get("session_id", "")
        
        # Use RAG to find relevant products
        try:
            relevant_products = await self.rag_retriever.search(user_message, top_k=5)
        except Exception:
            # Fallback if RAG not initialized
            relevant_products = []
        
        # Enhance user message with context
        if relevant_products:
            context = "Based on semantic search, here are relevant products:\n"
            for product in relevant_products:
                context += f"- {product.get('title', 'Unknown')} (ID: {product.get('id')})\n"
            enhanced_message = f"{context}\n\nUser request: {user_message}"
        else:
            enhanced_message = user_message
        
        messages.append(LLMMessage(role="user", content=enhanced_message))
        
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
            "tool_results": tool_results_for_graph,
            "agent": self.name,
            "rag_context": relevant_products,
        }
