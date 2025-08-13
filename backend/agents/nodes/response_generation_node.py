#Unified response emitter for both legacy and extended workflows. Generates a plain-language, grounded answer based on the current state If citations are present (web-enriched), it naturally references sources; otherwise it emits a local-only answer.
import logging
from typing import Any, Dict, List
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

class ResponseGenerationNode:
    def __init__(self, llm): self.llm = llm

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        msgs: List[Any] = state.get("messages", []) or []
        q = next((m.content for m in reversed(msgs)
                  if isinstance(m, HumanMessage) and isinstance(m.content, str) and m.content.strip()), "")
        ctx = state.get("context", "") or ""
        cites = state.get("citations", []) or []
        src_lines = [" | ".join([x for x in [c.get("domain"), c.get("title"), c.get("date")] if x]) for c in cites[:5]]
        sources = ("\nSources:\n- " + "\n- ".join(src_lines)) if src_lines else ""
        prompt = (
            "You are a helpful assistant. Answer in plain, user-friendly language.\n"
            "Base your answer strictly on Context; if info is missing, say so and suggest where to look.\n\n"
            f"Context:\n{ctx}\n{sources}\n\nQuestion: {q}"
        )
        try:
            resp = await self.llm.ainvoke([SystemMessage(content=prompt)])
            content = (getattr(resp, "content", "") or "").strip() or "I could not complete the answer generation at this time."
        except Exception as e:
            logging.getLogger("chatbot-server").warning("Response gen failed: %s", e)
            content = "I could not complete the answer generation at this time."
        logging.getLogger("chatbot-server").info("Emit: citations=%d", len(cites))
        return {"messages": [AIMessage(content=content)], "final_answer": content}