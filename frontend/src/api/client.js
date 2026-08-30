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

// POST /feedback -> { ok: true }
export function sendFeedback(payload, opts) {
  return postJson("/feedback", payload, opts);
}

export { BASE_URL };
