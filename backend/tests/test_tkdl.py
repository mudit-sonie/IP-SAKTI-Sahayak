"""TKDL / prior-art cross-check scaffold (roadmap S12)."""
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


def test_tkdl_check_is_honest_and_lists_terms(client):
    mid = client.post(
        "/matters",
        json={
            "title": "Turmeric wound gel",
            "formulation_label": "Proprietary Ayurvedic medicine",
            "profile": {
                "key_ingredients": ["Curcuma longa", "Aloe vera"],
                "intended_use": "wound healing",
            },
        },
    ).json()["id"]

    m = client.post(f"/matters/{mid}/tkdl-check").json()
    assert m["tkdl"]["status"] == "not_connected"
    assert m["tkdl"]["references"] == []
    assert "Curcuma longa" in m["tkdl"]["search_terms"]
    assert "wound healing" in m["tkdl"]["search_terms"]
    assert "not" in m["tkdl"]["note"].lower()
    assert any(a["action"] == "tkdl.checked" for a in m["audit"])


def test_tkdl_check_missing_matter(client):
    assert client.post("/matters/nope/tkdl-check").status_code == 404
