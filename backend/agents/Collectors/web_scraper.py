import os
import logging
import requests
from bs4 import BeautifulSoup
from typing import List
from fastapi import HTTPException

logger = logging.getLogger("chatbot-server")


class WebScraper:
    """
    Web scraper class for collecting data from websites.
    """
    
    def __init__(self, chunk_size: int = 500, max_chunk_count: int = 256):
        """
        Initialize the WebScraper.
        
        Args:
            chunk_size: Size of each text chunk
            max_chunk_count: Maximum number of chunks to process
        """
        self.chunk_size = chunk_size
        self.max_chunk_count = max_chunk_count
    
    async def scrape_website(self, page_url: str) -> List[str]:
        """
        Scrape a website and return text chunks.
        
        Args:
            page_url: URL of the website to scrape
            
        Returns:
            List of text chunks from the website
            
        Raises:
            HTTPException: If URL is invalid or scraping fails
        """
        # Validate URL
        page_url = page_url.strip()
        if not page_url.lower().startswith(("http://", "https://")):
            raise HTTPException(
                status_code=400, detail="URL must start with http:// or https://"
            )

        logger.info("Scraping website: %s", page_url)
        
        # Fetch the webpage
        try:
            resp = requests.get(page_url, timeout=30)
            resp.raise_for_status()
        except Exception as exc:
            logger.error("Failed to GET %s: %s", page_url, exc)
            raise HTTPException(status_code=500, detail=f"Could not fetch page: {exc}")

        # Parse HTML and extract text
        soup = BeautifulSoup(resp.text, "html.parser")
        paras = [p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()]
        full_text = "\n".join(paras)

        if not full_text.strip():
            logger.warning("No text found at %s; returning empty chunks", page_url)
            return []

        # Break into chunks
        raw_chunks: List[str] = []
        for i in range(0, len(full_text), self.chunk_size):
            raw_chunks.append(full_text[i : i + self.chunk_size])

        # Cap at max chunk count
        if len(raw_chunks) > self.max_chunk_count:
            logger.info(
                "Truncating chunks from %d to %d (MAX_CHUNKS)",
                len(raw_chunks),
                self.max_chunk_count,
            )
            raw_chunks = raw_chunks[:self.max_chunk_count]

        logger.info("Scraped %d chunks from %s", len(raw_chunks), page_url)
        return raw_chunks
