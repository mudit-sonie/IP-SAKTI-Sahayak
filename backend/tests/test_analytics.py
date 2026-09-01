"""Anonymized analytics (roadmap S16)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def _tmp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("QUERY_CACHE_ENABLED", "false")
    get_settings.cache_clear()
    import app.store.repos as repos

    monkeypatch.setattr(repos, "_matter_repo", None)
    yield
    get_settings.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_analytics_counts_queries_without_storing_text(client, tmp_path):
    client.post("/query", json={"query": "patent term in India", "jurisdiction": "india"})
    client.post("/query", json={"query": "trademark classes", "jurisdiction": "international"})

    body = client.get("/analytics").json()
    assert body["total_queries"] == 2
    assert body["by_jurisdiction"] == {"india": 1, "international": 1}
    assert sum(body["by_status"].values()) == 2
    assert 0.0 <= body["escalation_rate"] <= 1.0
    assert len(body["by_day"]) == 1

    # the persisted file must not contain the query text
    raw = (tmp_path / "analytics.json").read_text(encoding="utf-8")
    assert "patent term in India" not in raw
    assert "trademark classes" not in raw


def test_analytics_empty_summary(client):
    body = client.get("/analytics").json()
    assert body["total_queries"] == 0
    assert body["abs_flag_rate"] == 0.0
