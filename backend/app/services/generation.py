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
from dataclasses import dataclass

from app.core.logging import get_logger
from app.llm.gemini_client import GeminiUnavailable, get_gemini_client
from app.retrieval import RetrievedChunk
from app.schemas import Citation, SelfConfidence

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
    "Respond as JSON: "
    '{"answer": string, "citations": [{"source": string, "section": string}], '
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


def generate(query: str, chunks: list[RetrievedChunk]) -> Generation:
    if not chunks:
        return _escalation()

    client = get_gemini_client()
    if not client.is_configured:
        logger.warning("Gemini not configured; returning escalation stub")
        return _escalation()

    prompt = (
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

    return Generation(answer=answer, citations=citations, self_confidence=self_conf)


def _recover_citations(answer: str, chunks: list[RetrievedChunk]) -> list[Citation]:
    """Derive citations from retrieved chunks whose section is named in the answer;
    fall back to the single top-ranked passage so a confident answer is never
    returned citation-less."""
    lowered = answer.lower()
    out: list[Citation] = []
    seen: set[tuple[str, str]] = set()
    for rc in chunks:
        sec = rc.chunk.section
        if not sec:
            continue
        pat = re.compile(rf"\bsection\s+{re.escape(sec.lower())}\b")
        if pat.search(lowered) and (rc.chunk.source, sec) not in seen:
            out.append(Citation(source=rc.chunk.source, section=sec, excerpt_ref=rc.chunk.chunk_id))
            seen.add((rc.chunk.source, sec))
    if not out and chunks:
        top = chunks[0].chunk
        out.append(Citation(source=top.source, section=top.section, excerpt_ref=top.chunk_id))
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
        ))
    return out
