# IP-SAKTI Sahayak — Product Roadmap

> Built on branch `feature/product-roadmap`. This tracks the shift from
> "cited Q&A demo" to **the compliance workspace for taking an Ayurveda
> formulation from bench to market**.

The cited Q&A is the entry point. Retention comes from a persistent **matter**
(a formulation profile) that accumulates its ABS status, a generated compliance
checklist, cited document drafts, and deadlines.

## Architecture decisions (locked)

| Decision | Choice | Rationale |
|---|---|---|
| Persistence | **JSON documents on disk**, one file per aggregate, atomic write (temp + `os.replace`), advisory lock per aggregate | No infra; runs on any laptop; matches existing `query_cache.py` / `feedback.py` conventions. Swappable behind `app/store/`. |
| Auth | **Single implicit local user** (`owner="local"`), no login | Keeps the demo frictionless; real auth is its own future slice. All records carry an `owner` field so multi-user is an additive change. |
| Data-gated features | **Scaffold + ingestion hook now, real data later** | Amendment dates, TKDL, case law, state rules, multi-language need sources not in today's corpus. Build schema + API + UI + a marked ingestion entry point; never emit a fake answer on the core loop (CLAUDE.md). |

## Storage layout

```
backend/data/
  matters/<matter_id>.json        one document per matter (aggregate: profile,
                                  checklist items, deadlines, question history,
                                  drafts, audit trail)
  escalations/<escalation_id>.json facilitator queue entries
  faq/<faq_id>.json                human-reviewed answers, retrieved first
  drafts/                          rendered document drafts (md + pdf)
```

`app/store/` — generic `JsonStore` (get / put / list / delete, atomic, locked)
+ typed repositories (`MatterRepo`, `EscalationRepo`, `FaqRepo`).

## Slices

Each slice is a self-contained commit: schema + service + route + tests + UI.

### Foundation
- [x] **S0 — store layer**: `app/store/json_store.py` (atomic + locked), config
      (`DATA_DIR`, `*_enabled`), `MatterRepo`.
- [x] **S1 — matters**: `Matter` aggregate, CRUD API (`/matters`), Matters list
      + Matter detail screens, "Save as a matter" from the classifier.
- [x] **S1+ — formulation profile + classify-in-place**: `MatterProfile` fed as
      background into every question in the matter (never a citation);
      `/classify?matter=<id>` writes the classification back.

### Grounding moat (near-term)
- [x] **S2 — per-claim citations**: generation returns `claims[]` (`text` +
      `citations[]` indices) with inline `[n]` markers in `answer`; markers
      resolve to retrieved passages (a relied-upon passage the model omits from
      its citation list is appended, since it was still retrieved); Result
      renders footnote markers linked to the passage drawer.
- [x] **S3 — conflict surfacing**: generation returns `conflicts[] {topic,
      positions[] {summary, citations[]}}`; kept only when >=2 positions cite
      >=2 distinct instruments; a "Divergent positions" card on Result.
- [x] **S4 — corpus coverage map**: `GET /corpus` (per-source chunk/section
      counts, metadata, thin-coverage flag, configured + derived known gaps);
      `services/coverage.py`; a Coverage screen + nav link; "outside our corpus"
      note on Result when an escalation retrieved nothing on point. `as_of`
      lands with S6.
- [ ] **S5 — facilitator queue + reviewed FAQ**: escalations persist to a queue;
      a facilitator view answers them; reviewed answers land in `faq/` and are
      retrieved ahead of the model on matching questions.
- [x] **S6 — amendment awareness (scaffold)**: `as_of` / `amended_by` /
      `in_force` + `is_stale` on `Chunk`, merged from a curated overlay
      (`data/amendments.json`, `AMENDMENT_OVERLAY_PATH`) at corpus load — the
      ingestion hook, since amendment history isn't in the corpus. `Citation`
      and `ChunkResponse` carry `as_of` / `amended_by`; `/corpus` sources carry
      `as_of`. Result shows a "cited provision may have been amended" card + the
      passage drawer and export note it. Shipped overlay flags Biological
      Diversity Act ss.6/7/40 (BD Amendment Act, 2023) and Patents Rules 2003
      currency.

### Workflow layer (retention)
- [x] **S7 — compliance checklist**: rule-driven generator keyed on category +
      jurisdiction + ABS flag; tracked items with status + real citations
      (retrieval-grounded, score-gated); Checklist tab on the Matter screen.
- [x] **S8 — cited document drafts**: `services/drafts.py` — deterministic
      templates (Form 1 skeleton, NBA ABS application, disclosure-of-source,
      §3(p)/(e) argument), filled from the matter profile; every legal assertion
      carries a `[Legal basis: …]` marker grounded (score-gated) to a retrieved
      section, listed under "Traceability". `POST/GET/DELETE
      /matters/{id}/drafts[/{draft_id}]`, `GET /draft-kinds`; md persisted under
      `data/drafts/<matter>/`, re-rendered if the file is lost. Documents tab on
      the Matter screen.
