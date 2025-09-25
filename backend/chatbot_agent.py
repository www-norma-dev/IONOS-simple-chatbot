import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentStatePydantic
from pydantic import SecretStr

load_dotenv()

logging.basicConfig(
    level=getattr(logging, "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("chatbot-server")

_prompt: str = (
    """
    You are an expert AI assistant designed to help users by answering questions, providing explanations, and solving problems.
    Whenever a user asks a question, always check the knowledge base first to answer it.
    If you don't get enough information from the knowledge base, then do a web search to complement it.
    Combine your own knowledge with the results of the knowledge base and/or web search to provide clear, accurate, and helpful answers.
    If the user asks for a story, creative content, or advice, you may use your own reasoning and creativity, but always check if a web search could improve your response.
    If you cannot answer, or if the information is not available, say so honestly.
    Always be concise, friendly, and professional.
    If the user asks for sources, cite the web search results you used.
    """
)

@tool
def search_knowledge_base(query: str, config: RunnableConfig) -> str:
    """
    First, search your own documents to see if you have enough information.
    """
    logger.info(f"Searching knowledge base for: {query}")
    chunks = config["configurable"]["retriever"].invoke(query, k=2)
    return "\n\n".join(chunk.page_content for chunk in chunks)

@tool
def web_search(query: str) -> str:
    """
    Do a web search if the knowledge base doesn't have enough information.
    """
    logger.info(f"Searching web for: {query}")
    retriever = TavilySearchAPIRetriever(k=8)
    chunks = retriever.invoke(query)
    logger.info(chunks)
    return "\n\n".join(chunk.page_content for chunk in chunks)


def create_chatbot_agent(model_name: str) -> CompiledStateGraph:
    llm = ChatOpenAI(
        model=model_name,
        base_url="https://openai.inference.de-txl.ionos.com/v1",
        api_key=SecretStr(os.getenv("IONOS_API_KEY", "")),
        temperature=0,
        max_tokens=1024,
    )
    return create_react_agent(model=llm, prompt=_prompt, tools=[search_knowledge_base, web_search], state_schema=AgentStatePydantic)
