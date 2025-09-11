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
    "You are an expert AI assistant designed to help users by answering questions, providing explanations, and solving problems.\n"
    "You have access to a web search tool.\n"
    "Whenever a user asks a question, always consider if a web search could provide up-to-date or relevant information.\n"
    "If so, use the web_search tool to gather facts, context, or recent data before answering.\n"
    "Combine your own knowledge with the results of your web search to provide clear, accurate, and helpful answers.\n"
    "If the user asks for a story, creative content, or advice, you may use your own reasoning and creativity, but always check if a web search could improve your response.\n"
    "Be transparent about when you use web search.\n"
    "If you cannot answer, or if the information is not available, say so honestly.\n"
    "Always be concise, friendly, and professional.\n"
    "If the user asks for sources, cite the web search results you used.\n"
)


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
