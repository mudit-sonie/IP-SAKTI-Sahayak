// Thin client for the IP-SAKTI Sahayak backend (PRD §4).
// Response shapes are defined by backend/app/schemas.py — treat changes there
// as breaking and update this file + the screens that read it.

const BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message, { status, cause } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.cause = cause;
  }
}

async function postJson(path, body, { signal } = {}) {
  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if (err.name === "AbortError") throw err;
    throw new ApiError(
      `Could not reach the IP-SAKTI backend at ${BASE_URL}. Is it running (uvicorn app.main:app)?`,
      { cause: err },
    );
  }
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new ApiError(
      `Backend returned ${res.status}${detail ? `: ${detail.slice(0, 300)}` : ""}`,
      { status: res.status },
    );
  }
  return res.json();
}

export function getHealth({ signal } = {}) {
  return fetch(`${BASE_URL}/health`, { signal }).then((r) => r.json());
}

// GET /chunk/{id} -> { chunk_id, text, source, section, citation, source_url, ... }
// The exact statute passage behind a citation's excerpt_ref.
export async function getChunk(chunkId, { signal } = {}) {
  const res = await fetch(
    `${BASE_URL}/chunk/${encodeURIComponent(chunkId)}`,
    { signal },
  );
  if (!res.ok) {
    throw new ApiError(`Could not load passage (${res.status})`, {
      status: res.status,
    });
  }
  return res.json();
}

// POST /classify — stateless. Send the full answers dict each call; the response
// is either { next_question } or { formulation_category, complete: true }.
export function classify(answers, opts) {
  return postJson("/classify", { answers }, opts);
}

// POST /query — the main RAG call.
// -> { answer, citations[{source,section,excerpt_ref}], confidence{retrieval_score,
//      self_confidence,status}, abs_flag, abs_note }
export function query(
  { query: q, jurisdiction = "india", formulationCategory = null },
  opts,
) {
  return postJson(
    "/query",
    {
      query: q,
      jurisdiction,
      formulation_category: formulationCategory,
    },
    opts,
  );
}

// GET /corpus -> CorpusCoverage { generated_at, corpus_loaded, chunk_count,
//   source_count, jurisdictions, sources[{source, jurisdiction, document_type,
//   organization, source_url, year, chunk_count, section_count, sections[], thin}],
//   known_gaps[] }
export async function getCorpus({ signal } = {}) {
  const res = await fetch(`${BASE_URL}/corpus`, { signal });
  if (!res.ok) {
    throw new ApiError(`Could not load corpus coverage (${res.status})`, {
      status: res.status,
    });
  }
  return res.json();
}

// GET /state-rules -> { as_of, note, authorities: [{ key, state, authority,
//   portal_url, note }] }
export async function getStateRules({ signal } = {}) {
  const res = await fetch(`${BASE_URL}/state-rules`, { signal });
  if (!res.ok) throw new ApiError(`Could not load state rules (${res.status})`);
  return res.json();
}

// GET /fees -> { disclaimer, schedules: [{ track, title, as_of, source, source_url,
//   entities[], items[], renewal_bands[], notes[] }] }
export async function getFees({ signal } = {}) {
  const res = await fetch(`${BASE_URL}/fees`, { signal });
  if (!res.ok) throw new ApiError(`Could not load fee schedules (${res.status})`);
  return res.json();
}

// POST /compare -> { query, india: QueryResponse, international: QueryResponse }
export function compare(
  { query: q, formulationCategory = null, context = null },
  opts,
) {
  return postJson(
    "/compare",
    { query: q, formulation_category: formulationCategory, context },
    opts,
  );
}

// POST /feedback -> { ok: true }
export function sendFeedback(payload, opts) {
  return postJson("/feedback", payload, opts);
}

