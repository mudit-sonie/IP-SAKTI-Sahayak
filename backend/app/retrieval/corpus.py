"""Load the processed legal corpus (chunks.jsonl) into memory.

Expected line schema (produced by the legal-corpus-ingestion pipeline):

    {
      "chunk_id": "patents_act_1970_sec_3_p",
      "text": "...",
      "metadata": {
        "source": "The Patents Act, 1970",
        "section": "3(p)",
        "jurisdiction": "India",
        "page_start": 12,
        "page_end": 12
      }
    }

Until the ingestion team ships chunks.jsonl, this loads nothing and the retriever
degrades to "no hits" -> every /query escalates. That is the intended Day 1 state.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def source(self) -> str:
        return str(self.metadata.get("source", "Unknown source"))

    @property
    def section(self) -> str:
        return str(self.metadata.get("section", ""))

    @property
    def jurisdiction(self) -> str:
        return str(self.metadata.get("jurisdiction", "")).lower()

    # --- amendment awareness (S6) — populated from the amendment overlay, if any ---
    @property
    def as_of(self) -> str | None:
        """ISO date the source text is current as of, when known."""
        return self.metadata.get("as_of") or None

    @property
    def amended_by(self) -> str | None:
        """Citation of an amending instrument known to affect this provision."""
        return self.metadata.get("amended_by") or None

    @property
    def in_force(self) -> bool | None:
        v = self.metadata.get("in_force")
        return v if isinstance(v, bool) else None

    @property
    def is_stale(self) -> bool:
        return bool(self.amended_by) or self.in_force is False


def _coerce(raw: dict[str, Any]) -> Chunk | None:
    text = (raw.get("text") or "").strip()
    chunk_id = raw.get("chunk_id") or raw.get("id")
    if not text or not chunk_id:
        return None
    meta = raw.get("metadata") or {}
    return Chunk(chunk_id=str(chunk_id), text=text, metadata=dict(meta))


def _load_amendment_overlay(path: str | Path | None) -> dict[str, dict]:
    """Optional currency / amendment metadata, keyed by source_id.

    Schema (all fields optional):
        { "<source_id>": {
            "as_of": "YYYY-MM-DD",
            "provisions": { "<section>": {
                "amended_by": "The Patents (Amendment) Act, 2005",
                "in_force": true } } } }

    The file is the deliberate ingestion hook for S6: amendment history is not in
    today's corpus, so this stays absent until someone curates it. When present,
    its values are merged onto chunk metadata at load time.
    """
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("amendment overlay %s could not be read (%s); ignoring", p, exc)
        return {}
    if not isinstance(data, dict):
        logger.error("amendment overlay %s is not an object; ignoring", p)
        return {}
    logger.info("loaded amendment overlay for %d source(s) from %s", len(data), p)
    return data


def _apply_overlay(chunk: Chunk, overlay: dict[str, dict]) -> None:
    entry = overlay.get(chunk.metadata.get("source_id", ""))
    if not isinstance(entry, dict):
        return
    if entry.get("as_of") and not chunk.metadata.get("as_of"):
        chunk.metadata["as_of"] = entry["as_of"]
    provisions = entry.get("provisions") or {}
    sec = chunk.section
    # exact section, or a sub-clause of an amended section ('6' covers '6(1)')
    prov = provisions.get(sec) or next(
        (v for k, v in provisions.items()
         if sec == k or sec.startswith(k + "(") or sec.startswith(k + ".")),
        None,
    )
    if isinstance(prov, dict):
        if prov.get("amended_by"):
            chunk.metadata["amended_by"] = prov["amended_by"]
        if isinstance(prov.get("in_force"), bool):
            chunk.metadata["in_force"] = prov["in_force"]
        if prov.get("as_of"):
            chunk.metadata["as_of"] = prov["as_of"]


def load_chunks(path: str | Path | None = None) -> list[Chunk]:
    settings = get_settings()
    p = Path(path or settings.corpus_chunks_path)
    if not p.exists():
        logger.warning("corpus file %s not found; retrieval will return no hits", p)
        return []

    overlay = _load_amendment_overlay(getattr(settings, "amendment_overlay_path", None))

    chunks: list[Chunk] = []
    with p.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                logger.error("corpus %s line %d: bad JSON, skipped", p, lineno)
                continue
            chunk = _coerce(obj)
            if chunk is not None:
                if overlay:
                    _apply_overlay(chunk, overlay)
                chunks.append(chunk)
    logger.info("loaded %d corpus chunks from %s", len(chunks), p)
    return chunks


def filter_by_jurisdiction(chunks: Iterable[Chunk], jurisdiction: str) -> list[Chunk]:
    """India query -> India corpus; International -> TRIPS + CBD/Nagoya only.

    Chunks with no jurisdiction tag are kept for both, so a partially tagged
    corpus still returns something.
    """
    j = jurisdiction.lower()
    out = []
    for c in chunks:
        cj = c.jurisdiction
        if not cj or cj == j or (j == "international" and cj in {"international", "treaty"}):
            out.append(c)
    return out
