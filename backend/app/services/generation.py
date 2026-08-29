"""Grounded generation over retrieved chunks (Gemini, forced JSON output).

Contract with the model:
    { "answer": str, "citations": [{"source": str, "section": str}],
      "self_confidence": "high" | "medium" | "low" }

If Gemini is unconfigured/unavailable or there are no retrieved chunks, we return
a deterministic "escalate" stub instead of inventing an answer — the escalate path
is a feature, not an error.
"""
from __future__ import annotations

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
    "the context. Respond as JSON: "
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
    return Generation(answer=answer, citations=citations, self_confidence=self_conf)


def _coerce_citations(
    raw: object, chunks: list[RetrievedChunk]
) -> list[Citation]:
    """Keep only citations that correspond to a passage we actually retrieved."""
    allowed = {
        (rc.chunk.source.lower(), rc.chunk.section.lower()): rc.chunk for rc in chunks
    }
    allowed_sources = {rc.chunk.source.lower() for rc in chunks}
    out: list[Citation] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source") or "").strip()
        section = str(item.get("section") or "").strip()
        if source.lower() not in allowed_sources:
            continue
        excerpt = None
        hit = allowed.get((source.lower(), section.lower()))
        if hit is not None:
            excerpt = hit.chunk_id
        out.append(Citation(source=source, section=section, excerpt_ref=excerpt))
    return out
