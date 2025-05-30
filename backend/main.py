import os
import uuid
import logging
import httpx
import requests
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

# ——— Logging setup ——————————————————————————————————————————————
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("chatbot-server")

# ——— Load .env —————————————————————————————————————————————
load_dotenv()

# Shared secret for your frontend ↔ backend lock
api_key = os.getenv("ACCEPTED_API_KEY", "")
if not api_key:
    raise KeyError("ACCEPTED_API_KEY not found in environment.")

# IONOS LLM config\ionos_api_url = os.getenv("IONOS_API_URL", "")
ionos_model_id = os.getenv("IONOS_MODEL_ID", "")
ionos_api_key = os.getenv("IONOS_API_KEY", "")
ionos_api_url=os.getenv("IONOS_API_URL", "")
if not (ionos_api_url and ionos_model_id and ionos_api_key):
    raise KeyError("IONOS_API_URL, IONOS_MODEL_ID or IONOS_API_KEY not found in environment.")

# RAG config
website_url = os.getenv("WEBSITE_URL", "")
k_retrieval = int(os.getenv("RAG_K", 3))
if not website_url:
    raise KeyError("WEBSITE_URL not found in environment.")

# ——— FastAPI setup ————————————————————————————————————————————
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
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
) -> str:
    if api_key_query == api_key or api_key_header == api_key:
        return api_key
    logger.warning("Unauthorized access attempt with api-key=%s header=%s", api_key_query, api_key_header)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )

# ——— Chat history state ————————————————————————————————————————
EXCLUDED_CHATS = ["image", "info"]
INITIAL_CHATLOG = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "info", "content": (
        "Hello!\n\nI'm a personal assistant chatbot. I will respond as"
        " best I can to any messages you send me."
    )},
]
chat_log = list(INITIAL_CHATLOG)

class UserInputIn(BaseModel):
    prompt: str

# ——— RAG index state ——————————————————————————————————————————
vectorizer = TfidfVectorizer()
chunk_texts = []
tfidf_matrix = None

@app.on_event("startup")
def build_rag_index():
    global chunk_texts, tfidf_matrix
    logger.info("Scraping website for RAG index: %s", website_url)
    resp = requests.get(website_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    paras = [p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()]

    # Chunk paragraphs into 500-char slices
    chunk_texts = []
    for para in paras:
        for i in range(0, len(para), 500):
            chunk_texts.append(para[i : i + 500])

    if not chunk_texts:
        logger.warning("No text chunks found for RAG index.")

    tfidf_matrix = vectorizer.fit_transform(chunk_texts)
    logger.info("Built TF-IDF matrix with %d chunks", len(chunk_texts))

# ——— IONOS LLM helper with logging —————————————————————————————————
async def call_ionos_llm(prompt: str) -> str:
    url = f"{ionos_api_url.rstrip('/')}/{ionos_model_id}/predictions"
    headers = {
        "Authorization": f"Bearer {ionos_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "properties": {"input": prompt},
        "option": {"temperature": 0.8, "maxTokens": 500, "seed": uuid.uuid4().int & ((1 << 16) - 1)},
    }
    logger.debug("IONOS request payload: %s", payload)
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(url, headers=headers, json=payload)
    logger.info("IONOS response status: %s", resp.status_code)
    resp.raise_for_status()
    output = resp.json().get("properties", {}).get("output", "").strip()
    return output

# ——— OpenAPI & Swagger UI —————————————————————————————————————
@app.get("/docs", include_in_schema=False)
async def get_documentation(api_key: str = Security(get_api_key)):
    openapi_url = "/openapi.json?api-key=" + api_key
    return get_swagger_ui_html(openapi_url=openapi_url, title="docs")

@app.get("/openapi.json", include_in_schema=False)
async def openapi(api_key: str = Security(get_api_key)):
    return get_openapi(title="FastAPI", version="0.1.0", routes=app.routes)

# ——— Chat endpoints —————————————————————————————————————————
@app.get("/")
async def get_chat_logs():
    return chat_log

@app.post("/")
async def chat(
    request: Request,
    user_input: UserInputIn,
    api_key: str = Security(get_api_key),
):
    # 1) record the user's message
    logger.info("User prompt: %s", user_input.prompt)
    chat_log.append({"role": "user", "content": user_input.prompt})

    # 2) vectorize and retrieve top-k chunks
    user_vec = vectorizer.transform([user_input.prompt])
    sims = cosine_similarity(user_vec, tfidf_matrix).flatten()
    best_idxs = sims.argsort()[::-1][:k_retrieval]
    context = "\n".join(chunk_texts[i] for i in best_idxs)
    logger.debug("RAG context: %s", context)

    # 3) build the prompt
    prompt_text = f"Context:\n{context}\n\nConversation:\n"
    ai_prompts = [m for m in chat_log if m["role"] not in EXCLUDED_CHATS]
    prompt_text += "\n".join(f"{m['role']}: {m['content']}" for m in ai_prompts)
    logger.debug("Full prompt to LLM: %s", prompt_text)

    # 4) call IONOS
    bot_response = await call_ionos_llm(prompt_text)
    chat_log.append({"role": "assistant", "content": bot_response})
    return chat_log

@app.post("/i")
async def gen_image(
    request: Request,
    user_input: UserInputIn,
    api_key: str = Security(get_api_key),
):
    raise HTTPException(status_code=501, detail="Image endpoint not implemented")

@app.delete("/")
async def clear_chat_log(api_key: str = Security(get_api_key)):
    global chat_log
    logger.info("Clearing chat log")
    chat_log = list(INITIAL_CHATLOG)
    return chat_log

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
