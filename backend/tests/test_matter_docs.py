"""Matter documents as context (roadmap S20)."""
from __future__ import annotations

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


def test_upload_ready_and_chunked(client):
    mid = _matter(client)
    m = client.post(
        f"/matters/{mid}/documents",
        json={"filename": "draft-claims.txt", "text": DOC},
    ).json()
    assert len(m["documents"]) == 1
    doc = m["documents"][0]
    assert doc["status"] == "ready"
    assert doc["chunk_count"] >= 1

    detail = client.get(f"/matters/{mid}/documents/{doc['id']}").json()
    assert "Withania somnifera" in detail["text"]
    assert detail["chunks"]


def test_non_text_file_fails_cleanly(client):
    mid = _matter(client)
    m = client.post(
        f"/matters/{mid}/documents",
        json={"filename": "scan.pdf", "text": "%PDF-1.4 ..."},
    ).json()
    assert m["documents"][0]["status"] == "failed"
    assert "plain-text" in m["documents"][0]["error"]


def test_doc_context_feeds_generation_and_freezes_on_question(client, monkeypatch):
    mid = _matter(client)
    client.post(
        f"/matters/{mid}/documents",
        json={"filename": "draft-claims.txt", "text": DOC},
    )

    captured = {}

    def fake_generate(query, chunks, *, context=None, doc_context=None):
        captured["doc_context"] = doc_context
        from app.services.generation import Generation

        return Generation("Answer.", [], SelfConfidence.high)

    import app.services.pipeline as pipe

    monkeypatch.setattr(pipe.generation, "generate", fake_generate)

    res = client.post(
        f"/matters/{mid}/questions",
        json={"query": "Is the spray-drying step enough to avoid the section 3 exclusions?"},
    ).json()

    # the matter-doc snippet reached generation as background
    assert captured.get("doc_context")
    assert any("spray-drying" in s for s in captured["doc_context"])
    # and is frozen onto the question record
    assert res["question"]["doc_context"]
    assert res["result"]["doc_context"]


def test_delete_document(client):
    mid = _matter(client)
    m = client.post(
        f"/matters/{mid}/documents", json={"filename": "d.txt", "text": DOC}
    ).json()
    did = m["documents"][0]["id"]
    m = client.request("DELETE", f"/matters/{mid}/documents/{did}").json()
    assert m["documents"] == []
    assert client.get(f"/matters/{mid}/documents/{did}").status_code == 404
