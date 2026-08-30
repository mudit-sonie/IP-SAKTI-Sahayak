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

## Day 2 — 30 Aug  🟢 core loop landed
Core loop end-to-end on real India-corpus data. **Milestone met**: classify →
hybrid retrieval → Gemini generation → confidence → cited answer, live through the
frontend.

| Workstream | Owner | Status | Notes |
|---|---|---|---|
| Corpus preprocessing (PDF → cleaned text) | Kavish | 🟢 done | `44ffdaa` — 15 docs cleaned to per-document `.txt` under `corpus/preprocessing_corpus/cleaned_corpus/documents/`. |
| Ingestion pipeline (cleaned text → `chunks.jsonl`) | Dewashish | 🟢 done | `backend/scripts/ingest_corpus.py` — deterministic, no LLM. **902 India chunks** committed (+ `documents.json`, `validation_report.json`). Section-aware; `rebreak_jammed_lines()` fixes one-line chapter/section jams from the PDF cleanup; `clause_split()` emits an independently-citable chunk per lettered clause (Patents Act `3(p)`, `3(e)`, …). Footnote/amendment marginalia stripped; legal text unchanged. |
| Retrieval on real data | Dewashish | 🟢 hybrid live | Chroma (`bge-small-en-v1.5`, local CPU) + BM25 over 902 chunks. Scores are meaningful (0.45–1.0): NBA-approval-before-patent → BD Act §6 (0.98), benefit-sharing → BD Act §21 (1.0), term of a patent → Patents Act §53, "traditional knowledge patent bar" → Patents Act §3(p) (0.84). `hybrid.py` degrades gracefully to whichever index is ready. |
| Full core loop (→ cited answer) | Dewashish | 🟢 live | Gemini wired (`gemini-2.5-flash`, single key in `backend/.env`). `/query` returns `status: answered` with real citations + `excerpt_ref` for well-covered questions (patent term, NBA approval, turmeric/TK patentability) and cleanly escalates — no invented citation — when retrieval is thin. 14/14 pytest green. |
| Frontend → real API on core flow | Dewashish (covering Mudit) | 🟢 done | `src/api/client.js` + `.env` (`VITE_API_BASE_URL`). Classify is now an API-driven wizard off `/classify`; Result calls `/query` on mount and renders real answer, citations, confidence badge (retrieval % + self-confidence), ABS panel, and the escalate state. Verified end-to-end through the browser (CORS preflight + 200s in the log). Build + lint green. |

### Day 2 blockers / asks
- **Gemini quota** — one free-tier key (`gemini-2.5-flash`, ~250 req/day). Fine for dev; **add 2–3 more keys to `GEMINI_API_KEYS`** (comma-separated) before demo day so the multi-key rotation has headroom during a live Q&A.
- **Retrieval tuning (Day 4)** — some correct answers still escalate on phrasing the corpus doesn't lexically/semantically match (e.g. "classical Ayurvedic formulation" doesn't reach Patents Act §3(p) the way "traditional knowledge" or "turmeric" does). Candidates: lower `RETRIEVAL_ESCALATE_THRESHOLD`, tune `HYBRID_BM25_WEIGHT`, light query expansion. Budget real time for it.
- Vector index — `data/chroma/` is gitignored; rebuild with `python -m scripts.build_index` (first run pulls the ~130 MB embedding model; ~3 min to embed 902 chunks on CPU).
- TRIPS / CBD / Nagoya / Patents Rules 2003 not yet chunked — different source formatting, moved to Day 3 (international corpus day). `ingest_corpus.py --stdout` lists them at 0 chunks / needs_review.
- `corpus/preprocessing_corpus/` carries the source PDFs again (~90 MB) plus cleaned text — repo is heavy; consider shallow/LFS before demo.
- Ayurveda Aahar regulations 2022: cleaned text is Devanagari + garbled OCR — needs a clean English FSSAI source before it can be ingested.
- chromadb posthog telemetry prints harmless `capture()` errors to the log; disabled in `vector.py` for new clients.

## Day 3 — 31 Aug  (not started)
International thin corpus (TRIPS + CBD/Nagoya) + Patents Rules 2003 chunked and
jurisdiction-routed; ABS helper polish; frontend polish (jurisdiction mismatch
prompt, citation excerpt display, loading states).

## Day 4 — 1 Sep  (not started)
Integration buffer; 10–15 Q&A spot-checks vs source text; demo rehearsal + deploy.
