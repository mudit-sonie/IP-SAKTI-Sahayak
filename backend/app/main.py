"""FastAPI application entrypoint.

    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import router
from app.config import get_settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="IP-SAKTI Sahayak API",
        version=__version__,
        description="Citation-grounded RAG assistant for Ayurveda IPR (SIH 2026 / PS 26045).",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.get("/")
    def root() -> dict:
        return {"name": "IP-SAKTI Sahayak API", "version": __version__, "docs": "/docs"}

    @app.on_event("startup")
    def _warm() -> None:
        # Build indices once at boot rather than on the first request.
        from app.retrieval import get_retriever

        get_retriever()
        logger.info("startup complete (env=%s)", settings.app_env)

    return app


app = create_app()
