"""Rule-based retrieval query expansion."""
from app.retrieval.expansion import expand_query


def test_ayurveda_patent_question_gets_tk_bridge_terms():
    q = "Can a classical Ayurvedic formulation be patented in India?"
    out = expand_query(q)
    assert out.startswith(q)
    assert "traditional knowledge" in out.lower()


def test_single_trigger_does_not_fire():
    # "patent" alone, no Ayurveda/traditional context -> untouched
    assert expand_query("What is the term of a patent in India?") == (
        "What is the term of a patent in India?"
    )


def test_unrelated_query_untouched():
    q = "How do I register a trade mark for my clinic logo?"
    assert expand_query(q) == q
