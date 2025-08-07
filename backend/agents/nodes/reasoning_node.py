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

Think step by step:
1. What is the user asking for?
2. Do I have sufficient information from the RAG chunks to answer?
3. What's the best way to structure my response?
4. Are there any specific aspects I should focus on?

Provide your reasoning analysis:
"""
        
        messages = [SystemMessage(content=reasoning_prompt)]
        response = await self.llm.ainvoke(messages)
        
        reasoning_text = response.content
        logger.debug(f"Reasoning: {reasoning_text}")
        
        return {
            "reasoning": reasoning_text,
            "next_action": "respond_directly"
        }
