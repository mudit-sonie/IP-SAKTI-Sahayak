"""Anonymized usage analytics (roadmap S16).

Aggregate counters only — the query text is never stored, and there is no user
identifier to store. One JSON file (`data/analytics.json`), updated under a lock
on each query, read back for the /analytics summary.
"""
from __future__ import annotations

import json
import os
import threading
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.core.logging import get_logger
from app.schemas import AnalyticsSummary, QueryRequest, QueryResponse

logger = get_logger(__name__)

_LOCK = threading.Lock()
_MAX_DAYS = 60
_TOP_SOURCES = 12


def _path() -> Path:
    return Path(get_settings().data_dir) / "analytics.json"


def _blank() -> dict:
    return {
        "total_queries": 0,
        "by_status": {},
        "by_jurisdiction": {},
        "by_category": {},
        "top_sources": {},
        "abs_flag_count": 0,
        "from_faq_count": 0,
        "escalation_count": 0,
        "by_day": {},
    }


def _load() -> dict:
    p = _path()
    if not p.exists():
        return _blank()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return {**_blank(), **data}
    except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover
        logger.warning("analytics file unreadable (%s); starting fresh", exc)
        return _blank()


def _save(data: dict) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(f".json.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def _bump(d: dict, key: str | None) -> None:
    if not key:
        return
    d[key] = d.get(key, 0) + 1


def record(req: QueryRequest, resp: QueryResponse) -> None:
    if not get_settings().analytics_enabled:
        return
    status = resp.confidence.status.value
    day = datetime.now(timezone.utc).date().isoformat()
    sources = [c.source for c in resp.citations if c.source]
    try:
        with _LOCK:
            data = _load()
            data["total_queries"] += 1
            _bump(data["by_status"], status)
            _bump(data["by_jurisdiction"], req.jurisdiction.value)
            _bump(data["by_category"], (req.formulation_category or "unclassified"))
            _bump(data["by_day"], day)
            for s in set(sources):
                _bump(data["top_sources"], s)
            if resp.abs_flag:
                data["abs_flag_count"] += 1
            if resp.from_faq:
                data["from_faq_count"] += 1
            if status == "escalate":
                data["escalation_count"] += 1
            # keep by_day bounded
            if len(data["by_day"]) > _MAX_DAYS:
                for k in sorted(data["by_day"])[:-_MAX_DAYS]:
                    data["by_day"].pop(k, None)
            _save(data)
    except Exception as exc:  # pragma: no cover - analytics must never break a query
        logger.warning("analytics record failed: %s", exc)


def summary() -> AnalyticsSummary:
    data = _load()
    total = max(data["total_queries"], 1)
    top = dict(Counter(data["top_sources"]).most_common(_TOP_SOURCES))
    return AnalyticsSummary(
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        total_queries=data["total_queries"],
        by_status=data["by_status"],
        by_jurisdiction=data["by_jurisdiction"],
        by_category=data["by_category"],
        top_sources=top,
        abs_flag_rate=round(data["abs_flag_count"] / total, 3),
        from_faq_rate=round(data["from_faq_count"] / total, 3),
        escalation_rate=round(data["escalation_count"] / total, 3),
        by_day=dict(sorted(data["by_day"].items())),
    )
