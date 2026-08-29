# PRD — IP-SAKTI Sahayak (Tech Team)
**SIH 2026 | Problem Statement 26045 | Ministry of AYUSH — AIIA**
**Build window: 29 Aug – 1 Sep**

---

## 1. What we're building

A citation-grounded RAG assistant that answers Ayurveda IPR questions, backed by a real (small) legal corpus, with mandatory source citations, a confidence-based escalation path, a working jurisdiction toggle (India / International), and an ABS-compliance second-pass helper. No mocks on the core loop — every demoed answer must trace to a real statute/treaty section in our corpus.

**Non-goals for this build** (explicitly out of scope — do not spend time here):
- Knowledge graph / agentic multi-tool orchestration
- Multilingual or voice interface (mention as Phase 3 in the pitch only)
- Paid-source connectors (TKDL real access, subscription APIs)
- Any jurisdiction beyond India + (TRIPS, CBD/Nagoya) for International
- User auth/accounts, persistence across sessions

---

## 2. Locked architecture

### Query-time flow
```
User query
   → Formulation classifier (rule-based decision tree, 4-6 questions)
   → Jurisdiction toggle (India / International — user-selected, defaults to India)
   → Hybrid retrieval (BM25 + Chroma vector search)
        ├─ India query → India corpus (9 sources)
        └─ International query → thin corpus (TRIPS + CBD/Nagoya only)
   → [If query touches biological resources] ABS-helper second pass
        → narrow retrieval over Biological Diversity Act + Rules only
   → Grounded generation (Gemini, forced structured JSON output:
        { answer, citations: [{source, section}], self_confidence })
   → Confidence check (retrieval top-score threshold + self_confidence as secondary signal)
        ├─ above threshold → Cited answer (rendered as citation cards)
        └─ below threshold → Escalate state (human IP facilitator contact)
```

### One-time batch (ingestion — start Day 1, highest lead time)
```
11 source docs (9 India + TRIPS + CBD/Nagoya)
   → clean / OCR if needed
   → structure-aware chunking (by section/clause, NOT token windows)
   → metadata tagging (Act/Treaty name, section/article number, jurisdiction, date)
   → embed (bge-small-en or all-MiniLM-L6-v2, local) → index into Chroma + BM25
```

### Stack (all free-tier / local, zero cloud credits)
| Layer | Choice |
|---|---|
| LLM | Gemini Flash, multi-key rotation (reuse HackRx `brain.py` pattern) |
| Embeddings | `bge-small-en` or `all-MiniLM-L6-v2`, local via sentence-transformers |
| Sparse retrieval | `rank_bm25`, in-process |
| Vector store | Chroma, local/embedded |
| Backend | FastAPI |
| Frontend | React |
| Hosting (demo day) | Local machine, or free-tier Render / HF Spaces if a live link is wanted |

---

## 3. Corpus — MVP source list (11 documents)

**India (9):**
1. Patents Act, 1970 — Section 3(p) TK bar
2. Patents (Amendment) Rules, 2024
3. Biological Diversity Act, 2002 + (Amendment) Act, 2023
4. Biological Diversity Rules, 2024
5. Drugs and Cosmetics Act, 1940 + Rules, 1945
6. Drugs and Magic Remedies (Objectionable Advertisements) Act
7. FSSAI (Ayurveda Aahara) Regulations, 2022
8. GI Act, 1999
9. Trade Marks Act, 1999

**International (2, thin corpus):**
10. TRIPS Agreement
11. Convention on Biological Diversity + Nagoya Protocol

**Prior-art / TKDL substitute:** TKDL itself is access-restricted (patent examiners only, under Access Agreements) — do NOT attempt to scrape or fake real TKDL access. Build a small illustrative prior-art index instead from public-domain sources: Ayurvedic Pharmacopoeia of India entries, well-known classical formulations (Ashwagandharishta, Triphala churna, etc.). Frame this honestly in the demo as "illustrative index; production integrates via the official TKDL Access Agreement, as patent offices already do."

Sources: India Code (indiacode.nic.in), IP India (ipindia.gov.in), NBA (nbaindia.org), FSSAI, official gazette PDFs.

