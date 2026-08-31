"""Matter workspace API — CRUD + recording a grounded question.

The grounded pipeline is stubbed so these run offline and fast.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from app.schemas import AnswerStatus, Confidence, QueryResponse, SelfConfidence


@pytest.fixture(autouse=True)
def _tmp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    # fresh repo bound to the tmp dir
    import app.store.repos as repos

    monkeypatch.setattr(repos, "_matter_repo", None)
    yield
    get_settings.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture()
def stub_pipeline(monkeypatch):
    def fake_run_query(req):
        return QueryResponse(
            answer=f"Grounded answer to: {req.query}",
            citations=[],
            confidence=Confidence(
                retrieval_score=0.9,
                self_confidence=SelfConfidence.high,
                status=AnswerStatus.answered,
            ),
            abs_flag="herb" in req.query.lower(),
        )

    import app.services.matters as matters_svc

    monkeypatch.setattr(matters_svc.pipeline, "run_query", fake_run_query)


def test_create_list_get_matter(client):
    r = client.post("/matters", json={"title": "Ashwagandha churna", "jurisdiction": "india"})
    assert r.status_code == 201
    mid = r.json()["id"]

    r = client.get("/matters")
    assert r.status_code == 200
    assert [m["id"] for m in r.json()] == [mid]

    r = client.get(f"/matters/{mid}")
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Ashwagandha churna"
    assert body["abs_status"] == "unknown"
    assert body["audit"][0]["action"] == "matter.created"


def test_update_and_delete(client):
    mid = client.post("/matters", json={"title": "x"}).json()["id"]

    r = client.patch(f"/matters/{mid}", json={"notes": "call the IP cell"})
    assert r.status_code == 200
    assert r.json()["notes"] == "call the IP cell"

    assert client.delete(f"/matters/{mid}").status_code == 204
    assert client.get(f"/matters/{mid}").status_code == 404


def test_missing_matter_404(client):
    assert client.get("/matters/deadbeef").status_code == 404
    assert client.patch("/matters/deadbeef", json={"title": "y"}).status_code == 404


def test_ask_records_question_and_updates_abs_status(client, stub_pipeline):
    mid = client.post("/matters", json={"title": "m", "jurisdiction": "india"}).json()["id"]

    r = client.post(f"/matters/{mid}/questions", json={"query": "What is the patent term?"})
    assert r.status_code == 200
    body = r.json()
    assert body["question"]["status"] == "answered"
    assert body["matter"]["abs_status"] == "clear"
    assert len(body["matter"]["questions"]) == 1

    r = client.post(f"/matters/{mid}/questions", json={"query": "Do I need approval to use a wild herb?"})
    assert r.json()["matter"]["abs_status"] == "flagged"


def test_ask_empty_query_422(client, stub_pipeline):
    mid = client.post("/matters", json={"title": "m"}).json()["id"]
    assert client.post(f"/matters/{mid}/questions", json={"query": "   "}).status_code == 422
