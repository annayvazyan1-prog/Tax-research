"""Streamlit UI for the multi-agent tax-research system, skinned to look like
IRS.gov (irs.gov/retirement-plans/401k-plans).

Run:
    .venv/bin/streamlit run app.py

The page chrome (gov banner, IRS header, nav, breadcrumb, sidebar) is static
HTML/CSS recreated to match the screenshot. The main content area drives the
existing LangGraph agent: type a question, get a verified, cited answer.
"""

from __future__ import annotations

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.graph import build_graph

# --- IRS palette ---------------------------------------------------------
HEADER_BLUE = "#2a5a91"
NAV_NAVY = "#112e51"
LINK_BLUE = "#0071bc"
GOV_GRAY = "#f0f0f0"

st.set_page_config(page_title="401(k) plans | Internal Revenue Service",
                   page_icon="🇺🇸", layout="wide")


@st.cache_resource(show_spinner=False)
def get_graph():
    """Compile the LangGraph once and reuse across reruns."""
    return build_graph()


# --- Global CSS: strip Streamlit chrome, load fonts, define IRS classes ---
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;700&family=Merriweather:wght@700&display=swap');

    #MainMenu, footer, header[data-testid="stHeader"] {{ display: none; }}
    [data-testid="stAppViewContainer"] {{ background: #fff; }}
    .block-container {{ padding: 0 !important; max-width: 100% !important; }}
    html, body, [class*="css"] {{ font-family: 'Public Sans', Arial, sans-serif; }}

    .gov-banner {{
        background: {GOV_GRAY}; font-size: 12px; color: #1b1b1b;
        padding: 6px 32px;
    }}
    .gov-banner a {{ color: {LINK_BLUE}; text-decoration: none; }}

    .irs-header {{
        background: {HEADER_BLUE}; color: #fff; padding: 18px 32px;
        display: flex; align-items: center; justify-content: space-between;
    }}
    .irs-logo {{ font-size: 30px; font-weight: 700; letter-spacing: 1px;
        font-family: 'Merriweather', Georgia, serif; }}
    .irs-utility a {{ color: #fff; text-decoration: none; font-size: 14px;
        margin-left: 22px; }}

    .irs-nav {{
        background: {NAV_NAVY}; padding: 0 32px; display: flex;
        align-items: center; justify-content: space-between;
    }}
    .irs-nav .links a {{ color: #fff; text-decoration: none; font-size: 15px;
        font-weight: 600; display: inline-block; padding: 16px 16px; }}
    .irs-nav .links a:hover {{ background: {HEADER_BLUE}; }}
    .irs-search {{ background: #fff; border: none; padding: 8px 12px;
        width: 240px; font-size: 14px; }}

    .breadcrumb {{ padding: 18px 32px 0; font-size: 15px; color: #565c65; }}
    .breadcrumb a {{ color: {LINK_BLUE}; text-decoration: none; }}

    .page-title {{ padding: 6px 32px 12px; font-size: 44px; font-weight: 700;
        font-family: 'Merriweather', Georgia, serif; color: #1b1b1b; }}

    .content-wrap {{ padding: 0 32px 48px; }}

    .side-nav a {{ display: block; padding: 16px 4px; font-size: 17px;
        font-weight: 700; color: #1b1b1b; text-decoration: none;
        border-bottom: 1px solid #d6d7d9; }}
    .side-nav a:first-child {{ border-top: 1px solid #d6d7d9; }}
    .side-nav a:hover {{ color: {LINK_BLUE}; }}

    .lead {{ font-size: 17px; line-height: 1.6; color: #1b1b1b; }}

    .answer-box {{ border-left: 5px solid {HEADER_BLUE}; background: #f7f9fb;
        padding: 16px 22px; margin-top: 8px; font-size: 16px; line-height: 1.6; }}
    .conflict-box {{ border-left: 5px solid #d54309; background: #fff5f0;
        padding: 12px 18px; margin-top: 16px; font-size: 15px; }}

    div.stButton > button {{
        background: {HEADER_BLUE}; color: #fff; border: none; border-radius: 0;
        font-weight: 700; padding: 8px 26px; }}
    div.stButton > button:hover {{ background: {NAV_NAVY}; color: #fff; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Page chrome (static, matches the screenshot) ------------------------
st.markdown(
    """
    <div class="gov-banner">🇺🇸 An official website of the United States government &nbsp;
        <a href="#">Here's how you know ⌄</a></div>

    <div class="irs-header">
        <div class="irs-logo">&#9670; IRS</div>
        <div class="irs-utility">
            <a href="#">Help</a><a href="#">News</a><a href="#">English ⌄</a>
            <a href="#">Tax Pros</a><a href="#">Sign in</a>
        </div>
    </div>

    <div class="irs-nav">
        <div class="links">
            <a href="#">File</a><a href="#">Pay</a><a href="#">Refunds</a>
            <a href="#">Credits &amp; Deductions</a><a href="#">Forms</a>
            <a href="#">Report Fraud</a>
        </div>
        <input class="irs-search" placeholder="Search" />
    </div>

    <div class="breadcrumb">
        <a href="#">Home</a> / <a href="#">Retirement Plans</a> / 401(k) plans
    </div>
    <div class="page-title">401(k) plans</div>
    """,
    unsafe_allow_html=True,
)

# --- Body: sidebar nav + main research area ------------------------------
st.markdown('<div class="content-wrap">', unsafe_allow_html=True)
side, main = st.columns([1, 3], gap="large")

with side:
    st.markdown(
        """
        <div class="side-nav">
            <a href="#">IRAs</a>
            <a href="#">Types of retirement plans</a>
            <a href="#">Required minimum distributions</a>
            <a href="#">Published guidance</a>
            <a href="#">Forms and publications</a>
            <a href="#">Operate a retirement plan</a>
            <a href="#">News</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

with main:
    st.markdown(
        '<p class="lead">Ask about current 401(k) / retirement tax rules. '
        'Answers are researched across the web, cross-checked against curated '
        'IRS figures, and cited — no number is stated unless it verifies.</p>',
        unsafe_allow_html=True,
    )

    question = st.text_input(
        "Your question",
        placeholder="What are the 2026 401(k) contribution limits and what changed from 2025?",
        label_visibility="collapsed",
    )
    go = st.button("Search")

    if go:
        q = (question or "").strip() or (
            "What are the 2026 401(k) contribution limits and what changed from 2025?"
        )
        with st.spinner("Researching, extracting claims, and verifying against IRS ground truth…"):
            final = get_graph().invoke({"question": q, "round": 0},
                                       config={"recursion_limit": 25})

        st.markdown(f"### {q}")
        answer = final.get("answer") or "_(no answer produced)_"
        st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

        conflicts = final.get("conflicts") or []
        if conflicts:
            items = "".join(f"<li>{c}</li>" for c in conflicts)
            st.markdown(
                f'<div class="conflict-box"><b>⚠ Verification conflicts</b>'
                f'<ul>{items}</ul></div>',
                unsafe_allow_html=True,
            )

        cites = final.get("citations") or []
        if cites:
            st.markdown("#### Sources")
            for i, c in enumerate(cites, 1):
                st.markdown(f"{i}. [{c.title}]({c.url})")

st.markdown('</div>', unsafe_allow_html=True)
