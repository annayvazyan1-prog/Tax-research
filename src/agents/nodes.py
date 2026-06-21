"""Agent nodes. Each is a LangGraph node: (state) -> partial state update.

Every node binds its OWN model via make_llm(role), so the per-agent model
assignment in config.REGISTRY is what actually drives behavior here.
"""

from __future__ import annotations

from config import MAX_SUBQUESTIONS
from src.agents.common import call, parse_json
from src.agents.prompts import (
    EXTRACTOR_SYSTEM,
    ORCHESTRATOR_DECISION_SYSTEM,
    PLANNER_SYSTEM,
    SYNTHESIZER_SYSTEM,
    VERIFIER_SYSTEM,
)
from src.models_factory import make_llm
from src.state import Citation, Claim, SearchResult
from src.tools.knowledge_tool import kb_context
from src.tools.tavily_search import tavily_search


# --- Orchestrator: plan / re-plan ---------------------------------------
def planner_node(state: dict) -> dict:
    llm = make_llm("planner")
    feedback = state.get("feedback", "")
    user = f"User question: {state['question']}"
    if feedback:
        user += f"\n\nPrevious-round feedback (close these gaps): {feedback}"
    raw = call(llm, PLANNER_SYSTEM.format(max_subq=MAX_SUBQUESTIONS), user)
    subs = parse_json(raw, default=[state["question"]])
    subs = [s for s in subs if isinstance(s, str)][:MAX_SUBQUESTIONS] or [state["question"]]
    return {"sub_questions": subs, "round": state.get("round", 0) + 1}


# --- Researcher: one per sub-question, runs in parallel (via Send) -------
def researcher_node(state: dict) -> dict:
    """Invoked with a per-branch state carrying a single 'sub_question'."""
    sub_q = state["sub_question"]
    llm = make_llm("researcher")
    # Let the (fast, cheap) model tighten the search query.
    query = call(
        llm,
        "Rewrite the following into one concise web search query for current, "
        "authoritative tax information. Respond with only the query.",
        sub_q,
    ).strip().strip('"')
    results = tavily_search(query or sub_q, sub_question=sub_q)
    return {"search_results": results}


# --- Extractor: results -> structured claims ----------------------------
def extractor_node(state: dict) -> dict:
    llm = make_llm("extractor")
    results: list[SearchResult] = state.get("search_results", [])
    if not results:
        return {"claims": []}
    payload = "\n\n".join(
        f"[sub-question: {r.sub_question}]\nTitle: {r.title}\nURL: {r.url}\n"
        f"Date: {r.published_date}\nContent: {r.content[:1200]}"
        for r in results
    )
    raw = call(llm, EXTRACTOR_SYSTEM, payload)
    items = parse_json(raw, default=[])
    claims = [
        Claim(
            text=i.get("text", ""),
            source_url=i.get("source_url", ""),
            source_title=i.get("source_title", ""),
            published_date=i.get("published_date"),
        )
        for i in items if isinstance(i, dict) and i.get("text")
    ]
    return {"claims": claims}


# --- Verifier: cross-check claims against KB + authority -----------------
def verifier_node(state: dict) -> dict:
    from config import AUTHORITATIVE_DOMAINS

    llm = make_llm("verifier")
    claims: list[Claim] = state.get("claims", [])
    if not claims:
        return {"conflicts": []}
    listing = "\n".join(
        f"{idx}. {c.text}  (source: {c.source_url}, date: {c.published_date})"
        for idx, c in enumerate(claims)
    )
    raw = call(llm, VERIFIER_SYSTEM.format(kb_context=kb_context()), listing)
    verdicts = parse_json(raw, default=[])
    by_index = {v.get("index"): v for v in verdicts if isinstance(v, dict)}

    conflicts: list[str] = []
    for idx, c in enumerate(claims):
        v = by_index.get(idx, {})
        c.verdict = v.get("verdict", "unverified")
        c.kb_conflict = v.get("kb_conflict")
        c.authoritative = bool(v.get("authoritative")) or any(
            d in c.source_url for d in AUTHORITATIVE_DOMAINS
        )
        if c.verdict == "conflicting" and c.kb_conflict:
            conflicts.append(f"{c.text} — {c.kb_conflict}")
    return {"claims": claims, "conflicts": conflicts}


# --- Orchestrator: enough evidence, or loop? ----------------------------
def decide_node(state: dict) -> dict:
    from config import MAX_RESEARCH_ROUNDS

    if state.get("round", 1) >= MAX_RESEARCH_ROUNDS:
        return {"needs_more": False, "feedback": ""}
    llm = make_llm("planner")
    claims = state.get("claims", [])
    supported = [c for c in claims if c.verdict in ("supported",)]
    summary = (
        f"Question: {state['question']}\n"
        f"Verified-supported claims: {len(supported)} / {len(claims)} total\n"
        f"Conflicts: {state.get('conflicts', [])}\n"
        f"Sub-questions covered: {state.get('sub_questions', [])}"
    )
    raw = call(llm, ORCHESTRATOR_DECISION_SYSTEM, summary)
    decision = parse_json(raw, default={"needs_more": False, "feedback": ""})
    return {
        "needs_more": bool(decision.get("needs_more")),
        "feedback": decision.get("feedback", ""),
    }


# --- Synthesizer: write the grounded answer -----------------------------
def synthesizer_node(state: dict) -> dict:
    llm = make_llm("synthesizer")
    claims: list[Claim] = state.get("claims", [])
    usable = [c for c in claims if c.verdict in ("supported",) or c.authoritative]
    listing = "\n".join(
        f"- {c.text} [{c.verdict}] (source: {c.source_url} | {c.source_title})"
        for c in usable
    ) or "(no verified claims)"
    conflicts = state.get("conflicts", [])
    user = (
        f"Question: {state['question']}\n\nVerified claims:\n{listing}\n\n"
        f"Conflicts flagged in verification: {conflicts}"
    )
    raw = call(llm, SYNTHESIZER_SYSTEM, user)
    out = parse_json(raw, default={"answer": raw, "citations": []})
    citations = [
        Citation(url=c.get("url", ""), title=c.get("title", ""))
        for c in out.get("citations", []) if isinstance(c, dict)
    ]
    return {"answer": out.get("answer", ""), "citations": citations}
