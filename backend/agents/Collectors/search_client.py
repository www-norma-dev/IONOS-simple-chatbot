"""
Search client wrapper for SERP providers.

This module provides a unified interface to perform web searches against
different providers (e.g., Tavily, Brave, Bing, SerpAPI). The concrete
provider integration can be implemented later while keeping the node
interfaces stable.
"""

import logging
from typing import Any, Dict, List, Optional
import httpx


logger = logging.getLogger("chatbot-server")


class SearchClient:
    """Unified search client with provider-agnostic interface."""

    def __init__(
        self,
        provider: str = "",
        api_key: Optional[str] = None,
        default_region: str = "",
        safe_search: str = "moderate",
    ) -> None:
        self.provider = provider
        self.api_key = api_key
        self.default_region = default_region
        self.safe_search = safe_search

    async def search(
        self,
        queries: List[str],
        search_filters: Optional[Dict[str, Any]] = None,
        budget: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute queries and return SERP results.

        The structure of the result items should be:
          {"title": str, "url": str, "snippet": str, "rank": int, "date": str | None, "engine": str}

        This is a scaffold implementation that returns an empty list.
        Provider-specific logic will be implemented later.
        """
        logger.debug(
            "SearchClient.search called with provider=%s, queries=%d",
            self.provider,
            0 if queries is None else len(queries),
        )

        results: List[Dict[str, Any]] = []

        if not queries:
            # Ensure at least one noop-safe query to trigger fallback provider
            queries = [""]

        max_queries = 3
        if budget and isinstance(budget.get("max_queries"), int):
            max_queries = budget["max_queries"]

        provider = (self.provider or "").lower()
        if provider == "tavily":
            # Minimal Tavily integration
            # API: POST https://api.tavily.com/search with { api_key, query, include_answer: false }
            base_url = "https://api.tavily.com/search"
            headers = {"Content-Type": "application/json"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                for qi, q in enumerate(queries[:max_queries]):
                    try:
                        payload = {
                            "api_key": self.api_key or "",
                            "query": q,
                            "include_answer": False,
                            # Be generous by default
                            "search_type": "general",
                            "search_depth": "advanced",
                            "max_results": 8,
                        }
                        # If caller provided explicit include_domains, pass through
                        if search_filters and search_filters.get("include_domains"):
                            payload["include_domains"] = search_filters.get("include_domains")
                        resp = await client.post(base_url, json=payload, headers=headers)
                        resp.raise_for_status()
                        data = resp.json()
                        items = data.get("results", []) or []
                        # Also look at 'news' key if present
                        if not items and data.get("news"):
                            items = data.get("news") or []
                        for idx, item in enumerate(items):
                            results.append({
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("content", ""),
                                "rank": idx + 1,
                                "date": item.get("published_date"),
                                "engine": "tavily",
                            })
                    except Exception as exc:
                        logger.warning("Tavily search failed for query %d: %s", qi, exc)
        # Fallback to DuckDuckGo via duckduckgo-search if no results and provider was tavily
        if not results:
            try:
                from duckduckgo_search import DDGS
                ddg = DDGS()
                max_q = max_queries
                for qi, q in enumerate(queries[:max_q]):
                    for idx, item in enumerate(ddg.text(q or "", max_results=8) or []):
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("href", ""),
                            "snippet": item.get("body", ""),
                            "rank": idx + 1,
                            "date": None,
                            "engine": "duckduckgo",
                        })
            except Exception as exc:
                logger.warning("DuckDuckGo fallback failed: %s", exc)

        else:
            logger.debug("Search provider not configured or unsupported: %s", provider)

        return results


