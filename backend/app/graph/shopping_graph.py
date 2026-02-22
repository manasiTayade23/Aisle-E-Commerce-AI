"""LangGraph-based multi-agent shopping assistant workflow."""

import logging
from typing import Dict, Any, Annotated
try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from app.agents import (
    RouterAgent,
    SearchAgent,
    CartAgent,
    ComparisonAgent,
    RecommendationAgent,
)
from app.llm import create_llm
from app.rag.retriever import RAGRetriever

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    """State for the shopping graph."""
    user_message: str
    session_id: str
    messages: list
    response: str
    tool_calls: list
    agent: str
    next_agent: str
    rag_context: list


class ShoppingGraph:
    """Multi-agent shopping assistant using LangGraph."""
    
    def __init__(self, llm_provider: str = None):
        """Initialize the shopping graph with agents."""
        # Create LLM instance
        self.llm = create_llm(provider=llm_provider)
        
        # Initialize RAG retriever
        self.rag_retriever = RAGRetriever()
        
        # Create agents
        self.router = RouterAgent(self.llm)
        self.search_agent = SearchAgent(self.llm)
        self.cart_agent = CartAgent(self.llm)
        self.comparison_agent = ComparisonAgent(self.llm)
        self.recommendation_agent = RecommendationAgent(self.llm, self.rag_retriever)
        
        # Build graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("router", self._route)
        workflow.add_node("search", self._search_node)
        workflow.add_node("cart", self._cart_node)
        workflow.add_node("comparison", self._comparison_node)
        workflow.add_node("recommendation", self._recommendation_node)
        
        # Set entry point
        workflow.set_entry_point("router")
        
        # Add edges
        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "search": "search",
                "cart": "cart",
                "comparison": "comparison",
                "recommendation": "recommendation",
            }
        )
        
        # All agent nodes end
        workflow.add_edge("search", END)
        workflow.add_edge("cart", END)
        workflow.add_edge("comparison", END)
        workflow.add_edge("recommendation", END)
        
        return workflow.compile()
    
    async def _route(self, state: GraphState) -> GraphState:
        """Route to appropriate agent."""
        result = await self.router.process(state)
        return result
    
    async def _search_node(self, state: GraphState) -> GraphState:
        """Handle search requests."""
        result = await self.search_agent.process(state)
        return result
    
    async def _cart_node(self, state: GraphState) -> GraphState:
        """Handle cart requests."""
        result = await self.cart_agent.process(state)
        return result
    
    async def _comparison_node(self, state: GraphState) -> GraphState:
        """Handle comparison requests."""
        result = await self.comparison_agent.process(state)
        return result
    
    async def _recommendation_node(self, state: GraphState) -> GraphState:
        """Handle recommendation requests."""
        result = await self.recommendation_agent.process(state)
        return result
    
    def _route_decision(self, state: GraphState) -> str:
        """Decide which agent to route to."""
        return state.get("next_agent", "search")
    
    async def stream_response(
        self,
        session_id: str,
        user_message: str,
        conversation_history: list = None
    ):
        """Stream response from the graph."""
        import json
        from app.tools import execute_tool

        logger.info("[graph] stream_response: initializing state")
        # Initialize state
        state: GraphState = {
            "user_message": user_message,
            "session_id": session_id,
            "messages": conversation_history or [],
            "response": "",
            "tool_calls": [],
            "agent": "",
            "next_agent": "",
            "rag_context": [],
        }

        logger.info("[graph] stream_response: calling graph.ainvoke")
        # Run graph
        final_state = await self.graph.ainvoke(state)
        agent_name = final_state.get("agent", "unknown")
        tool_calls = final_state.get("tool_calls", [])
        response = final_state.get("response", "")
        logger.info("[graph] ainvoke done agent=%s tool_calls_count=%d response_len=%d", agent_name, len(tool_calls), len(response))

        # Stream agent info
        yield json.dumps({
            "type": "agent",
            "agent": agent_name
        }) + "\n"
        logger.info("[graph] yielded type=agent agent=%s", agent_name)

        # Execute tools and stream results
        for i, tool_call in enumerate(tool_calls):
            tool_name = tool_call.get("name")
            tool_input = tool_call.get("input", {})

            logger.info("[graph] tool_call[%d] name=%s input=%s", i, tool_name, tool_input)
            # Stream tool call
            yield json.dumps({
                "type": "tool_call",
                "name": tool_name,
                "input": tool_input,
            }) + "\n"

            # Execute tool
            try:
                result = await execute_tool(tool_name, tool_input, session_id)
                result_data = json.loads(result)

                yield json.dumps({
                    "type": "tool_result",
                    "name": tool_name,
                    "data": result_data,
                }) + "\n"
                logger.info("[graph] tool_result[%d] name=%s result_keys=%s", i, tool_name, list(result_data.keys()) if isinstance(result_data, dict) else "n/a")
            except Exception as e:
                logger.exception("[graph] tool execution failed name=%s", tool_name)
                yield json.dumps({
                    "type": "error",
                    "content": f"Tool execution error: {str(e)}"
                }) + "\n"

        # Stream response text
        if response:
            chunk_size = 50
            num_chunks = 0
            for i in range(0, len(response), chunk_size):
                chunk = response[i:i + chunk_size]
                yield json.dumps({
                    "type": "text",
                    "content": chunk
                }) + "\n"
                num_chunks += 1
            logger.info("[graph] yielded response text chunks count=%d total_len=%d", num_chunks, len(response))
        else:
            logger.info("[graph] no response text to stream (response is empty)")

        yield json.dumps({"type": "done"}) + "\n"
        logger.info("[graph] stream_response: yielded done")
