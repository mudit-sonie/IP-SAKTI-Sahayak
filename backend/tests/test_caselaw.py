"""Case-law layer (roadmap S14)."""
from app.retrieval.corpus import Chunk
from app.retrieval.hybrid import RetrievedChunk
from app.services.caselaw import case_notes


def _rc(meta, text="The court held that section 3(d) requires enhanced efficacy."):
    return RetrievedChunk(chunk=Chunk(chunk_id=meta["source"], text=text, metadata=meta), score=1.0)


def test_case_notes_extracts_only_cases():
    chunks = [
        _rc({"document_type": "Act", "source": "The Patents Act, 1970", "section": "3(d)"}),
        _rc({
            "document_type": "case",
            "source": "Novartis AG v. Union of India",
            "citation": "(2013) 6 SCC 1",
            "court": "Supreme Court of India",
            "year": "2013",
            "source_url": "http://example/novartis",
        }),
    ]
    notes = case_notes(chunks)
    assert len(notes) == 1
    n = notes[0]
    assert n.case_name == "Novartis AG v. Union of India"
    assert n.citation == "(2013) 6 SCC 1"
    assert n.year == 2013
    assert n.excerpt


def test_no_cases_gives_empty():
    assert case_notes([_rc({"document_type": "Act", "source": "X"})]) == []


def test_query_contract_has_case_notes(client):
    body = client.post("/query", json={"query": "patent term", "jurisdiction": "india"}).json()
    assert body["case_notes"] == []  # none ingested yet
