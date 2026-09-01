"""Matter documents as context (roadmap S20).

The user attaches their own documents (PDF / DOCX / TXT / MD) to a matter. They
are read to understand *what is being asked about* and injected into generation
as background — they are NEVER cited. `citations[]` stays corpus-only.

Pipeline:
  upload -> store original bytes -> (background) extract text -> chunk ->
  embed into a per-matter Chroma collection (matter_docs.doc_retriever) ->
  status flips processing -> ready | failed.

Retrieval lane: DocRetriever (embeddings) with a term-overlap fallback for when
Chroma / the embedder is unavailable.

Storage: data/matter_docs/<matter_id>/<doc_id>.json  (extracted text + chunks)
         data/matter_docs/<matter_id>/orig/<doc_id><ext>  (original upload)
Gitignored, never logged.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.core.logging import get_logger
from app.schemas import DocSnippet, MatterDocument, MatterDocumentDetail
from app.services import doc_extract, doc_retriever
from app.store.repos import get_matter_repo, new_id

logger = get_logger(__name__)

_CHUNK_TARGET = 900
_SNIPPET_MIN_OVERLAP = 2
_STOP = {
    "the", "a", "an", "is", "are", "do", "does", "to", "of", "in", "for", "on",
    "and", "or", "can", "my", "our", "this", "that", "what", "how", "be", "it",
    "as", "at", "by", "with", "if", "not", "i", "we", "have", "has",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _root(matter_id: str) -> Path:
    return Path(get_settings().data_dir) / "matter_docs" / matter_id


def _meta_path(matter_id: str, doc_id: str) -> Path:
    return _root(matter_id) / f"{doc_id}.json"


def _ext(filename: str) -> str:
    return ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""


def _tokens(text: str) -> set[str]:
    return {
        t for t in re.findall(r"[a-z0-9]+", text.lower())
        if len(t) > 2 and t not in _STOP
    }


def _chunk(text: str) -> list[str]:
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
    final: list[str] = []
    for c in out:
        if len(c) <= _CHUNK_TARGET * 1.5:
            final.append(c)
        else:
            for i in range(0, len(c), _CHUNK_TARGET):
                final.append(c[i:i + _CHUNK_TARGET])
    return final or ([text.strip()] if text.strip() else [])


# --------------------------------------------------------------------------- #
# Upload + async processing
# --------------------------------------------------------------------------- #
def register(matter_id: str, filename: str, data: bytes) -> tuple[MatterDocument, bool]:
    """Persist the original upload and return a `processing` record. The caller
    schedules `process()`. Returns (doc, should_process)."""
    doc_id = new_id("doc_")
    ext = _ext(filename)
    now = _now()
    doc = MatterDocument(
        id=doc_id, filename=filename, bytes=len(data), uploaded_at=now,
        status="processing",
    )
    if ext and ext not in doc_extract.ALLOWED_EXT:
        doc.status = "failed"
        doc.error = (
            f"Unsupported file type '{ext}'. Upload a PDF, Word (.docx), or "
            "plain-text (.txt / .md) file."
        )
        return doc, False

    orig_dir = _root(matter_id) / "orig"
    orig_dir.mkdir(parents=True, exist_ok=True)
    (orig_dir / f"{doc_id}{ext}").write_bytes(data)
    return doc, True


def process(matter_id: str, doc_id: str) -> None:
    """Extract -> chunk -> embed. Updates the document's status on the matter."""
    matter = get_matter_repo().get(matter_id)
    ref = next((d for d in matter.documents if d.id == doc_id), None) if matter else None
    display_name = ref.filename if ref else doc_id
    orig = next(
        (p for p in (_root(matter_id) / "orig").glob(f"{doc_id}.*")), None
    )
    status, error, chunks, page_count, media = "failed", None, [], None, "text/plain"
    if orig is None:
        error = "The uploaded file is missing."
    else:
        try:
            text, media, page_count = doc_extract.extract(
                display_name, orig.read_bytes()
            )
            chunks = _chunk(text)
            _meta_path(matter_id, doc_id).write_text(
                json.dumps({
                    "id": doc_id, "matter_id": matter_id, "filename": display_name,
                    "text": text, "chunks": chunks, "uploaded_at": _now(),
                }, ensure_ascii=False),
                encoding="utf-8",
            )
            doc_retriever.index_doc(matter_id, doc_id, display_name, chunks)
            status, error = "ready", None
        except doc_extract.ExtractionError as exc:
            error = str(exc)
        except Exception as exc:  # pragma: no cover
            logger.exception("matter doc processing failed")
            error = f"Processing failed: {exc}"

    try:
        with get_matter_repo().mutate(matter_id) as m:
            for d in m.documents:
                if d.id == doc_id:
                    d.status = status
                    d.error = error
                    d.chunk_count = len(chunks)
                    d.page_count = page_count
                    d.media_type = media
                    break
            m.updated_at = _now()
    except KeyError:  # matter deleted mid-processing
        pass
    logger.info("matter doc %s/%s -> %s", matter_id, doc_id, status)


def detail(matter_id: str, doc_id: str) -> MatterDocumentDetail | None:
    p = _meta_path(matter_id, doc_id)
    if not p.exists():
        return None
    raw = json.loads(p.read_text(encoding="utf-8"))
    return MatterDocumentDetail(
        document=MatterDocument(
            id=raw["id"], filename=raw["filename"], uploaded_at=raw["uploaded_at"],
            status="ready", chunk_count=len(raw.get("chunks", [])),
            bytes=len(raw["text"].encode("utf-8")),
        ),
        text=raw["text"],
        chunks=raw.get("chunks", []),
    )


def delete(matter_id: str, doc_id: str) -> None:
    _meta_path(matter_id, doc_id).unlink(missing_ok=True)
    for p in (_root(matter_id) / "orig").glob(f"{doc_id}.*"):
        p.unlink(missing_ok=True)
    doc_retriever.remove_doc(matter_id, doc_id)


def drop_matter(matter_id: str) -> None:
    doc_retriever.drop_matter(matter_id)


def _stored_chunks(matter_id: str) -> list[tuple[str, str, int, str]]:
    root = _root(matter_id)
    if not root.exists():
        return []
    out: list[tuple[str, str, int, str]] = []
    for p in root.glob("*.json"):
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for i, ch in enumerate(raw.get("chunks", [])):
            out.append((raw["id"], raw["filename"], i, ch))
    return out


def snippets(matter_id: str, query: str, k: int = 3) -> list[DocSnippet]:
    # Prefer the embeddings lane; fall back to term overlap.
    hits = doc_retriever.search(matter_id, query, k)
    if hits is not None:
        return hits

    qt = _tokens(query)
    if not qt:
        return []
    scored = []
    for doc_id, filename, ci, ch in _stored_chunks(matter_id):
        overlap = len(qt & _tokens(ch))
        if overlap >= _SNIPPET_MIN_OVERLAP:
            scored.append((overlap, doc_id, filename, ci, ch))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [
        DocSnippet(
            doc_id=doc_id, filename=filename,
            locator=f"{filename} — part {ci + 1}", text=ch.strip()[:700],
        )
        for _s, doc_id, filename, ci, ch in scored[:k]
    ]
