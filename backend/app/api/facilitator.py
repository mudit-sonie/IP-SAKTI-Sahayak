"""Facilitator queue + reviewed FAQ routes (roadmap S5).

    GET    /escalations                list the queue (optional ?status=)
    GET    /escalations/{id}           one escalation
    POST   /escalations/{id}/answer    answer it (optionally publish to FAQ)
    POST   /escalations/{id}/dismiss   drop it from the queue
    GET    /faq                        published reviewed answers
    POST   /faq                        add one directly
    DELETE /faq/{id}                   remove one
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.config import get_settings
from app.schemas import (
    Escalation,
    EscalationAnswerRequest,
    FaqCreateRequest,
    FaqEntry,
)
from app.services import escalations as svc

router = APIRouter(tags=["facilitator"])


def _require_queue() -> None:
    if not get_settings().escalations_enabled:
        raise HTTPException(status_code=404, detail="facilitator queue is disabled")


@router.get("/escalations", response_model=list[Escalation])
def list_escalations(status: str | None = Query(default=None)) -> list[Escalation]:
    _require_queue()
    return svc.list_escalations(status=status)


@router.get("/escalations/{escalation_id}", response_model=Escalation)
def get_escalation(escalation_id: str) -> Escalation:
    _require_queue()
    esc = svc.get_escalation(escalation_id)
    if esc is None:
        raise HTTPException(status_code=404, detail="escalation not found")
    return esc


@router.post("/escalations/{escalation_id}/answer", response_model=Escalation)
def answer_escalation(
    escalation_id: str, req: EscalationAnswerRequest
) -> Escalation:
    _require_queue()
    try:
        return svc.answer(escalation_id, req)
    except KeyError:
        raise HTTPException(status_code=404, detail="escalation not found")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/escalations/{escalation_id}/dismiss", response_model=Escalation)
def dismiss_escalation(escalation_id: str) -> Escalation:
    _require_queue()
    try:
        return svc.dismiss(escalation_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="escalation not found")


@router.get("/faq", response_model=list[FaqEntry])
def list_faq() -> list[FaqEntry]:
    return svc.list_faq()


@router.post("/faq", response_model=FaqEntry, status_code=201)
def create_faq(req: FaqCreateRequest) -> FaqEntry:
    if not get_settings().faq_enabled:
        raise HTTPException(status_code=404, detail="FAQ is disabled")
    if not req.question.strip() or not req.answer.strip():
        raise HTTPException(status_code=422, detail="question and answer are required")
    return svc.create_faq(req)


@router.delete("/faq/{faq_id}", status_code=204)
def delete_faq(faq_id: str) -> None:
    if not svc.delete_faq(faq_id):
        raise HTTPException(status_code=404, detail="FAQ entry not found")
