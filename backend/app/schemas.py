"""Pydantic models — the wire contract from PRD section 4.

Frontend builds against these shapes with mock data from Day 1, so treat any
change here as a breaking API change and announce it in the team channel.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Shared enums
# --------------------------------------------------------------------------- #
class Jurisdiction(str, Enum):
    india = "india"
    international = "international"


class FormulationCategory(str, Enum):
    classical = "classical"
    proprietary = "proprietary"
    new_drug = "new_drug"
    phytopharmaceutical = "phytopharmaceutical"
    ayurveda_aahar = "ayurveda_aahar"
    cosmetic = "cosmetic"


class SelfConfidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class AnswerStatus(str, Enum):
    answered = "answered"
    escalate = "escalate"


# --------------------------------------------------------------------------- #
# /classify
# --------------------------------------------------------------------------- #
class ClassifyRequest(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)


class NextQuestion(BaseModel):
    id: str
    text: str
    options: list[str]


class ClassifyResponse(BaseModel):
    formulation_category: Optional[FormulationCategory] = None
    next_question: Optional[NextQuestion] = None
    complete: bool = False


# --------------------------------------------------------------------------- #
# /query
# --------------------------------------------------------------------------- #
class QueryRequest(BaseModel):
    query: str
    jurisdiction: Jurisdiction = Jurisdiction.india
    formulation_category: Optional[str] = None


class Citation(BaseModel):
    source: str
    section: str
    excerpt_ref: Optional[str] = None


class Confidence(BaseModel):
    retrieval_score: float = 0.0
    self_confidence: SelfConfidence = SelfConfidence.low
    status: AnswerStatus = AnswerStatus.escalate


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: Confidence
    abs_flag: bool = False
    abs_note: Optional[str] = None


# --------------------------------------------------------------------------- #
# /abs-check
# --------------------------------------------------------------------------- #
class AbsCheckRequest(BaseModel):
    query: str
    formulation_category: Optional[str] = None


class AbsCheckResponse(BaseModel):
    triggered: bool
    answer: Optional[str] = None
    citations: list[Citation] = Field(default_factory=list)