- [x] **S9 — deadlines**: `services/deadlines.py` — from one anchor date the
      user supplies (patent filing / priority, TM / GI application) derive the
      statutory windows (RFE, renewals, term, convention/PCT, TM exam reply),
      each grounded where the corpus allows; plus manual entries. `POST
      /matters/{id}/deadlines/derive`, `POST/PATCH/DELETE
      /matters/{id}/deadlines[/{id}]`. Deadlines tab with overdue / due-soon
      flagging; re-derivation preserves the done flag per rule.
- [x] **S10 — comparison mode**: `POST /compare` runs the pipeline for both
      jurisdictions; a Compare screen renders India / International side by side
      (answer, confidence, ABS flag, citations), reached from any answer.
- [ ] **S11 — fee calculators**: patent fees by entity size, GI fees — a small
      rules table + a calculator widget.

### AYUSH-scale (scaffold now)
- [ ] **S12 — TKDL / prior-art cross-check**: `tkdl_check` service with a clearly
      marked data hook; UI slot on the Matter screen; honest "not connected yet".
- [ ] **S13 — state-level rules**: jurisdiction gains an optional `state`; ASU&H
      licensing authority table; ingestion hook for state rules.
- [ ] **S14 — case-law layer**: `document_type: "case"` support in corpus +
      retrieval; a "How courts have applied this" block.
- [ ] **S15 — multi-language**: i18n scaffold (frontend string catalog + a
      `lang` param that translates the *answer* post-generation, citations stay
      verbatim English source text).
- [ ] **S16 — anonymized analytics**: aggregate question/topic counts to a
      `/analytics` summary (no PII); a lightweight dashboard.
- [ ] **S20 — matter documents as context**: user attaches their own documents
      to a matter; read for context, never cited. Separate retrieval lane +
      per-matter Chroma namespace. Full spec under "Deep context" below.

### Trust & safety (non-negotiable before public)
- [x] **S17 — FTO / infringement always-escalate**: `services/safety.py` forces
      `status: escalate` in the pipeline before generation for high-stakes
      question types, regardless of retrieval score.
- [x] **S18 — answer export**: timestamped Markdown of an answer with citations
      + source URLs, as a file download (`GET .../questions/{qid}/export`).
      PDF rendering can layer on later.
- [x] **S19 — audit log**: append-only trail per matter, surfaced on the
      Activity tab.

### Deep context
- [ ] **S20 — matter documents as context**: the user attaches their own
      documents to a matter (draft patent claims, product dossier, label
      artwork text, lab report, prior NBA correspondence). The assistant reads
      them to understand *what is being asked about* — it never cites them.

  **The hard rule.** User documents feed generation context only. `citations[]`
  stays corpus-only. This is the same separation as the formulation profile
  (S1+), just richer — the moat is "every citation traces to authoritative law",
  and a user's draft is not law.

  **Storage.** Per-matter, local only: `data/matters/<id>/docs/<doc_id>.<ext>`
  for the original + `.../docs/<doc_id>.json` for extracted text + chunks.
  Gitignored. Not in logs. Needs an explicit local-only data statement in the
  UI — today's disclaimer says "do not enter confidential data" and this
  feature deliberately invites it.

  **Ingestion.** PDF / DOCX / TXT → text extraction (reuse the PDF path from the
  `legal-corpus-ingestion` skill; add a DOCX reader) → section/paragraph
  chunking (looser than the statute chunker — these aren't legal instruments)
  → embed into a **matter-namespaced Chroma collection**
  (`matter_docs_<matter_id>`), separate from `ip_sakti_corpus`. Runs async on
  upload; the doc shows `status: processing | ready | failed`.

  **Retrieval lane.** New `DocRetriever(matter_id)` alongside `HybridRetriever`.
  At query time the pipeline runs both: corpus hits become the citable
  passages; the top matter-doc hits are injected into the prompt as
  `"From the user's own documents (background, not a source of law): …"`,
  each tagged with the doc name + location so the answer can say "your draft
  section 4 states X, but section 3(p) of the Patents Act …".

  **Schema.** `MatterDocument{ id, filename, media_type, bytes, uploaded_at,
  status, page_count, chunk_count, error? }`; `Matter.documents: list[...]`.
  `QueryResponse` gains `doc_context: list[DocSnippet{ doc_id, filename,
  locator, text }]` so the UI can show what the answer leaned on, visually
  distinct from citations.

  **API.** `POST /matters/{id}/documents` (multipart upload),
  `GET /matters/{id}/documents`, `GET /matters/{id}/documents/{doc_id}` (text +
  chunks), `DELETE /matters/{id}/documents/{doc_id}`. Config:
  `MATTER_DOCS_ENABLED`, `MATTER_DOCS_MAX_MB`, allowed media types.

  **Frontend.** A Documents tab on the Matter screen: drag-drop upload, per-doc
  status, remove. On an answer, a "Grounded partly in your documents" strip
  listing the `doc_context` snippets under the citations block, clearly not
  styled as citations.

  **Risks / open questions.** OCR for scanned PDFs (defer — accept text PDFs
  first); size and count limits; whether a stale doc chunk can mislead the
  model (mitigate with the explicit "not a source of law" framing + always
  showing which snippets were used); no cross-matter document reuse in this
  slice (a shared "project" tier is a separate future item, only meaningful
  once multi-user auth exists).

## Non-goals for this branch

Real authentication, Postgres, payment, the expert marketplace, push
notifications, offline mode. Additive later.
