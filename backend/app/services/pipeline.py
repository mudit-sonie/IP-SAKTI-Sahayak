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
from app.schemas import AnswerStatus, QueryRequest, QueryResponse
from app.services import abs_helper, confidence, generation

logger = get_logger(__name__)


def run_query(req: QueryRequest) -> QueryResponse:
    retriever = get_retriever()
    retrieval_query = expand_query(req.query)
    if retrieval_query != req.query:
        logger.info("query expanded for retrieval: %r", retrieval_query)
    chunks, top_score = retriever.retrieve(
        retrieval_query,
        jurisdiction=req.jurisdiction.value,
        top_k=6,
    )

    gen = generation.generate(req.query, chunks)
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
        confidence=conf,
        abs_flag=abs_result.triggered,
        abs_note=abs_note,
    )
