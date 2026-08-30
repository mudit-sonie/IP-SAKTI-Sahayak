"""On-disk /query cache."""
import app.config as config_mod
from app.schemas import (
    AnswerStatus,
    Confidence,
    Jurisdiction,
    QueryRequest,
    QueryResponse,
    SelfConfidence,
)
from app.services import query_cache


def _fresh_settings(tmp_path):
    config_mod.get_settings.cache_clear()
    import os

    os.environ["QUERY_CACHE_DIR"] = str(tmp_path / "qc")
    os.environ["QUERY_CACHE_ENABLED"] = "true"
    return config_mod.get_settings()


def test_roundtrip_answered(tmp_path):
    _fresh_settings(tmp_path)
    req = QueryRequest(query="What is the term of a patent?", jurisdiction=Jurisdiction.india)
    resp = QueryResponse(
        answer="Twenty years.",
        confidence=Confidence(
            retrieval_score=0.9,
            self_confidence=SelfConfidence.high,
            status=AnswerStatus.answered,
        ),
    )
    assert query_cache.get(req) is None
    query_cache.put(req, resp)
    hit = query_cache.get(req)
    assert hit is not None
    assert hit.answer == "Twenty years."
    assert hit.cached is True

    config_mod.get_settings.cache_clear()


def test_escalate_not_cached(tmp_path):
    _fresh_settings(tmp_path)
    req = QueryRequest(query="unanswerable", jurisdiction=Jurisdiction.india)
    resp = QueryResponse(
        answer="escalating",
        confidence=Confidence(status=AnswerStatus.escalate),
    )
    query_cache.put(req, resp)
    assert query_cache.get(req) is None

    config_mod.get_settings.cache_clear()
