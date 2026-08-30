"""GET /chunk/{id} — the statute passage behind a citation."""


def test_unknown_chunk_returns_404(client):
    r = client.get("/chunk/does_not_exist_123")
    assert r.status_code == 404


def test_known_chunk_returns_passage(client):
    health = client.get("/health").json()
    if not health["corpus_loaded"]:
        return  # CI has no corpus; nothing to fetch

    # pull a real chunk id via a query, then fetch it back
    q = client.post(
        "/query", json={"query": "term of a patent in India", "jurisdiction": "india"}
    ).json()
    refs = [c["excerpt_ref"] for c in q["citations"] if c.get("excerpt_ref")]
    if not refs:
        return

    r = client.get(f"/chunk/{refs[0]}")
    assert r.status_code == 200
    body = r.json()
    assert body["chunk_id"] == refs[0]
    assert body["text"].strip()
    assert body["source"]
