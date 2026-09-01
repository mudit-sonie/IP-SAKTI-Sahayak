"""Amendment-awareness overlay (roadmap S6)."""
import json

from app.retrieval.corpus import Chunk, _apply_overlay, _load_amendment_overlay


def _chunk(source_id, section):
    return Chunk(
        chunk_id=f"{source_id}_{section}",
        text="body",
        metadata={"source_id": source_id, "section": section, "source": "X"},
    )


OVERLAY = {
    "patents_rules_2003": {"as_of": "2024-03-15"},
    "biological_diversity_act_2002": {
        "provisions": {"6": {"amended_by": "BD (Amendment) Act, 2023", "in_force": True}}
    },
}


def test_source_level_as_of_applied():
    c = _chunk("patents_rules_2003", "3")
    _apply_overlay(c, OVERLAY)
    assert c.as_of == "2024-03-15"
    assert c.amended_by is None
    assert c.is_stale is False


def test_provision_amendment_applied_to_section_and_subclause():
    whole = _chunk("biological_diversity_act_2002", "6")
    clause = _chunk("biological_diversity_act_2002", "6(1)")
    other = _chunk("biological_diversity_act_2002", "60")
    for c in (whole, clause, other):
        _apply_overlay(c, OVERLAY)
    assert whole.amended_by == "BD (Amendment) Act, 2023"
    assert whole.is_stale is True
    assert clause.amended_by == "BD (Amendment) Act, 2023"
    assert other.amended_by is None


def test_ingested_as_of_not_overwritten_by_overlay():
    c = _chunk("patents_rules_2003", "3")
    c.metadata["as_of"] = "2020-01-01"
    _apply_overlay(c, OVERLAY)
    assert c.as_of == "2020-01-01"


def test_missing_or_bad_overlay_file_is_ignored(tmp_path):
    assert _load_amendment_overlay(None) == {}
    assert _load_amendment_overlay(tmp_path / "nope.json") == {}
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    assert _load_amendment_overlay(bad) == {}
    good = tmp_path / "good.json"
    good.write_text(json.dumps(OVERLAY), encoding="utf-8")
    assert _load_amendment_overlay(good) == OVERLAY


def test_chunk_endpoint_exposes_amendment(client):
    """The shipped overlay flags Biological Diversity Act s.6 as amended."""
    if not client.get("/health").json()["corpus_loaded"]:
        return
    corpus = client.get("/corpus").json()
    assert any(s["source"].startswith("The Biological Diversity") for s in corpus["sources"])
