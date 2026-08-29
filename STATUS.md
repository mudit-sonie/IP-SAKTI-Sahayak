# Build Status — IP-SAKTI Sahayak

Live task board. Maintained by the tech lead. Spec: `PRD_Tech_Team_IP-SAKTI-Sahayak.md`.

---

## Day 1 — 29 Aug

**EOD target (PRD §6):** all 11 source docs identified and cleaning in progress;
backend skeleton runs; frontend renders static screens against mock data.

| Workstream | Owner | Status | Notes |
|---|---|---|---|
| Corpus sourcing | Anuj | 🟡 mostly done | 10/11 PDFs committed (`23a7d07`). **Gaps:** GI Act 1999 (no PDF — scrape from ipindia.gov.in, see `corpus/india/06_geographical_indications:/readme.md`); confirm Biological Diversity Rules 2024 + BD (Amendment) Act 2023 are present and not just the 2002 Act. |
| Corpus cleaning / OCR | Kavish | 🔴 not started in repo | Handed over per `23a7d07`. No cleaned text or `chunks.jsonl` committed yet. Highest lead-time item — needs to be visibly moving today. |
| Ingestion pipeline (chunking + metadata → `chunks.jsonl`) | Kavish / TBD | 🔴 not started | Skill exists (`.claude/skills/legal-corpus-ingestion`). Output must land at `backend/data/processed/chunks.jsonl`. |
| **Backend scaffolding** | **Dewashish (lead)** | 🟢 **done** | FastAPI app + `/health` `/classify` `/query` `/abs-check`, hybrid BM25+Chroma retrieval infra, Gemini multi-key rotation, rule-based classifier, confidence + ABS second pass, pipeline orchestration, pytest suite. Runs today; returns `escalate` until corpus chunks exist (by design). |
| Frontend scaffolding | TBD | 🔴 not started | No `frontend/` dir yet. Needs: React shell, routing, screens (classifier wizard, query + citation cards, confidence/escalate states, jurisdiction toggle) built against `backend/app/schemas.py` shapes with mock JSON. |
| Gemini keys provisioned | TBD | ⚪ unknown | Need ≥3 free-tier keys in `backend/.env` (`GEMINI_API_KEYS=`) for rotation. |

### Day 1 blockers / asks
- **Cleaning + ingestion must start now** — the Day 2 milestone (real end-to-end
  loop) depends entirely on `chunks.jsonl` existing. This is the critical path.
- Someone needs to own the **frontend scaffold** today.
- Collect Gemini API keys.
- Decide who renames the `:`-containing `corpus/` dirs (breaks Windows checkout —
  see CLAUDE.md gotcha) or confirm we all work on macOS/Linux/WSL.

---

## Day 2 — 30 Aug  (not started)
Core loop end-to-end on real India-corpus data. Non-negotiable milestone.

## Day 3 — 31 Aug  (not started)
International thin corpus + ABS helper wired live; frontend polish.

## Day 4 — 1 Sep  (not started)
Integration buffer; 10–15 Q&A spot-checks vs source text; demo rehearsal + deploy.
