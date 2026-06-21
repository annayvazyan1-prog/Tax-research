# Multi-Agent Tax-Research System

A LangGraph multi-agent system that answers questions about **current** 401(k) /
retirement tax rules using Tavily web search — with an **orchestrator** agent and
**a different model assigned to each agent**, chosen to match the job.

The defining principle: **agents gather and reason; they never become the source
of a tax number.** A deterministic knowledge base of curated IRS figures is the
verifier's ground truth, so when the open web disagrees with the IRS, the system
flags the conflict instead of trusting the web.

```bash
pip install -r requirements.txt
cp .env.example .env          # add ANTHROPIC / OPENAI / TAVILY keys
python run.py "What are the 2026 401(k) limits and what changed from 2025?"

python -m unittest discover tests   # offline tests (no keys needed)
```

## The agents and their models

| Agent | Model | Provider | Why this model |
|-------|-------|----------|----------------|
| Orchestrator / planner | `claude-sonnet-4-6` | Anthropic | Decomposition + routing — reasoning-heavy |
| Researchers ×N | `claude-haiku-4-5` | Anthropic | Parallel, fast, cheap — runs the search volume |
| Claim extractor | `gpt-4o-mini` | OpenAI | Cheap, reliable structured-JSON extraction |
| Verifier | `claude-sonnet-4-6` | Anthropic | Cross-checks claims — **different family from the extractor** |
| Synthesizer | `claude-sonnet-4-6` | Anthropic | Faithful writing + advice-vs-explanation guardrail |

Assignments live in `config.py` (`REGISTRY`) — change one line to re-route an
agent. Swapping models doesn't touch agent logic; nodes bind their model via
`make_llm(role)`.

### Why different models per agent (not a gimmick)

1. **Capability matching** — frontier reasoning for planning/synthesis; small,
   fast models for high-volume search and extraction.
2. **Cost & latency** — you don't pay top-tier prices to run N parallel Tavily
   searches.
3. **Decorrelated errors** — the verifier runs on a *different model family* than
   the extractor that produced the claims, so it catches mistakes a same-model
   check would rubber-stamp. `config.assert_decorrelated()` enforces this at
   startup and a test guards it.

## The graph

```
        ┌─────────────┐
START ─►│  planner    │  (Claude)  decompose → sub-questions
        └──────┬──────┘
               │  Send fan-out (one branch per sub-question)
        ┌──────▼──────┐
        │ researcher  │  (Haiku) ×N parallel ── Tavily
        └──────┬──────┘
        ┌──────▼──────┐
        │  extractor  │  (GPT-4o-mini)  results → structured claims
        └──────┬──────┘
        ┌──────▼──────┐
        │  verifier   │  (Claude)  claims ✓ vs deterministic Tax KB
        └──────┬──────┘
        ┌──────▼──────┐
        │   decide    │  (Claude)  gaps? ──yes──► back to planner (bounded)
        └──────┬──────┘
               │ no
        ┌──────▼──────┐
        │ synthesizer │  (Claude)  grounded, cited, advice-safe answer
        └──────┬──────┘
              END
```

- **Parallel fan-out** uses LangGraph's `Send`: the planner emits one researcher
  branch per sub-question; results merge via an `operator.add` reducer on
  `search_results` (see `src/state.py`).
- **Bounded orchestration loop**: `decide` can send the graph back to `planner`
  with feedback to close gaps, capped by `MAX_RESEARCH_ROUNDS` in `config.py`.

## Grounding & guardrails

- Every claim carries a source URL + snippet + date; the synthesizer cites with
  `[n]` markers and may only use `supported`/authoritative claims.
- The verifier boosts authoritative domains (`irs.gov`, `treasury.gov`, …) and
  marks any figure that contradicts the curated KB as `conflicting`, with the
  difference spelled out.
- The synthesizer explains current rules; it does **not** give personalized
  financial/tax/legal advice.

## Layout

```
config.py                     model registry + orchestration limits + invariants
run.py                        CLI entrypoint
src/
  state.py                    ResearchState, Claim, SearchResult + reducers
  models_factory.py           role -> LangChain chat model
  graph.py                    LangGraph wiring (fan-out + conditional loop)
  tools/
    tavily_search.py          Tavily client wrapper
    knowledge_tool.py         deterministic tax-fact ground truth (verifier)
  agents/
    prompts.py                all system prompts (guardrails)
    jsonutil.py               dependency-free lenient JSON parse (tested offline)
    common.py                 LLM call helper
    nodes.py                  the five agent nodes
tests/test_config_and_state.py   offline tests: registry, decorrelation, reducers
```

## Notes

- Model IDs are current as of mid-2026; verify the exact strings against each
  provider's docs before running, since they change.
- This is research tooling, not financial/tax/legal advice.
- To fold into the explainer project, point `tools/knowledge_tool.py` at that
  repo's richer dated knowledge base instead of the inlined facts.
