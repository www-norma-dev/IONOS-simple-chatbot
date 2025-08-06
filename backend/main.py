import os
import logging

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    BaseMessage,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from pydantic import SecretStr, BaseModel
from mangum import Mangum

from typing import List
from agents.Collectors import WebScraper
from agents import create_react_agent

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
current_url: str = ""  # Track the current URL being discussed

# ─── RAG index state ────────────────────────────────────────────────────
vectorizer = TfidfVectorizer()
chunk_texts: List[str] = []  # List[str]
tfidf_matrix = None  # will become a sparse matrix after fitting

# ─── ReAct Agent ────────────────────────────────────────────────────────
react_agent = None  # Will be initialized when needed


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


# ─── WebScraper instance ────────────────────────────────────────────────
web_scraper = WebScraper(chunk_size=CHUNK_SIZE, max_chunk_count=MAX_CHUNK_COUNT)



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
    logger.info("Initializing RAG index using URL: %s", current_url)

    # 2) Scrape the website using WebScraper
    try:
        chunk_texts = await web_scraper.scrape_website(current_url)
    except HTTPException:
        # Re-raise HTTPExceptions as they are already properly formatted
        raise
    except Exception as exc:
        logger.error("Unexpected error during web scraping: %s", exc)
        raise HTTPException(status_code=500, detail=f"Web scraping error: {exc}")

    # 3) Build TF-IDF index
    if chunk_texts:
        tfidf_matrix = vectorizer.fit_transform(chunk_texts)
        logger.info("Built TF-IDF matrix with %d chunks", len(chunk_texts))
    else:
        tfidf_matrix = vectorizer.fit_transform([""])
        logger.warning("Built TF-IDF on empty text, matrix shape=%s", tfidf_matrix.shape)

    # 4) Reset chat history
    chat_log = get_initial_chat()
    
    return {
        "status": "RAG index initialized", 
        "url": current_url,
        "num_chunks": len(chunk_texts),
        "message": f"Successfully scraped and indexed {len(chunk_texts)} chunks from {current_url}"
    }


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
        user_vec = vectorizer.transform([user_input.prompt])
        sims = cosine_similarity(user_vec, tfidf_matrix).flatten()
        best_idxs = sims.argsort()[::-1][:RAG_K]
        top_chunks = [chunk_texts[i] for i in best_idxs]
        logger.info("Retrieved %d relevant chunks for query", len(top_chunks))

    # 4) Initialize ReAct agent if not already done
    if react_agent is None:
        logger.info("Initializing ReAct agent with model: %s", model_id)
        react_agent = create_react_agent(
            model_name=model_id,
            api_key=IONOS_API_KEY,
            base_url="https://openai.inference.de-txl.ionos.com/v1",
            temperature=0.1,
            max_tokens=1000,
            chunk_size=CHUNK_SIZE,
            max_chunk_count=MAX_CHUNK_COUNT
        )

    # 5) Process message through ReAct agent with RAG context
    try:
        response_text = await react_agent.process_message_with_rag(
            message=user_input.prompt,
            rag_chunks=top_chunks,
            current_url=current_url if current_url else None
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
