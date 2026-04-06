"""Parse opportunity markdown sections into structured display data."""

from __future__ import annotations

import re

from coliseum.domain.opportunity import OpportunitySignal


def parse_opportunity_sections(opp: OpportunitySignal, markdown_body: str) -> dict | None:
    """Return structured display sections or None on any failure (triggers frontend fallback)."""
    try:
        return {
            "scout": _parse_scout(opp),
            "research": _parse_research(markdown_body),
            "trader": _parse_trader(opp),
        }
    except Exception:
        return None


def _parse_scout(opp: OpportunitySignal) -> dict:
    return {
        "outcome_status": opp.outcome_status,
        "risk_level": opp.risk_level,
        "summary": opp.rationale,
        "evidence": opp.evidence_bullets,
        "resolution_source": opp.resolution_source,
        "remaining_risks": [
            r for r in opp.remaining_risks
            if r.lower() not in ("none identified", "none")
        ],
        "sources": opp.scout_sources,
        "is_structured": bool(opp.outcome_status),
    }


def _parse_research(markdown_body: str) -> dict | None:
    m = re.search(r"## Research Synthesis\n+(.*?)(?=\n## |\Z)", markdown_body, re.DOTALL)
    if not m:
        return None
    s = m.group(1)

    flip = re.search(r"\*\*Flip Risk:\*\*\s*(YES|NO|UNCERTAIN)", s)
    conf = re.search(r"Confidence:\s*(HIGH|MEDIUM|LOW)", s)

    if flip:
        flip_risk = flip.group(1)
    else:
        flip_risk = "UNCERTAIN"

    if conf:
        confidence = conf.group(1)
    else:
        confidence = None

    return {
        "flip_risk": flip_risk,
        "confidence": confidence,
        "event_status": _subsection(s, "Event Status"),
        "evidence_for": _bullets(s, "Key Evidence For YES"),
        "evidence_against": _bullets(s, "Key Evidence Against YES"),
        "resolution_mechanics": _subsection(s, "Resolution Mechanics"),
        "conclusion": _subsection(s, "Conclusion"),
        "unconfirmed": [u for u in _bullets(s, "Unconfirmed") if u.lower() != "none"],
        "sources": re.findall(r"https?://\S+", s),
    }


def _subsection(text: str, header: str) -> str:
    """Extract text under a **Header:** marker up to the next ** or end."""
    m = re.search(
        rf"\*\*{re.escape(header)}:\*\*\s*\n?(.*?)(?=\n\*\*|\Z)",
        text,
        re.DOTALL,
    )
    if m:
        return m.group(1).strip()
    else:
        return ""


def _bullets(text: str, header: str) -> list[str]:
    """Extract bullet list items under a **Header:** marker."""
    m = re.search(
        rf"\*\*{re.escape(header)}:\*\*\s*\n((?:[-•]\s*.+\n?)+)",
        text,
    )
    if not m:
        return []
    return [
        re.sub(r"^[-•]\s*", "", line).strip()
        for line in m.group(1).splitlines()
        if line.strip()
    ]


def _parse_trader(opp: OpportunitySignal) -> dict | None:
    """Extract trader verdict if available."""
    if not opp.trader_decision:
        return None
    return {
        "decision": opp.trader_decision,
        "tldr": opp.trader_tldr or "",
    }
