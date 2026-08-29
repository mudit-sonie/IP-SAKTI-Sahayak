# CLAUDE.md

Guidance for Claude Code (and humans) working in this repo.

## What this is

**IP-SAKTI Sahayak** — a citation-grounded RAG assistant for Ayurveda intellectual
property and regulatory questions. SIH 2026, Problem Statement 26045, Ministry of
AYUSH / AIIA. Build window **29 Aug – 1 Sep 2026**.

Authoritative spec: [`PRD_Tech_Team_IP-SAKTI-Sahayak.md`](PRD_Tech_Team_IP-SAKTI-Sahayak.md).
Read it before making design decisions. Key rule: **no mocks on the core loop** —
every demoed answer must trace to a real statute/treaty section in our corpus.

## Repo layout

```
corpus/                 source legal PDFs (India + International) — see corpus/README.md
  india/                9 India sources
  international/         TRIPS, CBD/Nagoya
backend/                FastAPI RAG backend — see backend/README.md
  app/                  application code
  scripts/build_index.py   build BM25+Chroma from processed corpus
  tests/                pytest suite
.claude/skills/legal-corpus-ingestion/   deterministic PDF → chunks.jsonl pipeline skill
frontend/               React app (not yet scaffolded as of Day 1)
```

## Architecture (locked — see PRD §2)

```
query → formulation classifier (rule-based tree)
      → jurisdiction toggle (india | international, default india)
      → hybrid retrieval (BM25 + Chroma), jurisdiction-routed
      → [if biological-resource touch] ABS second pass over Biodiversity Act + Rules
      → grounded generation (Gemini, forced JSON: answer/citations/self_confidence)
      → confidence check (retrieval top-score threshold PRIMARY, self_confidence secondary)
           ≥ threshold → cited answer     |     < threshold → escalate
```

### Stack

| Layer | Choice |
|---|---|
| LLM | Gemini Flash, multi-key rotation (`app/llm/gemini_client.py`) |
| Embeddings | `bge-small-en` / `all-MiniLM-L6-v2`, local via sentence-transformers |
| Sparse | `rank_bm25`, in-process |
| Vector store | Chroma, local/embedded |
| Backend | FastAPI |
| Frontend | React |

All free-tier / local. Zero cloud credits.

## API contract (PRD §4)

`POST /classify`, `POST /query`, `POST /abs-check`, `GET /health`. Shapes are
defined in `backend/app/schemas.py` — **that file is the source of truth**. The
frontend builds every screen against these shapes with mock JSON from Day 1;
changing a shape is a breaking change, announce it.

## Working conventions

- **Config / tunables** live in `backend/app/config.py` (env-driven). The retrieval
  escalate threshold and hybrid weight are there; they get tuned on Day 4, not
  hardcoded elsewhere.
- **Legal text is authoritative.** Never let an LLM rewrite, summarise, paraphrase,
  or "correct" statute text during ingestion. See the `legal-corpus-ingestion`
  skill for the full rulebook. Chunk by section/clause, never token windows.
- **Escalate is a feature, not a bug.** When retrieval is weak or Gemini is
  unavailable, the backend returns `status: escalate` with no invented citation.
  Keep it that way.
- **Citations are filtered** against retrieved passages in `generation.py` — the
  model cannot cite a source that wasn't in its context.
- Prefer official sources (India Code, IP India, CDSCO, FSSAI, NBA, WTO, CBD) over
  third-party copies.

## Commands

```bash
# backend dev server
cd backend && ./run.sh            # or .\run.ps1 on Windows
# tests
cd backend && pytest
# (re)build retrieval indices once ingestion has produced chunks.jsonl
cd backend && python -m scripts.build_index
```

## Day-by-day status

See [`STATUS.md`](STATUS.md) for the live task board (updated by the lead).

## Known environment gotcha

Several `corpus/` subdirectories were created on macOS with a `:` in the folder
name (e.g. `01_patents_act_1970:/`). **`:` is illegal in Windows/NTFS paths**, so
`git checkout` cannot materialise those files on Windows — they show as deleted in
`git status` on a Windows clone. Do **not** `git add -A` / commit those deletions.
Work on macOS/Linux/WSL for anything touching `corpus/`, or rename the dirs to drop
the `:` (coordinate first — it rewrites paths for everyone). This repo sets
`core.protectNTFS=false` locally as a stopgap so commits of other paths still work.

## Git

- Commit in small, focused chunks with descriptive messages.
- Do not add a Claude/AI co-author signature to commits in this repo.
