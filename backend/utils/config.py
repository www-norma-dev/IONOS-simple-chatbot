"""
Configuration utilities for the chatbot application.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration management for the chatbot application."""
    
    # IONOS AI Model Hub config
    IONOS_API_KEY = os.getenv("IONOS_API_KEY", "")
    IONOS_BASE_URL = "https://openai.inference.de-txl.ionos.com/v1"
    
    # RAG configuration
    RAG_K = int(os.getenv("RAG_K", "3"))  # top-k chunks to retrieve
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))  # chunk size in characters
    MAX_CHUNK_COUNT = int(os.getenv("MAX_CHUNK_COUNT", "256"))  # max number of chunks
    DOC_SOURCES = [s for s in os.getenv("DOC_SOURCES", "").split("|") if s.strip()]  # pipe-separated list of paths/URLs
    
    # Agent configuration
    DEFAULT_TEMPERATURE = 0.1
    DEFAULT_MAX_TOKENS = 1000
    
    # CORS configuration
    ALLOWED_ORIGINS = [
        "http://localhost:8000",
        "http://localhost:3000",
    ]
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values."""
        if not cls.IONOS_API_KEY:
            raise ValueError("IONOS_API_KEY not found in environment.")
    
    @classmethod
    def get_agent_config(cls) -> Dict[str, Any]:
        """Get configuration for ReAct agent."""
        return {
            "api_key": cls.IONOS_API_KEY,
            "base_url": cls.IONOS_BASE_URL,
            "temperature": cls.DEFAULT_TEMPERATURE,
            "max_tokens": cls.DEFAULT_MAX_TOKENS,
            "chunk_size": cls.CHUNK_SIZE,
            "max_chunk_count": cls.MAX_CHUNK_COUNT
        }
    
    @classmethod
    def get_rag_config(cls) -> Dict[str, Any]:
        """Get configuration for RAG system."""
        return {
            "chunk_size": cls.CHUNK_SIZE,
            "max_chunk_count": cls.MAX_CHUNK_COUNT,
            "top_k": cls.RAG_K
        }
