"""Shared graph state and data types.

LangGraph threads a single typed state object through every node. List fields
use reducers (operator.add) so parallel researchers can append concurrently
without clobbering each other.
"""

from __future__ import annotations

import operator
from dataclasses import dataclass, field
from typing import Annotated, Optional, TypedDict


@dataclass
class SearchResult:
    sub_question: str
    url: str
    title: str
    content: str
    score: float = 0.0
    published_date: Optional[str] = None


@dataclass
class Claim:
    """A single factual assertion extracted from search, with its source."""
    text: str
    source_url: str
    source_title: str = ""
    published_date: Optional[str] = None
    # Filled by the verifier:
    authoritative: bool = False
    kb_conflict: Optional[str] = None     # description if it contradicts the KB
    verdict: str = "unverified"           # supported | conflicting | unverified


@dataclass
class Citation:
    url: str
    title: str


def _dedup_claims(existing: list[Claim], new: list[Claim]) -> list[Claim]:
    """Reducer that merges claim lists and drops near-duplicates (same text+url)."""
    seen = {(c.text.strip().lower(), c.source_url) for c in existing}
    out = list(existing)
    for c in new:
        key = (c.text.strip().lower(), c.source_url)
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


class ResearchState(TypedDict, total=False):
    question: str
    # Orchestrator output:
    sub_questions: list[str]
    round: int                                  # research loop counter
    feedback: str                               # orchestrator's note when looping back
    # Accumulated by parallel researchers (reducer appends):
    search_results: Annotated[list[SearchResult], operator.add]
    # Downstream:
    claims: Annotated[list[Claim], _dedup_claims]
    conflicts: list[str]
    needs_more: bool
    answer: str
    citations: list[Citation]
