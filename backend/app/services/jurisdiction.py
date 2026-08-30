"""Jurisdiction mismatch guard.

The user picks a jurisdiction toggle (india / international) which routes
retrieval. If the question itself clearly points the other way, surface a note so
the UI can offer to switch — we do NOT silently re-route, because the toggle is a
deliberate choice.
"""
from __future__ import annotations

import re

_INDIA = re.compile(
    r"\b(india|indian|india code|ip india|cdsco|fssai|nba|"
    r"national biodiversity authority|state biodiversity board|"
    r"patents act|trade marks act|geographical indications? of goods|"
    r"biological diversity act|drugs and cosmetics act)\b",
    re.I,
)
_INTL = re.compile(
    r"\b(trips|wto|world trade organization|paris convention|berne convention|"
    r"nagoya protocol|convention on biological diversity|\bcbd\b|wipo|pct|"
    r"madrid protocol|international treaty)\b",
    re.I,
)


def mismatch_note(query: str, jurisdiction: str) -> str | None:
    j = jurisdiction.lower()
    if j == "international" and _INDIA.search(query) and not _INTL.search(query):
        return (
            "Your question refers to Indian law, but the jurisdiction is set to "
            "International. Switch to India for statute-level guidance — the "
            "international corpus only covers TRIPS and CBD/Nagoya."
        )
    if j == "india" and _INTL.search(query) and not _INDIA.search(query):
        return (
            "Your question refers to an international instrument, but the "
            "jurisdiction is set to India. Switch to International to search "
            "TRIPS and CBD/Nagoya."
        )
    return None
