"""Matter documents as context (roadmap S20).

The user attaches their own text documents to a matter. They are read to
understand *what is being asked about* and injected into generation as
background — they are NEVER cited. `citations[]` stays corpus-only.

Scope of this slice: plain-text uploads (.txt / .md). Binary extraction
(PDF/DOCX) and a per-matter Chroma namespace are follow-ups; the retrieval lane
here is an in-process BM25 over the document chunks, which is enough for the
handful of files a matter carries.

Storage: one JSON per document at data/matter_docs/<matter_id>__<doc_id>.json
holding the original text + chunks. Gitignored, never logged.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from app.config import get_settings
from app.core.logging import get_logger
from app.schemas import DocSnippet, MatterDocument, MatterDocumentDetail
from app.store.json_store import JsonStore
from app.store.repos import new_id

logger = get_logger(__name__)

_ALLOWED_EXT = {".txt", ".md", ".markdown", ".text"}
_CHUNK_TARGET = 900
_SNIPPET_MIN_OVERLAP = 2  # distinct query terms a chunk must share to surface
_STOP = {
    "the", "a", "an", "is", "are", "do", "does", "to", "of", "in", "for", "on",
    "and", "or", "can", "my", "our", "this", "that", "what", "how", "be", "it",
    "as", "at", "by", "with", "if", "not", "i", "we", "have", "has",
}
_store = JsonStore("matter_docs")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _key(matter_id: str, doc_id: str) -> str:
    return f"{matter_id}__{doc_id}"


def _tokens(text: str) -> set[str]:
    return {
        t for t in re.findall(r"[a-z0-9]+", text.lower())
        if len(t) > 2 and t not in _STOP
    }


def _chunk(text: str) -> list[str]:
    """Loose paragraph packing — these are not legal instruments."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out: list[str] = []
    buf = ""
    for p in paras:
        if buf and len(buf) + len(p) + 1 > _CHUNK_TARGET:
            out.append(buf)
            buf = p
        else:
            buf = f"{buf}\n{p}".strip()
    if buf:
        out.append(buf)
    # a single giant paragraph -> hard wrap
    final: list[str] = []
    for c in out:
        if len(c) <= _CHUNK_TARGET * 1.5:
            final.append(c)
            continue
        for i in range(0, len(c), _CHUNK_TARGET):
            final.append(c[i:i + _CHUNK_TARGET])
    return final or ([text.strip()] if text.strip() else [])


# --------------------------------------------------------------------------- #
# CRUD
# --------------------------------------------------------------------------- #
def create(matter_id: str, filename: str, text: str) -> MatterDocument:
    settings = get_settings()
    doc_id = new_id("doc_")
    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    raw_bytes = len(text.encode("utf-8"))
    now = _now()

    doc = MatterDocument(
        id=doc_id, filename=filename, media_type="text/markdown"
        if ext in {".md", ".markdown"} else "text/plain",
        bytes=raw_bytes, uploaded_at=now, status="processing",
    )

    if ext and ext not in _ALLOWED_EXT:
        doc.status = "failed"
        doc.error = (
            "Only plain-text files (.txt, .md) are supported in this build. "
            "For a PDF or Word file, paste the text into a .txt file first."
        )
    elif raw_bytes > settings.matter_docs_max_kb * 1024:
        doc.status = "failed"
        doc.error = f"File exceeds the {settings.matter_docs_max_kb} KB limit."
    elif not text.strip():
        doc.status = "failed"
        doc.error = "The file is empty."
    else:
        chunks = _chunk(text)
        doc.chunk_count = len(chunks)
        doc.status = "ready"
        _store.put(_key(matter_id, doc_id), {
            "id": doc_id, "matter_id": matter_id, "filename": filename,
            "text": text, "chunks": chunks, "uploaded_at": now,
        })
        logger.info("matter doc stored: %s/%s (%d chunks)", matter_id, doc_id, len(chunks))
    return doc


def detail(matter_id: str, doc_id: str) -> MatterDocumentDetail | None:
    raw = _store.get(_key(matter_id, doc_id))
    if raw is None:
        return None
    return MatterDocumentDetail(
        document=MatterDocument(
            id=raw["id"], filename=raw["filename"], uploaded_at=raw["uploaded_at"],
            status="ready", chunk_count=len(raw.get("chunks", [])),
            bytes=len(raw["text"].encode("utf-8")),
        ),
        text=raw["text"],
        chunks=raw.get("chunks", []),
    )


def delete(matter_id: str, doc_id: str) -> bool:
    return _store.delete(_key(matter_id, doc_id))


# --------------------------------------------------------------------------- #
# Retrieval lane (S20) — term-overlap over the matter's own document chunks.
# A tiny per-matter corpus makes BM25 idf degenerate, so a stop-word-filtered
# overlap count is both simpler and more stable here.
# --------------------------------------------------------------------------- #
def snippets(matter_id: str, query: str, k: int = 3) -> list[DocSnippet]:
    docs = [
        r for r in _store.list()
        if str(r.get("matter_id")) == matter_id and r.get("chunks")
    ]
    if not docs:
        return []
    qt = _tokens(query)
    if not qt:
        return []
    scored: list[tuple[int, str, str, int, str]] = []
    for d in docs:
        for i, ch in enumerate(d["chunks"]):
            overlap = len(qt & _tokens(ch))
            if overlap >= _SNIPPET_MIN_OVERLAP:
                scored.append((overlap, d["id"], d["filename"], i, ch))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [
        DocSnippet(
            doc_id=doc_id,
            filename=filename,
            locator=f"{filename} — part {ci + 1}",
            text=ch.strip()[:700],
        )
        for _score, doc_id, filename, ci, ch in scored[:k]
    ]
