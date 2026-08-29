"""In-process BM25 sparse index over the corpus (rank_bm25)."""
from __future__ import annotations

import re

from app.core.logging import get_logger
from app.retrieval.corpus import Chunk

logger = get_logger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:\([a-z0-9]+\))?", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens, keeping section-style tokens like ``3(p)`` intact.

    Legal stopwords (shall / may / not / except ...) are deliberately NOT removed
    - they carry meaning in statute text.
    """
    return [t.lower() for t in _TOKEN_RE.findall(text)]


class BM25Index:
    def __init__(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks
        self._bm25 = None
        if not chunks:
            return
        try:
            from rank_bm25 import BM25Okapi

            self._bm25 = BM25Okapi([tokenize(c.text) for c in chunks])
        except Exception as exc:  # pragma: no cover
            logger.warning("BM25 unavailable (%s); sparse retrieval disabled", exc)

    @property
    def ready(self) -> bool:
        return self._bm25 is not None

    def search(self, query: str, top_k: int) -> list[tuple[Chunk, float]]:
        if not self.ready:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(
            zip(self._chunks, scores), key=lambda kv: kv[1], reverse=True
        )
        return [(c, float(s)) for c, s in ranked[:top_k] if s > 0]
