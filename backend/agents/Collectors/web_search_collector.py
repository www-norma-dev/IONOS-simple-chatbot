"""
Minimal web search collector - starter pack for developers to extend.
"""

from typing import List
from langchain_community.retrievers import TavilySearchAPIRetriever


class WebSearchCollector:
    """Minimal web search using LangChain Tavily - extend as needed."""
    
    def __init__(self, max_results: int = 5):
        self.retriever = TavilySearchAPIRetriever(k=max_results)

    async def collect_chunks_only(self, query: str) -> List[str]:
        """Simple web search returning text chunks - same interface as DocumentCollector."""
        try:
            docs = await self.retriever.ainvoke(query)
            return [d.page_content for d in docs if d.page_content]
        except:
            return []  # Graceful fallback
