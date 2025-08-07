"""
RAG Initializer - Handles website scraping and TF-IDF index building.
"""

import logging
from typing import List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from fastapi import HTTPException

from agents.Collectors import WebScraper

logger = logging.getLogger("chatbot-server")


class RAGInitializer:
    """
    Handles RAG (Retrieval-Augmented Generation) initialization including
    web scraping and TF-IDF index building.
    """
    
    def __init__(self, chunk_size: int = 500, max_chunk_count: int = 256):
        """
        Initialize the RAG system.
        
        Args:
            chunk_size: Size of each text chunk
            max_chunk_count: Maximum number of chunks to process
        """
        self.chunk_size = chunk_size
        self.max_chunk_count = max_chunk_count
        self.web_scraper = WebScraper(
            chunk_size=chunk_size, 
            max_chunk_count=max_chunk_count
        )
        self.vectorizer = TfidfVectorizer()
    
    async def initialize_rag_index(self, url: str) -> Tuple[List[str], any]:
        """
        Initialize RAG index by scraping website and building TF-IDF matrix.
        
        Args:
            url: URL to scrape and index
            
        Returns:
            Tuple of (chunk_texts, tfidf_matrix)
            
        Raises:
            HTTPException: If scraping or indexing fails
        """
        logger.info("Initializing RAG index using URL: %s", url)
        
        # 1) Scrape the website
        try:
            chunk_texts = await self.web_scraper.scrape_website(url)
        except HTTPException:
            # Re-raise HTTPExceptions as they are already properly formatted
            raise
        except Exception as exc:
            logger.error("Unexpected error during web scraping: %s", exc)
            raise HTTPException(status_code=500, detail=f"Web scraping error: {exc}")
        
        # 2) Build TF-IDF index
        if chunk_texts:
            tfidf_matrix = self.vectorizer.fit_transform(chunk_texts)
            logger.info("Built TF-IDF matrix with %d chunks", len(chunk_texts))
        else:
            tfidf_matrix = self.vectorizer.fit_transform([""])
            logger.warning("Built TF-IDF on empty text, matrix shape=%s", tfidf_matrix.shape)
        
        return chunk_texts, tfidf_matrix
    
    def get_relevant_chunks(self, query: str, chunk_texts: List[str], tfidf_matrix, top_k: int = 3) -> List[str]:
        """
        Retrieve the most relevant chunks for a given query.
        
        Args:
            query: User query
            chunk_texts: List of text chunks
            tfidf_matrix: Pre-built TF-IDF matrix
            top_k: Number of top chunks to retrieve
            
        Returns:
            List of relevant chunks
        """
        if not chunk_texts or tfidf_matrix is None:
            return []
        
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            user_vec = self.vectorizer.transform([query])
            sims = cosine_similarity(user_vec, tfidf_matrix).flatten()
            best_idxs = sims.argsort()[::-1][:top_k]
            top_chunks = [chunk_texts[i] for i in best_idxs]
            
            logger.info("Retrieved %d relevant chunks for query", len(top_chunks))
            return top_chunks
            
        except Exception as exc:
            logger.error("Error retrieving relevant chunks: %s", exc)
            return []
    
    def get_initialization_result(self, url: str, num_chunks: int) -> dict:
        """
        Get the standardized initialization result.
        
        Args:
            url: The initialized URL
            num_chunks: Number of chunks processed
            
        Returns:
            Dictionary with initialization status
        """
        return {
            "status": "RAG index initialized", 
            "url": url,
            "num_chunks": num_chunks,
            "message": f"Successfully scraped and indexed {num_chunks} chunks from {url}"
        }
