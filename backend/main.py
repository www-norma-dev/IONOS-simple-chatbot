import os
import logging

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    BaseMessage,
)

from fastapi import FastAPI, HTTPException, Request, Security, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import SecretStr, BaseModel
from mangum import Mangum

from typing import List
import shutil
from agents import create_react_agent
from utils import RAGInitializer, Config

# ─── Configuration validation ────────────────────────────────────────────
Config.validate()

# ─── Logging setup ───────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT
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
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

# ─── Chat history state ─────────────────────────────────────────────────
chat_log: list[BaseMessage] = []
current_url: str = ""  # Track the current URL being discussed

# ─── RAG index state ────────────────────────────────────────────────────
chunk_texts: List[str] = []  # List[str]
tfidf_matrix = None  # will become a sparse matrix after fitting

# ─── RAG Initializer ────────────────────────────────────────────────────
rag_initializer = RAGInitializer(chunk_size=Config.CHUNK_SIZE, max_chunk_count=Config.MAX_CHUNK_COUNT)

# ─── ReAct Agent ────────────────────────────────────────────────────────
react_agent = None  # Will be initialized when needed

# ─── Upload storage ─────────────────────────────────────────────────────
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(__file__), "uploaded_docs"))
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_initial_chat() -> list[BaseMessage]:
    return [
        SystemMessage(
            content="You are an assistant. Your role is to help the user query information about a website."
        ),
        AIMessage(
            content=(
                "Hello!\n\nI'm a personal assistant chatbot. "
                "I will respond as best I can to any messages you send me."
            )
        ),
    ]



@app.post("/init")
async def init_index(
    req: NewChatRequest,
):
    """
    Initialize the chatbot with a URL and build RAG index from scraped content.
    """
    global chunk_texts, tfidf_matrix, chat_log, current_url

    # 1) Set the current URL context
    current_url = req.page_url.strip()

    # 2) Use RAGInitializer to scrape and build index
    try:
        chunk_texts, tfidf_matrix = await rag_initializer.initialize_rag_index(current_url)
    except HTTPException:
        # Re-raise HTTPExceptions as they are already properly formatted
        raise
    except Exception as exc:
        logger.error("Unexpected error during RAG initialization: %s", exc)
        raise HTTPException(status_code=500, detail=f"RAG initialization error: {exc}")

    # 3) Reset chat history
    chat_log = get_initial_chat()
    
    # 4) Return standardized result
    return rag_initializer.get_initialization_result(current_url, len(chunk_texts))


# ─── File upload endpoint ────────────────────────────────────────────────
@app.post("/upload")
async def upload(files: List[UploadFile] = File(...)):
    """
    Accept multiple files and store them server-side. Returns list of file paths
    that can be used as `doc_sources` in chat requests.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    allowed_exts = {".pdf", ".docx", ".txt"}
    saved_paths: List[str] = []

    for file in files:
        original_name = file.filename or "uploaded"
        ext = os.path.splitext(original_name)[1].lower()
        if ext not in allowed_exts:
            logger.warning("Skipping unsupported file type: %s", original_name)
            continue

        safe_name = original_name.replace("..", "").replace("/", "_").replace("\\", "_")
        target_path = os.path.join(UPLOAD_DIR, safe_name)

        # Ensure unique filename
        base, extension = os.path.splitext(target_path)
        idx = 1
        while os.path.exists(target_path):
            target_path = f"{base}_{idx}{extension}"
            idx += 1

        try:
            with open(target_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        finally:
            await file.close()

        saved_paths.append(target_path)

    if not saved_paths:
        raise HTTPException(status_code=400, detail="No supported files uploaded")

    logger.info("Uploaded %d files", len(saved_paths))
    return {"doc_sources": saved_paths}


# ─── Chat endpoints ─────────────────────────────────────────────────────
@app.get("/")
async def get_chat_logs():
    logger.info("Received GET /; returning chat_log")
    return chat_log


@app.post("/")
async def chat(request: Request, user_input: UserMessage):
    global chat_log, react_agent, current_url

    # 1) Log prompt
    logger.info("Received chat POST; prompt=%s", user_input.prompt)

    # 2) Get the model identifier from headers
    model_id = request.headers.get("x-model-id")
    if not model_id:
        raise HTTPException(status_code=400, detail="Missing x-model-id header")

    # 3) Retrieve relevant chunks using RAG
    top_chunks = []
    if chunk_texts and tfidf_matrix is not None:
        top_chunks = rag_initializer.get_relevant_chunks(
            query=user_input.prompt,
            chunk_texts=chunk_texts,
            tfidf_matrix=tfidf_matrix,
            top_k=Config.RAG_K
        )

    # 4) Initialize ReAct agent if not already done
    if react_agent is None:
        logger.info("Initializing ReAct agent with model: %s", model_id)
        react_agent = create_react_agent(
            model_name=model_id,
            api_key=Config.IONOS_API_KEY,
            base_url="https://openai.inference.de-txl.ionos.com/v1",
            temperature=0.1,
            max_tokens=1000,
            chunk_size=Config.CHUNK_SIZE,
            max_chunk_count=Config.MAX_CHUNK_COUNT
        )

    # 5) Determine document sources
    # Priority: request-specific doc_sources -> env-configured DOC_SOURCES -> none
    doc_sources = user_input.doc_sources if user_input.doc_sources is not None else Config.DOC_SOURCES

    # 6) Process message through ReAct agent with RAG context and potential doc sources
    try:
        response_text = await react_agent.process_message_with_rag(
            message=user_input.prompt,
            rag_chunks=top_chunks,
            current_url=current_url if current_url else None,
            doc_sources=doc_sources,
        )
        
        # Update chat log for consistency
        user_message = HumanMessage(content=user_input.prompt)
        ai_message = AIMessage(content=response_text)
        chat_log.extend([user_message, ai_message])
        
        # Keep chat log manageable (last 20 messages)
        if len(chat_log) > 20:
            chat_log = chat_log[-20:]
            
    except Exception as exc:
        logger.error("ReAct agent error: %s", exc)
        raise HTTPException(status_code=500, detail="Agent processing error")

    return response_text




# ─── Run the app with Uvicorn if executed directly ───────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
