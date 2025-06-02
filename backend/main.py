# main.py
import os
import uuid
import logging
import requests
import httpx

from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel
from mangum import Mangum

from typing import List, Optional

# ─── Logging setup ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("chatbot-server")

# ─── Load environment variables from .env ────────────────────────────────
load_dotenv()

# ─── Shared secret for frontend ↔ backend lock ──────────────────────────
ACCEPTED_API_KEY = os.getenv("ACCEPTED_API_KEY", "")
if not ACCEPTED_API_KEY:
    raise KeyError("ACCEPTED_API_KEY not found in environment.")

# ─── IONOS AI Model Hub config ──────────────────────────────────────────
IONOS_API_KEY  = os.getenv("IONOS_API_KEY", "")
IONOS_MODEL_ID = os.getenv("IONOS_MODEL_ID", "")
IONOS_API_URL  = os.getenv("IONOS_API_URL", "").rstrip("/")  # e.g. "https://inference.de-txl.ionos.com"
if not (IONOS_API_KEY and IONOS_MODEL_ID and IONOS_API_URL):
    raise KeyError("IONOS_API_URL, IONOS_MODEL_ID, or IONOS_API_KEY not found in environment.")

# ─── RAG configuration ───────────────────────────────────────────────────
# We remove “WEBSITE_URL = …” here, because we’ll no longer rely on .env alone.
RAG_K      = int(os.getenv("RAG_K", "3"))      # top-k chunks to retrieve
MAX_CHUNKS = int(os.getenv("MAX_RAG_CHUNKS", "100"))  # cap total number of 500-char chunks

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

api_key_query  = APIKeyQuery(name="api-key", auto_error=False)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

def get_api_key(
    api_key_query: Optional[str] = Security(api_key_query),
    api_key_header: Optional[str] = Security(api_key_header),
) -> str:
    """
    Ensures the caller provides the correct shared secret (via x-api-key header or ?api-key query).
    """
    if api_key_query == ACCEPTED_API_KEY or api_key_header == ACCEPTED_API_KEY:
        return ACCEPTED_API_KEY

    logger.warning(
        "get_api_key: unauthorized attempt. api_key_query=%s, api_key_header=%s",
        api_key_query, api_key_header
    )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )

# ─── Chat history state ─────────────────────────────────────────────────
EXCLUDED_CHATS  = ["image", "info"]
INITIAL_CHATLOG = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "info",   "content": (
        "Hello!\n\nI'm a personal assistant chatbot. "
        "I will respond as best I can to any messages you send me."
    )},
]
chat_log: List[dict] = list(INITIAL_CHATLOG)

class UserInputIn(BaseModel):
    prompt: str

class InitRequest(BaseModel):
    page_url: str   # <-- the front‐end will send this

# ─── RAG index state ────────────────────────────────────────────────────
vectorizer   = TfidfVectorizer()
chunk_texts  : List[str] = []        # List[str]
tfidf_matrix = None      # will become a sparse matrix after fitting

@app.post("/init")
async def init_index(
    req: InitRequest,
    api_key: str = Security(get_api_key),
):
    """
    Rebuild the RAG index from scratch using the URL passed in the request body.
    """
    global chunk_texts, tfidf_matrix, chat_log

    # 1) Scrape the URL that the front end sent
    page_url = req.page_url.strip()
    if not page_url.lower().startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    logger.info("Re-building RAG index using URL: %s", page_url)
    try:
        resp = requests.get(page_url, timeout=30)
        resp.raise_for_status()
    except Exception as exc:
        logger.error("Failed to GET %s: %s", page_url, exc)
        raise HTTPException(status_code=500, detail=f"Could not fetch page: {exc}")

    soup = BeautifulSoup(resp.text, "html.parser")
    paras = [
        p.get_text().strip()
        for p in soup.find_all("p")
        if p.get_text().strip()
    ]
    full_text = "\n".join(paras)

    if not full_text.strip():
        logger.warning("No text found at %s; RAG index will be empty", page_url)

    # 2) Break into 500-character chunks:
    raw_chunks: List[str] = []
    for i in range(0, len(full_text), 500):
        raw_chunks.append(full_text[i : i + 500])

    # 3) Cap at MAX_CHUNKS
    if len(raw_chunks) > MAX_CHUNKS:
        logger.info(
            "Truncating chunks from %d to %d (MAX_CHUNKS)",
            len(raw_chunks), MAX_CHUNKS
        )
        raw_chunks = raw_chunks[:MAX_CHUNKS]

    chunk_texts = raw_chunks

    # 4) Fit TF-IDF (even if chunk_texts is empty, fit on [""] to avoid None)
    if chunk_texts:
        tfidf_matrix = vectorizer.fit_transform(chunk_texts)
        logger.info("Built TF-IDF matrix with %d chunks", len(chunk_texts))
    else:
        tfidf_matrix = vectorizer.fit_transform([""])
        logger.warning("Built TF-IDF on empty text, matrix shape=%s", tfidf_matrix.shape)

    # 5) Whenever you re‐init the RAG index, you probably want to clear previous chat history:
    chat_log = list(INITIAL_CHATLOG)
    return {"status": "RAG initialized", "num_chunks": len(chunk_texts)}

