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

from .Collectors import WebScraper, DocumentCollector
from .nodes import ReasoningNode, ContextPreparationNode, ResponseGenerationNode

logger = logging.getLogger("chatbot-server")


def add_messages(left: List[BaseMessage], right: List[BaseMessage]) -> List[BaseMessage]:
    """Add messages function for state management."""
    return left + right


class AgentState(TypedDict):
    """State of the ReAct agent."""
    messages: Annotated[List[BaseMessage], add_messages]
    current_url: Optional[str]
    rag_chunks: List[str]
    doc_sources: List[str]
    reasoning: str
    next_action: Optional[str]
    context: str


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
        self.web_scraper = WebScraper(
            chunk_size=config.chunk_size,
            max_chunk_count=config.max_chunk_count
        )
        self.document_collector = DocumentCollector(
            chunk_size=config.chunk_size,
            max_chunk_count=config.max_chunk_count,
        )
        
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
        self.context_preparation_node = ContextPreparationNode(self.document_collector)
        self.response_generation_node = ResponseGenerationNode(self.llm)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
        self.app.get_graph(xray=False).draw_mermaid_png(
                output_file_path="supervisor_agent_graph.png"
        )
    
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
    
    async def process_message_with_rag(self, message: str, rag_chunks: List[str], current_url: Optional[str] = None, doc_sources: Optional[List[str]] = None) -> str:
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
                doc_sources=doc_sources or [],
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
