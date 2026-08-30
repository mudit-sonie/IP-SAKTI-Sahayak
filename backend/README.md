# IP-SAKTI Sahayak — Backend

FastAPI backend for the citation-grounded Ayurveda IPR RAG assistant
(SIH 2026, PS 26045). Query-time flow:

```
/query → hybrid retrieval (BM25 + Chroma, jurisdiction-routed)
       → grounded generation (Gemini, forced JSON)
       → confidence check (retrieval top-score threshold, primary)
       → ABS second pass (Biological Diversity Act + Rules) if triggered
       → cited answer  |  escalate
```

## Quick start

```bash
cd backend
cp .env.example .env          # add GEMINI_API_KEYS (comma-separated)
python -m venv .venv && . .venv/bin/activate     # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Or just `./run.sh` (POSIX) / `.\run.ps1` (Windows).

Open http://localhost:8000/docs for the live contract.

## Endpoints (PRD §4)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness + `corpus_loaded` / `gemini_configured` flags |
| POST | `/classify` | rule-based formulation classifier (stateless, send full answers dict) |
| POST | `/query` | main RAG query |
| POST | `/abs-check` | ABS second pass (also invoked internally by `/query`) |

Request/response shapes live in `app/schemas.py` and are the source of truth for
the frontend mock data — treat changes there as breaking.

## Layout

```
app/
  main.py            FastAPI app factory, CORS, startup warm-up
  config.py          env-driven Settings (all tunables live here)
  schemas.py         wire contract (pydantic)
  api/routes.py      the 4 endpoints
  llm/gemini_client.py   multi-key rotation (HackRx brain.py pattern)
  retrieval/
    corpus.py        load chunks.jsonl
    bm25.py          rank_bm25 sparse index
    vector.py        Chroma + sentence-transformers (lazy/optional)
    hybrid.py        min-max normalise + weight-fuse → top_score
  services/
    classifier.py    decision tree
    generation.py    grounded prompt + JSON parse + citation filter
    confidence.py    threshold logic
    abs_helper.py    ABS trigger + narrow retrieval
    pipeline.py      /query orchestration
scripts/build_index.py   build/refresh indices from the processed corpus
tests/                    contract + classifier tests (run: pytest)
```

## Corpus dependency

The retriever reads `CORPUS_CHUNKS_PATH` (default `data/processed/chunks.jsonl`),
produced by `scripts/ingest_corpus.py` (deterministic, no LLM — follows the
`legal-corpus-ingestion` rulebook). Until that file exists the backend runs fine
but every `/query` returns `status: escalate` — this is intentional (no mocks on
the core loop).

```bash
python -m scripts.ingest_corpus            # cleaned corpus -> data/processed/chunks.jsonl
python -m scripts.ingest_corpus --stdout   # dry run: per-source chunk counts, writes nothing
python -m scripts.build_index              # (re)build BM25 + Chroma from chunks.jsonl
```

`chunks.jsonl` + `documents.json` + `validation_report.json` are committed so the
rest of the team doesn't need the raw corpus to run retrieval. Current corpus:
**532 India chunks** across the Patents Act, Trade Marks Act, Biological Diversity
Act, Drugs & Cosmetics Act, Drugs & Magic Remedies Act, and the GI Act. TRIPS /
CBD / Nagoya and the Patents Rules 2003 are staged for Day 3 (different source
formatting — `--stdout` shows them at 0 chunks / `needs_review`).

## Tuning

- `RETRIEVAL_ESCALATE_THRESHOLD` — below this fused top-score, `/query` forces
  escalate. Tune during Day 4 spot-checks; start conservative.
- `HYBRID_BM25_WEIGHT` — BM25 vs vector weight in fusion (0..1).

## Tests

```bash
cd backend && pytest
```

CI has no corpus and no Gemini key, so tests assert the *escalate* contract shape
plus the full classifier decision tree.
