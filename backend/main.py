# main.py

import os
import uuid
import logging
import httpx
import numpy as np

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
from dotenv import load_dotenv
load_dotenv()

# ─── Shared secret for frontend ↔ backend lock ──────────────────────────
api_key = os.getenv("ACCEPTED_API_KEY", "")
if not api_key:
    raise KeyError("ACCEPTED_API_KEY not found in environment.")

# ─── IONOS AI Model Hub config ──────────────────────────────────────────
ionos_api_key = os.getenv("IONOS_API_KEY", "")
ionos_model_id = os.getenv("IONOS_MODEL_ID", "")
ionos_api_url = os.getenv("IONOS_API_URL", "")
if not (ionos_api_key and ionos_model_id and ionos_api_url):
    raise KeyError("IONOS_API_URL, IONOS_MODEL_ID, or IONOS_API_KEY not found in environment.")

# ─── RAG configuration ───────────────────────────────────────────────────
website_url = os.getenv("WEBSITE_URL", "")
if not website_url:
    raise KeyError("WEBSITE_URL not found in environment.")
k_retrieval = int(os.getenv("RAG_K", "3"))              # top‐k chunks to retrieve
MAX_CHUNKS = int(os.getenv("MAX_RAG_CHUNKS", "100"))     # cap total number of 500‐char chunks

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

api_key_query = APIKeyQuery(name="api-key", auto_error=False)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

def get_api_key(
    api_key_query: Optional[str] = Security(api_key_query),
    api_key_header: Optional[str] = Security(api_key_header),
) -> str:
    """
    Ensures the caller provides the correct shared secret (via x-api-key or query).
    """
    if api_key_query == api_key or api_key_header == api_key:
        return api_key

    # Log unauthorized attempts
    logger.warning(
        "get_api_key: unauthorized attempt. api_key_query=%s, api_key_header=%s",
        api_key_query, api_key_header
    )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )

# ─── Chat history state ─────────────────────────────────────────────────
EXCLUDED_CHATS = ["image", "info"]
INITIAL_CHATLOG = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "info", "content": (
        "Hello!\n\nI'm a personal assistant chatbot. I will respond as"
        " best I can to any messages you send me."
    )},
]
chat_log: List[dict] = list(INITIAL_CHATLOG)

class UserInputIn(BaseModel):
    prompt: str

# ─── RAG index state ────────────────────────────────────────────────────
chunk_texts: List[str] = []
chunk_embeddings: List[np.ndarray] = []   # holds embedding vectors for each chunk
embedding_model = None                     # placeholder for IONOS embedding model ID
embedding_endpoint = None                  # placeholder for the /embeddings endpoint URL

# ─── Utility: Call IONOS embeddings endpoint ───────────────────────────
def get_embedding(text: str) -> np.ndarray:
    """
    Calls IONOS’s OpenAI-compatible embeddings endpoint for a single text chunk.
    Returns a NumPy array of floats representing the embedding.
    """
    url = embedding_endpoint  # e.g., "https://inference.de-txl.ionos.com/embeddings"
    headers = {
        "Authorization": f"Bearer {ionos_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": embedding_model,   # e.g., "PARAPHRASE-MULTILINGUAL-MPNET-BASE-V2"
        "input": text
    }

    resp = httpx.post(url, headers=headers, json=payload, timeout=60.0)
    resp.raise_for_status()
    data = resp.json()
    # the JSON structure is: {"data":[{"embedding":[...]}], ...}
    embedding_list = data["data"][0]["embedding"]
    return np.array(embedding_list, dtype=np.float32)