// --------------------------------------------------------------------------- //
// Matters — the persistent workspace (see PRODUCT_ROADMAP.md)
// --------------------------------------------------------------------------- //
async function reqJson(path, { method = "GET", body, signal } = {}) {
  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (err) {
    if (err.name === "AbortError") throw err;
    throw new ApiError(
      `Could not reach the IP-SAKTI backend at ${BASE_URL}. Is it running?`,
      { cause: err },
    );
  }
  if (res.status === 204) return null;
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new ApiError(
      `Backend returned ${res.status}${detail ? `: ${detail.slice(0, 300)}` : ""}`,
      { status: res.status },
    );
  }
  return res.json();
}

export const matters = {
  list: (opts) => reqJson("/matters", opts),
  get: (id, opts) => reqJson(`/matters/${id}`, opts),
  create: (payload, opts) =>
    reqJson("/matters", { method: "POST", body: payload, ...opts }),
  update: (id, payload, opts) =>
    reqJson(`/matters/${id}`, { method: "PATCH", body: payload, ...opts }),
  remove: (id, opts) =>
    reqJson(`/matters/${id}`, { method: "DELETE", ...opts }),
  ask: (id, payload, opts) =>
    reqJson(`/matters/${id}/questions`, {
      method: "POST",
      body: payload,
      ...opts,
    }),
  regenerateChecklist: (id, opts) =>
    reqJson(`/matters/${id}/checklist`, { method: "POST", ...opts }),
  addChecklistItem: (id, payload, opts) =>
    reqJson(`/matters/${id}/checklist/items`, {
      method: "POST",
      body: payload,
      ...opts,
    }),
  setChecklistStatus: (id, itemId, status, opts) =>
    reqJson(`/matters/${id}/checklist/${itemId}`, {
      method: "PATCH",
      body: { status },
      ...opts,
    }),
  // TKDL / prior-art cross-check (S12)
  tkdlCheck: (id, opts) =>
    reqJson(`/matters/${id}/tkdl-check`, { method: "POST", ...opts }),
  // Deadlines (S9)
  deriveDeadlines: (id, anchor, anchorDate, opts) =>
    reqJson(`/matters/${id}/deadlines/derive`, {
      method: "POST",
      body: { anchor, anchor_date: anchorDate },
      ...opts,
    }),
  addDeadline: (id, payload, opts) =>
    reqJson(`/matters/${id}/deadlines`, {
      method: "POST",
      body: payload,
      ...opts,
    }),
  setDeadlineDone: (id, deadlineId, done, opts) =>
    reqJson(`/matters/${id}/deadlines/${deadlineId}`, {
      method: "PATCH",
      body: { done },
      ...opts,
    }),
  deleteDeadline: (id, deadlineId, opts) =>
    reqJson(`/matters/${id}/deadlines/${deadlineId}`, {
      method: "DELETE",
      ...opts,
    }),
  // Document drafts (S8)
  draftKinds: (opts) => reqJson("/draft-kinds", opts),
  createDraft: (id, kind, opts) =>
    reqJson(`/matters/${id}/drafts`, { method: "POST", body: { kind }, ...opts }),
  deleteDraft: (id, draftId, opts) =>
    reqJson(`/matters/${id}/drafts/${draftId}`, { method: "DELETE", ...opts }),
  draftUrl: (id, draftId) => `${BASE_URL}/matters/${id}/drafts/${draftId}`,
};

// --------------------------------------------------------------------------- //
// Facilitator queue + reviewed FAQ (S5)
// --------------------------------------------------------------------------- //
export const facilitator = {
  listEscalations: (status, opts) =>
    reqJson(
      `/escalations${status ? `?status=${encodeURIComponent(status)}` : ""}`,
      opts,
    ),
  answerEscalation: (id, payload, opts) =>
    reqJson(`/escalations/${id}/answer`, {
      method: "POST",
      body: payload,
      ...opts,
    }),
  dismissEscalation: (id, opts) =>
    reqJson(`/escalations/${id}/dismiss`, { method: "POST", ...opts }),
  listFaq: (opts) => reqJson("/faq", opts),
  createFaq: (payload, opts) =>
    reqJson("/faq", { method: "POST", body: payload, ...opts }),
  deleteFaq: (id, opts) =>
    reqJson(`/faq/${id}`, { method: "DELETE", ...opts }),
};

export { BASE_URL };
