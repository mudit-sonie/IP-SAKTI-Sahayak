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


_captured = {}


@pytest.fixture()
def stub_pipeline(monkeypatch):
    def fake_run_query(req):
        _captured["context"] = req.context
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


def test_profile_is_injected_as_question_context(client, stub_pipeline):
    mid = client.post("/matters", json={"title": "m"}).json()["id"]
    client.patch(
        f"/matters/{mid}",
        json={
            "profile": {
                "dosage_form": "churna",
                "key_ingredients": ["amalaki", "haritaki"],
                "intended_use": "digestive",
            }
        },
    )
    client.post(f"/matters/{mid}/questions", json={"query": "is this classical?"})
    assert "churna" in _captured["context"]
    assert "amalaki" in _captured["context"]


def test_classifying_via_patch_generates_checklist(client, stub_checklist_grounding):
    mid = client.post("/matters", json={"title": "m", "jurisdiction": "india"}).json()["id"]
    assert client.get(f"/matters/{mid}").json()["checklist"] == []

    r = client.patch(
        f"/matters/{mid}",
        json={"formulation_category": "classical", "formulation_label": "Classical"},
    )
    assert len(r.json()["checklist"]) > 0


@pytest.fixture()
def stub_checklist_grounding(monkeypatch):
    import app.services.checklist as cl

    monkeypatch.setattr(cl, "_ground", lambda probe, jurisdiction: [])


def test_checklist_generated_on_classified_matter(client, stub_checklist_grounding):
    r = client.post(
        "/matters",
        json={
            "title": "Proprietary blend",
            "jurisdiction": "india",
            "formulation_category": "proprietary",
            "formulation_label": "Patent / Proprietary Ayurvedic Medicine",
        },
    )
    body = r.json()
    assert len(body["checklist"]) > 0
    assert all(i["status"] == "todo" for i in body["checklist"])
    # no ABS items until the matter is ABS-flagged
    assert not any(i["group"] == "ABS" for i in body["checklist"])


def test_checklist_status_patch_and_regenerate_preserves_it(client, stub_checklist_grounding):
    mid = client.post(
        "/matters",
        json={"title": "m", "jurisdiction": "india", "formulation_category": "classical"},
    ).json()["id"]
    item = client.get(f"/matters/{mid}").json()["checklist"][0]

    r = client.patch(f"/matters/{mid}/checklist/{item['id']}", json={"status": "done"})
    assert r.status_code == 200

    r = client.post(f"/matters/{mid}/checklist")
    kept = next(i for i in r.json()["checklist"] if i["id"] == item["id"])
    assert kept["status"] == "done"
