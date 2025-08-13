"""
Simple web retrieval node using LangChain's TavilySearchAPIRetriever.

Minimal, starter-pack implementation: fetch top-k snippets and build a
compact context string for the emitter. Requires TAVILY_API_KEY in env.
"""

import logging
from typing import Dict, Any, List

from langchain_community.retrievers import TavilySearchAPIRetriever


logger = logging.getLogger("chatbot-server")


class WebRetrieveSimpleNode:
    """Fetches web snippets via Tavily and returns a context string."""

    def __init__(self, k: int = 4):
        self.retriever = TavilySearchAPIRetriever(k=k)

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug("Entering simple web retrieve node")

        # Extract user question
        question = ""
        messages = state.get("messages", []) or []
        for m in reversed(messages):
            content = getattr(m, "content", None)
            if isinstance(content, str) and content.strip():
                question = content.strip()
                break

        # Sync call interface; Tavily retriever is synchronous under the hood
        try:
            docs = self.retriever.get_relevant_documents(question)
        except Exception as exc:
            logger.warning("Tavily retriever failed: %s", exc)
            docs = []

        parts: List[str] = []
        citations: List[Dict[str, Any]] = []
        for i, d in enumerate(docs[:8]):
            txt = getattr(d, "page_content", "")
            meta = getattr(d, "metadata", {}) or {}
            url = meta.get("source") or meta.get("url")
            title = meta.get("title")
            if txt:
                parts.append(f"Snippet {i+1}: {txt}")
            if url or title:
                citations.append({"url": url, "title": title})

        context = "\n".join(parts)
        logger.info("Web retrieval returned %d snippets", len(docs))
        return {"context": context, "citations": citations}


