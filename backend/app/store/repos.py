"""Typed repositories over JsonStore.

Repositories own (de)serialisation to pydantic models and read-modify-write
safety. Business logic lives in app/services/*.
"""
from __future__ import annotations

import secrets
from typing import Iterator

from app.core.logging import get_logger
from app.schemas import Escalation, FaqEntry, Matter, MatterSummary
from app.store.json_store import JsonStore

logger = get_logger(__name__)


def new_id(prefix: str = "") -> str:
    token = secrets.token_hex(6)
    return f"{prefix}{token}" if prefix else token


class MatterRepo:
    def __init__(self) -> None:
        self._store = JsonStore("matters")

    def get(self, matter_id: str) -> Matter | None:
        raw = self._store.get(matter_id)
        return Matter.model_validate(raw) if raw else None

    def save(self, matter: Matter) -> None:
        self._store.put(matter.id, matter.model_dump(mode="json"))

    def delete(self, matter_id: str) -> bool:
        return self._store.delete(matter_id)

    def list_summaries(self, owner: str | None = None) -> list[MatterSummary]:
        out: list[MatterSummary] = []
        for raw in self._store.list():
            if owner is not None and raw.get("owner") != owner:
                continue
            m = Matter.model_validate(raw)
            out.append(
                MatterSummary(
                    id=m.id,
                    title=m.title,
                    jurisdiction=m.jurisdiction,
                    formulation_label=m.formulation_label,
                    abs_status=m.abs_status,
                    question_count=len(m.questions),
                    open_checklist_items=sum(
                        1 for c in m.checklist if c.status != "done"
                    ),
                    updated_at=m.updated_at,
                )
            )
        out.sort(key=lambda s: s.updated_at, reverse=True)
        return out

    def mutate(self, matter_id: str):
        """Context manager: load, yield for mutation, save under the store lock.

            with repo.mutate(mid) as m:
                m.notes = "..."
        """
        return _Mutation(self._store, matter_id, Matter)


class _Mutation:
    def __init__(self, store: JsonStore, record_id: str, model) -> None:
        self._store = store
        self._id = record_id
        self._model = model
        self._obj = None

    def __enter__(self):
        self._store.lock().acquire()
        raw = self._store.get(self._id)
        if raw is None:
            self._store.lock().release()
            raise KeyError(self._id)
        self._obj = self._model.model_validate(raw)
        return self._obj

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None and self._obj is not None:
                self._store.put(self._id, self._obj.model_dump(mode="json"))
        finally:
            self._store.lock().release()


class EscalationRepo:
    def __init__(self) -> None:
        self._store = JsonStore("escalations")

    def get(self, eid: str) -> Escalation | None:
        raw = self._store.get(eid)
        return Escalation.model_validate(raw) if raw else None

    def save(self, esc: Escalation) -> None:
        self._store.put(esc.id, esc.model_dump(mode="json"))

    def delete(self, eid: str) -> bool:
        return self._store.delete(eid)

    def list(self, status: str | None = None) -> list[Escalation]:
        out = [Escalation.model_validate(r) for r in self._store.list()]
        if status is not None:
            out = [e for e in out if e.status == status]
        out.sort(key=lambda e: e.created_at, reverse=True)
        return out

    def mutate(self, eid: str):
        return _Mutation(self._store, eid, Escalation)


class FaqRepo:
    def __init__(self) -> None:
        self._store = JsonStore("faq")

    def get(self, fid: str) -> FaqEntry | None:
        raw = self._store.get(fid)
        return FaqEntry.model_validate(raw) if raw else None

    def save(self, entry: FaqEntry) -> None:
        self._store.put(entry.id, entry.model_dump(mode="json"))

    def delete(self, fid: str) -> bool:
        return self._store.delete(fid)

    def list(self) -> list[FaqEntry]:
        out = [FaqEntry.model_validate(r) for r in self._store.list()]
        out.sort(key=lambda f: f.updated_at, reverse=True)
        return out


_matter_repo: MatterRepo | None = None
_escalation_repo: EscalationRepo | None = None
_faq_repo: FaqRepo | None = None


def get_matter_repo() -> MatterRepo:
    global _matter_repo
    if _matter_repo is None:
        _matter_repo = MatterRepo()
    return _matter_repo


def get_escalation_repo() -> EscalationRepo:
    global _escalation_repo
    if _escalation_repo is None:
        _escalation_repo = EscalationRepo()
    return _escalation_repo


def get_faq_repo() -> FaqRepo:
    global _faq_repo
    if _faq_repo is None:
        _faq_repo = FaqRepo()
    return _faq_repo
