"""Typed repositories over JsonStore.

Repositories own (de)serialisation to pydantic models and read-modify-write
safety. Business logic lives in app/services/*.
"""
from __future__ import annotations

import secrets
from typing import Iterator

from app.core.logging import get_logger
from app.schemas import Matter, MatterSummary
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
        return _Mutation(self._store, matter_id)


class _Mutation:
    def __init__(self, store: JsonStore, matter_id: str) -> None:
        self._store = store
        self._id = matter_id
        self._matter: Matter | None = None

    def __enter__(self) -> Matter:
        self._store.lock().acquire()
        raw = self._store.get(self._id)
        if raw is None:
            self._store.lock().release()
            raise KeyError(self._id)
        self._matter = Matter.model_validate(raw)
        return self._matter

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None and self._matter is not None:
                self._store.put(self._id, self._matter.model_dump(mode="json"))
        finally:
            self._store.lock().release()


_matter_repo: MatterRepo | None = None


def get_matter_repo() -> MatterRepo:
    global _matter_repo
    if _matter_repo is None:
        _matter_repo = MatterRepo()
    return _matter_repo
