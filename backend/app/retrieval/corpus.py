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


def _coerce(raw: dict[str, Any]) -> Chunk | None:
    text = (raw.get("text") or "").strip()
    chunk_id = raw.get("chunk_id") or raw.get("id")
    if not text or not chunk_id:
        return None
    meta = raw.get("metadata") or {}
    return Chunk(chunk_id=str(chunk_id), text=text, metadata=dict(meta))


def load_chunks(path: str | Path | None = None) -> list[Chunk]:
    settings = get_settings()
    p = Path(path or settings.corpus_chunks_path)
    if not p.exists():
        logger.warning("corpus file %s not found; retrieval will return no hits", p)
        return []

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
