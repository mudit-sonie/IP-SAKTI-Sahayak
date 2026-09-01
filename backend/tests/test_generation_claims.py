"""Unit tests for per-claim citation resolution (S2) and conflict surfacing (S3)."""
from app.retrieval.corpus import Chunk
from app.retrieval.hybrid import RetrievedChunk
from app.services.generation import (
    ESCALATE_ANSWER,
    _PassageResolver,
    _parse_conflicts,
    _resolve_inline_claims,
)
from app.schemas import Citation


def _rc(chunk_id, source, section):
    return RetrievedChunk(
        chunk=Chunk(
            chunk_id=chunk_id,
            text=f"text of {chunk_id}",
            metadata={"source": source, "section": section, "source_url": "http://x"},
        ),
        score=1.0,
    )


CHUNKS = [
    _rc("c_a", "The Patents Act, 1970", "3(p)"),
    _rc("c_b", "The Patents Act, 1970", "53"),
    _rc("c_c", "Biological Diversity Act, 2002", "6"),
]


def test_markers_remapped_to_citation_positions():
    citations = [Citation(source="The Patents Act, 1970", section="53", excerpt_ref="c_b")]
    resolver = _PassageResolver(citations, CHUNKS)
    answer = "A classical formulation is not patentable. [1] The term is 20 years. [2]"
    text, claims = _resolve_inline_claims(answer, resolver)

    # passage 2 (c_b) was already citation #1; passage 1 (c_a) gets appended as #2
    assert [c.excerpt_ref for c in citations] == ["c_b", "c_a"]
    assert claims[0].text.endswith("[2]")
    assert claims[0].citations == [2]
    assert claims[1].citations == [1]
    assert "[2]" in text and "[1]" in text


def test_no_markers_falls_back_to_plain_answer():
    text, claims = _resolve_inline_claims(
        "Just prose, no markers.", _PassageResolver([], CHUNKS)
    )
    assert claims == []
    assert text == "Just prose, no markers."


def test_escalate_answer_produces_no_claims():
    _, claims = _resolve_inline_claims(ESCALATE_ANSWER, _PassageResolver([], CHUNKS))
    assert claims == []


def test_out_of_range_marker_dropped():
    citations = [Citation(source="The Patents Act, 1970", section="3(p)", excerpt_ref="c_a")]
    resolver = _PassageResolver(citations, CHUNKS)
    text, claims = _resolve_inline_claims(
        "Classical items are barred. [1] Extra note. [9]", resolver
    )
    assert "[9]" not in text
    assert claims[0].citations == [1]
    assert claims[1].citations == []


def test_conflict_kept_when_cross_instrument():
    resolver = _PassageResolver([], CHUNKS)
    raw = [{
        "topic": "NBA approval before filing",
        "positions": [
            {"summary": "Patents Act allows deferred disclosure.", "passages": [2]},
            {"summary": "Biodiversity Act requires prior approval.", "passages": [3]},
        ],
    }]
    conflicts = _parse_conflicts(raw, resolver)
    assert len(conflicts) == 1
    assert conflicts[0].topic == "NBA approval before filing"
    assert [p.citations for p in conflicts[0].positions] == [[1], [2]]


def test_conflict_dropped_when_same_instrument():
    resolver = _PassageResolver([], CHUNKS)
    raw = [{
        "topic": "same act",
        "positions": [
            {"summary": "one", "passages": [1]},
            {"summary": "two", "passages": [2]},
        ],
    }]
    assert _parse_conflicts(raw, resolver) == []


def test_conflict_dropped_when_single_position():
    resolver = _PassageResolver([], CHUNKS)
    raw = [{"topic": "x", "positions": [{"summary": "only one", "passages": [1]}]}]
    assert _parse_conflicts(raw, resolver) == []
