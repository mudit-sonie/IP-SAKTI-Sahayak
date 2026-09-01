"""/compare — one question, both jurisdictions (roadmap S10)."""


def test_compare_returns_both_jurisdictions(client):
    r = client.post(
        "/compare",
        json={"query": "Can a classical Ayurvedic formulation be patented?"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["query"]
    for side in ("india", "international"):
        assert set(body[side]) >= {"answer", "citations", "confidence"}
        assert body[side]["confidence"]["status"] in {"answered", "escalate"}

    health = client.get("/health").json()
    if health["corpus_loaded"]:
        assert body["india"]["retrieval"]["jurisdiction"] == "india"
        assert body["international"]["retrieval"]["jurisdiction"] == "international"


def test_compare_validates_jurisdiction_free_request(client):
    r = client.post("/compare", json={})
    assert r.status_code == 422
