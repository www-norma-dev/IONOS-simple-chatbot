"""
Unified response emitter for both legacy and extended workflows.

Generates a plain-language, grounded answer based on the current state.
If citations are present (web-enriched), it naturally references sources;
otherwise it emits a local-only answer.
"""

import logging
from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

logger = logging.getLogger("chatbot-server")


class ResponseGenerationNode:
    """Single emitter node for legacy and extended flows."""

    def __init__(self, llm):
        self.llm = llm

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize and emit the final answer."""
        logger.debug("Entering unified response generation node")

        # Extract user question
        user_message = None
        for msg in reversed(state.get("messages", []) or []):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break

        context = state.get("context", "")
        citations = state.get("citations", []) or []
        reasoning = state.get("reasoning", "")

        # Build a non-technical prompt that adapts to presence of citations
        citation_hint = "\n- Where relevant, mention sources by site name or title." if citations else ""
        response_prompt = f"""
You are a helpful assistant. Answer in plain, user-friendly language.
Avoid technical terms like 'chunks', 'RAG', or 'retrieval'.{citation_hint}

Context:
{context}

Question: {user_message}

Guidelines:
- Be concise, clear, and non-technical.
- Base your answer on the provided context.
- If you couldn't find the requested source or article, say so and suggest where to look.
"""

        messages = [SystemMessage(content=response_prompt)]
        try:
            response = await self.llm.ainvoke(messages)
            content = (response.content or "").strip()
            if not content:
                content = "I could not complete the answer generation at this time."
        except Exception:
            content = "I could not complete the answer generation at this time."

        ai_message = AIMessage(content=content)
        try:
            import logging as _logging
            _logging.getLogger("chatbot-server").info("Emit: citations=%d", len(citations))
        except Exception:
            pass
        return {"messages": [ai_message], "final_answer": content}
