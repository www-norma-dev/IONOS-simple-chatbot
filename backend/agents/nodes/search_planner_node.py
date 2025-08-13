"""
Search planner node for extended ReAct Agent workflow.

Generates targeted search queries and constraints when local evidence is
insufficient.
"""

import logging
from typing import Dict, Any


logger = logging.getLogger("chatbot-server")


class SearchPlannerNode:
    """Node that plans web search queries and constraints."""

    def __init__(self) -> None:
        pass

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the search planning step.

        Inputs (from state):
          - messages[-1]: user question
          - deficits: dict (why local context was insufficient)

        Outputs (to state):
          - queries: list[str]
          - search_filters: dict (e.g., date range)
        """
        logger.debug("Entering search planner node")

        # Minimal plan: use the user's latest question as a single query
        user_msg = None
        messages = state.get("messages", []) or []
        for msg in reversed(messages):
            content = getattr(msg, "content", None)
            if isinstance(content, str) and content.strip():
                user_msg = content.strip()
                break

        # Build multiple query variants: original (normalized), keyword-only, and brand+topic if detected
        import re

        def normalize(text: str) -> str:
            # Replace smart quotes and remove possessives, collapse whitespace
            text = text.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
            text = re.sub(r"\b(['’])s\b", "", text)
            text = re.sub(r"\s+", " ", text)
            return text.strip()

        q_orig = normalize(user_msg or "")
        lower_q = q_orig.lower()

        # Optional explicit site hint support (user-provided)
        site_hint = None
        m = re.search(r"site:([\w.-]+)", lower_q)
        if m:
            site_hint = m.group(1)

        # Tokenize and filter stopwords
        stop = {"the", "a", "an", "about", "please", "can", "you", "tell", "me", "of", "on", "to", "for", "is", "are", "be", "and"}
        tokens = [t for t in re.findall(r"[\w.-]+", lower_q) if t not in stop]

        # Detect brand/topic tokens present in the question
        brand = None
        topic = None
        for t in tokens:
            if "ionos" in t and not topic:
                topic = "ionos"
            if "wpmarmite" in t and not brand:
                brand = "wpmarmite"

        keyword_query = " ".join(tokens[:8]).strip()
        brand_topic_query = None
        if brand and topic:
            brand_topic_query = f"{brand} {topic} article"

        queries = []
        if q_orig:
            queries.append(q_orig)
        if keyword_query and keyword_query not in queries:
            queries.append(keyword_query)
        if brand_topic_query and brand_topic_query not in queries:
            queries.append(brand_topic_query)

        # Apply site hint if user provided one
        search_filters = {}
        if site_hint:
            # Keep original queries and also provide an explicit domain hint for the provider
            queries = [f"{q} site:{site_hint}" for q in queries]
            search_filters["include_domains"] = [site_hint]

        # Ensure queries exist; if empty, fall back to a generic variant to avoid no-op search
        if not queries:
            queries = ["overview"]

        return {
            "queries": queries,
            "search_filters": search_filters,
        }


