"""
Reasoning node for ReAct Agent workflow.
"""

import logging
from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger("chatbot-server")


class ReasoningNode:
    """Node for reasoning about the user's query."""
    
    def __init__(self, llm):
        self.llm = llm
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the reasoning node logic."""
        logger.debug("Entering reasoning node")
        
        # Get the last user message
        user_message = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
        
        if not user_message:
            return {
                "reasoning": "No user message found",
                "next_action": "respond_directly"
            }
        
        # Create reasoning prompt
        reasoning_prompt = f"""
You are an intelligent assistant with reasoning capabilities. Analyze the user's query and determine the best approach.

Current context:
- User message: "{user_message}"
- Current URL: {state.get("current_url", "None")}
- Available RAG chunks: {len(state.get("rag_chunks", []))} chunks
 - Available document sources: {len(state.get("doc_sources", []))} sources

Think step by step:
1. What is the user asking for?
2. Do I have sufficient information from the RAG chunks to answer?
3. If not, and if document sources are available, should I collect and use them?
4. What's the best way to structure my response?
5. Are there any specific aspects I should focus on?

Provide your reasoning analysis:
"""
        
        # Pass a single HumanMessage to the chat model (expected input type)
        response = await self.llm.ainvoke([HumanMessage(content=reasoning_prompt)])
        
        reasoning_text = response.content
        logger.debug(f"Reasoning: {reasoning_text}")
        
        # Simple heuristic: if there are no RAG chunks and we have doc sources, suggest collecting docs
        next_action = "respond_directly"
        if not state.get("rag_chunks") and state.get("doc_sources"):
            next_action = "collect_documents"

        return {
            "reasoning": reasoning_text,
            "next_action": next_action,
        }
