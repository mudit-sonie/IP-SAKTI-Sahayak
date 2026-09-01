<p align="center">
  <img src="assets/BabySharks.png" alt="Architecture" width="400">
</p>

# IP-SAKTI-Sahayak

SIH 2026 (PS 26045) — citation-grounded RAG assistant for Ayurveda intellectual
property and regulatory guidance. Every demoed answer traces to a real
statute/treaty section in our corpus, or it escalates to a human.

- **Spec:** [`PRD_Tech_Team_IP-SAKTI-Sahayak.md`](PRD_Tech_Team_IP-SAKTI-Sahayak.md)
- **Working notes / task board:** [`STATUS.md`](STATUS.md)
- **Contributor guide:** [`CLAUDE.md`](CLAUDE.md)
- Component docs: [`backend/README.md`](backend/README.md) · [`frontend/README.md`](frontend/README.md)

> ⚠️ This README is a quick-start for the team. A polished public README comes later.

---

## Repo layout

```
corpus/       source legal PDFs + cleaned text (India + International)
backend/      FastAPI RAG backend (retrieval + Gemini generation + confidence)
frontend/     React (Vite) app — wired to the live backend API
```

---

## Getting started

### 0. Prerequisites

- Python **3.10+**, Node **18+**
- A Google AI Studio API key (free): https://aistudio.google.com/apikey
  Free tier is **~20 requests/day per key per model** — grab a few keys.

### 1. Clone / pull

```bash
git clone https://github.com/mudit-sonie/IP-SAKTI-Sahayak.git
cd IP-SAKTI-Sahayak
# already cloned? just: git pull
```

### 2. Backend

```bash
cd backend
python -m venv .venv
. .venv/bin/activate            # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then edit .env — see below

# build the retrieval indices from the committed chunks.jsonl
# (first run downloads the ~130 MB embedding model; ~3 min to embed on CPU)
python -m scripts.build_index

# run
./run.sh                        # Windows: .\run.ps1   (or: uvicorn app.main:app --reload)
# -> http://localhost:8000/docs
```

**`backend/.env`** — the only thing you must set is the Gemini keys:

```
GEMINI_API_KEYS=key1,key2,key3      # comma-separated; the client rotates on quota errors
GEMINI_MODEL=gemini-3.5-flash-lite
```

Everything else has sane defaults. Without keys the backend still runs — every
`/query` just returns `status: escalate` (by design, no mocks on the core loop).

**Optional but recommended for demos** — pre-answer the gold questions so they're
instant and don't burn quota:

```bash
python -m scripts.warm_cache
```

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env            # VITE_API_BASE_URL=http://localhost:8000 (default is fine)
npm run dev                     # -> http://localhost:5173
```

The frontend calls the backend on `:8000`. Start the backend first.

---

## Common tasks

```bash
# backend tests
cd backend && pytest

# rebuild retrieval indices (after corpus/chunks change)
cd backend && python -m scripts.build_index

# re-run the corpus ingestion (cleaned text -> chunks.jsonl)
cd backend && python -m scripts.ingest_corpus            # --stdout for a dry run

# frontend build / lint
cd frontend && npm run build && npm run lint
```

## Gotchas

- **`data/chroma/`, `data/cache/`, `data/feedback.jsonl` are gitignored** —
  they're rebuilt/created locally. `chunks.jsonl` **is** committed, so you don't
  need the raw corpus to run retrieval.
- **Gemini quota:** ~20 req/day/key. If `/query` suddenly returns the escalation
  stub with `retrieval 100%`, you've hit the daily limit — add more keys or use
  the cache.
- `corpus/` folder names must not contain `:` (macOS artifact, fixed in `2a42196`).
- Don't `git add -A` from a stale branch — it can mass-delete `corpus/`
  (see [`CLAUDE.md`](CLAUDE.md)).

## 👥 Team & Contributors

- **Mudit Sonie**
- **Anuj Paroha**
- **Avishi Poddar**
- **Dewashish Lambore**
- **Kavish Nag**
- **Poorvi Dhall**
