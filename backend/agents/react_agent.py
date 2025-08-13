"""
ReAct Agent implementation using LangGraph for extensible agent architecture.
"""

import json
import logging
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from dataclasses import dataclass
from functools import reduce
from operator import add

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import SecretStr

from .nodes import (
    ReasoningNode,
    ContextPreparationNode,
    ResponseGenerationNode,
    ResponseDraftNode,
    ResponseSufficiencyNode,
    # Keep robust chain available but not required for starter
    # SearchPlannerNode,
    # WebSearchNode,
    # WebReadExtractNode,
    # EvidenceRankerNode,
    # ContextMergeNode,
    WebRetrieveSimpleNode,
)
from utils.config import Config

logger = logging.getLogger("chatbot-server")


def add_messages(left: List[BaseMessage], right: List[BaseMessage]) -> List[BaseMessage]:
    """Add messages function for state management."""
    return left + right


class AgentState(TypedDict, total=False):
    """State of the ReAct agent."""
    messages: Annotated[List[BaseMessage], add_messages]
    current_url: Optional[str]
    rag_chunks: List[str]
    reasoning: str
    next_action: Optional[str]
    context: str
    # Extended workflow fields (optional)
    local_passages: List[Dict[str, Any]]
    web_results: List[Dict[str, Any]]
    web_passages: List[Dict[str, Any]]
    ranked_passages: List[Dict[str, Any]]
    draft_answer: str
    final_answer: str
    citations: List[Dict[str, Any]]
    deficits: Dict[str, Any]
    budgets: Dict[str, Any]
    decision: str
    # Planner/search fields
    queries: List[str]
    search_filters: Dict[str, Any]


@dataclass
class ReActConfig:
    """Configuration for the ReAct agent."""
    model_name: str
    api_key: str
    base_url: str
    temperature: float = 0.1
    max_tokens: int = 1000
    chunk_size: int = 500
    max_chunk_count: int = 256
    max_iterations: int = 5


