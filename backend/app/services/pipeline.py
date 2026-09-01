"""Query-time orchestration (PRD section 2 flow).

    retrieve (jurisdiction-routed)
      -> generate (grounded, structured JSON)
      -> confidence check (retrieval threshold primary)
      -> [if ABS-triggered] second pass over Biological Diversity Act + Rules
      -> assemble QueryResponse
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.retrieval import get_retriever
from app.retrieval.expansion import expand_query
from app.schemas import (
    AnswerStatus,
    Confidence,
    QueryRequest,
    QueryResponse,
    RetrievalInfo,
    SelfConfidence,
)
from app.services import abs_helper, confidence, generation, query_cache, safety
from app.services.jurisdiction import mismatch_note

logger = get_logger(__name__)


def run_query(req: QueryRequest, *, use_cache: bool = True) -> QueryResponse:
    if use_cache:
        hit = query_cache.get(req)
        if hit is not None:
            logger.info("query cache hit: %r", req.query)
            return hit

    resp = _run_query_uncached(req)
    query_cache.put(req, resp)
    return resp


def _run_query_uncached(req: QueryRequest) -> QueryResponse:
    retriever = get_retriever()
    retrieval_query = expand_query(req.query)
    if retrieval_query != req.query:
        logger.info("query expanded for retrieval: %r", retrieval_query)
    chunks, top_score = retriever.retrieve(
        retrieval_query,
        jurisdiction=req.jurisdiction.value,
        top_k=6,
    )

    pool_n, pool_sources = retriever.jurisdiction_scope(req.jurisdiction.value)
    retrieval_info = RetrievalInfo(
        jurisdiction=req.jurisdiction.value,
        expanded_query=retrieval_query if retrieval_query != req.query else None,
        passages_searched=pool_n,
        sources_searched=pool_sources,
        top_sections=[
            f"{rc.chunk.source.split(',')[0]} — Section {rc.chunk.section}"
            for rc in chunks[:5]
            if rc.chunk.section
        ],
    )

    # High-stakes questions (FTO / infringement / "is my product legal") never
    # get a retrieval answer, however good the retrieval looks — they escalate.
    if safety.is_high_stakes(req.query):
        logger.info("high-stakes question — forced escalate: %r", req.query)
        return QueryResponse(
            answer=safety.ESCALATE_NOTE,
            citations=[],
            confidence=Confidence(
                retrieval_score=top_score,
                self_confidence=SelfConfidence.low,
                status=AnswerStatus.escalate,
            ),
            jurisdiction_note=mismatch_note(req.query, req.jurisdiction.value),
            retrieval=retrieval_info,
        )

    gen = generation.generate(req.query, chunks, context=req.context)
    conf = confidence.score(
        top_score, gen.self_confidence, has_citations=bool(gen.citations)
    )

    abs_result = abs_helper.run(req.query, req.formulation_category)
    abs_note = abs_result.note if abs_result.triggered else None

    # Fold ABS citations in so the UI can render them alongside the main answer.
    citations = list(gen.citations)
    if abs_result.triggered and abs_result.citations:
        seen = {(c.source, c.section) for c in citations}
        for c in abs_result.citations:
            if (c.source, c.section) not in seen:
                citations.append(c)

    answer = gen.answer
    if conf.status == AnswerStatus.escalate and abs_result.triggered and abs_result.answer:
        # Retrieval was weak on the main pass but ABS pass found something concrete.
        answer = (
            f"{gen.answer}\n\nABS note: {abs_result.answer}"
            if gen.answer
            else abs_result.answer
        )

    return QueryResponse(
        answer=answer,
        citations=citations,
        claims=gen.claims,
        conflicts=gen.conflicts,
        confidence=conf,
        abs_flag=abs_result.triggered,
        abs_note=abs_note,
        jurisdiction_note=mismatch_note(req.query, req.jurisdiction.value),
        retrieval=retrieval_info,
    )
