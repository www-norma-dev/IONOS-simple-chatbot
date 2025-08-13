"""
Response sufficiency gate node for extended ReAct Agent workflow.

Determines if the locally available context is sufficient to answer the
user's question. If insufficient, downstream search and merge nodes
should be invoked.
"""

import logging
from typing import Dict, Any
from utils.config import Config


logger = logging.getLogger("chatbot-server")


class ResponseSufficiencyNode:
    """Node that decides if more evidence is needed beyond local context."""

    def __init__(self) -> None:
        pass

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the sufficiency decision step.

        Inputs (from state):
          - draft_answer: str
          - local_passages: list[dict]
          - budgets/thresholds (optional)

        Outputs (to state):
          - decision: "sufficient" | "insufficient"
          - deficits: dict (why insufficient)
        """
        logger.debug("Entering response sufficiency node")

        local_passages = state.get("local_passages", []) or []

        # Extract the latest user message text
        user_text = ""
        for msg in reversed(state.get("messages", []) or []):
            content = getattr(msg, "content", None)
            if isinstance(content, str) and content.strip():
                user_text = content.strip().lower()
                break

        # Simple triggers that indicate web search is likely needed
        web_triggers = [
            "article",
            "review",
            "news",
            "latest",
            "today",
            "update",
            "price",
            "law",
        ]
        trigger_hit = any(k in user_text for k in web_triggers)

        min_hits = getattr(Config, "MIN_LOCAL_HITS", 3)
        # Consider a passage non-empty only if it has at least ~200 chars
        non_empty = [p for p in local_passages if isinstance(p.get("text"), str) and len(p.get("text")) >= 200]
        has_coverage = len(non_empty) >= max(1, int(min_hits))

        if trigger_hit and not has_coverage:
            decision = "insufficient"
            deficits = {"reason": "trigger_and_low_coverage"}
        elif has_coverage and not trigger_hit:
            decision = "sufficient"
            deficits = {}
        else:
            # Borderline: lean towards web to be helpful
            decision = "insufficient"
            deficits = {"reason": "borderline"}

        logger.info("Sufficiency decision: %s", decision)
        return {
            "decision": decision,
            "deficits": deficits,
        }


