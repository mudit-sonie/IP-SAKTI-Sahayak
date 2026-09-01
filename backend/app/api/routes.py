"""HTTP routes — the PRD section 4 API contract.

    GET  /health      liveness + which subsystems are wired
    POST /classify     rule-based formulation classifier
    POST /query        main RAG query
    POST /abs-check     ABS second pass (also called internally by /query)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.llm.gemini_client import get_gemini_client
from app.retrieval import get_retriever
from app.schemas import (
    AbsCheckRequest,
    AbsCheckResponse,
    ChunkResponse,
    ClassifyRequest,
    ClassifyResponse,
    CompareRequest,
    CompareResponse,
    CorpusCoverage,
    DraftKindInfo,
    FeeEstimateRequest,
    FeeEstimateResponse,
    FeesResponse,
    Jurisdiction,
    LanguageOption,
    StateAuthority,
    StateRulesResponse,
    TranslateRequest,
    TranslateResponse,
    FeedbackRequest,
    FeedbackResponse,
    QueryRequest,
    QueryResponse,
)
from app.services import abs_helper, coverage, feedback, pipeline
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


@router.post("/compare", response_model=CompareResponse)
def post_compare(req: CompareRequest) -> CompareResponse:
    """Run one question against both jurisdictions for a side-by-side view (S10)."""
    def _run(j: Jurisdiction) -> QueryResponse:
        return pipeline.run_query(
            QueryRequest(
                query=req.query,
                jurisdiction=j,
                formulation_category=req.formulation_category,
                context=req.context,
            )
        )

    return CompareResponse(
        query=req.query,
        india=_run(Jurisdiction.india),
        international=_run(Jurisdiction.international),
    )


@router.get("/chunk/{chunk_id}", response_model=ChunkResponse)
def get_chunk(chunk_id: str) -> ChunkResponse:
    """The exact statute passage behind a citation's ``excerpt_ref``."""
    chunk = get_retriever().get_chunk(chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail=f"unknown chunk id: {chunk_id}")
    meta = chunk.metadata
    return ChunkResponse(
        chunk_id=chunk.chunk_id,
        text=chunk.text,
        source=chunk.source,
        section=chunk.section,
        citation=meta.get("citation"),
        source_url=meta.get("source_url"),
        jurisdiction=meta.get("jurisdiction"),
        page_start=meta.get("page_start"),
        page_end=meta.get("page_end"),
        as_of=meta.get("as_of") or None,
        amended_by=meta.get("amended_by") or None,
        in_force=meta.get("in_force") if isinstance(meta.get("in_force"), bool) else None,
    )


@router.get("/corpus", response_model=CorpusCoverage)
def get_corpus() -> CorpusCoverage:
    """Coverage map: which instruments/sections the assistant answers from, plus
    known gaps. Backs the Coverage screen and the 'outside our corpus' banner."""
    return coverage.build_coverage()


@router.get("/fees", response_model=FeesResponse)
def get_fees() -> FeesResponse:
    """The patent & GI fee schedules backing the calculator (S11)."""
    from app.services import fees

    return fees.get_schedules()


@router.post("/fees/estimate", response_model=FeeEstimateResponse)
def estimate_fees(req: FeeEstimateRequest) -> FeeEstimateResponse:
    from app.services import fees

    try:
        return fees.estimate(req)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/languages", response_model=list[LanguageOption])
def get_languages() -> list[LanguageOption]:
    """Languages an answer can be translated into post-generation (S15)."""
    from app.services import translate

    return [LanguageOption(**o) for o in translate.languages()]


@router.post("/translate", response_model=TranslateResponse)
def post_translate(req: TranslateRequest) -> TranslateResponse:
    """Translate a generated answer. Citations/quoted law stay English."""
    from app.services import translate

    out = translate.translate(req.text, req.lang)
    if out is None:
        return TranslateResponse(lang="en", text=req.text, translated=False)
    return TranslateResponse(lang=req.lang, text=out, translated=True)


@router.get("/state-rules", response_model=StateRulesResponse)
def get_state_rules() -> StateRulesResponse:
    """ASU&H drug licensing authorities by state (S13 scaffold)."""
    from app.services import state_rules

    return state_rules.list_authorities()


@router.get("/state-rules/{state_key}", response_model=StateAuthority)
def get_state_rule(state_key: str) -> StateAuthority:
    from app.services import state_rules

    a = state_rules.get_authority(state_key)
    if a is None:
        raise HTTPException(status_code=404, detail="unknown state key")
    return a


@router.get("/draft-kinds", response_model=list[DraftKindInfo])
def draft_kinds() -> list[DraftKindInfo]:
    """The document-draft templates a matter can generate (S8)."""
    from app.services.drafts import KIND_INFO

    return list(KIND_INFO.values())


@router.post("/feedback", response_model=FeedbackResponse)
def post_feedback(req: FeedbackRequest) -> FeedbackResponse:
    if req.rating not in {"up", "down"}:
        raise HTTPException(status_code=422, detail="rating must be 'up' or 'down'")
    feedback.record(req)
    return FeedbackResponse(ok=True)


@router.post("/abs-check", response_model=AbsCheckResponse)
def post_abs_check(req: AbsCheckRequest) -> AbsCheckResponse:
    result = abs_helper.run(req.query, req.formulation_category)
    return AbsCheckResponse(
        triggered=result.triggered,
        answer=result.answer,
        citations=result.citations or [],
    )
