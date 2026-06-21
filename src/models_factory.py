"""Factory: agent role -> a ready LangChain chat model.

Keeps provider SDK details out of the agents. Each provider package is imported
lazily so you only need the SDKs for the providers you actually use.
"""

from __future__ import annotations

from functools import lru_cache

from config import ANTHROPIC, OPENAI, ModelSpec, spec_for


def _build(spec: ModelSpec):
    if spec.provider == ANTHROPIC:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=spec.model, temperature=spec.temperature)
    if spec.provider == OPENAI:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=spec.model, temperature=spec.temperature)
    raise ValueError(f"Unknown provider: {spec.provider}")


@lru_cache(maxsize=None)
def make_llm(role: str):
    """Return (and cache) the chat model assigned to an agent role."""
    return _build(spec_for(role))
