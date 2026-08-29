"""Build / refresh the retrieval indices from the processed corpus.

    python -m scripts.build_index

Reads CORPUS_CHUNKS_PATH (chunks.jsonl from the legal-corpus-ingestion pipeline),
constructs the BM25 index in memory and embeds any new chunks into the persistent
Chroma store under CHROMA_DIR. Safe to re-run; already-embedded chunk ids are
skipped.

This is a thin wrapper — the real work lives in app.retrieval. Kept as a script so
ingestion can call it as the last pipeline step without importing the web app.
"""
from __future__ import annotations

import sys

from app.core.logging import get_logger
from app.retrieval.corpus import load_chunks
from app.retrieval.hybrid import HybridRetriever

logger = get_logger("build_index")


def main() -> int:
    chunks = load_chunks()
    if not chunks:
        logger.error(
            "no chunks loaded — has the ingestion pipeline produced chunks.jsonl yet?"
        )
        return 1
    retriever = HybridRetriever(chunks)
    sample, top = retriever.retrieve("traditional knowledge patent bar", top_k=3)
    logger.info("index build OK: %d chunks, smoke query top_score=%.3f", len(chunks), top)
    for rc in sample:
        logger.info("  %s | %s %s", rc.chunk.source, rc.chunk.section, round(rc.score, 3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
