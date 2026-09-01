"""Document drafts (roadmap S8)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from app.schemas import DraftKind
from app.services import drafts


@pytest.fixture(autouse=True)
def _tmp_dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DRAFTS_DIR", str(tmp_path / "drafts"))
    get_settings.cache_clear()
    import app.store.repos as repos

    monkeypatch.setattr(repos, "_matter_repo", None)
    yield
    get_settings.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def _matter(client) -> str:
    r = client.post(
        "/matters",
        json={
            "title": "Ashwagandha sleep churna",
            "jurisdiction": "india",
            "formulation_category": "proprietary",
            "formulation_label": "Proprietary Ayurvedic medicine",
            "profile": {
                "dosage_form": "churna",
                "key_ingredients": ["Withania somnifera", "Bacopa monnieri"],
                "intended_use": "supports sleep quality",
                "process_novelty": "novel dual-extract ratio",
                "source_notes": "cultivated in Madhya Pradesh",
            },
        },
    )
    assert r.status_code == 201
    return r.json()["id"]


def test_draft_kinds_endpoint(client):
    r = client.get("/draft-kinds")
    assert r.status_code == 200
    kinds = {k["kind"] for k in r.json()}
    assert kinds == {"form1", "nba_abs", "disclosure_of_source", "s3p_rebuttal"}


@pytest.mark.parametrize("kind", [k.value for k in DraftKind])
def test_generate_download_delete_each_kind(client, kind):
    mid = _matter(client)

    r = client.post(f"/matters/{mid}/drafts", json={"kind": kind})
    assert r.status_code == 201
    matter = r.json()
    assert len(matter["drafts"]) == 1
    draft = matter["drafts"][0]
    assert draft["kind"] == kind

    dl = client.get(f"/matters/{mid}/drafts/{draft['id']}")
    assert dl.status_code == 200
    assert "attachment" in dl.headers["content-disposition"]
    md = dl.text
    # filled from the profile, and carries the disclaimer + traceability section
    assert "Withania somnifera" in md
    assert "not a filing" in md.lower()
    assert "Traceability" in md

    d = client.delete(f"/matters/{mid}/drafts/{draft['id']}")
    assert d.status_code == 200
    assert d.json()["drafts"] == []

    assert client.get(f"/matters/{mid}/drafts/{draft['id']}").status_code == 404


def test_render_is_pure_and_grounded_markers_present():
    """render() adds a legal-basis marker for every legal assertion."""
    from app.schemas import Matter, MatterProfile

    m = Matter(
        id="x", title="t", created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z", formulation_category="proprietary",
        profile=MatterProfile(key_ingredients=["Turmeric"]),
    )
    out = drafts.render(m, DraftKind.disclosure_of_source)
    assert "[Legal basis:" in out.markdown
    assert out.markdown == drafts.render(m, DraftKind.disclosure_of_source).markdown


def test_unknown_kind_rejected(client):
    mid = _matter(client)
    assert client.post(f"/matters/{mid}/drafts", json={"kind": "bogus"}).status_code == 422