class ReActAgent:
    """
    ReAct (Reasoning + Acting) Agent using LangGraph for extensible architecture.
    
    This agent uses a graph-based workflow for better extensibility and control.
    """
    
    def __init__(self, config: ReActConfig):
        self.config = config
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=config.model_name,
            base_url=config.base_url,
            api_key=SecretStr(config.api_key),
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
        
        # Initialize node instances
        self.reasoning_node = ReasoningNode(self.llm)
        self.context_preparation_node = ContextPreparationNode()
        self.response_generation_node = ResponseGenerationNode(self.llm)
        # Extended nodes (no separate finalize; use unified response_generation_node)
        self.response_draft_node = ResponseDraftNode(self.llm)
        self.response_sufficiency_node = ResponseSufficiencyNode()
        # Minimal web retrieval for starter pack
        self.web_retrieve_simple_node = WebRetrieveSimpleNode(k=4)
        
        # legacy workflow graph(Legacy: Reasoning → ContextPreparation → ResponseGeneration → END)
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
        if Config.GRAPH_RENDER_ENABLED:
            try:
                self.app.get_graph(xray=False).draw_mermaid_png(
                    output_file_path="supervisor_agent_graph.png"
                )
            except Exception:
                logger.debug("Graph rendering disabled or failed for legacy graph")

        # Build the extended workflow graph
        self.extended_workflow = self._build_extended_workflow()
        self.extended_app = self.extended_workflow.compile()
        if Config.GRAPH_RENDER_ENABLED:
            try:
                self.extended_app.get_graph(xray=False).draw_mermaid_png(
                    output_file_path="supervisor_agent_graph_extended.png"
                )
            except Exception:
                logger.debug("Graph rendering disabled or failed for extended graph")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for the ReAct agent."""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes with the node instances
        workflow.add_node("reasoning", self.reasoning_node.execute)
        workflow.add_node("context_preparation", self.context_preparation_node.execute)
        workflow.add_node("response_generation", self.response_generation_node.execute)
        
        # Set entry point
        workflow.set_entry_point("reasoning")
        
        # Add edges
        workflow.add_edge("reasoning", "context_preparation")
        workflow.add_edge("context_preparation", "response_generation")
        workflow.add_edge("response_generation", END)
        

        return workflow

    def _build_extended_workflow(self) -> StateGraph:
        """Build the extended LangGraph workflow with gated web search."""
        workflow = StateGraph(AgentState)

        # Reuse existing nodes then extend
        workflow.add_node("reasoning", self.reasoning_node.execute)
        workflow.add_node("context_preparation", self.context_preparation_node.execute)
        workflow.add_node("response_draft", self.response_draft_node.execute)
        workflow.add_node("response_sufficiency", self.response_sufficiency_node.execute)
        workflow.add_node("web_retrieve_simple", self.web_retrieve_simple_node.execute)
        workflow.add_node("response_generation", self.response_generation_node.execute)

        workflow.set_entry_point("reasoning")
        workflow.add_edge("reasoning", "context_preparation")
        workflow.add_edge("context_preparation", "response_draft")
        workflow.add_edge("response_draft", "response_sufficiency")

        # Conditional branch after sufficiency gate
        def route_after_sufficiency(state: Dict[str, Any]) -> str:
            decision = state.get("decision")
            return decision if decision in ("sufficient", "insufficient") else "insufficient"

        try:
            workflow.add_conditional_edges(
                "response_sufficiency",
                route_after_sufficiency,
                {
                    "sufficient": "response_generation",
                    "insufficient": "web_retrieve_simple",
                },
            )
        except Exception:
            # Fallback: linearize to insufficient path; sufficiency node should decide minimal work
            workflow.add_edge("response_sufficiency", "web_retrieve_simple")

        workflow.add_edge("web_retrieve_simple", "response_generation")
        workflow.add_edge("response_generation", END)

        # Also ensure sufficient path can end
        workflow.add_edge("response_generation", END)

        return workflow
    
    async def process_message_with_rag(self, message: str, rag_chunks: List[str], current_url: Optional[str] = None) -> str:
        """
        Process a user message using pre-retrieved RAG chunks through the LangGraph workflow.
        
        Args:
            message: The user's message
            rag_chunks: Pre-retrieved relevant chunks from RAG
            current_url: Optional current URL context
            
        Returns:
            The agent's response
        """
        try:
            # Create initial state
            initial_state = AgentState(
                messages=[HumanMessage(content=message)],
                current_url=current_url,
                rag_chunks=rag_chunks,
                reasoning="",
                next_action=None,
                context=""
            )
            
            # Run the workflow
            final_state = await self.app.ainvoke(initial_state)
            
            # Get the last AI message
            for msg in reversed(final_state["messages"]):
                if isinstance(msg, AIMessage):
                    return msg.content
            
            return "I apologize, but I couldn't generate a response."
            
        except Exception as e:
            logger.error(f"Error in LangGraph workflow: {str(e)}")
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"

    async def process_message_extended_with_rag(self, message: str, rag_chunks: List[str], current_url: Optional[str] = None) -> str:
        """Process a user message using the extended workflow with gated web search.

        Builds additional state (local_passages, budgets, etc.) and runs the
        extended graph. Falls back gracefully on errors.
        """
        try:
            logger.info("Extended flow: starting with %d rag_chunks", 0 if rag_chunks is None else len(rag_chunks))
            # Map rag_chunks to local_passages with stub scores and metadata
            local_passages: List[Dict[str, Any]] = []
            for chunk in rag_chunks or []:
                local_passages.append({
                    "text": chunk,
                    "score": 0.0,
                    "source": "local",
                    "url": current_url,
                })

            initial_state = AgentState(
                messages=[HumanMessage(content=message)],
                current_url=current_url,
                rag_chunks=rag_chunks,
                reasoning="",
                next_action=None,
                context="",
                local_passages=local_passages,
            )

            final_state = await self.extended_app.ainvoke(initial_state)
            web_used = bool((final_state.get("citations") or []))
            logger.info(
                "Extended flow: completed; local_passages=%d, web_used=%s",
                len(final_state.get("local_passages", []) or []),
                web_used,
            )

            # Prefer explicit final_answer if present
            final_answer = final_state.get("final_answer")
            if isinstance(final_answer, str) and final_answer.strip():
                return final_answer

            # Otherwise, return the last AI message content
            for msg in reversed(final_state.get("messages", [])):
                if isinstance(msg, AIMessage):
                    return msg.content

            return "I apologize, but I couldn't generate a response."

        except Exception as e:
            logger.error(f"Error in extended LangGraph workflow: {str(e)}")
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"
    
    async def process_message(self, message: str, current_url: Optional[str] = None) -> str:
        """
        Process a user message through the LangGraph workflow (with dynamic scraping if needed).
        
        Args:
            message: The user's message
            current_url: Optional current URL context
            
        Returns:
            The agent's response
        """
        # For now, this method can be used for future extensions with dynamic scraping
        # Currently, we primarily use process_message_with_rag
        return await self.process_message_with_rag(message, [], current_url)
    
# Factory function for creating ReAct agent
def create_react_agent(
    model_name: str,
    api_key: str,
    base_url: str,
    **kwargs
) -> ReActAgent:
    """
    Factory function to create a ReAct agent with LangGraph.
    
    Args:
        model_name: Name of the model to use
        api_key: API key for the model
        base_url: Base URL for the model API
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured ReAct agent with LangGraph workflow
    """
    config = ReActConfig(
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
        **kwargs
    )
    
    return ReActAgent(config)
