"""Facilitator queue (roadmap S5).

Every escalate response is persisted here for a human IP facilitator to answer.
Answering optionally publishes the answer to the reviewed FAQ, which is then
served ahead of the model on matching questions.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from app.config import get_settings
from app.core.logging import get_logger
from app.llm.gemini_client import get_gemini_client
from app.schemas import (
    Escalation,
    EscalationAnswerRequest,
    EscalationStatus,
    FaqCreateRequest,
    FaqEntry,
    QueryRequest,
    QueryResponse,
)
from app.services import faq, safety
from app.store.repos import get_escalation_repo, get_faq_repo, new_id

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _norm(q: str) -> str:
    return re.sub(r"\s+", " ", q.strip().lower())


def _reason(req: QueryRequest) -> str:
    if safety.is_high_stakes(req.query):
        return "high_stakes"
    if not get_gemini_client().is_configured:
        return "no_gemini"
    return "low_retrieval"


def record_from_query(req: QueryRequest, resp: QueryResponse) -> None:
    """Persist an escalation, unless queueing is off or a duplicate is open."""
    if not get_settings().escalations_enabled:
        return
    norm = _norm(req.query)
    for e in get_escalation_repo().list(status=EscalationStatus.open.value):
        if _norm(e.query) == norm and e.jurisdiction == req.jurisdiction:
            return
    esc = Escalation(
        id=new_id("esc_"),
        created_at=_now(),
        query=req.query,
        jurisdiction=req.jurisdiction,
        formulation_category=req.formulation_category,
        context=req.context,
        retrieval_score=resp.confidence.retrieval_score,
        self_confidence=resp.confidence.self_confidence,
        reason=_reason(req),
        source="matter" if req.matter_id else "query",
        matter_id=req.matter_id,
    )
    get_escalation_repo().save(esc)
    logger.info("escalation queued: %s (%s)", esc.id, esc.reason)


def list_escalations(status: str | None = None) -> list[Escalation]:
    return get_escalation_repo().list(status=status)


def get_escalation(eid: str) -> Escalation | None:
    return get_escalation_repo().get(eid)


def answer(eid: str, req: EscalationAnswerRequest) -> Escalation:
    if not req.answer.strip():
        raise ValueError("answer must not be empty")
    with get_escalation_repo().mutate(eid) as esc:
        esc.answer = req.answer.strip()
        esc.answer_citations = req.citations
        esc.answered_at = _now()
        esc.status = EscalationStatus.answered
        if req.publish_faq and get_settings().faq_enabled:
            entry = FaqEntry(
                id=new_id("faq_"),
                question=esc.query,
                jurisdiction=esc.jurisdiction,
                formulation_category=esc.formulation_category,
                answer=esc.answer,
                citations=req.citations,
                keywords=faq.keywords(esc.query),
                created_at=_now(),
                updated_at=_now(),
                source_escalation_id=esc.id,
            )
            get_faq_repo().save(entry)
            esc.faq_id = entry.id
            logger.info("FAQ published from escalation %s -> %s", eid, entry.id)
        return esc


def dismiss(eid: str) -> Escalation:
    with get_escalation_repo().mutate(eid) as esc:
        esc.status = EscalationStatus.dismissed
        return esc


def list_faq() -> list[FaqEntry]:
    return get_faq_repo().list()


def create_faq(req: FaqCreateRequest) -> FaqEntry:
    entry = FaqEntry(
        id=new_id("faq_"),
        question=req.question.strip(),
        jurisdiction=req.jurisdiction,
        formulation_category=req.formulation_category,
        answer=req.answer.strip(),
        citations=req.citations,
        keywords=faq.keywords(req.question),
        created_at=_now(),
        updated_at=_now(),
    )
    get_faq_repo().save(entry)
    return entry


def delete_faq(fid: str) -> bool:
    return get_faq_repo().delete(fid)
