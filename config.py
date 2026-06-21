"""Per-agent model registry.

The whole point of the system: each agent runs on the model best suited to its
job. Assignment lives here so swapping a model is a one-line change, and the
decorrelation invariant (verifier must differ in family from the extractor) is
visible in one place.

Roles -> (provider, model):
  planner / orchestrator : Anthropic Claude  — decomposition + routing (reasoning)
  researcher             : Anthropic Haiku   — parallel, cheap, high-volume search
  extractor              : OpenAI GPT-4o-mini — cheap structured JSON extraction
  verifier               : Anthropic Claude  — checks claims; != extractor family
  synthesizer            : Anthropic Claude  — faithful writing + advice guardrail
"""

from __future__ import annotations

from dataclasses import dataclass

ANTHROPIC = "anthropic"
OPENAI = "openai"


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model: str
    temperature: float = 0.0


# Single source of truth. Change a value here to re-route an agent.
REGISTRY: dict[str, ModelSpec] = {
    "planner":     ModelSpec(ANTHROPIC, "claude-sonnet-4-6", 0.1),
    "researcher":  ModelSpec(ANTHROPIC, "claude-haiku-4-5", 0.0),
    "extractor":   ModelSpec(OPENAI,    "gpt-4o-mini", 0.0),
    "verifier":    ModelSpec(ANTHROPIC, "claude-sonnet-4-6", 0.0),
    "synthesizer": ModelSpec(ANTHROPIC, "claude-sonnet-4-6", 0.2),
}

# Orchestration limits.
MAX_RESEARCH_ROUNDS = 2      # how many times the orchestrator may loop back
MAX_SUBQUESTIONS = 4         # cap fan-out width
TAVILY_RESULTS_PER_QUERY = 4

# Domains we treat as authoritative for tax facts (verifier boosts these).
AUTHORITATIVE_DOMAINS = (
    "irs.gov", "treasury.gov", "ssa.gov", "dol.gov", "congress.gov",
    "federalregister.gov",
)


def spec_for(role: str) -> ModelSpec:
    if role not in REGISTRY:
        raise KeyError(f"No model assigned for agent role '{role}'. Add it to REGISTRY.")
    return REGISTRY[role]


def assert_decorrelated() -> None:
    """Guard the core invariant: the verifier must not share a model family with
    the extractor, or cross-checking loses its value."""
    if spec_for("verifier").provider == spec_for("extractor").provider:
        raise ValueError(
            "Verifier and extractor share a provider; cross-checking won't "
            "decorrelate errors. Assign different families in REGISTRY."
        )
