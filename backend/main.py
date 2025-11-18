import logging


 
from langchain_core.messages import (
    HumanMessage,
    AIMessage, filter_messages,
)

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.runnables import RunnableConfig
 
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt.chat_agent_executor import AgentStatePydantic
from pydantic import BaseModel
from mangum import Mangum

from typing import Optional

from chatbot_agent import create_chatbot_agent
from studio_client import studio_call, is_studio_model
import json
import os

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
    # No chat log stored on backend anymore
    return []


@app.get("/studio/models")
async def get_studio_models():
    """Return available fine-tuned Studio models from env."""
    import os
    models = {
        "qwen-gdpr": os.getenv("STUDIO_MODEL_QWEN_GDPR"),
        "granite-gdpr": os.getenv("STUDIO_MODEL_GRANITE_GDPR"),
        "qwen3-sharegpt": os.getenv("STUDIO_QWEN3_SHAREGPT"),
        "Qwen3-customersupport": os.getenv("STUDIO_QWEN3_customersupport"),
        "AlpacaBot": os.getenv("STUDIO_ALPACA_BOT"),
    }
    # Filter out None values
    return {k: v for k, v in models.items() if v}


@app.post("/")
async def chat(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    stream = request.query_params.get("stream") == "true"
    
    model_id = request.headers.get("x-model-id")
    
    if not model_id:
        raise HTTPException(status_code=400, detail="Missing x-model-id header")
    
    # Keep chat log manageable (last 50 messages)
    if len(messages) > 50:
        messages = messages[-50:]
    
    # Route to Studio or Hub based on model ID format
    if is_studio_model(model_id):
        if stream:
            raise HTTPException(status_code=400, detail="Studio models do not support streaming")
        try:
            text = studio_call(model_id, messages)
            return {"type": "ai", "content": text}
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e))
    
    # Hub inference model
    is_reasoning_model = "gpt-oss" in model_id.lower() or "o1" in model_id.lower()
    
    if is_reasoning_model:
        # Direct API call for reasoning models (no tools)
        from openai import OpenAI
        client = OpenAI(base_url="https://openai.inference.de-txl.ionos.com/v1", api_key=os.getenv("IONOS_API_KEY"))
        openai_msgs = [{"role": "user" if m["type"] in ("human", "user") else "assistant", "content": m["content"]}
                       for m in messages if m["type"] in ("human", "user", "ai", "assistant")]
        
        if stream:
            def generate():
                yield f"data: {json.dumps({'status': 'thinking'})}\n\n"
                try:
                    for chunk in client.chat.completions.create(model=model_id, messages=openai_msgs, stream=True, max_tokens=2048):
                        if chunk.choices[0].delta.content:
                            yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return StreamingResponse(generate(), media_type="text/event-stream")
        
        response = client.chat.completions.create(model=model_id, messages=openai_msgs, max_tokens=2048)
        return {"type": "ai", "content": response.choices[0].message.content}
    
    # Regular models - use agent for web search
    agent = create_chatbot_agent(model_id)
    
    def build_state_messages(msgs):
        state_messages = []
        for m in msgs:
            if m["type"] == "human":
                state_messages.append(HumanMessage(content=m["content"]))
            elif m["type"] == "ai":
                state_messages.append(AIMessage(content=m["content"]))
            elif m["type"] == "tool":
                state_messages.append({"type": "tool", "name": m.get("name", "tool"), "content": m["content"]})
            else:
                state_messages.append(m)
        return state_messages
    
    state_messages = build_state_messages(messages)
    
    if stream:
        def generate():
            yield f"data: {json.dumps({'status': 'thinking'})}\n\n"
            try:
                result = AgentStatePydantic.model_validate(
                    agent.invoke(input=AgentStatePydantic(messages=state_messages), config=RunnableConfig())
                )
                content = result.messages[-1].content if result.messages else ""
                
                # Stream response smoothly
                import time
                for i in range(0, len(content), 5):
                    yield f"data: {json.dumps({'content': content[i:i+5]})}\n\n"
                    time.sleep(0.01)
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        return StreamingResponse(generate(), media_type="text/event-stream")
    
    # Non-streaming
    state = AgentStatePydantic(messages=state_messages)
    result = agent.invoke(input=state, config=RunnableConfig())
    state = AgentStatePydantic.model_validate(result)
    return state.messages[-1]


# ─── Run the app with Uvicorn if executed directly ───────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
