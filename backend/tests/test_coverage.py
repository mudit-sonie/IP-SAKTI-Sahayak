"""Contract tests for /corpus (roadmap S4)."""


def test_corpus_coverage_shape(client):
    r = client.get("/corpus")
    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {
        "generated_at", "corpus_loaded", "chunk_count", "source_count",
        "jurisdictions", "sources", "known_gaps",
    }
    assert isinstance(body["sources"], list)
    assert body["known_gaps"], "known gaps must be surfaced honestly"

    if body["corpus_loaded"]:
        assert body["source_count"] == len(body["sources"])
        assert body["chunk_count"] == sum(s["chunk_count"] for s in body["sources"])
        # sorted by descending chunk count
        counts = [s["chunk_count"] for s in body["sources"]]
        assert counts == sorted(counts, reverse=True)
        for s in body["sources"]:
            assert s["section_count"] == len(s["sections"])
            assert s["thin"] == (s["chunk_count"] < 5)
