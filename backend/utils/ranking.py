"""
Ranking utilities for evidence passages.

Provides a simple MMR selection helper. Scoring is performed upstream.
"""

from typing import List, Dict, Any, Tuple


def mmr_diversify(
    scored_passages: List[Tuple[Dict[str, Any], float]],
    lambda_weight: float = 0.7,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """Return a diversified top-k selection using a placeholder MMR algorithm.

    This simplified version returns the top-k by score. Replace with a real MMR
    implementation when needed.
    """
    sorted_items = sorted(scored_passages, key=lambda x: x[1], reverse=True)
    return [item[0] for item in sorted_items[:top_k]]


