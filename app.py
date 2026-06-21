"""Streamlit UI for the multi-agent tax-research system.

Warm, editorial design (sunset gold + charcoal + cream). The page is just the
research tool: ask a question, get a verified, cited answer.

Run:
    .venv/bin/streamlit run app.py
"""

from __future__ import annotations

import os

import streamlit as st

# Local dev loads keys from .env. On Streamlit Cloud there is no .env — keys
# come from the app's Secrets (Manage app → Settings → Secrets) via st.secrets.
# Bridge whichever is present into the environment so the provider SDKs
# (Anthropic / OpenAI / Tavily) can authenticate.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

REQUIRED_KEYS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "TAVILY_API_KEY")


def _bridge_secrets() -> list[str]:
    """Pull required keys from st.secrets into os.environ; return any missing."""
    missing: list[str] = []
    for key in REQUIRED_KEYS:
        if os.environ.get(key):
            continue
        try:
            val = st.secrets[key]
        except Exception:
            val = None
        if val:
            os.environ[key] = str(val)
        else:
            missing.append(key)
    return missing


MISSING_KEYS = _bridge_secrets()

from src.graph import build_graph

# --- Palette (from the warm home-decor reference) ------------------------
GOLD = "#c98a3c"
GOLD_DEEP = "#a8641e"
INK = "#262220"
CREAM = "#faf6f0"
WARM_GRAY = "#6b6259"
SAGE = "#7d8b6a"

st.set_page_config(page_title="Retirement Tax Research", page_icon="🪙",
                   layout="wide")


@st.cache_resource(show_spinner=False)
def get_graph():
    """Compile the LangGraph once and reuse across reruns."""
    return build_graph()


