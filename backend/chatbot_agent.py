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

_prompt: str = ("You are an assistant. Your role is to answer user's question."
                "Whenever an user ask a question, first search your documents, if you don't have enough information, do a web search."
                "Once you have enough information, you can answer the user query.")


@tool
def web_search(query: str) -> str:
    """
    Do a web search to query additional information for the user.
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
    return create_react_agent(model=llm, prompt=_prompt, tools=[web_search], state_schema=AgentStatePydantic)
