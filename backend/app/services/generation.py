"""Grounded generation over retrieved chunks (Gemini, forced JSON output).

Contract with the model:
    { "answer": str, "citations": [{"source": str, "section": str}],
      "self_confidence": "high" | "medium" | "low" }

If Gemini is unconfigured/unavailable or there are no retrieved chunks, we return
a deterministic "escalate" stub instead of inventing an answer — the escalate path
is a feature, not an error.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.llm.gemini_client import GeminiUnavailable, get_gemini_client
from app.retrieval import RetrievedChunk
from app.schemas import (
    Citation,
    Claim,
    Conflict,
    ConflictPosition,
    SelfConfidence,
)

logger = get_logger(__name__)

SYSTEM_INSTRUCTION = (
    "You are an Ayurveda intellectual-property and regulatory assistant for India. "
    "Answer ONLY from the numbered context passages provided. Every factual claim "
    "must trace to a passage. If the context is insufficient, say so plainly and "
    "set self_confidence to \"low\". Never cite a statute or section that is not in "
    "the context.\n"
    "CITATIONS ARE MANDATORY when you give a substantive answer: for every passage "
    "you relied on, add one entry to \"citations\" copying its source name and "
    "section EXACTLY as they appear in that passage's header line "
    "(\"[n] <source>, Section <section>\"). Use the header's section value, not a "
    "sub-clause you inferred. If you cannot ground the answer in any passage, return "
    "an empty citations list and self_confidence \"low\".\n"
    "INLINE MARKERS: in \"answer\", place a bracketed marker like [1] or [2][3] "
    "immediately after each sentence, naming the passage number(s) that support "
    "that specific sentence. The marker number is the passage's [n] from the "
    "context block. Every substantive sentence must carry at least one marker; "
    "purely transitional sentences may omit them.\n"
    "Set self_confidence \"high\" when at least one passage directly and "
    "unambiguously answers the question; \"medium\" when passages support a "
    "partial or qualified answer; \"low\" only when no passage is on point. Do "
    "not under-rate a clear, well-supported answer.\n"
    "CONFLICTS: if two or more passages from DIFFERENT instruments take divergent "
    "positions on the same point, add an entry to \"conflicts\": "
    '{"topic": short phrase, "positions": [{"summary": one sentence, '
    '"passages": [n, ...]}, ...]}. Each position\'s passages are the [n] numbers '
    "backing it. Only report a genuine divergence between instruments, not a "
    "mere difference in detail; omit \"conflicts\" or leave it empty otherwise.\n"
    "Respond as JSON: "
    '{"answer": string, "citations": [{"source": string, "section": string}], '
    '"conflicts": [{"topic": string, "positions": [{"summary": string, '
    '"passages": [int]}]}], '
    '"self_confidence": "high" | "medium" | "low"}.'
)

ESCALATE_ANSWER = (
    "I couldn't find a confident, citation-backed answer in the legal corpus for "
    "this question. Routing you to a human IP facilitator."
)


@dataclass
class Generation:
    answer: str
    citations: list[Citation]
    self_confidence: SelfConfidence
    claims: list[Claim] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)


def _context_block(chunks: list[RetrievedChunk]) -> str:
    lines = []
    for i, rc in enumerate(chunks, 1):
        c = rc.chunk
        header = f"[{i}] {c.source}"
        if c.section:
            header += f", Section {c.section}"
        lines.append(f"{header}\n{c.text}")
    return "\n\n".join(lines)


def _escalation() -> Generation:
    return Generation(ESCALATE_ANSWER, [], SelfConfidence.low)


def generate(
    query: str,
    chunks: list[RetrievedChunk],
    *,
    context: str | None = None,
) -> Generation:
    if not chunks:
        return _escalation()

    client = get_gemini_client()
    if not client.is_configured:
        logger.warning("Gemini not configured; returning escalation stub")
        return _escalation()

    background = ""
    if context:
        background = (
            "Background on the product this question is about (supplied by the "
            "user; NOT a source of law — the legal answer must still come only "
            f"from the numbered passages):\n{context}\n\n"
        )

    prompt = (
        f"{background}"
        f"Question:\n{query}\n\n"
        f"Context passages:\n{_context_block(chunks)}\n\n"
        "Answer the question using only these passages."
    )
    try:
        data = client.generate_json(
            prompt, system_instruction=SYSTEM_INSTRUCTION, temperature=0.2
        )
    except GeminiUnavailable as exc:
        logger.warning("generation failed, escalating: %s", exc)
        return _escalation()

    answer = str(data.get("answer") or "").strip() or ESCALATE_ANSWER
    citations = _coerce_citations(data.get("citations"), chunks)
    try:
        self_conf = SelfConfidence(str(data.get("self_confidence", "low")).lower())
    except ValueError:
        self_conf = SelfConfidence.low

    # Safety net: the model sometimes writes a well-grounded answer but leaves the
    # citations array empty. If it was confident, recover citations from the
    # retrieved passages it actually had in context (never invents a new source).
    if not citations and answer != ESCALATE_ANSWER and self_conf != SelfConfidence.low:
        citations = _recover_citations(answer, chunks)

    resolver = _PassageResolver(citations, chunks)
    answer, claims = _resolve_inline_claims(answer, resolver)
    conflicts = _parse_conflicts(data.get("conflicts"), resolver)

    return Generation(
        answer=answer,
        citations=citations,
        self_confidence=self_conf,
        claims=claims,
        conflicts=conflicts,
    )


_MARKER_RE = re.compile(r"\[\s*(\d+(?:\s*[,;]\s*\d+)*)\s*\]")


class _PassageResolver:
    """Maps a model context-passage number ([1] = first passage) to the 1-based
    position of that passage's Citation, appending a Citation for any relied-upon
    passage the model omitted (it was still retrieved, so it is citable)."""

    def __init__(self, citations: list[Citation], chunks: list[RetrievedChunk]):
        self.citations = citations
        self.chunks = chunks
        self._by_chunk: dict[str, int] = {}
        for i, c in enumerate(citations, 1):
            if c.excerpt_ref:
                self._by_chunk.setdefault(c.excerpt_ref, i)

    def resolve(self, passage_no: int) -> int | None:
        if not (1 <= passage_no <= len(self.chunks)):
            return None
        chunk = self.chunks[passage_no - 1].chunk
        hit = self._by_chunk.get(chunk.chunk_id)
        if hit is not None:
            return hit
        self.citations.append(Citation(
            source=chunk.source,
            section=chunk.section,
            excerpt_ref=chunk.chunk_id,
            source_url=chunk.metadata.get("source_url"),
        ))
        idx = len(self.citations)
        self._by_chunk[chunk.chunk_id] = idx
        return idx

    def source_of(self, final_index: int) -> str | None:
        if 1 <= final_index <= len(self.citations):
            return self.citations[final_index - 1].source
        return None


def _parse_conflicts(raw: object, resolver: _PassageResolver) -> list[Conflict]:
    """Keep only genuine cross-instrument divergences: >=2 positions, each with a
    resolvable citation, and the positions cite >=2 distinct sources overall."""
    if not isinstance(raw, list):
        return []
    out: list[Conflict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        topic = str(item.get("topic") or "").strip()
        raw_positions = item.get("positions")
        if not topic or not isinstance(raw_positions, list):
            continue
        positions: list[ConflictPosition] = []
        sources: set[str] = set()
        for pos in raw_positions:
            if not isinstance(pos, dict):
                continue
            summary = str(pos.get("summary") or "").strip()
            nums = pos.get("passages") or pos.get("citations") or []
            if not summary or not isinstance(nums, list):
                continue
            refs = sorted({
                r for n in nums
                if isinstance(n, int) and (r := resolver.resolve(n)) is not None
            })
            if not refs:
                continue
            positions.append(ConflictPosition(summary=summary, citations=refs))
            sources.update(s for r in refs if (s := resolver.source_of(r)))
        if len(positions) >= 2 and len(sources) >= 2:
            out.append(Conflict(topic=topic, positions=positions))
    return out


def _resolve_inline_claims(
    answer: str,
    resolver: _PassageResolver,
) -> tuple[str, list[Claim]]:
    """Rewrite the model's inline passage markers to citation numbers and split
    the answer into per-claim segments."""
    if not answer or ESCALATE_ANSWER in answer:
        return answer, []

    def _remap(match: re.Match) -> str:
        nums = [int(n) for n in re.split(r"[,;]", match.group(1))]
        resolved = sorted({fi for n in nums if (fi := resolver.resolve(n)) is not None})
        return "".join(f"[{i}]" for i in resolved)

    rewritten = _MARKER_RE.sub(_remap, answer).strip()

    claims: list[Claim] = []
    for sentence in _split_sentences(rewritten):
        refs = sorted({int(n) for m in _MARKER_RE.finditer(sentence)
                       for n in re.split(r"[,;]", m.group(1))})
        claims.append(Claim(text=sentence, citations=refs))
    # No inline markers at all -> not a per-claim answer; let the UI fall back.
    if not any(cl.citations for cl in claims):
        return rewritten, []
    return rewritten, claims


def _split_sentences(text: str) -> list[str]:
    parts: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for piece in re.split(r"(?<=[.!?\]])\s+(?=[A-Z0-9(])", line):
            piece = piece.strip()
            if piece:
                parts.append(piece)
    return parts


def _recover_citations(answer: str, chunks: list[RetrievedChunk]) -> list[Citation]:
    """Derive citations from retrieved chunks whose section is named in the answer;
    fall back to the single top-ranked passage so a confident answer is never
    returned citation-less."""
    lowered = answer.lower()
    out: list[Citation] = []
    seen: set[tuple[str, str]] = set()

    def _cite(chunk) -> Citation:
        return Citation(
            source=chunk.source,
            section=chunk.section,
            excerpt_ref=chunk.chunk_id,
            source_url=chunk.metadata.get("source_url"),
        )

    for rc in chunks:
        sec = rc.chunk.section
        if not sec:
            continue
        pat = re.compile(rf"\bsection\s+{re.escape(sec.lower())}\b")
        if pat.search(lowered) and (rc.chunk.source, sec) not in seen:
            out.append(_cite(rc.chunk))
            seen.add((rc.chunk.source, sec))
    if not out and chunks:
        out.append(_cite(chunks[0].chunk))
    return out


def _norm_section(section: str) -> str:
    """'Section 6(1)' / 'sec. 6' / 'Article 27.1' -> '6(1)' / '6' / '27.1'."""
    s = section.strip()
    s = re.sub(r"^(section|sec\.?|article|art\.?)\s*", "", s, flags=re.IGNORECASE)
    return s.strip()


def _coerce_citations(
    raw: object, chunks: list[RetrievedChunk]
) -> list[Citation]:
    """Keep only citations that correspond to a passage we actually retrieved.

    The model varies section formatting ('6' vs 'Section 6' vs '6(1)'); we
    normalise, match on the retrieved section prefix, and de-duplicate.
    """
    by_source: dict[str, list[RetrievedChunk]] = {}
    for rc in chunks:
        by_source.setdefault(rc.chunk.source.lower(), []).append(rc)

    out: list[Citation] = []
    seen: set[tuple[str, str]] = set()
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source") or "").strip()
        section = _norm_section(str(item.get("section") or ""))
        candidates = by_source.get(source.lower())
        if not candidates:
            continue
        # Prefer the retrieved chunk whose section the model's section starts with
        # (so 'Section 6(1)' resolves to retrieved section '6'); else use as-is.
        hit = next(
            (rc for rc in candidates
             if section == rc.chunk.section
             or section.startswith(rc.chunk.section + "(")
             or section.startswith(rc.chunk.section + ".")),
            None,
        )
        resolved_section = hit.chunk.section if hit is not None else section
        key = (source.lower(), resolved_section.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(Citation(
            source=source,
            section=resolved_section,
            excerpt_ref=hit.chunk.chunk_id if hit is not None else None,
            source_url=(hit.chunk.metadata.get("source_url") if hit is not None else None),
        ))
    return out
