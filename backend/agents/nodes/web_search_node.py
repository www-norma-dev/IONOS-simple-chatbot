"""
Web search node for extended ReAct Agent workflow.

Executes planned queries against a configured search provider and returns
SERP results.
"""

import logging
from typing import Dict, Any, List

from agents.Collectors import SearchClient
from utils.config import Config


logger = logging.getLogger("chatbot-server")


class WebSearchNode:
    """Node that performs web search and returns SERP results."""

    def __init__(self) -> None:
        pass

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the web search step.

        Inputs (from state):
          - queries: list[str]
          - search_filters: dict
          - budgets: dict

        Outputs (to state):
          - web_results: list[dict]
        """
        logger.debug("Entering web search node")

        queries: List[str] = state.get("queries", []) or []
        budgets = state.get("budgets", {}) or {}

        provider = Config.SEARCH_PROVIDER
        api_key = Config.SEARCH_API_KEY
        client = SearchClient(provider=provider, api_key=api_key)

        # Prefer recent only if explicitly requested by recency cues
        filters = state.get("search_filters", {}) or {}
        q_text = " ".join(queries).lower()
        if any(k in q_text for k in ["latest", "today", "this week", "this month", "2025", "2024"]):
            filters["recent"] = True
        web_results = await client.search(queries=queries, search_filters=filters, budget=budgets)
        # Log count for visibility
        try:
            import logging as _logging
            _logging.getLogger("chatbot-server").info(
                "Web search queries=%s returned %d results", queries, len(web_results)
            )
        except Exception:
            pass

        # Fallback: if no results and we used a 'recent' filter, retry without it
        if not web_results and filters.get("recent"):
            try:
                filters2 = dict(filters)
                filters2.pop("recent", None)
                web_results = await client.search(queries=queries, search_filters=filters2, budget=budgets)
                try:
                    import logging as _logging
                    _logging.getLogger("chatbot-server").info(
                        "Web search fallback (no recent) returned %d results", len(web_results)
                    )
                except Exception:
                    pass
            except Exception:
                pass

        return {
            "web_results": web_results,
        }


