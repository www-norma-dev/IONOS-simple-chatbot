"""
Context preparation node for ReAct Agent workflow.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("chatbot-server")


class ContextPreparationNode:
    """Node for preparing context from RAG chunks and optional document sources."""

    def __init__(self, document_collector=None):
        self.document_collector = document_collector

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the context preparation node logic."""
        logger.debug("Entering context preparation node")
        
        rag_chunks = state.get("rag_chunks", [])
        current_url = state.get("current_url")
        doc_sources: List[str] = state.get("doc_sources", [])
        next_action: str | None = state.get("next_action")
        
        # Prepare context from RAG chunks
        context_parts = []
        
        # Use RAG chunks if available, otherwise attempt to collect from documents
        if rag_chunks:
            context_parts.append(f"Information from {current_url or 'the website'}:")
            for i, chunk in enumerate(rag_chunks[:5]):  # Limit to first 5 chunks
                context_parts.append(f"Chunk {i+1}: {chunk}")
        elif self.document_collector and doc_sources and (
            next_action == "collect_documents" or not rag_chunks
        ):
            try:
                doc_chunks = await self.document_collector.collect_documents(doc_sources)
            except Exception as exc:
                logger.error("Document collection failed: %s", exc)
                doc_chunks = []

            if doc_chunks:
                context_parts.append("Information from documents:")
                for i, chunk in enumerate(doc_chunks[:5]):
                    context_parts.append(f"Doc {i+1}: {chunk}")
            else:
                context_parts.append("No relevant information found in the knowledge base.")
        else:
            context_parts.append("No relevant information found in the knowledge base.")
        
        context = "\n".join(context_parts)
        logger.debug(f"Prepared context with {len(rag_chunks)} chunks")
        
        return {"context": context}
