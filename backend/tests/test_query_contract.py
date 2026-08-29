"""Contract-shape tests for /query and /abs-check.

No corpus and no Gemini key in CI, so /query must still return a well-formed
response with status == "escalate" (the designed fallback), never a 500.
"""


def test_query_returns_contract_shape_and_escalates(client):
    r = client.post(
        "/query",
        json={"query": "Can a classical Ayurvedic formulation be patented?", "jurisdiction": "india"},
    )
    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {"answer", "citations", "confidence", "abs_flag", "abs_note"}
    assert body["confidence"]["status"] == "escalate"
    assert isinstance(body["citations"], list)


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