# ─── Utility: Call IONOS chat endpoint ──────────────────────────────────
async def call_ionos_chat(prompt: str) -> str:
    """
    Calls IONOS’s OpenAI-compatible chat completions endpoint with a single prompt.
    Returns the assistant’s response text.
    """
    url = f"{ionos_api_url.rstrip('/')}/{ionos_model_id}/chat/completions"
    headers = {
        "Authorization": f"Bearer {ionos_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": ionos_model_id,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 500,
        "n": 1,
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    response_json = resp.json()
    # The JSON structure: {"choices":[{"message":{"role":"assistant","content":"..."}}], ...}
    return response_json["choices"][0]["message"]["content"]

# ─── Build RAG index at startup ─────────────────────────────────────────
@app.on_event("startup")
def build_rag_index():
    """
    1. Scrape text from WEBSITE_URL using Unstructured.io’s partition() function.
    2. Concatenate all element texts into one string.
    3. Split into 500‐character chunks and cap at MAX_CHUNKS.
    4. Generate embeddings for each chunk via IONOS /embeddings.
    5. Store (chunk_text, chunk_embedding) in memory.
    """
    global chunk_texts, chunk_embeddings, embedding_model, embedding_endpoint

    logger.info("Starting RAG index build using Unstructured.io and IONOS embeddings")

    # Determine embedding endpoint & model
    embedding_endpoint = os.path.join(ionos_api_url.rstrip("/"), "embeddings")
    embedding_model = os.getenv("EMBEDDING_MODEL_ID", "PARAPHRASE-MULTILINGUAL-MPNET-BASE-V2")

    # 1) Scrape via Unstructured.io
    try:
        from unstructured.partition.auto import partition  # dynamic import
        elements = partition(url=website_url)
        logger.info("Unstructured.io partition succeeded: %d elements", len(elements))
        texts = [elem.to_string() for elem in elements if hasattr(elem, "to_string")]
        full_text = "\n".join(texts)
    except Exception as e:
        logger.warning("Unstructured.partition error (%s); falling back to BeautifulSoup", e)
        try:
            import requests
            from bs4 import BeautifulSoup
            resp = requests.get(website_url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            paras = [p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()]
            full_text = "\n".join(paras)
            logger.info("BeautifulSoup fallback succeeded: %d paragraphs", len(paras))
        except Exception as bs_err:
            logger.error("BeautifulSoup fallback also failed: %s", bs_err)
            full_text = ""

    if not full_text.strip():
        logger.warning("No text retrieved from %s; RAG index will be empty", website_url)

    # 2) Split into 500‐character slices
    raw_chunks: List[str] = []
    for i in range(0, len(full_text), 500):
        raw_chunks.append(full_text[i : i + 500])

    # 3) Cap total chunks at MAX_CHUNKS
    if len(raw_chunks) > MAX_CHUNKS:
        logger.info("Truncating chunks from %d to %d (MAX_CHUNKS)", len(raw_chunks), MAX_CHUNKS)
        raw_chunks = raw_chunks[:MAX_CHUNKS]

    chunk_texts = raw_chunks

    # 4) Generate embeddings for each chunk
    chunk_embeddings = []
    for idx, chunk in enumerate(chunk_texts):
        try:
            emb = get_embedding(chunk)
            chunk_embeddings.append(emb)
            if idx % 10 == 0:
                logger.info("Embedded chunk %d/%d", idx + 1, len(chunk_texts))
        except Exception as exc:
            logger.error("Failed to embed chunk %d: %s", idx, exc)
            chunk_embeddings.append(np.zeros(768, dtype=np.float32))  # fallback zero vector

    logger.info("Completed embedding %d chunks", len(chunk_embeddings))

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
    """
    Return the full chat log (system + info + user/assistant messages).
    """
    logger.info("Received GET / request; returning chat_log")
    return chat_log

@app.post("/")
async def chat(
    request: Request,
    user_input: UserInputIn,
    api_key: str = Security(get_api_key),
):
    """
    1) Log incoming headers and body
    2) Append user prompt to chat_log.
    3) Embed the prompt via IONOS /embeddings.
    4) Compute cosine similarity vs. stored chunk_embeddings to pick top‐k_retrieval chunks.
    5) Build prompt: “Context:\n{top_chunks}  Conversation:\n{history}”.
    6) Call IONOS /chat/completions to get a response.
    7) Append assistant’s response to chat_log and return the updated log.
    """
    global chat_log

    # Log request headers
    headers = dict(request.headers)
    logger.info("Received POST / with headers: %s", headers)
    logger.info("Received POST / body (prompt): %s", user_input.prompt)

    # Append user's message
    logger.info("User prompt: %s", user_input.prompt)
    chat_log.append({"role": "user", "content": user_input.prompt})

    if not chunk_embeddings:
        logger.error("RAG index is not initialized; chunk_embeddings is empty.")
        raise HTTPException(status_code=500, detail="RAG index not initialized")

    # 3) Embed user prompt
    try:
        user_emb = get_embedding(user_input.prompt)
    except Exception as e:
        logger.error("Failed to embed user prompt: %s", e)
        raise HTTPException(status_code=500, detail="Embedding error")

    # 4) Compute cosine similarities
    matrix = np.vstack(chunk_embeddings)  # shape: (num_chunks, embedding_dim)
    user_vec = user_emb.reshape(1, -1)    # shape: (1, embedding_dim)
    sims = (matrix @ user_vec.T).flatten() / (
        np.linalg.norm(matrix, axis=1) * np.linalg.norm(user_vec)
    )
    sims = np.nan_to_num(sims, nan=0.0)
    top_indices = np.argsort(sims)[::-1][:k_retrieval]
    context_chunks = [chunk_texts[i] for i in top_indices if i < len(chunk_texts)]
    context = "\n".join(context_chunks)
    logger.debug("Retrieved top‐%d chunks for context: %s", k_retrieval, context_chunks)

    # 5) Build the combined prompt
    prompt_text = f"Context:\n{context}\n\nConversation:\n"
    history = [m for m in chat_log if m["role"] not in EXCLUDED_CHATS]
    prompt_text += "\n".join(f"{m['role']}: {m['content']}" for m in history)
    logger.debug("Full prompt to LLM: %s", prompt_text)

    # 6) Call IONOS chat endpoint
    try:
        assistant_response = await call_ionos_chat(prompt_text)
    except Exception as exc:
        logger.error("IONOS chat API error: %s", exc)
        raise HTTPException(status_code=500, detail="LLM chat error")

    # Log the assistant’s response
    logger.info("Assistant response: %s", assistant_response)

    # 7) Append assistant’s response
    chat_log.append({"role": "assistant", "content": assistant_response})
    return chat_log

@app.post("/i")
async def gen_image(
    request: Request,
    user_input: UserInputIn,
    api_key: str = Security(get_api_key),
):
    """
    Image generation is not implemented in this version.
    """
    logger.warning("Received POST /i but image generation is not implemented")
    raise HTTPException(status_code=501, detail="Image endpoint not implemented")

@app.delete("/")
async def clear_chat_log(api_key: str = Security(get_api_key)):
    """
    Clear the chat log, resetting to the initial system + info messages.
    """
    global chat_log
    logger.info("Received DELETE /; clearing chat_log")
    chat_log = list(INITIAL_CHATLOG)
    return chat_log

# ─── Run the app with Uvicorn if executed directly ───────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
