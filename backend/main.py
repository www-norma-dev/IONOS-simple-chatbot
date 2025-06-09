import os
import logging
import requests

from bs4 import BeautifulSoup
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    BaseMessage,
)
from langchain_openai import ChatOpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from pydantic import SecretStr, BaseModel
from mangum import Mangum

from typing import List

# ─── Logging setup ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("chatbot-server")

# ─── Load environment variables from .env ────────────────────────────────
load_dotenv()

# ─── IONOS AI Model Hub config ──────────────────────────────────────────
IONOS_API_KEY = os.getenv("IONOS_API_KEY", "")
if not IONOS_API_KEY:
    raise KeyError("IONOS_API_KEY not found in environment.")


# ─── RAG configuration ───────────────────────────────────────────────────
RAG_K = int(os.getenv("RAG_K", "3"))  # top-k chunks to retrieve
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))  # cap total number of 500-char chunks
MAX_CHUNK_COUNT = int(os.getenv("MAX_CHUNK_COUNT", "256"))  # cap total number of chunks


# ─── REQUEST MODELS ───────────────────────────────────────────────────
class NewChatRequest(BaseModel):
    page_url: str  # <-- the front‐end will send this


class UserMessage(BaseModel):
    prompt: str


# ─── FastAPI app setup ──────────────────────────────────────────────────
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
handler = Mangum(app)

origins = [
    "http://localhost:8000",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

# ─── Chat history state ─────────────────────────────────────────────────
chat_log: list[BaseMessage] = []


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


# ─── RAG index state ────────────────────────────────────────────────────
vectorizer = TfidfVectorizer()
chunk_texts: List[str] = []  # List[str]
tfidf_matrix = None  # will become a sparse matrix after fitting


# ─── Utility: Call IONOS /predictions endpoint ─────────────────────────────────
async def _call_ionos_llm(model: str, prompt: str, rag: list[str]) -> str:
    llm = ChatOpenAI(
        model=model,
        base_url="https://openai.inference.de-txl.ionos.com/v1",
        api_key=SecretStr(IONOS_API_KEY),
        temperature=0.8,
        max_tokens=500,
    )

    rag_message = SystemMessage(
        content="Information obtained from the website:\n" + "\n".join(rag)
    )
    user_message = HumanMessage(content=prompt)

    chat_log.append(rag_message)
    chat_log.append(user_message)

    logger.debug(
        "Full prompt to LLM:\n%s", "\n".join(message.content for message in chat_log)
    )

    response = await llm.ainvoke(chat_log)

    chat_log.append(AIMessage(content=response.content))

    return response.content.strip()


@app.post("/init")
async def init_index(
    req: NewChatRequest,
):
    """
    Rebuild the RAG index from scratch using the URL passed in the request body.
    """
    global chunk_texts, tfidf_matrix, chat_log

    # 1) Scrape the URL that the front end sent
    page_url = req.page_url.strip()
    if not page_url.lower().startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400, detail="URL must start with http:// or https://"
        )

    logger.info("Re-building RAG index using URL: %s", page_url)
    try:
        resp = requests.get(page_url, timeout=30)
        resp.raise_for_status()
    except Exception as exc:
        logger.error("Failed to GET %s: %s", page_url, exc)
        raise HTTPException(status_code=500, detail=f"Could not fetch page: {exc}")

    soup = BeautifulSoup(resp.text, "html.parser")
    paras = [p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()]
    full_text = "\n".join(paras)

    if not full_text.strip():
        logger.warning("No text found at %s; RAG index will be empty", page_url)

    # 2) Break into 500-character chunks:
    raw_chunks: List[str] = []
    for i in range(0, len(full_text), CHUNK_SIZE):
        raw_chunks.append(full_text[i : i + CHUNK_SIZE])

    # 3) Cap at MAX_CHUNKS
    if len(raw_chunks) > MAX_CHUNK_COUNT:
        logger.info(
            "Truncating chunks from %d to %d (MAX_CHUNKS)",
            len(raw_chunks),
            MAX_CHUNK_COUNT,
        )
        raw_chunks = raw_chunks[:MAX_CHUNK_COUNT]

    chunk_texts = raw_chunks

    # 4) Fit TF-IDF (even if chunk_texts is empty, fit on [""] to avoid None)
    if chunk_texts:
        tfidf_matrix = vectorizer.fit_transform(chunk_texts)
        logger.info("Built TF-IDF matrix with %d chunks", len(chunk_texts))
    else:
        tfidf_matrix = vectorizer.fit_transform([""])
        logger.warning(
            "Built TF-IDF on empty text, matrix shape=%s", tfidf_matrix.shape
        )

    # 5) Whenever you re‐init the RAG index, you probably want to clear previous chat history:
    chat_log = get_initial_chat()
    return {"status": "RAG initialized", "num_chunks": len(chunk_texts)}


# ─── Chat endpoints ─────────────────────────────────────────────────────
@app.get("/")
async def get_chat_logs():
    logger.info("Received GET /; returning chat_log")
    return [message.content for message in chat_log]


@app.post("/")
async def chat(
    request: Request,
    user_input: UserMessage,
):
    global chat_log

    # 1) Log headers & prompt
    headers = dict(request.headers)
    logger.info("Received POST / with headers: %s", headers)
    logger.info("Received POST / body (prompt): %s", user_input.prompt)

    # 2) TF-IDF retrieval (if we have chunks)
    top_chunks = ""
    if chunk_texts and tfidf_matrix is not None:
        user_vec = vectorizer.transform([user_input.prompt])
        sims = cosine_similarity(user_vec, tfidf_matrix).flatten()
        best_idxs = sims.argsort()[::-1][:RAG_K]
        top_chunks = [chunk_texts[i] for i in best_idxs if i < len(chunk_texts)]
        logger.debug("RAG context (top %d chunks): %s", RAG_K, top_chunks)
    else:
        logger.warning("TF-IDF not initialized or no chunks; skipping RAG context.")

    # 3) Call IONOS
    try:
        response = await _call_ionos_llm(
            "mistralai/Mixtral-8x7B-Instruct-v0.1", user_input.prompt, top_chunks
        )
    except Exception as exc:
        logger.error("IONOS predictions API error: %s", exc)
        raise HTTPException(status_code=500, detail="LLM chat error")

    return response


@app.delete("/")
async def clear_chat_log(api_key: str = Security(get_api_key)):
    global chat_log
    logger.info("Received DELETE /; clearing chat_log")
    chat_log = get_initial_chat()
    return chat_log


# ─── Run the app with Uvicorn if executed directly ───────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
