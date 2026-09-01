"""Facilitator queue + reviewed FAQ (roadmap S5)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def _tmp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("QUERY_CACHE_ENABLED", "false")
    monkeypatch.setenv("GEMINI_API_KEYS", "")  # force the escalate path
    get_settings.cache_clear()
    import app.store.repos as repos

    monkeypatch.setattr(repos, "_matter_repo", None)
    monkeypatch.setattr(repos, "_escalation_repo", None)
    monkeypatch.setattr(repos, "_faq_repo", None)
    yield
    get_settings.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


Q = "What is the correct HSN classification for a triphala tablet exported to Nepal?"


def test_escalation_queued_then_answered_and_served_from_faq(client):
    r = client.post("/query", json={"query": Q, "jurisdiction": "india"})
    assert r.json()["confidence"]["status"] == "escalate"

    queue = client.get("/escalations", params={"status": "open"}).json()
    assert len(queue) == 1
    esc = queue[0]
    assert esc["query"] == Q
    assert esc["reason"] in {"low_retrieval", "no_gemini", "high_stakes"}

    ans = client.post(
        f"/escalations/{esc['id']}/answer",
        json={
            "answer": "A reviewed facilitator answer with the classification.",
            "citations": [],
            "publish_faq": True,
        },
    ).json()
    assert ans["status"] == "answered"
    assert ans["faq_id"]

    faq = client.get("/faq").json()
    assert len(faq) == 1

    again = client.post("/query", json={"query": Q, "jurisdiction": "india"}).json()
    assert again["from_faq"] is True
    assert again["confidence"]["status"] == "answered"
    assert "reviewed facilitator answer" in again["answer"]


def test_open_escalation_deduplicated(client):
    client.post("/query", json={"query": Q, "jurisdiction": "india"})
    client.post("/query", json={"query": Q.upper(), "jurisdiction": "india"})
    assert len(client.get("/escalations").json()) == 1


def test_faq_match_is_jurisdiction_scoped(client):
    client.post("/query", json={"query": Q, "jurisdiction": "india"})
    esc = client.get("/escalations").json()[0]
    client.post(
        f"/escalations/{esc['id']}/answer",
        json={"answer": "reviewed", "publish_faq": True},
    )
    # same question, other jurisdiction -> FAQ must not short-circuit
    other = client.post(
        "/query", json={"query": Q, "jurisdiction": "international"}
    ).json()
    assert other.get("from_faq") is False


def test_dismiss_removes_from_open_queue(client):
    client.post("/query", json={"query": Q, "jurisdiction": "india"})
    esc = client.get("/escalations").json()[0]
    client.post(f"/escalations/{esc['id']}/dismiss")
    assert client.get("/escalations", params={"status": "open"}).json() == []


def test_manual_faq_create_and_delete(client):
    e = client.post(
        "/faq",
        json={
            "question": "Do I need a licence to manufacture an Ayurvedic drug?",
            "answer": "Yes — from the State Licensing Authority.",
            "jurisdiction": "india",
        },
    ).json()
    assert e["keywords"]
    assert client.delete(f"/faq/{e['id']}").status_code == 204
    assert client.get("/faq").json() == []
