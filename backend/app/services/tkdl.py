"""TKDL / prior-art cross-check (roadmap S12).

The Traditional Knowledge Digital Library is access-controlled — it is shared
with patent offices under non-disclosure agreements, and there is no public API.
This module is the scaffold and the clearly-marked data hook: it assembles the
search terms a formal TKDL search would use and reports, honestly, that no
connector is wired. It never fabricates prior art.

To connect a real source later: implement the branch guarded by
`settings.tkdl_enabled and settings.tkdl_api_url`.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.config import get_settings
from app.core.logging import get_logger
from app.schemas import Matter, TkdlResult

logger = get_logger(__name__)

_NOT_CONNECTED_NOTE = (
    "No TKDL connector is wired to this deployment. The TKDL is access-controlled "
    "and available to patent examiners under NDA, not via a public API. A formal "
    "prior-art search on the terms above should be run by someone with TKDL "
    "access (or a registered patent agent). Nothing here is a clearance."
)

_CONFIGURED_NOTE = (
    "A TKDL endpoint is configured but the connector is not implemented in this "
    "build. Treat as not checked."
)


def search_terms(matter: Matter) -> list[str]:
    terms: list[str] = []
    terms.extend(matter.profile.key_ingredients)
    if matter.formulation_label:
        terms.append(matter.formulation_label)
    if matter.profile.intended_use:
        terms.append(matter.profile.intended_use)
    # de-dupe, keep order, drop blanks
    seen: set[str] = set()
    out: list[str] = []
    for t in (s.strip() for s in terms):
        key = t.lower()
        if t and key not in seen:
            seen.add(key)
            out.append(t)
    return out


def check(matter: Matter) -> TkdlResult:
    settings = get_settings()
    terms = search_terms(matter)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    configured = bool(settings.tkdl_enabled and settings.tkdl_api_url)
    logger.info(
        "tkdl check for matter %s (%d terms, connector=%s)",
        matter.id, len(terms), "configured" if configured else "absent",
    )
    return TkdlResult(
        status="not_connected",
        checked_at=now,
        search_terms=terms,
        note=_CONFIGURED_NOTE if configured else _NOT_CONNECTED_NOTE,
    )
