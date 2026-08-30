"""On-disk cache for /query responses.

Keyed by a hash of (normalised query, jurisdiction, formulation_category). A hit
returns the stored QueryResponse with ``cached=True``. Used to (a) make repeated
demo questions instant and (b) keep the demo alive past Gemini's daily free-tier
quota — warm the cache with the gold questions ahead of time.

Only *answered* responses are cached; an ``escalate`` may become answerable once
more corpus / keys land, so we don't want to pin it.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.config import get_settings
from app.core.logging import get_logger
from app.schemas import AnswerStatus, QueryRequest, QueryResponse

logger = get_logger(__name__)


def _key(req: QueryRequest) -> str:
    raw = "\x1f".join(
        [
            (req.query or "").strip().lower(),
            req.jurisdiction.value,
            (req.formulation_category or "").strip().lower(),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _path(req: QueryRequest) -> Path:
    settings = get_settings()
    return Path(settings.query_cache_dir) / f"{_key(req)}.json"


def get(req: QueryRequest) -> QueryResponse | None:
    settings = get_settings()
    if not settings.query_cache_enabled:
        return None
    p = _path(req)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        resp = QueryResponse.model_validate(data)
    except Exception as exc:  # pragma: no cover - corrupt cache entry
        logger.warning("bad cache entry %s (%s); ignoring", p, exc)
        return None
    resp.cached = True
    return resp


def put(req: QueryRequest, resp: QueryResponse) -> None:
    settings = get_settings()
    if not settings.query_cache_enabled:
        return
    if resp.confidence.status != AnswerStatus.answered:
        return
    p = _path(req)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = resp.model_copy(update={"cached": False})
    p.write_text(
        payload.model_dump_json(indent=2, exclude_none=True), encoding="utf-8"
    )
