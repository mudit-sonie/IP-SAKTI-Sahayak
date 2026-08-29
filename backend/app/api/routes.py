"""HTTP routes — the PRD section 4 API contract.

    GET  /health      liveness + which subsystems are wired
    POST /classify     rule-based formulation classifier
    POST /query        main RAG query
    POST /abs-check     ABS second pass (also called internally by /query)
"""
from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.llm.gemini_client import get_gemini_client
from app.retrieval import get_retriever
from app.schemas import (
    AbsCheckRequest,
    AbsCheckResponse,
    ClassifyRequest,
    ClassifyResponse,
    QueryRequest,
    QueryResponse,
)
from app.services import abs_helper, pipeline
from app.services.classifier import classify

router = APIRouter()


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    retriever = get_retriever()
    return {
        "status": "ok",
        "env": settings.app_env,
        "corpus_loaded": retriever.has_corpus,
        "gemini_configured": get_gemini_client().is_configured,
        "escalate_threshold": settings.retrieval_escalate_threshold,
    }


@router.post("/classify", response_model=ClassifyResponse)
def post_classify(req: ClassifyRequest) -> ClassifyResponse:
    return classify(req.answers)


@router.post("/query", response_model=QueryResponse)
def post_query(req: QueryRequest) -> QueryResponse:
    return pipeline.run_query(req)


@router.post("/abs-check", response_model=AbsCheckResponse)
def post_abs_check(req: AbsCheckRequest) -> AbsCheckResponse:
    result = abs_helper.run(req.query, req.formulation_category)
    return AbsCheckResponse(
        triggered=result.triggered,
        answer=result.answer,
        citations=result.citations or [],
    )
