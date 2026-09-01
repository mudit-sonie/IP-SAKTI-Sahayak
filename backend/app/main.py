"""FastAPI application entrypoint.

    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.facilitator import router as facilitator_router
from app.api.matters import router as matters_router
from app.api.routes import router
from app.config import get_settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build indices once at boot rather than on the first request.
    from app.retrieval import get_retriever

    get_retriever()
    logger.info("startup complete (env=%s)", get_settings().app_env)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="IP-SAKTI Sahayak API",
        version=__version__,
        description="Citation-grounded RAG assistant for Ayurveda IPR (SIH 2026 / PS 26045).",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    app.include_router(matters_router)
    app.include_router(facilitator_router)

    @app.get("/")
    def root() -> dict:
        return {"name": "IP-SAKTI Sahayak API", "version": __version__, "docs": "/docs"}

    return app


app = create_app()
