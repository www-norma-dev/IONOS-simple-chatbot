"""
Response generation node for ReAct Agent workflow.
"""

import logging
from typing import Dict, Any

from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger("chatbot-server")


class ResponseGenerationNode:
    """Node for generating the final response."""
    
    def __init__(self, llm):
        self.llm = llm
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the response generation node logic."""
        logger.debug("Entering response generation node")
        
        # Get the user's question
        user_message = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
        
        context = state.get("context", "No context available.")
        reasoning = state.get("reasoning", "")
        
        # Create response prompt
        response_prompt = f"""
You are a helpful assistant. Based on your reasoning and the available information, provide a comprehensive answer to the user's question.

Your Reasoning:
{reasoning}

Available Information:
{context}

User Question: {user_message}

Guidelines:
1. Use the reasoning you provided to structure your response
2. Base your answer on the available information
3. Be helpful, accurate, and well-structured
4. If information is insufficient, be honest about limitations
5. Provide actionable insights when possible

Response:
"""
        
        # Pass a single HumanMessage to the chat model (expected input type)
        response = await self.llm.ainvoke([HumanMessage(content=response_prompt)])
        
        # Create the AI message for the conversation
        ai_message = AIMessage(content=response.content.strip())
        
        return {"messages": [ai_message]}
