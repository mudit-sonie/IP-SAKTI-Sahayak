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
    gemini_model: str = Field(default="gemini-3.5-flash", alias="GEMINI_MODEL")

    # --- Retrieval ---
    embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5", alias="EMBEDDING_MODEL"
    )
    chroma_dir: str = Field(default="./data/chroma", alias="CHROMA_DIR")
    corpus_chunks_path: str = Field(
        default="./data/processed/chunks.jsonl", alias="CORPUS_CHUNKS_PATH"
    )
    retrieval_escalate_threshold: float = Field(
        default=0.35, alias="RETRIEVAL_ESCALATE_THRESHOLD"
    )
    hybrid_bm25_weight: float = Field(default=0.5, alias="HYBRID_BM25_WEIGHT")

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
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
