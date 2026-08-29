"""ABS-compliance second pass (PRD section 2 + risk note in section 7).

Trigger logic is deliberately simple and explainable: a keyword/category match.
If the query text or the formulation category touches biological resources /
traditional knowledge, run a narrow retrieval over the Biological Diversity Act
+ Rules only and attach a short compliance note.

Not over-engineered on purpose — this is the MVP rule the PRD asks for.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.logging import get_logger
from app.retrieval import get_retriever
from app.schemas import Citation
from app.services.generation import generate

logger = get_logger(__name__)

# Sources the ABS pass is allowed to retrieve from. Must match the `source`
# metadata written by the ingestion pipeline (kept loose via lower() compare).
ABS_SOURCES = {
    "the biological diversity act, 2002",
    "biological diversity act, 2002",
    "the biological diversity (amendment) act, 2023",
    "the biological diversity rules, 2024",
    "biological diversity rules, 2024",
}

_TRIGGER_KEYWORDS = (
    "biological resource",
    "biological material",
    "biodiversity",
    "bio-diversity",
    "benefit sharing",
    "benefit-sharing",
    "access and benefit",
    " abs ",
    "nagoya",
    "traditional knowledge",
    "national biodiversity authority",
    "state biodiversity board",
    "prior approval",
    "biosurvey",
    "bio-utilisation",
    "bio-utilization",
    "herb",
    "plant extract",
    "medicinal plant",
    "endemic",
)

# Formulation categories that, by nature, use biological resources.
_TRIGGER_CATEGORIES = {
    "classical",
    "proprietary",
    "phytopharmaceutical",
    "ayurveda_aahar",
}


@dataclass
class AbsResult:
    triggered: bool
    answer: str | None = None
    citations: list[Citation] | None = None
    note: str | None = None


def is_triggered(query: str, formulation_category: str | None) -> bool:
    q = f" {query.lower()} "
    if any(kw in q for kw in _TRIGGER_KEYWORDS):
        return True
    if formulation_category and formulation_category.lower() in _TRIGGER_CATEGORIES:
        return True
    return False


def run(query: str, formulation_category: str | None) -> AbsResult:
    if not is_triggered(query, formulation_category):
        return AbsResult(triggered=False)

    retriever = get_retriever()
    chunks, top_score = retriever.retrieve(
        query,
        jurisdiction="india",
        top_k=4,
        restrict_sources=ABS_SOURCES,
    )
    if not chunks:
        return AbsResult(
            triggered=True,
            answer=None,
            citations=[],
            note=(
                "This query appears to involve biological resources or traditional "
                "knowledge. Access and benefit-sharing obligations under the "
                "Biological Diversity Act, 2002 and Rules, 2024 are likely to apply "
                "(e.g. prior approval / intimation to the NBA or the State "
                "Biodiversity Board). Corpus lookup did not return a specific "
                "provision — confirm with an IP facilitator."
            ),
        )

    gen = generate(query, chunks)
    return AbsResult(
        triggered=True,
        answer=gen.answer,
        citations=gen.citations,
        note=(
            "ABS second pass: retrieved from the Biological Diversity Act / Rules. "
            "Verify NBA / SBB approval requirements before filing or commercialising."
        ),
    )
