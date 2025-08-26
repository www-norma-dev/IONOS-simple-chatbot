import logging

from langchain_community.document_loaders import WebBaseLoader
from langchain_community.retrievers import TFIDFRetriever
from langchain_core.messages import (
    HumanMessage,
    AIMessage, filter_messages,
)

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.runnables import RunnableConfig
from langchain_text_splitters import RecursiveCharacterTextSplitter
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

# Per-user session storage
user_sessions = {}
retriever: Optional[TFIDFRetriever] = None

def reset_chatbot(model_name):
    agent = create_chatbot_agent(model_name)
    state = AgentStatePydantic(messages=[AIMessage(
        content=(
            "Hello!\n\nI'm a personal assistant chatbot. "
            "I will respond as best I can to any messages you send me."
        )
    )])
    return agent, state


@app.post("/init")
async def init_index(
        req: NewChatRequest,
):
    global retriever

    url = req.page_url.strip()
    loader = WebBaseLoader(url)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    retriever = TFIDFRetriever.from_documents(chunks)

    return {
        "status": "RAG index initialized",
        "url": url,
        "num_chunks": len(chunks),
        "message": f"Successfully scraped and indexed {len(chunks),} chunks from {url}"
    }


# ─── Chat endpoints ─────────────────────────────────────────────────────

@app.get("/")
async def get_chat_logs(request: Request):
    user_id = request.headers.get("x-user-id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing x-user-id header")
    session = user_sessions.get(user_id)
    if session is None:
        return []
    return filter_messages(session["state"].messages, exclude_tool_calls=True)



@app.post("/")
async def chat(request: Request, user_input: UserMessage):
    user_id = request.headers.get("x-user-id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing x-user-id header")
    model_id = request.headers.get("x-model-id")
    if not model_id:
        raise HTTPException(status_code=400, detail="Missing x-model-id header")

    # Get or create session for this user
    session = user_sessions.get(user_id)
    if session is None or session["model_id"] != model_id:
        agent, state = reset_chatbot(model_id)
        user_sessions[user_id] = {"agent": agent, "state": state, "model_id": model_id}
    else:
        agent = session["agent"]
        state = session["state"]

    try:
        state.messages += [HumanMessage(content=user_input.prompt)]
        result = agent.invoke(input=state, config=RunnableConfig(configurable={'retriever': retriever}))
        state = AgentStatePydantic.model_validate(result)
        user_sessions[user_id]["state"] = state

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
