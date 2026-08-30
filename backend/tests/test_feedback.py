"""POST /feedback -> append-only jsonl."""
import json

import app.services.feedback as fb


def test_feedback_appends(client, tmp_path, monkeypatch):
    log = tmp_path / "feedback.jsonl"
    monkeypatch.setattr(fb, "LOG_PATH", log)

    r = client.post(
        "/feedback",
        json={
            "query": "term of a patent?",
            "rating": "up",
            "jurisdiction": "india",
            "cited_sections": ["53"],
        },
    )
    assert r.status_code == 200 and r.json()["ok"] is True

    r2 = client.post(
        "/feedback",
        json={"query": "x", "rating": "down", "note": "wrong section"},
    )
    assert r2.status_code == 200

    lines = log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["rating"] == "up" and first["cited_sections"] == ["53"]


def test_feedback_rejects_bad_rating(client):
    r = client.post("/feedback", json={"query": "x", "rating": "meh"})
    assert r.status_code == 422
