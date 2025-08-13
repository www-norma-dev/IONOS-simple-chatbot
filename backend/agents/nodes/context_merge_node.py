"""
Context merge node for extended ReAct Agent workflow.

Merges ranked local and web evidence into a unified context string and
constructs normalized citation metadata for grounded answering.
"""

import logging
from typing import Dict, Any, List

from utils.citations import normalize_citation, dedupe_citations


logger = logging.getLogger("chatbot-server")


class ContextMergeNode:
    """Node that merges evidence into context and citations."""

    def __init__(self) -> None:
        pass

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the context merge step.

        Inputs (from state):
          - ranked_passages: list[dict]

        Outputs (to state):
          - context: str (unified)
          - citations: list[dict]
        """
        logger.debug("Entering context merge node")

        # Build a simple merged context from ranked passages
        ranked: List[Dict[str, Any]] = state.get("ranked_passages", []) or []

        merged_parts: List[str] = []
        citation_items: List[Dict[str, Any]] = []
        for i, p in enumerate(ranked[:8]):
            text = p.get("text", "").strip()
            if not text:
                continue
            url = p.get("url")
            title = p.get("title")
            merged_parts.append(f"Source {i+1} ({title or url}):\n{text}")
            citation_items.append(normalize_citation({"url": url, "title": title}))

        merged_context = "\n".join(merged_parts) if merged_parts else state.get("context", "")
        citations = dedupe_citations(citation_items)

        return {
            "context": merged_context,
            "citations": citations,
        }


