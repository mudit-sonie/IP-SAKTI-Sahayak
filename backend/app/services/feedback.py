"""Append-only answer feedback log (``backend/data/feedback.jsonl``).

Thumbs up/down + optional note from the Result screen. Not analytics
infrastructure — it's the raw material for the Day-4 spot-check ("15 Q&As vs
source text") and a quick signal on where retrieval/generation is weak.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.logging import get_logger
from app.schemas import FeedbackRequest

logger = get_logger(__name__)

LOG_PATH = Path(__file__).resolve().parents[2] / "data" / "feedback.jsonl"


def record(req: FeedbackRequest) -> None:
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rating": req.rating,
        "query": req.query,
        "jurisdiction": req.jurisdiction,
        "formulation_category": req.formulation_category,
        "answer_status": req.answer_status,
        "cited_sections": req.cited_sections,
        "note": (req.note or "").strip() or None,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.info("feedback: %s on %r", req.rating, req.query[:60])
