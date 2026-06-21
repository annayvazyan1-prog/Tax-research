"""Deterministic tax-fact ground truth for the verifier.

This is the trust anchor. When Tavily returns a number, the verifier checks it
against these curated, sourced figures rather than trusting the open web. In the
combined project this would import the richer knowledge base from the explainer
repo; it's inlined here so this service is self-contained.

Figures verified against IRS announcements for tax year 2026.
"""

from __future__ import annotations

# Canonical 2026 facts, each with the authoritative source.
KB_FACTS_2026: dict[str, dict] = {
    "employee_deferral_limit": {
        "value": 24_500, "unit": "USD",
        "desc": "401(k)/403(b)/457 employee elective deferral limit",
        "source": "https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500",
    },
    "catchup_50_plus": {
        "value": 8_000, "unit": "USD",
        "desc": "Age 50+ catch-up contribution",
        "source": "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-401k-and-profit-sharing-plan-contribution-limits",
    },
    "super_catchup_60_63": {
        "value": 11_250, "unit": "USD",
        "desc": "Age 60-63 'super' catch-up (SECURE 2.0)",
        "source": "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-401k-and-profit-sharing-plan-contribution-limits",
    },
    "combined_415_limit": {
        "value": 72_000, "unit": "USD",
        "desc": "Combined employee + employer annual additions limit",
        "source": "https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500",
    },
    "roth_catchup_wage_threshold": {
        "value": 150_000, "unit": "USD",
        "desc": "Prior-year FICA wages above which 50+ catch-up must be Roth (2026)",
        "source": "https://www.irs.gov/retirement-plans",
    },
    "ira_limit": {
        "value": 7_500, "unit": "USD",
        "desc": "Traditional/Roth IRA contribution limit",
        "source": "https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500",
    },
}


def kb_context(year: int = 2026) -> str:
    """Render the KB as authoritative context for the verifier prompt."""
    if year != 2026:
        return f"(No curated KB facts for {year}; treat web figures as unverified.)"
    lines = [f"Authoritative {year} tax facts (ground truth):"]
    for key, f in KB_FACTS_2026.items():
        lines.append(f"- {f['desc']}: ${f['value']:,} [{f['source']}]")
    return "\n".join(lines)