st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Sans+3:wght@400;600;700&display=swap');

    #MainMenu, footer, header[data-testid="stHeader"] {{ display: none; }}
    [data-testid="stAppViewContainer"] {{ background: {CREAM}; }}
    .block-container {{ padding: 0 !important; max-width: 100% !important; }}
    html, body, [class*="css"] {{ font-family: 'Source Sans 3', Arial, sans-serif;
        color: {INK}; }}

    /* Hero */
    .hero {{
        background: linear-gradient(135deg, #e0a857 0%, {GOLD} 40%, {GOLD_DEEP} 100%);
        padding: 64px 24px 70px; text-align: center; color: #fff;
    }}
    .hero h1 {{ font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
        font-size: 52px; margin: 0; letter-spacing: .5px;
        text-shadow: 0 1px 14px rgba(0,0,0,.18); }}
    .hero p {{ font-size: 19px; margin: 14px auto 0; max-width: 640px;
        opacity: .96; }}

    /* Section label, like the reference's charcoal headers */
    .label {{ font-size: 13px; font-weight: 700; letter-spacing: 2px;
        text-transform: uppercase; color: {INK}; margin: 4px 0 10px; }}
    .label::after {{ content: ""; display: block; width: 46px; height: 3px;
        background: {GOLD}; margin-top: 7px; }}

    .lead {{ font-size: 18px; line-height: 1.65; color: {WARM_GRAY};
        margin: 30px 0 18px; }}

    /* Result cards */
    .answer-card {{ background: #fff; border: 1px solid #ece3d6;
        border-left: 5px solid {GOLD}; border-radius: 6px;
        padding: 26px 30px; margin-top: 8px; font-size: 16.5px;
        line-height: 1.7; box-shadow: 0 6px 22px rgba(40,30,20,.06); }}
    .answer-card h1, .answer-card h2, .answer-card h3 {{
        font-family: 'Playfair Display', Georgia, serif; color: {INK}; }}
    .answer-card table {{ border-collapse: collapse; margin: 10px 0; }}
    .answer-card th, .answer-card td {{ border: 1px solid #e6ddd0;
        padding: 6px 12px; }}
    .answer-card th {{ background: {CREAM}; }}
    .answer-card a {{ color: {GOLD_DEEP}; }}

    .conflict-card {{ background: #fdf3ec; border-left: 5px solid #b5491f;
        border-radius: 6px; padding: 16px 22px; margin-top: 18px;
        font-size: 15px; color: #5c2a14; }}

    .q-echo {{ font-family: 'Playfair Display', Georgia, serif;
        font-size: 26px; color: {INK}; margin: 6px 0 14px; }}

    /* Sources list — gold chevron rows like the reference */
    .src {{ display: flex; gap: 12px; padding: 13px 4px; align-items: baseline;
        border-bottom: 1px solid #e8dfd2; }}
    .src .chev {{ color: {GOLD}; font-weight: 700; }}
    .src a {{ color: {INK}; text-decoration: none; font-weight: 600; }}
    .src a:hover {{ color: {GOLD_DEEP}; }}
    .src .n {{ color: {WARM_GRAY}; font-size: 13px; }}

    /* Inputs */
    [data-testid="stTextInput"] input {{ background: #fff; border: 1px solid #ddd2c2;
        border-radius: 6px; padding: 13px 16px; font-size: 16px; }}
    [data-testid="stTextInput"] input:focus {{ border-color: {GOLD};
        box-shadow: 0 0 0 2px rgba(201,138,60,.25); }}
    div.stButton > button {{ background: {GOLD}; color: #fff; border: none;
        border-radius: 6px; font-weight: 700; letter-spacing: .4px;
        padding: 11px 34px; font-size: 16px; }}
    div.stButton > button:hover {{ background: {GOLD_DEEP}; color: #fff; }}

    .tagline {{ color: {SAGE}; font-weight: 600; font-size: 14px;
        margin-top: 26px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Hero ----------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>Retirement Tax Research</h1>
        <p>Verified, cited answers on current 401(k) and retirement tax rules —
        researched across the web and cross-checked against authoritative IRS figures.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Centered content ----------------------------------------------------
left, mid, right = st.columns([1, 2.4, 1])
with mid:
    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="label">Ask a question</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="lead">Type any question about current retirement or tax rules. '
        'No figure is stated unless it verifies against the curated IRS knowledge base.</p>',
        unsafe_allow_html=True,
    )

    # Track whether a research run is in flight and the last result, so the
    # button can be disabled *only* while running and re-enabled when done —
    # and so the rendered answer survives Streamlit's reruns.
    st.session_state.setdefault("running", False)
    st.session_state.setdefault("result", None)

    def _start_research():
        st.session_state.running = True

    question = st.text_input(
        "Your question",
        placeholder="What are the 2026 401(k) contribution limits and what changed from 2025?",
        label_visibility="collapsed",
        disabled=st.session_state.running,
    )
    st.button(
        "Researching…" if st.session_state.running else "Research",
        disabled=st.session_state.running,
        on_click=_start_research,
    )

    # This block runs on the rerun triggered by the click: the button is now
    # disabled, we do the work, store the result, re-enable, and rerun.
    if st.session_state.running:
        if MISSING_KEYS:
            st.error(
                "Missing API key(s): **" + ", ".join(MISSING_KEYS) + "**.\n\n"
                "On Streamlit Cloud, open **Manage app → Settings → Secrets** and add them "
                "in TOML form:\n\n```toml\n"
                'ANTHROPIC_API_KEY = "sk-ant-..."\n'
                'OPENAI_API_KEY = "sk-..."\n'
                'TAVILY_API_KEY = "tvly-..."\n```\n\n'
                "Locally, put the same keys in a `.env` file."
            )
            st.session_state.running = False
        else:
            q = (question or "").strip() or (
                "What are the 2026 401(k) contribution limits and what changed from 2025?"
            )
            with st.spinner("Planning, searching, extracting claims, and verifying against IRS ground truth…"):
                final = get_graph().invoke({"question": q, "round": 0},
                                           config={"recursion_limit": 25})
            st.session_state.result = {"question": q, "final": final}
            st.session_state.running = False
            st.rerun()

    result = st.session_state.result
    if result:
        final = result["final"]
        st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="q-echo">{result["question"]}</div>', unsafe_allow_html=True)
        answer = final.get("answer") or "_(no answer produced)_"
        st.markdown(f'<div class="answer-card">{answer}</div>', unsafe_allow_html=True)

        conflicts = final.get("conflicts") or []
        if conflicts:
            items = "".join(f"<li>{c}</li>" for c in conflicts)
            st.markdown(
                f'<div class="conflict-card"><b>⚠ Verification conflicts</b>'
                f'<ul style="margin:6px 0 0">{items}</ul></div>',
                unsafe_allow_html=True,
            )

        cites = final.get("citations") or []
        if cites:
            st.markdown('<div style="height:26px"></div>', unsafe_allow_html=True)
            st.markdown('<div class="label">Sources</div>', unsafe_allow_html=True)
            rows = "".join(
                f'<div class="src"><span class="chev">›</span>'
                f'<span><a href="{c.url}" target="_blank">{c.title or c.url}</a>'
                f'<br><span class="n">{c.url}</span></span></div>'
                for c in cites
            )
            st.markdown(rows, unsafe_allow_html=True)

    st.markdown('<div class="tagline">Research tooling — not financial, tax, or legal advice.</div>',
                unsafe_allow_html=True)
    st.markdown('<div style="height:60px"></div>', unsafe_allow_html=True)
