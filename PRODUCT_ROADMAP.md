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
- [ ] **S1 — matters**: `Matter` aggregate, CRUD API (`/matters`), Matters list
      + Matter detail screens, thread classify→ask→result into a matter.

### Grounding moat (near-term)
- [ ] **S2 — per-claim citations**: generation returns `claims[]` with inline
      `[n]` markers; Result renders footnote markers linked to passages.
- [ ] **S3 — conflict surfacing**: when retrieved passages from different
      instruments give divergent positions, return both under `conflicts[]`.
- [ ] **S4 — corpus coverage map**: `/corpus` endpoint (sources, sections,
      `as_of`, known gaps); a Coverage screen; "outside our corpus" banner.
- [ ] **S5 — facilitator queue + reviewed FAQ**: escalations persist to a queue;
      a facilitator view answers them; reviewed answers land in `faq/` and are
      retrieved ahead of the model on matching questions.
- [ ] **S6 — amendment awareness (scaffold)**: `as_of` / `amended_by` /
      `in_force` optional metadata on `Chunk`; ingestion hook; Citation carries
      `as_of`; Result shows "as of <date>" and a stale-provision warning.

### Workflow layer (retention)
- [ ] **S7 — compliance checklist**: rule-driven generator keyed on category +
      jurisdiction + ABS flag; tracked items with status + citations; on the
      Matter screen.
- [ ] **S8 — cited document drafts**: templates (Form 1 skeleton, NBA ABS
      application, disclosure-of-source, §3(p) rebuttal); filled from the matter;
      every clause traceable to a section.
- [ ] **S9 — deadlines**: derived (renewal schedules, filing windows) + manual;
      on the Matter screen; simple due-soon flagging.
- [ ] **S10 — comparison mode**: run two jurisdictions for one question,
      rendered side by side.
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

### Trust & safety (non-negotiable before public)
- [ ] **S17 — FTO / infringement always-escalate**: a classifier for
      high-stakes question types that forces `status: escalate` regardless of
      retrieval score.
- [ ] **S18 — answer export**: timestamped PDF of an answer with citations, for
      the user's filing records.
- [ ] **S19 — audit log**: append-only trail per matter (every question, answer,
      status, checklist change, draft render).

## Non-goals for this branch

Real authentication, Postgres, payment, the expert marketplace, push
notifications, offline mode. Additive later.
