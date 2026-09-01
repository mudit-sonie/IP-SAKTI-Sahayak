"""Human-reviewed FAQ (roadmap S5).

A facilitator's answer to an escalation can be published as an FAQ entry. On a
later question, a close-enough FAQ match is served *ahead of* the model — a
reviewed answer always beats a generated one.

Matching is deliberately simple and conservative: stop-word-filtered token
Jaccard over the question, same jurisdiction, above a configurable threshold.
"""
from __future__ import annotations

import re

from app.config import get_settings
from app.core.logging import get_logger
from app.schemas import FaqEntry
from app.store.repos import get_faq_repo

logger = get_logger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "a", "an", "is", "are", "was", "were", "do", "does", "did", "i", "we",
    "to", "of", "in", "for", "on", "and", "or", "can", "could", "my", "our",
    "this", "that", "what", "how", "when", "why", "be", "it", "as", "at", "by",
    "with", "if", "not", "have", "has", "any", "would", "should",
}


def tokens(text: str) -> set[str]:
    return {
        t for t in _TOKEN_RE.findall(text.lower())
        if len(t) > 2 and t not in _STOP
    }


def keywords(question: str) -> list[str]:
    return sorted(tokens(question))[:24]


def match(query: str, jurisdiction: str) -> FaqEntry | None:
    if not get_settings().faq_enabled:
        return None
    qt = tokens(query)
    if not qt:
        return None
    threshold = get_settings().faq_match_threshold
    best: FaqEntry | None = None
    best_score = 0.0
    for entry in get_faq_repo().list():
        if entry.jurisdiction.value != jurisdiction:
            continue
        et = set(entry.keywords) or tokens(entry.question)
        if not et:
            continue
        score = len(qt & et) / len(qt | et)
        if score > best_score:
            best, best_score = entry, score
    if best is not None and best_score >= threshold:
        logger.info("FAQ hit (%.2f) for %r -> %s", best_score, query, best.id)
        return best
    return None
