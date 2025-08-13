"""
Web reader for fetching pages and extracting readable content.

This module defines a thin wrapper that will use httpx.AsyncClient and a
readability-style extraction approach to produce clean passages suitable
for ranking and synthesis.
"""

import logging
from typing import Any, Dict, List, Optional
import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag


logger = logging.getLogger("chatbot-server")


class WebReader:
    """Fetch pages and extract text passages (scaffold)."""

    def __init__(
        self,
        concurrency_limit: int = 6,
        per_page_timeout_seconds: float = 12.0,
    ) -> None:
        self.concurrency_limit = concurrency_limit
        self.per_page_timeout_seconds = per_page_timeout_seconds

    async def fetch_and_extract(
        self,
        urls: List[str],
        budget: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch URLs and return extracted passages with metadata.

        Each result item should look like:
          {"url": str, "title": str | None, "passage": str, "date": str | None}

        This scaffold returns an empty list; implementation to follow.
        """
        logger.debug(
            "WebReader.fetch_and_extract called for %d urls", 0 if urls is None else len(urls)
        )
        if not urls:
            return []

        max_pages = 6
        if budget and isinstance(budget.get("max_pages"), int):
            max_pages = budget["max_pages"]

        results: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=self.per_page_timeout_seconds) as client:
            for url in urls[:max_pages]:
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    # Content-Type check: skip non-HTML quickly
                    ctype = resp.headers.get("Content-Type", "").lower()
                    if "text/html" not in ctype:
                        continue
                    soup = BeautifulSoup(resp.text, "lxml")
                    title = (soup.title.string.strip() if soup.title and soup.title.string else "")
                    # Extract readable paragraphs, strip anchors/nav/script
                    for t in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
                        t.decompose()
                    # Prefer main/article sections if present
                    candidates = soup.find_all(["article", "main"]) or [soup]
                    paragraphs: List[str] = []
                    for c in candidates:
                        for p in c.find_all("p"):
                            if isinstance(p, Tag):
                                txt = p.get_text().strip()
                                if txt:
                                    paragraphs.append(txt)
                    text = "\n".join(paragraphs)
                    if not text:
                        continue
                    # Sliding windows ~800 chars with 200 overlap
                    window_size = 800
                    overlap = 200
                    start = 0
                    while start < len(text) and len(results) < max_pages:
                        end = min(start + window_size, len(text))
                        passage = text[start:end]
                        if len(passage) >= 200:
                            results.append({
                                "url": url,
                                "title": title,
                                "passage": passage,
                                "date": None,
                            })
                        if end == len(text):
                            break
                        start = end - overlap
                except Exception as exc:
                    logger.warning("WebReader failed for %s: %s", url, exc)

        return results


