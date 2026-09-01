"""Corpus coverage map (roadmap S4).

Introspects the loaded chunks so the UI can show exactly which instruments,
and which sections of them, the assistant can answer from — and be honest
about the known gaps it cannot.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.config import get_settings
from app.retrieval import get_retriever
from app.retrieval.corpus import Chunk
from app.schemas import CorpusCoverage, CorpusSource


def _section_sort_key(sec: str) -> tuple:
    """Order '3', '3(p)', '10', '10A' the way a lawyer reads them."""
    num, rest = "", ""
    for ch in sec:
        if ch.isdigit() and not rest:
            num += ch
        else:
            rest += ch
    return (int(num) if num else 1_000_000, rest)


def _build_source(name: str, chunks: list[Chunk], thin_threshold: int) -> CorpusSource:
    first = chunks[0].metadata
    sections = sorted(
        {c.section for c in chunks if c.section}, key=_section_sort_key
    )
    year = first.get("year")
    try:
        year = int(year) if year is not None else None
    except (TypeError, ValueError):
        year = None
    return CorpusSource(
        source=name,
        source_id=first.get("source_id"),
        jurisdiction=first.get("jurisdiction"),
        document_type=first.get("document_type"),
        organization=first.get("source_organization"),
        source_url=first.get("source_url"),
        year=year,
        chunk_count=len(chunks),
        section_count=len(sections),
        sections=sections,
        thin=len(chunks) < thin_threshold,
    )


def build_coverage() -> CorpusCoverage:
    settings = get_settings()
    retriever = get_retriever()
    chunks = retriever.all_chunks
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    by_source: dict[str, list[Chunk]] = {}
    jurisdictions: dict[str, int] = {}
    for c in chunks:
        by_source.setdefault(c.source, []).append(c)
        j = (c.metadata.get("jurisdiction") or "untagged").lower()
        jurisdictions[j] = jurisdictions.get(j, 0) + 1

    sources = [
        _build_source(name, group, settings.corpus_thin_source_threshold)
        for name, group in by_source.items()
    ]
    sources.sort(key=lambda s: (-s.chunk_count, s.source))

    gaps = list(settings.corpus_known_gaps_list)
    thin = [s.source for s in sources if s.thin]
    if thin:
        gaps.append(
            "Thin coverage (few sections ingested): " + "; ".join(thin)
        )

    return CorpusCoverage(
        generated_at=now,
        corpus_loaded=retriever.has_corpus,
        chunk_count=len(chunks),
        source_count=len(by_source),
        jurisdictions=jurisdictions,
        sources=sources,
        known_gaps=gaps,
    )
