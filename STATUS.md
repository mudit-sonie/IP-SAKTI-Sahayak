# Build Status — IP-SAKTI Sahayak

Live task board. Maintained by the tech lead. Spec: `PRD_Tech_Team_IP-SAKTI-Sahayak.md`.

---

## Day 1 — 29 Aug

**EOD target (PRD §6):** all 11 source docs identified and cleaning in progress;
backend skeleton runs; frontend renders static screens against mock data.

| Workstream | Owner | Status | Notes |
|---|---|---|---|
| Corpus sourcing | Anuj | 🟡 nearly done | 10 PDFs (`23a7d07`) + GI Act 1999 as formatted markdown (`3074cc7`, TOC + full sectioned text — good for chunking). **Remaining:** confirm Biological Diversity Rules 2024 + BD (Amendment) Act 2023 are present, not just the 2002 Act. |
| Corpus cleaning / OCR | Kavish | 🔴 not started in repo | Handed over per `23a7d07`. No cleaned text or `chunks.jsonl` committed yet. Highest lead-time item — needs to be visibly moving today. |
| Ingestion pipeline (chunking + metadata → `chunks.jsonl`) | Kavish / TBD | 🔴 not started | Skill exists (`.claude/skills/legal-corpus-ingestion`). Output must land at `backend/data/processed/chunks.jsonl`. |
| **Backend scaffolding** | **Dewashish (lead)** | 🟢 **done** | FastAPI app + `/health` `/classify` `/query` `/abs-check`, hybrid BM25+Chroma retrieval infra, Gemini multi-key rotation, rule-based classifier, confidence + ABS second pass, pipeline orchestration, pytest suite. Runs today; returns `escalate` until corpus chunks exist (by design). 14/14 pytest green, `uvicorn app.main:app` boots clean. |
| Frontend scaffolding | Mudit | 🟢 merged (`1d4a4d6`, PR `codex/frontend-mvp`) | Vite + React + react-router. Home + jurisdiction toggle → 4-question classify wizard → Ask → mock Result (citation cards, confidence badge, ABS section, escalation card). All mock data. **Follow-ups:** align classify categories/questions with `backend/app/schemas.py` enum (missing `phytopharmaceutical`; using display labels not enum values); replace client-side classify logic with `/classify` calls; add a shared API client + mock JSON matching real response shapes (`confidence.retrieval_score`, `abs_flag`, `citations[].excerpt_ref`); dead `submitted` state in `Ask.jsx`. |
| Gemini keys provisioned | TBD | ⚪ unknown | Need ≥3 free-tier keys in `backend/.env` (`GEMINI_API_KEYS=`) for rotation. |

### Day 1 blockers / asks
- **Cleaning + ingestion must start now** — the Day 2 milestone (real end-to-end
  loop) depends entirely on `chunks.jsonl` existing. This is the critical path.
- Frontend scaffold merged (Mudit). Toolchain re-pinned to stable Vite 6 / ESLint 9
  (`4ebbc6c`) — the PR's Vite 8 pins didn't build. `npm ci && npm run build` green.
- Collect Gemini API keys.
- Frontend PR got merged twice (`1d4a4d6` by lead, `df1df86` by Anuj) — harmless, but
  coordinate merges so it doesn't happen again.
- `:` in `corpus/` dir names fixed by rename (`2a42196`) — re-clone if you pulled before that.
- `.DS_Store` files keep getting committed (3 tracked). Add to `.gitignore` and
  `git rm --cached` them.
- `assets/BabySharks.png` is 2.2 MB for a README banner — fine, but compress if the
  repo size becomes a concern.

---

## Day 2 — 30 Aug  🟡 in progress
Core loop end-to-end on real India-corpus data. Non-negotiable milestone.

| Workstream | Owner | Status | Notes |
|---|---|---|---|
| Corpus preprocessing (PDF → cleaned text) | Kavish | 🟢 done | `44ffdaa` — 15 docs cleaned to per-document `.txt` under `corpus/preprocessing_corpus/cleaned_corpus/documents/`. |
| Ingestion pipeline (cleaned text → `chunks.jsonl`) | Dewashish | 🟢 done | New `backend/scripts/ingest_corpus.py` — deterministic, no LLM. **532 India chunks** committed at `backend/data/processed/chunks.jsonl` (+ `documents.json`, `validation_report.json`). Section-aware: Patents Act (152), Trade Marks Act (163), Biological Diversity Act (60), Drugs & Cosmetics Act (52), Drugs & Magic Remedies Act (18), GI Act (87). Footnote/amendment marginalia stripped; legal text unchanged. |
| Retrieval on real data | Dewashish | 🟢 BM25 live / 🟡 vector pending | `build_index` loads 532 chunks; BM25 hybrid smoke queries land on the right Act + section (BD Act §6 for NBA-approval-before-patent, GI Act §2 for "what is a GI", Magic Remedies §5 for ayurvedic cure ads, BD Act §21 for benefit-sharing). `hybrid.py` now leans fully on whichever index is ready so `top_score` stays a meaningful [0,1] confidence signal in BM25-only mode. **Chroma + sentence-transformers install in progress** (large: torch). |
| Full core loop (→ cited answer) | Dewashish | 🔴 blocked on Gemini keys | Pipeline runs end-to-end today: `/query` → real retrieval → confidence → response, `corpus_loaded: true`, 14/14 pytest green. Returns `status: escalate` **only** because `GEMINI_API_KEYS` is unset and `google-generativeai` isn't installed yet. **Ask: someone provision ≥3 free-tier Gemini keys into `backend/.env`** — that's the last thing between us and cited answers. |
| Frontend → real API on core flow | Mudit | 🔴 not started | Still on mock JSON. `/classify` + `/query` are live locally (`uvicorn app.main:app`, port 8000). Wire the Ask→Result path to `POST /query`; response shape unchanged from `schemas.py`. |

### Day 2 blockers / asks
- **Gemini keys** — critical path for the "cited answer" half of the milestone. Backend is ready; drop keys in `backend/.env` (`GEMINI_API_KEYS=k1,k2,k3`).
- Vector index (Chroma) — dependency install running; retrieval works BM25-only until then, quality already sane.
- TRIPS / CBD / Nagoya / Patents Rules 2003 not yet chunked — different source formatting, moved to Day 3 (international corpus day anyway). `ingest_corpus.py --stdout` lists them as 0 chunks / needs_review.
- `corpus/preprocessing_corpus/` carries both the source PDFs again (~90 MB) and the cleaned text — repo is getting heavy; consider a shallow/LFS strategy before demo.
- Ayurveda Aahar regulations 2022: cleaned text is Devanagari + garbled OCR, no usable English — needs a clean English source (FSSAI gazette) before it can be ingested.

## Day 3 — 31 Aug  (not started)
International thin corpus + ABS helper wired live; frontend polish.

## Day 4 — 1 Sep  (not started)
Integration buffer; 10–15 Q&A spot-checks vs source text; demo rehearsal + deploy.
