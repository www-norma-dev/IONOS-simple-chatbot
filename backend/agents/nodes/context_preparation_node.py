"""
Context preparation node for ReAct Agent workflow.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger("chatbot-server")


class ContextPreparationNode:
    """Node for preparing context from RAG chunks."""
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the context preparation node logic."""
        logger.debug("Entering context preparation node")
        
        rag_chunks = state.get("rag_chunks", [])
        current_url = state.get("current_url")
        
        # Prepare context from RAG chunks
        context_parts = []
        
        if rag_chunks:
            context_parts.append(f"Information from {current_url or 'the website'}:")
            for i, chunk in enumerate(rag_chunks[:5]):  # Limit to first 5 chunks
                context_parts.append(f"Chunk {i+1}: {chunk}")
        else:
            context_parts.append("No relevant information found in the knowledge base.")
        
        context = "\n".join(context_parts)
        logger.debug(f"Prepared context with {len(rag_chunks)} chunks")
        
        return {"context": context}
