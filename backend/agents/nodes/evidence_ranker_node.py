"""
Evidence ranking node for extended ReAct Agent workflow.

Unifies local and web passages, deduplicates, and ranks them for
downstream context preparation.
"""

import logging
from typing import Dict, Any, List, Tuple

from utils.ranking import mmr_diversify
import re


logger = logging.getLogger("chatbot-server")


class EvidenceRankerNode:
    """Node that ranks and deduplicates evidence passages."""

    def __init__(self) -> None:
        pass

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the evidence ranking step.

        Inputs (from state):
          - local_passages: list[dict]
          - web_passages: list[dict]
          - messages[-1]: user query (for scoring)

        Outputs (to state):
          - ranked_passages: list[dict]
        """
        logger.debug("Entering evidence ranker node")

        local: List[Dict[str, Any]] = state.get("local_passages", []) or []
        web: List[Dict[str, Any]] = state.get("web_passages", []) or []
        query = None
        for msg in reversed(state.get("messages", []) or []):
            content = getattr(msg, "content", None)
            if isinstance(content, str) and content.strip():
                query = content.strip()
                break

        unified: List[Dict[str, Any]] = []
        # Normalize local/web to a common schema
        for p in local:
            unified.append({
                "text": p.get("text", ""),
                "url": p.get("url"),
                "title": p.get("title"),
                "source": "local",
            })
        for p in web:
            unified.append({
                "text": p.get("passage", ""),
                "url": p.get("url"),
                "title": p.get("title"),
                "source": "web",
            })

        # Simple keyword-overlap scoring as a quick improvement over zeros
        def keyword_score(text: str, q: str) -> float:
            if not text or not q:
                return 0.0
            q_tokens = set(re.findall(r"[\w-]+", q.lower()))
            t_tokens = set(re.findall(r"[\w-]+", text.lower()))
            if not q_tokens:
                return 0.0
            return len(q_tokens & t_tokens) / len(q_tokens)

        scored: List[Tuple[Dict[str, Any], float]] = []
        for item in unified:
            s = keyword_score(item.get("text", ""), query or "")
            scored.append((item, s))
        # Dedup by URL + first 80 chars
        seen = set()
        deduped: List[Tuple[Dict[str, Any], float]] = []
        for item, score in scored:
            key = (item.get("url"), (item.get("text") or "")[:80])
            if key in seen:
                continue
            seen.add(key)
            deduped.append((item, score))
        ranked = mmr_diversify(deduped, top_k=10)

        return {
            "ranked_passages": ranked,
        }


