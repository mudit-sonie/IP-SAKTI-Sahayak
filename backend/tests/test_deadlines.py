"""Derived + manual deadlines (roadmap S9)."""
from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from app.schemas import DeadlineAnchor
from app.services import deadlines


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


def _matter(client, jurisdiction="india") -> str:
    r = client.post("/matters", json={"title": "Test", "jurisdiction": jurisdiction})
    return r.json()["id"]


def test_add_months_rolls_over_and_clamps():
    assert deadlines._add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert deadlines._add_months(date(2026, 3, 15), 48) == date(2030, 3, 15)
    assert deadlines._add_months(date(2024, 2, 29), 12) == date(2025, 2, 28)


def test_derive_patent_filing_windows():
    d = deadlines.derive(DeadlineAnchor.patent_filing, date(2026, 3, 1), "india")
    rules = {x.source_rule: x for x in d}
    assert rules["patent_rfe"].due_date == "2030-03-01"
    assert rules["patent_term_expiry"].due_date == "2046-03-01"
    assert all(x.kind == "derived" and x.anchor == "patent_filing" for x in d)


def test_derive_endpoint_and_done_preserved(client):
    mid = _matter(client)
    m = client.post(
        f"/matters/{mid}/deadlines/derive",
        json={"anchor": "patent_filing", "anchor_date": "2026-03-01"},
    ).json()
    assert len(m["deadlines"]) == 3
    assert m["anchor_dates"]["patent_filing"] == "2026-03-01"

    rfe = next(d for d in m["deadlines"] if d["source_rule"] == "patent_rfe")
    m = client.patch(
        f"/matters/{mid}/deadlines/{rfe['id']}", json={"done": True}
    ).json()

    # re-derive with a new date; the done flag for that rule survives
    m = client.post(
        f"/matters/{mid}/deadlines/derive",
        json={"anchor": "patent_filing", "anchor_date": "2027-01-01"},
    ).json()
    assert len(m["deadlines"]) == 3
    rfe2 = next(d for d in m["deadlines"] if d["source_rule"] == "patent_rfe")
    assert rfe2["due_date"] == "2031-01-01"
    assert rfe2["done"] is True


def test_manual_add_and_delete(client):
    mid = _matter(client)
    m = client.post(
        f"/matters/{mid}/deadlines",
        json={"title": "Send response to opposition", "due_date": "2026-10-01"},
    ).json()
    assert m["deadlines"][0]["kind"] == "manual"
    did = m["deadlines"][0]["id"]

    m = client.request(
        "DELETE", f"/matters/{mid}/deadlines/{did}"
    ).json()
    assert m["deadlines"] == []


def test_bad_date_rejected(client):
    mid = _matter(client)
    r = client.post(
        f"/matters/{mid}/deadlines/derive",
        json={"anchor": "patent_filing", "anchor_date": "March 2026"},
    )
    assert r.status_code == 422


def test_derive_replaces_only_same_anchor(client):
    mid = _matter(client)
    client.post(
        f"/matters/{mid}/deadlines/derive",
        json={"anchor": "patent_filing", "anchor_date": "2026-03-01"},
    )
    m = client.post(
        f"/matters/{mid}/deadlines/derive",
        json={"anchor": "patent_priority", "anchor_date": "2025-03-01"},
    ).json()
    anchors = {d["anchor"] for d in m["deadlines"]}
    assert anchors == {"patent_filing", "patent_priority"}
