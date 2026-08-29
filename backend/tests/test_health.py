def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "corpus_loaded" in body
    assert "gemini_configured" in body


def test_root_banner(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "IP-SAKTI Sahayak API"
