"""
Citations utilities for normalizing and deduplicating source metadata.
"""

from typing import Dict, Any, List


def normalize_citation(item: Dict[str, Any]) -> Dict[str, Any]:
    """Return a normalized citation dict.

    Expected keys in input (if present): url, title, date, accessed_at
    Output keys: url, title, published_or_updated_date, accessed_at
    """
    return {
        "url": item.get("url", ""),
        "title": item.get("title", ""),
        "published_or_updated_date": item.get("date"),
        "accessed_at": item.get("accessed_at"),
    }


def dedupe_citations(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate citations by URL preserving first occurrence order."""
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for it in items:
        url = it.get("url", "")
        if url and url not in seen:
            seen.add(url)
            deduped.append(it)
    return deduped


