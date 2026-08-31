"""Generic JSON document store.

    store = JsonStore("matters")
    store.put("abc123", {"id": "abc123", ...})
    doc = store.get("abc123")
    for doc in store.list(): ...

Design constraints (PRODUCT_ROADMAP.md):
- one file per aggregate: data_dir/<name>/<id>.json
- atomic writes: temp file + os.replace, so a crash never leaves a half file
- in-process locking: FastAPI runs sync routes in a threadpool, so two requests
  can touch the same store concurrently — a per-store RLock serialises writes
- no schema here: repositories on top validate with pydantic
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Iterator

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_ID_OK = set(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)


class StoreError(RuntimeError):
    """Raised for unrecoverable store problems (bad id, corrupt file on write)."""


def _safe_id(record_id: str) -> str:
    rid = (record_id or "").strip()
    if not rid or not set(rid) <= _ID_OK or len(rid) > 128:
        raise StoreError(f"invalid record id: {record_id!r}")
    return rid


class JsonStore:
    """A directory of JSON documents under ``<data_dir>/<name>/``."""

    _locks: dict[str, threading.RLock] = {}
    _locks_guard = threading.Lock()

    def __init__(self, name: str) -> None:
        self.name = name
        with JsonStore._locks_guard:
            self._lock = JsonStore._locks.setdefault(name, threading.RLock())

    @property
    def dir(self) -> Path:
        return Path(get_settings().data_dir) / self.name

    def _path(self, record_id: str) -> Path:
        return self.dir / f"{_safe_id(record_id)}.json"

    # ---- reads ----

    def exists(self, record_id: str) -> bool:
        return self._path(record_id).exists()

    def get(self, record_id: str) -> dict[str, Any] | None:
        p = self._path(record_id)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover
            logger.warning("corrupt store file %s (%s); skipping", p, exc)
            return None

    def list(self) -> Iterator[dict[str, Any]]:
        if not self.dir.exists():
            return
        for p in sorted(self.dir.glob("*.json")):
            try:
                yield json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover
                logger.warning("corrupt store file %s (%s); skipping", p, exc)

    # ---- writes ----

    def put(self, record_id: str, doc: dict[str, Any]) -> None:
        rid = _safe_id(record_id)
        p = self._path(rid)
        payload = json.dumps(doc, indent=2, ensure_ascii=False, default=str)
        with self._lock:
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(f".json.{os.getpid()}.tmp")
            tmp.write_text(payload, encoding="utf-8")
            os.replace(tmp, p)  # atomic on POSIX and Windows

    def delete(self, record_id: str) -> bool:
        p = self._path(record_id)
        with self._lock:
            if not p.exists():
                return False
            p.unlink()
            return True

    def lock(self) -> threading.RLock:
        """Expose the store lock for read-modify-write sequences in a repo."""
        return self._lock
