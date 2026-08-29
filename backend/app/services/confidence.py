"""Confidence scoring (PRD section 5).

Primary signal: retrieval top fused score vs a configured threshold — deterministic
and defensible. Secondary: the LLM's self-reported confidence, surfaced for UI
nuance but never able to *rescue* a low-retrieval answer.

Rule:
  - no hits / top_score < threshold      -> status = escalate
  - top_score >= threshold, no citations -> status = escalate
  - otherwise                            -> status = answered
"""
from __future__ import annotations

from app.config import get_settings
from app.schemas import AnswerStatus, Confidence, SelfConfidence


def score(
    retrieval_top_score: float,
    self_confidence: SelfConfidence | str,
    *,
    has_citations: bool,
) -> Confidence:
    settings = get_settings()
    threshold = settings.retrieval_escalate_threshold

    if isinstance(self_confidence, str):
        try:
            self_confidence = SelfConfidence(self_confidence.lower())
        except ValueError:
            self_confidence = SelfConfidence.low

    below = retrieval_top_score < threshold
    status = (
        AnswerStatus.escalate
        if (below or not has_citations)
        else AnswerStatus.answered
    )
    return Confidence(
        retrieval_score=round(float(retrieval_top_score), 4),
        self_confidence=self_confidence,
        status=status,
    )
