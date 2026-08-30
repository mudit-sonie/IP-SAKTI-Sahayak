"""Contract-shape tests for /query and /abs-check.

/query must always return a well-formed response, never a 500. With no corpus and
no Gemini key (CI) that means status == "escalate" (the designed fallback); with
both wired it may legitimately be "answered", so we only assert the escalate
fallback when /health reports the backend is not fully wired.
"""


def test_query_returns_contract_shape(client):
    health = client.get("/health").json()
    fully_wired = health["corpus_loaded"] and health["gemini_configured"]

    r = client.post(
        "/query",
        json={"query": "Can a classical Ayurvedic formulation be patented?", "jurisdiction": "india"},
    )
    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {"answer", "citations", "confidence", "abs_flag", "abs_note"}
    assert body["confidence"]["status"] in {"answered", "escalate"}
    assert isinstance(body["citations"], list)
    if not fully_wired:
        assert body["confidence"]["status"] == "escalate"


def test_abs_check_triggers_on_keyword(client):
    r = client.post(
        "/abs-check",
        json={"query": "Do I need NBA approval for using a medicinal plant biological resource?"},
    )
    assert r.status_code == 200
    assert r.json()["triggered"] is True


def test_abs_check_not_triggered_on_unrelated_query(client):
    r = client.post(
        "/abs-check",
        json={"query": "How do I register a trade mark for my clinic's logo?", "formulation_category": "cosmetic"},
    )
    assert r.status_code == 200
    assert r.json()["triggered"] is False


def test_query_jurisdiction_validation(client):
    r = client.post("/query", json={"query": "x", "jurisdiction": "mars"})
    assert r.status_code == 422
