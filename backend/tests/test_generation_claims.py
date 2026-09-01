"""Unit tests for per-claim citation resolution (roadmap S2)."""
from app.retrieval.corpus import Chunk
from app.retrieval.hybrid import RetrievedChunk
from app.services.generation import _resolve_inline_claims
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
    answer = "A classical formulation is not patentable. [1] The term is 20 years. [2]"
    text, claims = _resolve_inline_claims(answer, citations, CHUNKS)

    # passage 2 (c_b) was already citation #1; passage 1 (c_a) gets appended as #2
    assert [c.excerpt_ref for c in citations] == ["c_b", "c_a"]
    assert claims[0].text.endswith("[2]")
    assert claims[0].citations == [2]
    assert claims[1].citations == [1]
    assert "[2]" in text and "[1]" in text


def test_no_markers_falls_back_to_plain_answer():
    text, claims = _resolve_inline_claims("Just prose, no markers.", [], CHUNKS)
    assert claims == []
    assert text == "Just prose, no markers."


def test_escalate_answer_produces_no_claims():
    from app.services.generation import ESCALATE_ANSWER

    text, claims = _resolve_inline_claims(ESCALATE_ANSWER, [], CHUNKS)
    assert claims == []


def test_out_of_range_marker_dropped():
    citations = [Citation(source="The Patents Act, 1970", section="3(p)", excerpt_ref="c_a")]
    text, claims = _resolve_inline_claims(
        "Classical items are barred. [1] Extra note. [9]", citations, CHUNKS
    )
    assert "[9]" not in text
    assert claims[0].citations == [1]
    assert claims[1].citations == []