---

## 4. API contract (draft — refine once backend stubs exist, but frontend should build against this immediately)

### `POST /classify`
Runs the rule-based formulation classifier.
```json
// Request
{ "answers": { "q1": "...", "q2": "...", "...": "..." } }

// Response
{
  "formulation_category": "classical | proprietary | new_drug | phytopharmaceutical | ayurveda_aahar | cosmetic",
  "next_question": { "id": "q3", "text": "...", "options": ["...", "..."] } | null,
  "complete": true | false
}
```

### `POST /query`
Main RAG query endpoint.
```json
// Request
{
  "query": "string",
  "jurisdiction": "india | international",
  "formulation_category": "string (from /classify)"
}

// Response
{
  "answer": "string",
  "citations": [
    { "source": "Biological Diversity Act, 2002", "section": "Section 3", "excerpt_ref": "..." }
  ],
  "confidence": {
    "retrieval_score": 0.0,
    "self_confidence": "high | medium | low",
    "status": "answered | escalate"
  },
  "abs_flag": true | false,
  "abs_note": "string | null"
}
```

### `POST /abs-check` (only called internally by `/query` when `abs_flag` triggers — but expose as its own endpoint for testability)
```json
// Request
{ "query": "string", "formulation_category": "string" }

// Response
{ "triggered": true, "answer": "string", "citations": [ ... ] }
```

**Contract note:** frontend team should build all screens against these shapes with mock data starting Day 1 — do not wait for backend to be functional.

---

## 5. Confidence scoring — concrete method for MVP

Use **retrieval-score threshold as primary signal**, LLM self-reported confidence as secondary. Reasoning: retrieval-score is deterministic and defensible under judge questioning ("how do you know it's not hallucinating the confidence too?"); pure LLM self-assessment is not.

- If top retrieval hit (BM25/vector fused score) < threshold X → force `status: escalate` regardless of what the LLM says.
- If above threshold, still surface `self_confidence` from the LLM's structured output for UI nuance (e.g., "medium confidence" badge).
- Tune threshold X empirically during Day 4 spot-checks — start conservative (would rather over-escalate than show a wrong citation live).

---

## 6. Day-by-day (people-agnostic — internal team split, not prescribed here)

**Day 1 — 29th**
- Corpus sourcing/cleaning begins immediately (highest lead-time item).
- Backend scaffolding: FastAPI, retrieval infra (BM25 + Chroma), Gemini key rotation reused from HackRx.
- Frontend scaffolding: React shell, routing, screens built against the API contract above using mock JSON.
- **EOD target:** all 11 source docs identified and cleaning in progress; backend skeleton runs; frontend renders static screens against mock data.

**Day 2 — 30th**
- Core loop wired end-to-end with **real India-corpus data**: classifier → retrieval → generation → confidence → cited answer.
- This is the non-negotiable milestone. If not solid by EOD, everything else compresses — not the Day 4 buffer.
- Frontend swaps mock data for real API responses on the core flow.

**Day 3 — 31st**
- Jurisdiction toggle: wire in the thin International corpus (TRIPS + CBD/Nagoya).
- ABS-helper: second retrieval pass over Biological Diversity Act + Rules, triggered when query/formulation touches biological resources.
- Frontend: citation cards, confidence/escalate states, jurisdiction toggle UI, polish pass.

**Day 4 — 1st**
- Integration bug buffer.
- **Spot-check 10-15 sample Q&As against real source text** — this is the hallucination safety net, do not skip.
- Demo rehearsal, deployment for demo (local or live link), final fixes only.

---

## 7. Known risks (flag early if these bite)

- **Corpus chunking quality** is the single biggest risk to citation accuracy — worse than the retrieval or generation code. Legal text must be chunked by section/clause boundaries, not naive token windows, or citations will point to the wrong place.
- **ABS-helper trigger logic** (what counts as "touches biological resources") needs a simple, explainable rule — don't over-engineer; a keyword/category match off the formulation classifier output is enough for MVP.
- **Escalation threshold tuning** happens late (Day 4) by necessity — budget real time for it, don't treat it as a 10-minute afterthought.
