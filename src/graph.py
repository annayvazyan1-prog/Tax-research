"""LangGraph assembly.

Flow:
    planner ──(Send fan-out)──> researcher×N ──> extractor ──> verifier ──> decide
    decide ──needs_more?──> planner   (bounded loop)
            ──else────────> synthesizer ──> END

The fan-out uses Send: the planner emits one researcher branch per sub-question,
each with its own single-sub_question state. LangGraph runs them concurrently and
merges their `search_results` via the operator.add reducer on the state.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from config import assert_decorrelated
from src.agents.nodes import (
    decide_node,
    extractor_node,
    planner_node,
    researcher_node,
    synthesizer_node,
    verifier_node,
)
from src.state import ResearchState


def fan_out_to_researchers(state: ResearchState):
    """Conditional edge: dispatch one researcher per sub-question, in parallel."""
    return [
        Send("researcher", {"sub_question": sq})
        for sq in state["sub_questions"]
    ]


def route_after_decide(state: ResearchState) -> str:
    return "planner" if state.get("needs_more") else "synthesizer"


def build_graph():
    assert_decorrelated()  # fail fast if verifier/extractor share a family

    g = StateGraph(ResearchState)
    g.add_node("planner", planner_node)
    g.add_node("researcher", researcher_node)
    g.add_node("extractor", extractor_node)
    g.add_node("verifier", verifier_node)
    g.add_node("decide", decide_node)
    g.add_node("synthesizer", synthesizer_node)

    g.add_edge(START, "planner")
    g.add_conditional_edges("planner", fan_out_to_researchers, ["researcher"])
    g.add_edge("researcher", "extractor")
    g.add_edge("extractor", "verifier")
    g.add_edge("verifier", "decide")
    g.add_conditional_edges("decide", route_after_decide, ["planner", "synthesizer"])
    g.add_edge("synthesizer", END)

    return g.compile()
