"""State-level ASU&H rules scaffold (roadmap S13)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


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


def test_state_rules_directory(client):
    body = client.get("/state-rules").json()
    assert body["note"]
    keys = {a["key"] for a in body["authorities"]}
    assert {"kerala", "maharashtra", "other"} <= keys
    for a in body["authorities"]:
        assert a["authority"]


def test_unknown_state_key_404(client):
    assert client.get("/state-rules/atlantis").status_code == 404


def test_matter_state_feeds_licensing_checklist_item(client):
    mid = client.post(
        "/matters",
        json={"title": "Churna", "formulation_category": "proprietary"},
    ).json()["id"]

    m = client.patch(f"/matters/{mid}", json={"state": "kerala"}).json()
    assert m["state"] == "kerala"
    lic = next(
        c for c in m["checklist"] if c["source_rule"] == "asu_manufacturing_licence"
    )
    assert "Kerala" in (lic["detail"] or "")
