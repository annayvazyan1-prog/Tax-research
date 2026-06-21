"""Tavily search tool.

Thin wrapper over the official tavily-python client so the researcher agent
stays provider-agnostic. Returns normalized SearchResult objects.
"""

from __future__ import annotations

import os

from config import TAVILY_RESULTS_PER_QUERY
from src.state import SearchResult


def tavily_search(query: str, sub_question: str, max_results: int | None = None) -> list[SearchResult]:
    """Run one Tavily query. Network + TAVILY_API_KEY required."""
    from tavily import TavilyClient

    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    resp = client.search(
        query=query,
        max_results=max_results or TAVILY_RESULTS_PER_QUERY,
        search_depth="advanced",
        include_answer=False,
    )
    results = []
    for r in resp.get("results", []):
        results.append(SearchResult(
            sub_question=sub_question,
            url=r.get("url", ""),
            title=r.get("title", ""),
            content=r.get("content", ""),
            score=r.get("score", 0.0),
            published_date=r.get("published_date"),
        ))
    return results
