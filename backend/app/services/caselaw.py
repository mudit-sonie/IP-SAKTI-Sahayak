"""Case-law layer (roadmap S14, scaffold).

Judicial decisions ingested with ``document_type: "case"`` are retrieved
alongside the statute text but shown separately under "How courts have applied
this" — a court applies the law, it is not the law's text, so a case is never a
primary citation.

No case law is in the corpus yet, so `case_notes` returns [] today. Ingest cases
with metadata like:
    {"document_type": "case", "source": "Novartis AG v. Union of India",
     "citation": "(2013) 6 SCC 1", "court": "Supreme Court of India",
     "year": 2013, "section": "3(d)", "source_url": "..."}
"""
from __future__ import annotations

from app.retrieval import RetrievedChunk
from app.schemas import CaseNote

_MAX_NOTES = 4
_EXCERPT_CHARS = 480


def case_notes(chunks: list[RetrievedChunk]) -> list[CaseNote]:
    out: list[CaseNote] = []
    seen: set[str] = set()
    for rc in chunks:
        c = rc.chunk
        if not c.is_case:
            continue
        name = c.source
        if name in seen:
            continue
        seen.add(name)
        meta = c.metadata
        text = c.text.strip()
        if len(text) > _EXCERPT_CHARS:
            text = text[:_EXCERPT_CHARS].rsplit(" ", 1)[0] + "…"
        year = meta.get("year")
        try:
            year = int(year) if year is not None else None
        except (TypeError, ValueError):
            year = None
        out.append(CaseNote(
            case_name=name,
            citation=meta.get("citation"),
            court=meta.get("court") or meta.get("source_organization"),
            year=year,
            excerpt=text,
            chunk_id=c.chunk_id,
            source_url=meta.get("source_url"),
        ))
        if len(out) >= _MAX_NOTES:
            break
    return out
