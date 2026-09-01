"""Matter documents as context (roadmap S20)."""
from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from app.schemas import SelfConfidence


@pytest.fixture(autouse=True)
def _tmp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    import app.store.repos as repos

    monkeypatch.setattr(repos, "_matter_repo", None)
    yield
    get_settings.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def _matter(client) -> str:
    return client.post("/matters", json={"title": "Draft claims review"}).json()["id"]


DOC = (
    "Our draft independent claim 1 recites a process for preparing a standardised "
    "Withania somnifera root extract with a withanolide content of at least 5%.\n\n"
    "Claim 4 adds a spray-drying step at an inlet temperature below 120 C.\n\n"
    "The product is intended for sleep support and stress resilience."
)


def _upload(client, mid, name, data: bytes, mime="text/plain"):
    return client.post(
        f"/matters/{mid}/documents",
        files={"file": (name, io.BytesIO(data), mime)},
    )


def test_txt_upload_processes_to_ready(client):
    mid = _matter(client)
    r = _upload(client, mid, "draft-claims.txt", DOC.encode())
    assert r.status_code == 201
    assert r.json()["documents"][0]["status"] == "processing"

    # background processing has completed by the time the request returns
    doc = client.get(f"/matters/{mid}").json()["documents"][0]
    assert doc["status"] == "ready"
    assert doc["chunk_count"] >= 1

    detail = client.get(f"/matters/{mid}/documents/{doc['id']}").json()
    assert "Withania somnifera" in detail["text"]


def test_unsupported_type_fails_cleanly(client):
    mid = _matter(client)
    # rejected synchronously at register() — no background task scheduled
    doc = _upload(client, mid, "photo.png", b"\x89PNG...").json()["documents"][0]
    assert doc["status"] == "failed"
    assert "Unsupported file type" in doc["error"]


def test_oversize_rejected(client, monkeypatch):
    monkeypatch.setenv("MATTER_DOCS_MAX_MB", "1")
    get_settings.cache_clear()
    mid = _matter(client)
    r = _upload(client, mid, "big.txt", b"x" * (1_100_000))
    assert r.status_code == 422


def test_doc_context_feeds_generation_and_freezes(client, monkeypatch):
    mid = _matter(client)
    _upload(client, mid, "draft-claims.txt", DOC.encode())

    captured = {}

    def fake_generate(query, chunks, *, context=None, doc_context=None):
        captured["doc_context"] = doc_context
        from app.services.generation import Generation

        return Generation("Answer.", [], SelfConfidence.high)

    import app.services.pipeline as pipe

    monkeypatch.setattr(pipe.generation, "generate", fake_generate)

    res = client.post(
        f"/matters/{mid}/questions",
        json={"query": "Does the spray-drying step avoid the section 3 exclusions?"},
    ).json()

    assert captured.get("doc_context")
    assert any("spray-drying" in s for s in captured["doc_context"])
    assert res["question"]["doc_context"]
    assert res["result"]["doc_context"]


def test_delete_document(client):
    mid = _matter(client)
    did = _upload(client, mid, "d.txt", DOC.encode()).json()["documents"][0]["id"]
    m = client.request("DELETE", f"/matters/{mid}/documents/{did}").json()
    assert m["documents"] == []
    assert client.get(f"/matters/{mid}/documents/{did}").status_code == 404
