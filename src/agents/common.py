"""Shared LLM-call helper for agent nodes (imports LangChain; runtime-only)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.jsonutil import parse_json  # re-export for convenience

__all__ = ["call", "parse_json"]


def call(llm, system: str, user: str) -> str:
    """Single-shot system+user call returning text content."""
    resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    return resp.content if isinstance(resp.content, str) else str(resp.content)
