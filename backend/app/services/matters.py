"""Matter lifecycle — create, record a grounded question, keep derived state fresh.

A matter is the persistent formulation profile the workspace is built around.
Storage is a single JSON document per matter (app/store).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.config import get_settings
from app.core.logging import get_logger
from app.schemas import (
    AbsStatus,
    AuditEntry,
    Jurisdiction,
    Matter,
    MatterCreateRequest,
    MatterQuestion,
    MatterQuestionRequest,
    MatterUpdateRequest,
    QueryRequest,
    QueryResponse,
)
from app.services import pipeline
from app.store.repos import get_matter_repo, new_id

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _audit(matter: Matter, action: str, detail: str | None = None) -> None:
    matter.audit.append(AuditEntry(at=_now(), action=action, detail=detail))
    matter.updated_at = _now()


def create(req: MatterCreateRequest) -> Matter:
    now = _now()
    matter = Matter(
        id=new_id(),
        owner=get_settings().local_owner,
        title=req.title.strip() or "Untitled matter",
        created_at=now,
        updated_at=now,
        jurisdiction=req.jurisdiction,
        formulation_category=req.formulation_category,
        formulation_label=req.formulation_label,
        classification_rationale=req.classification_rationale,
        notes=req.notes,
    )
    _audit(matter, "matter.created", matter.title)
    get_matter_repo().save(matter)
    logger.info("matter created: %s (%s)", matter.id, matter.title)
    return matter


def update(matter_id: str, req: MatterUpdateRequest) -> Matter:
    repo = get_matter_repo()
    with repo.mutate(matter_id) as matter:
        for field in ("title", "jurisdiction", "formulation_category",
                      "formulation_label", "notes"):
            val = getattr(req, field)
            if val is not None:
                setattr(matter, field, val)
        _audit(matter, "matter.updated")
        return matter


def delete(matter_id: str) -> bool:
    return get_matter_repo().delete(matter_id)


def _recompute_abs_status(matter: Matter) -> None:
    """flagged wins once seen; else clear if any question ran clean; else unknown."""
    if any(q.abs_flag for q in matter.questions):
        matter.abs_status = AbsStatus.flagged
    elif matter.questions:
        matter.abs_status = AbsStatus.clear
    else:
        matter.abs_status = AbsStatus.unknown


def ask(matter_id: str, req: MatterQuestionRequest) -> tuple[Matter, MatterQuestion, QueryResponse]:
    repo = get_matter_repo()
    # Run the grounded pipeline outside the store lock (it can be slow).
    with repo.mutate(matter_id) as matter:
        jurisdiction = req.jurisdiction or matter.jurisdiction
        category = req.formulation_category or matter.formulation_category

    query_req = QueryRequest(
        query=req.query,
        jurisdiction=Jurisdiction(jurisdiction),
        formulation_category=category,
    )
    result = pipeline.run_query(query_req)

    question = MatterQuestion(
        id=new_id("q_"),
        query=req.query,
        jurisdiction=Jurisdiction(jurisdiction),
        formulation_category=category,
        asked_at=_now(),
        answer=result.answer,
        status=result.confidence.status,
        self_confidence=result.confidence.self_confidence,
        retrieval_score=result.confidence.retrieval_score,
        citations=result.citations,
        abs_flag=result.abs_flag,
    )

    with repo.mutate(matter_id) as matter:
        matter.questions.append(question)
        _recompute_abs_status(matter)
        _audit(
            matter,
            "question.asked",
            f"{req.query[:80]} → {question.status.value}",
        )
        saved = matter

    return saved, question, result
