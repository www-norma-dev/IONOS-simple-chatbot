"""
Context preparation node for ReAct Agent workflow.
"""

import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, filter_messages
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("chatbot-server")


class ContextPreparationNode:
    """Node for preparing context from RAG chunks and optional document sources."""

    def __init__(self, document_collector=None, web_search_collector=None):
        self.document_collector = document_collector
        self.web_search_collector = web_search_collector
        
    def _is_relevant(self, query: str, chunks: List[str], threshold: float = 0.1) -> bool:
        """Simple similarity check to see if RAG chunks are relevant to query."""
        if not chunks or not query.strip():
            return False
        try:
            # Combine all chunks into one text
            combined_text = " ".join(chunks[:3])  # Check first 3 chunks
            vectorizer = TfidfVectorizer(stop_words='english')
            vectors = vectorizer.fit_transform([query.lower(), combined_text.lower()])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return similarity > threshold
        except:
            return True  # If similarity check fails, assume relevant

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the context preparation node logic."""
        logger.debug("Entering context preparation node")
        
        rag_chunks = state.get("rag_chunks", [])
        current_url = state.get("current_url")
        doc_sources: List[str] = state.get("doc_sources", [])
        next_action: Optional[str] = state.get("next_action")
        
        # Prepare context from RAG chunks
        context_parts = []
        
        # Get user message using LangChain's filter_messages
        human_msgs = filter_messages(state["messages"], include_types=HumanMessage)
        last_human = human_msgs[-1] if human_msgs else None
        user_text = last_human.content if last_human else ""
        
        # Smart fallback: RAG first, then web search if irrelevant
        if rag_chunks and self._is_relevant(user_text, rag_chunks):
            # Use RAG chunks if they're relevant to the query
            context_parts.append(f"Information from {current_url or 'the website'}:")
            context_parts.extend(rag_chunks[:5])
        elif self.web_search_collector:
            # Fallback to web search when RAG is irrelevant or empty
            web_chunks = await self.web_search_collector.collect_chunks_only(user_text)
            if web_chunks:
                context_parts.append("Information from web search:")
                context_parts.extend(web_chunks[:5])
            elif rag_chunks:
                # Last resort: use irrelevant RAG chunks
                context_parts.append(f"Information from {current_url or 'the website'} (may not be directly relevant):")
                context_parts.extend(rag_chunks[:5])
            else:
                context_parts.append("No relevant information found.")
        elif rag_chunks:
            # Use RAG chunks if no web search available
            context_parts.append(f"Information from {current_url or 'the website'}:")
            context_parts.extend(rag_chunks[:5])
        elif self.document_collector and doc_sources:
            # Final fallback to documents
            doc_chunks = await self.document_collector.collect_documents(doc_sources)
            if doc_chunks:
                context_parts.append("Information from documents:")
                context_parts.extend(doc_chunks[:5])
            else:
                context_parts.append("No relevant information found.")
        
        context = "\n".join(context_parts)
        logger.debug(f"Prepared context with {len(rag_chunks)} chunks")
        
        return {"context": context}
