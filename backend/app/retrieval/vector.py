"""Chroma vector index over the corpus, embedded locally with sentence-transformers.

Kept lazy and optional: if chromadb / sentence-transformers aren't installed or the
model can't be downloaded, this disables itself and hybrid retrieval falls back to
BM25 only. That keeps the backend importable on Day 1 before models are pulled.
"""
from __future__ import annotations

from app.config import get_settings
from app.core.logging import get_logger
from app.retrieval.corpus import Chunk

logger = get_logger(__name__)

_COLLECTION = "ip_sakti_corpus"


class VectorIndex:
    def __init__(self, chunks: list[Chunk]) -> None:
        self._chunks_by_id = {c.chunk_id: c for c in chunks}
        self._collection = None
        self._embedder = None
        if not chunks:
            return
        try:
            self._build(chunks)
        except Exception as exc:  # pragma: no cover - optional dep / offline
            logger.warning("vector index unavailable (%s); using BM25 only", exc)

    def _build(self, chunks: list[Chunk]) -> None:
        import os

        os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        from sentence_transformers import SentenceTransformer

        settings = get_settings()
        device = settings.embedding_device
        if device == "auto":
            try:
                import torch

                device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:  # pragma: no cover - torch always present via ST
                device = "cpu"
        self._embedder = SentenceTransformer(settings.embedding_model, device=device)
        logger.info("embedding model %s on device=%s", settings.embedding_model, device)
        client = chromadb.PersistentClient(
            path=settings.chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = client.get_or_create_collection(
            _COLLECTION, metadata={"hnsw:space": "cosine"}
        )

        existing = set(self._collection.get().get("ids", []))
        pending = [c for c in chunks if c.chunk_id not in existing]
        if pending:
            embeddings = self._embedder.encode(
                [c.text for c in pending], show_progress_bar=False
            ).tolist()
            self._collection.add(
                ids=[c.chunk_id for c in pending],
                embeddings=embeddings,
                documents=[c.text for c in pending],
                metadatas=[{"source": c.source, "section": c.section} for c in pending],
            )
            logger.info("embedded %d new chunks into Chroma", len(pending))

    @property
    def ready(self) -> bool:
        return self._collection is not None and self._embedder is not None

    def search(self, query: str, top_k: int) -> list[tuple[Chunk, float]]:
        if not self.ready:
            return []
        q_emb = self._embedder.encode([query]).tolist()
        res = self._collection.query(query_embeddings=q_emb, n_results=top_k)
        ids = (res.get("ids") or [[]])[0]
        distances = (res.get("distances") or [[]])[0]
        out: list[tuple[Chunk, float]] = []
        for cid, dist in zip(ids, distances):
            chunk = self._chunks_by_id.get(cid)
            if chunk is None:
                continue
            # cosine distance -> similarity in [0, 1]
            out.append((chunk, max(0.0, 1.0 - float(dist))))
        return out
