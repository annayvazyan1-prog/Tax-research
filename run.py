"""CLI entrypoint.

    python run.py "What are the 2026 401(k) contribution limits and what changed?"

Requires API keys in the environment (see .env.example):
    ANTHROPIC_API_KEY, OPENAI_API_KEY, TAVILY_API_KEY
"""

from __future__ import annotations

import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.graph import build_graph


def main() -> None:
    question = " ".join(sys.argv[1:]).strip() or (
        "What are the 2026 401(k) contribution limits and what changed from 2025?"
    )
    graph = build_graph()
    final = graph.invoke(
        {"question": question, "round": 0},
        config={"recursion_limit": 25},
    )

    print("\n" + "=" * 72)
    print("QUESTION:", question)
    print("=" * 72)
    print("\n" + (final.get("answer") or "(no answer produced)"))

    if final.get("conflicts"):
        print("\n--- Verification conflicts ---")
        for c in final["conflicts"]:
            print("  •", c)

    cites = final.get("citations", [])
    if cites:
        print("\n--- Sources ---")
        for i, c in enumerate(cites, 1):
            print(f"  [{i}] {c.title} — {c.url}")
    print()


if __name__ == "__main__":
    main()
