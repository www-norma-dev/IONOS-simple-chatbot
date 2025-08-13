"""
Web read and extract node for extended ReAct Agent workflow.

Fetches selected URLs and extracts clean textual passages suitable for
downstream ranking and synthesis.
"""

import logging
from typing import Dict, Any, List

from agents.Collectors import WebReader


logger = logging.getLogger("chatbot-server")


class WebReadExtractNode:
    """Node that fetches pages and extracts passages."""

    def __init__(self) -> None:
        pass

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the web read and extraction step.

        Inputs (from state):
          - web_results: list[dict]
          - budgets: dict

        Outputs (to state):
          - web_passages: list[dict]
        """
        logger.debug("Entering web read+extract node")

        web_results: List[Dict[str, Any]] = state.get("web_results", []) or []
        budgets = state.get("budgets", {}) or {}

        urls: List[str] = [it.get("url") for it in web_results if it.get("url")]
        reader = WebReader()
        web_passages = await reader.fetch_and_extract(urls=urls, budget=budgets)
        # Log count for visibility
        try:
            import logging as _logging
            _logging.getLogger("chatbot-server").info("Web read+extract returned %d passages", len(web_passages))
        except Exception:
            pass

        return {
            "web_passages": web_passages,
        }


