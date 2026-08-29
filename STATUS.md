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

## Day 2 — 30 Aug  (not started)
Core loop end-to-end on real India-corpus data. Non-negotiable milestone.

## Day 3 — 31 Aug  (not started)
International thin corpus + ABS helper wired live; frontend polish.

## Day 4 — 1 Sep  (not started)
Integration buffer; 10–15 Q&A spot-checks vs source text; demo rehearsal + deploy.
