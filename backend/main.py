import logging

 
from langchain_core.messages import (
    HumanMessage,
    AIMessage, filter_messages,
)

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.runnables import RunnableConfig
 
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt.chat_agent_executor import AgentStatePydantic
from pydantic import BaseModel
from mangum import Mangum

from typing import Optional

from chatbot_agent import create_chatbot_agent

# ─── Logging setup ───────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("chatbot-server")


# ─── REQUEST MODELS ───────────────────────────────────────────────────
class NewChatRequest(BaseModel):
    page_url: str


class UserMessage(BaseModel):
    prompt: str
    # Optional list of document sources (paths or URLs) for this request
    doc_sources: list[str] | None = None


# ─── FastAPI app setup ──────────────────────────────────────────────────
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
handler = Mangum(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)


 





# ─── Chat endpoints ─────────────────────────────────────────────────────
@app.get("/")
async def get_chat_logs():
    logger.info("Received GET /; returning chat_log")
    # No chat log stored on backend anymore
    return []


@app.post("/")
async def chat(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    logger.info(f"Injecting messages into agent state: {messages}")
    model_id = request.headers.get("x-model-id")
    logger.info(f"Received x-model-id header: {model_id}")
    if not model_id:
        raise HTTPException(status_code=400, detail="Missing x-model-id header")
    # Create agent and state from scratch for each request
    agent = create_chatbot_agent(model_id)
    state_messages = []
    for m in messages:
        if m["type"] == "human":
            state_messages.append(HumanMessage(content=m["content"]))
        elif m["type"] == "ai":
            state_messages.append(AIMessage(content=m["content"]))
        elif m["type"] == "tool":
            state_messages.append({"type": "tool", "name": m.get("name", "tool"), "content": m["content"]})
        else:
            state_messages.append(m)
        logger.info(f"Injecting messages into agent state: {messages}")
    state = AgentStatePydantic(messages=state_messages)
    try:
        result = agent.invoke(input=state, config=RunnableConfig())
        state = AgentStatePydantic.model_validate(result)
        # Keep chat log manageable (last 20 messages)
        if len(state.messages) > 20:
            state.messages = state.messages[-20:]
    except Exception as exc:
        logger.error("ReAct agent error: %s", exc)
        raise HTTPException(status_code=500, detail="Agent processing error")
    return state.messages[-1]


# ─── Run the app with Uvicorn if executed directly ───────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
