"""
Response draft node for extended ReAct Agent workflow.

This node produces a preliminary draft answer using the currently prepared
local context. It does not emit an AIMessage; emission occurs in the
finalization node to ensure a single message is appended per turn.
"""

import logging
from typing import Dict, Any, Optional


logger = logging.getLogger("chatbot-server")


class ResponseDraftNode:
    """Node that creates a draft answer from local context only."""

    def __init__(self, llm: Optional[Any] = None):
        # LLM is optional for the initial scaffold; may be used in implementation
        self.llm = llm

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the response drafting step.

        Inputs (from state):
          - messages[-1]: latest user message
          - context: prepared local context text

        Outputs (to state):
          - draft_answer: str
          - citations: list[dict]
        """
        logger.debug("Entering response draft node")

        # Minimal draft: just acknowledge; real drafting will use LLM
        draft_answer: str = "Preliminary draft based on local context."
        citations: list[dict] = []

        return {
            "draft_answer": draft_answer,
            "citations": citations,
        }


