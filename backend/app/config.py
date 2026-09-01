"""Runtime configuration, loaded from environment / backend/.env.

Keep this the single source of truth for tunables. The retrieval threshold in
particular gets tuned during Day 4 spot-checks — do it here, not scattered in code.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Gemini ---
    gemini_api_keys: str = Field(default="", alias="GEMINI_API_KEYS")
    # Free tier is ~20 requests/day PER MODEL PER KEY (Google tightened this).
    # gemini-3.5-flash-lite is current, fast, and fine for grounded QA over
    # supplied context. Real fix for demo volume: multiple keys in
    # GEMINI_API_KEYS — the client rotates on 429. Each key/model is its own bucket.
    gemini_model: str = Field(default="gemini-3.5-flash-lite", alias="GEMINI_MODEL")

    # --- Retrieval ---
    embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5", alias="EMBEDDING_MODEL"
    )
    # "auto" picks cuda when a CUDA-enabled torch sees a GPU, else cpu. Force with
    # "cuda" / "cpu". CUDA needs a GPU torch build — see backend/requirements-gpu.txt.
    embedding_device: str = Field(default="auto", alias="EMBEDDING_DEVICE")
    chroma_dir: str = Field(default="./data/chroma", alias="CHROMA_DIR")
    corpus_chunks_path: str = Field(
        default="./data/processed/chunks.jsonl", alias="CORPUS_CHUNKS_PATH"
    )
    retrieval_escalate_threshold: float = Field(
        default=0.35, alias="RETRIEVAL_ESCALATE_THRESHOLD"
    )
    hybrid_bm25_weight: float = Field(default=0.5, alias="HYBRID_BM25_WEIGHT")

    # --- Corpus coverage (S4) ---
    # Known gaps surfaced on the Coverage screen. These are areas users will ask
    # about that today's corpus cannot answer — be honest about them up front.
    # Pipe-separated so commas can appear inside an item.
    corpus_known_gaps: str = Field(
        default=(
            "CBD / Nagoya Protocol full text not yet ingested — international ABS "
            "answers lean on TRIPS and the Indian Biological Diversity Act only|"
            "No case law / judicial interpretation in the corpus (S14)|"
            "No state-level ASU&H licensing rules (S13)|"
            "Amendment history and in-force dates not tracked — provisions are "
            "treated as current (S6)|"
            "TKDL prior-art database not connected (S12)|"
            "English source text only; no regional-language statutes (S15)"
        ),
        alias="CORPUS_KNOWN_GAPS",
    )
    # A source with fewer than this many chunks is flagged as thin coverage.
    corpus_thin_source_threshold: int = Field(
        default=5, alias="CORPUS_THIN_SOURCE_THRESHOLD"
    )
    # --- Amendment awareness (S6, scaffold) ---
    # Optional overlay of currency dates + per-provision amendment notes, merged
    # onto chunk metadata at load. Absent by default — amendment history is not
    # in the corpus yet; this is the curation hook. See the .example file.
    amendment_overlay_path: str = Field(
        default="./data/amendments.json", alias="AMENDMENT_OVERLAY_PATH"
    )

    # --- Query cache ---
    # On-disk cache of /query responses, keyed by (query, jurisdiction, category).
    # Lets a demo run gold questions for free and survive Gemini's daily quota.
    query_cache_enabled: bool = Field(default=True, alias="QUERY_CACHE_ENABLED")
    query_cache_dir: str = Field(
        default="./data/cache/query", alias="QUERY_CACHE_DIR"
    )

    # --- Workspace persistence (JSON documents on disk — see PRODUCT_ROADMAP.md) ---
    # Root for the matter / escalation / faq stores. One JSON file per aggregate,
    # written atomically. No DB by design: the app must run on any laptop.
    data_dir: str = Field(default="./data", alias="DATA_DIR")
    matters_enabled: bool = Field(default=True, alias="MATTERS_ENABLED")
    # TKDL prior-art cross-check (S12, scaffold). The Traditional Knowledge
    # Digital Library is access-controlled; no public connector exists. Until a
    # deployment wires one, tkdl_check always reports "not connected" and never
    # fabricates a hit.
    tkdl_enabled: bool = Field(default=False, alias="TKDL_ENABLED")
    tkdl_api_url: str = Field(default="", alias="TKDL_API_URL")

    # State-level ASU&H rules (S13, scaffold). Optional per-state overlay of extra
    # rule notes: data/state_rules/<state_key>.json. Absent by default.
    state_rules_dir: str = Field(default="", alias="STATE_RULES_DIR")

    # Facilitator queue + reviewed FAQ (S5). When escalations_enabled, every
    # escalate response is persisted for a human to answer; a published FAQ
    # answer is served ahead of the model on a matching question.
    # Anonymized usage analytics (S16). Aggregate counters only — no query text,
    # no PII. Persisted to data/analytics.json.
    analytics_enabled: bool = Field(default=True, alias="ANALYTICS_ENABLED")

    escalations_enabled: bool = Field(default=True, alias="ESCALATIONS_ENABLED")
    faq_enabled: bool = Field(default=True, alias="FAQ_ENABLED")
    # Min token-overlap (Jaccard) for a FAQ entry to short-circuit a query.
    faq_match_threshold: float = Field(default=0.6, alias="FAQ_MATCH_THRESHOLD")
    # Rendered document drafts (S8): data/drafts/<matter_id>/<draft_id>.md
    drafts_dir: str = Field(default="./data/drafts", alias="DRAFTS_DIR")
    # Local single-user mode: every record is stamped with this owner id. When
    # real auth arrives it becomes the authenticated user id.
    local_owner: str = Field(default="local", alias="LOCAL_OWNER")

    # --- App ---
    app_env: str = Field(default="dev", alias="APP_ENV")
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000", alias="CORS_ORIGINS"
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def gemini_key_list(self) -> list[str]:
        return [k.strip() for k in self.gemini_api_keys.split(",") if k.strip()]

    @property
    def corpus_known_gaps_list(self) -> list[str]:
        return [g.strip() for g in self.corpus_known_gaps.split("|") if g.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
