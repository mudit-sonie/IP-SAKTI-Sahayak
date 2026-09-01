"""Per-matter document retrieval lane (roadmap S20).

Each matter's uploaded documents get their own Chroma collection
(``matter_docs_<matter_id>``), separate from ``ip_sakti_corpus``. At query time
the pipeline runs this alongside the corpus retriever: corpus hits are the
citable passages; the top matter-doc hits are injected into the prompt as
background — never cited.

Degrades gracefully: if Chroma / the embedder aren't available, callers fall
back to the term-overlap scorer in ``matter_docs``.
"""
from __future__ import annotations

from app.config import get_settings
from app.core.logging import get_logger
from app.schemas import DocSnippet

logger = get_logger(__name__)

_client = None


def _chroma():
    global _client
    if _client is not None:
        return _client
    import os

    os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    _client = chromadb.PersistentClient(
        path=get_settings().chroma_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    return _client


def _embedder():
    try:
        from app.retrieval import get_retriever

        return get_retriever().embedder
    except Exception as exc:  # pragma: no cover
        logger.warning("doc-lane embedder unavailable: %s", exc)
        return None


def available() -> bool:
    try:
        return _embedder() is not None
    except Exception:  # pragma: no cover
        return False


def _collection(matter_id: str):
    return _chroma().get_or_create_collection(
        f"matter_docs_{matter_id}", metadata={"hnsw:space": "cosine"}
    )


def index_doc(matter_id: str, doc_id: str, filename: str, chunks: list[str]) -> bool:
    emb = _embedder()
    if emb is None or not chunks:
        return False
    try:
        col = _collection(matter_id)
        col.add(
            ids=[f"{doc_id}:{i}" for i in range(len(chunks))],
            embeddings=emb.encode(chunks, show_progress_bar=False).tolist(),
            documents=chunks,
            metadatas=[
                {"doc_id": doc_id, "filename": filename, "part": i}
                for i in range(len(chunks))
            ],
        )
        logger.info("indexed %d chunks for %s/%s", len(chunks), matter_id, doc_id)
        return True
    except Exception as exc:  # pragma: no cover
        logger.warning("doc index failed for %s/%s: %s", matter_id, doc_id, exc)
        return False


def remove_doc(matter_id: str, doc_id: str) -> None:
    try:
        _collection(matter_id).delete(where={"doc_id": doc_id})
    except Exception as exc:  # pragma: no cover
        logger.warning("doc unindex failed for %s/%s: %s", matter_id, doc_id, exc)


def drop_matter(matter_id: str) -> None:
    try:
        _chroma().delete_collection(f"matter_docs_{matter_id}")
    except Exception:  # pragma: no cover
        pass


def search(matter_id: str, query: str, k: int = 3) -> list[DocSnippet] | None:
    """Return top matter-doc snippets, or None if the lane is unavailable."""
    emb = _embedder()
    if emb is None:
        return None
    try:
        col = _collection(matter_id)
        if col.count() == 0:
            return []
        res = col.query(
            query_embeddings=emb.encode([query]).tolist(),
            n_results=min(k, col.count()),
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("doc search failed for %s: %s", matter_id, exc)
        return None
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    out: list[DocSnippet] = []
    for text, meta, dist in zip(docs, metas, dists):
        if float(dist) > 0.75:  # cosine distance — drop weak matches
            continue
        part = int(meta.get("part", 0))
        out.append(DocSnippet(
            doc_id=str(meta.get("doc_id", "")),
            filename=str(meta.get("filename", "document")),
            locator=f"{meta.get('filename', 'document')} — part {part + 1}",
            text=text.strip()[:700],
        ))
    return out
