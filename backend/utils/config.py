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
    
    # Agent configuration
    DEFAULT_TEMPERATURE = 0.1
    DEFAULT_MAX_TOKENS = 1000
    
    # Extended retrieval: provider configuration
    SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "")
    SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")
    
    # Extended retrieval: budgets
    MAX_QUERIES = int(os.getenv("MAX_QUERIES", "3"))
    MAX_PAGES = int(os.getenv("MAX_PAGES", "6"))
    MAX_MS = int(os.getenv("MAX_MS", "8000"))
    MAX_WEB_PASSAGES = int(os.getenv("MAX_WEB_PASSAGES", "16"))
    MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "6000"))
    
    # Extended retrieval: thresholds
    TAU_MAX_SIM = float(os.getenv("TAU_MAX_SIM", "0.35"))
    TAU_MEAN_TOP3 = float(os.getenv("TAU_MEAN_TOP3", "0.22"))
    MIN_LOCAL_HITS = int(os.getenv("MIN_LOCAL_HITS", "3"))
    SUFFICIENCY_MIN_CITATIONS = int(os.getenv("SUFFICIENCY_MIN_CITATIONS", "2"))
    
    # Feature flags
    EXTENDED_RETRIEVAL_ENABLED = os.getenv("EXTENDED_RETRIEVAL_ENABLED", "false").lower() == "true"
    BOOSTER_MODE_ENABLED = os.getenv("BOOSTER_MODE_ENABLED", "false").lower() == "true"
    GRAPH_RENDER_ENABLED = os.getenv("GRAPH_RENDER_ENABLED", "false").lower() == "true"
    
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

    @classmethod
    def get_extended_retrieval_config(cls) -> Dict[str, Any]:
        """Get configuration for extended retrieval (search + web read)."""
        return {
            "provider": cls.SEARCH_PROVIDER,
            "api_key": cls.SEARCH_API_KEY,
            "budgets": {
                "max_queries": cls.MAX_QUERIES,
                "max_pages": cls.MAX_PAGES,
                "max_ms": cls.MAX_MS,
                "max_web_passages": cls.MAX_WEB_PASSAGES,
                "max_context_tokens": cls.MAX_CONTEXT_TOKENS,
            },
            "thresholds": {
                "tau_max_sim": cls.TAU_MAX_SIM,
                "tau_mean_top3": cls.TAU_MEAN_TOP3,
                "min_local_hits": cls.MIN_LOCAL_HITS,
                "sufficiency_min_citations": cls.SUFFICIENCY_MIN_CITATIONS,
            },
            "flags": {
                "extended_retrieval_enabled": cls.EXTENDED_RETRIEVAL_ENABLED,
                "booster_mode_enabled": cls.BOOSTER_MODE_ENABLED,
                "graph_render_enabled": cls.GRAPH_RENDER_ENABLED,
            },
        }