# ─── Utility: Call IONOS /predictions endpoint ─────────────────────────────────
async def call_ionos_llm(prompt: str) -> str:
    """
    Calls IONOS’s predictions endpoint with a single prompt.
    Returns the assistant’s response text.
    """
    endpoint = f"{IONOS_API_URL}/{IONOS_MODEL_ID}/predictions"
    headers = {
        "Authorization": f"Bearer {IONOS_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "properties": { "input": prompt },
        "option": {
            "temperature": 0.8,
            "maxTokens": 500,
            "seed": uuid.uuid4().int & ((1 << 16) - 1),
        }
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(endpoint, headers=headers, json=payload)
    resp.raise_for_status()
    result = resp.json()
    # IONOS returns: { "properties": { "output": "..." } }
    return result.get("properties", {}).get("output", "").strip()

# ─── OpenAPI & Swagger UI endpoints ─────────────────────────────────────
@app.get("/docs", include_in_schema=False)
async def get_documentation(api_key: str = Security(get_api_key)):
    openapi_url = "/openapi.json?api-key=" + api_key
    return get_swagger_ui_html(openapi_url=openapi_url, title="docs")

@app.get("/openapi.json", include_in_schema=False)
async def openapi(api_key: str = Security(get_api_key)):
    return get_openapi(title="FastAPI", version="0.1.0", routes=app.routes)

# ─── Chat endpoints ─────────────────────────────────────────────────────
@app.get("/")
async def get_chat_logs(api_key: str = Security(get_api_key)):
    logger.info("Received GET /; returning chat_log")
    return chat_log

@app.post("/")
async def chat(
    request: Request,
    user_input: UserInputIn,
    api_key: str = Security(get_api_key),
):
    global chat_log

    # 1) Log headers & prompt
    headers = dict(request.headers)
    logger.info("Received POST / with headers: %s", headers)
    logger.info("Received POST / body (prompt): %s", user_input.prompt)

    # 2) Append user's message
    chat_log.append({"role": "user", "content": user_input.prompt})

    # 3) TF-IDF retrieval (if we have chunks)
    context = ""
    if chunk_texts and tfidf_matrix is not None:
        user_vec = vectorizer.transform([user_input.prompt])
        sims = cosine_similarity(user_vec, tfidf_matrix).flatten()
        best_idxs = sims.argsort()[::-1][:RAG_K]
        top_chunks = [chunk_texts[i] for i in best_idxs if i < len(chunk_texts)]
        context = "\n".join(top_chunks)
        logger.debug("RAG context (top %d chunks): %s", RAG_K, top_chunks)
    else:
        logger.warning("TF-IDF not initialized or no chunks; skipping RAG context.")

    # 4) Build the full prompt
    prompt_text = f"Context:\n{context}\n\nConversation:\n"
    history = [m for m in chat_log if m["role"] not in EXCLUDED_CHATS]
    for m in history:
        prompt_text += f"{m['role']}: {m['content']}\n"
    logger.debug("Full prompt to LLM:\n%s", prompt_text)

    # 5) Call IONOS /{model_id}/predictions
    try:
        bot_response = await call_ionos_llm(prompt_text)
    except Exception as exc:
        logger.error("IONOS predictions API error: %s", exc)
        raise HTTPException(status_code=500, detail="LLM chat error")

    # 6) Append assistant’s response
    chat_log.append({"role": "assistant", "content": bot_response})
    return chat_log

@app.post("/i")
async def gen_image(
    request: Request,
    user_input: UserInputIn,
    api_key: str = Security(get_api_key),
):
    logger.warning("Received POST /i; image endpoint not implemented")
    raise HTTPException(status_code=501, detail="Image endpoint not implemented")

@app.delete("/")
async def clear_chat_log(api_key: str = Security(get_api_key)):
    global chat_log
    logger.info("Received DELETE /; clearing chat_log")
    chat_log = list(INITIAL_CHATLOG)
    return chat_log

# ─── Optional utility: return a single embedding vector on demand ─────────
@app.post("/embeddings")
async def embeddings(
    request: Request,
    user_input: UserInputIn,
    api_key: str = Security(get_api_key),
):
    """
    Returns the raw embedding vector (via IONOS /v1/embeddings) for the given text.
    Just a helper endpoint—does not affect chat state.
    """
    embedding_endpoint = "https://openai.inference.de-txl.ionos.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {IONOS_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": os.getenv("EMBEDDING_MODEL_ID", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"),
        "input": [user_input.prompt],
    }

    try:
        resp = requests.post(embedding_endpoint, headers=headers, json=body, timeout=60.0)
        resp.raise_for_status()
        data = resp.json()
        embedding_vec = data["data"][0]["embedding"]
        return {"embedding": embedding_vec}
    except Exception as exc:
        logger.error("Failed to fetch embedding: %s", exc)
        raise HTTPException(status_code=500, detail="Embedding generation failed")

# ─── Run the app with Uvicorn if executed directly ───────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
