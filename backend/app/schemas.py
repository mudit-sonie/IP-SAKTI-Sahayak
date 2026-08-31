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
    # Human-readable decision path once complete — one line per answered question.
    rationale: list[str] = Field(default_factory=list)


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
    source_url: Optional[str] = None


# --------------------------------------------------------------------------- #
# /chunk/{chunk_id} — fetch the exact statute passage behind a citation
# --------------------------------------------------------------------------- #
class ChunkResponse(BaseModel):
    chunk_id: str
    text: str
    source: str
    section: str
    citation: Optional[str] = None
    source_url: Optional[str] = None
    jurisdiction: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None


class Confidence(BaseModel):
    retrieval_score: float = 0.0
    self_confidence: SelfConfidence = SelfConfidence.low
    status: AnswerStatus = AnswerStatus.escalate


class RetrievalInfo(BaseModel):
    """What the retrieval layer actually did — surfaced for transparency."""

    jurisdiction: str
    expanded_query: Optional[str] = None
    passages_searched: int = 0
    sources_searched: list[str] = Field(default_factory=list)
    top_sections: list[str] = Field(default_factory=list)


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: Confidence
    abs_flag: bool = False
    abs_note: Optional[str] = None
    cached: bool = False
    jurisdiction_note: Optional[str] = None
    retrieval: Optional[RetrievalInfo] = None


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


# --------------------------------------------------------------------------- #
# /feedback — thumbs up/down on an answer (feeds the Day-4 spot-check)
# --------------------------------------------------------------------------- #
class FeedbackRequest(BaseModel):
    query: str
    rating: str  # "up" | "down"
    note: Optional[str] = None
    jurisdiction: Optional[str] = None
    formulation_category: Optional[str] = None
    answer_status: Optional[str] = None
    cited_sections: list[str] = Field(default_factory=list)


class FeedbackResponse(BaseModel):
    ok: bool = True


# --------------------------------------------------------------------------- #
# Matters — the persistent workspace layer (PRODUCT_ROADMAP.md)
# --------------------------------------------------------------------------- #
class AbsStatus(str, Enum):
    unknown = "unknown"
    flagged = "flagged"
    clear = "clear"


class ChecklistStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    not_applicable = "not_applicable"


class MatterQuestion(BaseModel):
    """One query run inside a matter, with its grounded answer frozen in."""

    id: str
    query: str
    jurisdiction: Jurisdiction = Jurisdiction.india
    formulation_category: Optional[str] = None
    asked_at: str
    answer: str = ""
    status: AnswerStatus = AnswerStatus.escalate
    self_confidence: SelfConfidence = SelfConfidence.low
    retrieval_score: float = 0.0
    citations: list[Citation] = Field(default_factory=list)
    abs_flag: bool = False


class ChecklistItem(BaseModel):
    id: str
    title: str
    detail: Optional[str] = None
    group: Optional[str] = None  # "Licensing" | "ABS" | "Labelling" | ...
    status: ChecklistStatus = ChecklistStatus.todo
    citations: list[Citation] = Field(default_factory=list)
    source_rule: Optional[str] = None  # which generator rule produced this


class Deadline(BaseModel):
    id: str
    title: str
    due_date: str  # ISO date
    kind: str = "manual"  # "manual" | "derived"
    detail: Optional[str] = None
    done: bool = False


class DraftRef(BaseModel):
    id: str
    kind: str  # "form1" | "nba_abs" | "disclosure_of_source" | "s3p_rebuttal"
    title: str
    created_at: str
    rel_path: Optional[str] = None  # under data/drafts/


class AuditEntry(BaseModel):
    at: str
    action: str
    detail: Optional[str] = None


class Matter(BaseModel):
    id: str
    owner: str = "local"
    title: str
    created_at: str
    updated_at: str
    jurisdiction: Jurisdiction = Jurisdiction.india
    formulation_category: Optional[str] = None
    formulation_label: Optional[str] = None
    classification_rationale: list[str] = Field(default_factory=list)
    abs_status: AbsStatus = AbsStatus.unknown
    notes: Optional[str] = None
    questions: list[MatterQuestion] = Field(default_factory=list)
    checklist: list[ChecklistItem] = Field(default_factory=list)
    deadlines: list[Deadline] = Field(default_factory=list)
    drafts: list[DraftRef] = Field(default_factory=list)
    audit: list[AuditEntry] = Field(default_factory=list)


class MatterSummary(BaseModel):
    id: str
    title: str
    jurisdiction: Jurisdiction
    formulation_label: Optional[str] = None
    abs_status: AbsStatus = AbsStatus.unknown
    question_count: int = 0
    open_checklist_items: int = 0
    updated_at: str


class MatterCreateRequest(BaseModel):
    title: str
    jurisdiction: Jurisdiction = Jurisdiction.india
    formulation_category: Optional[str] = None
    formulation_label: Optional[str] = None
    classification_rationale: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class MatterUpdateRequest(BaseModel):
    title: Optional[str] = None
    jurisdiction: Optional[Jurisdiction] = None
    formulation_category: Optional[str] = None
    formulation_label: Optional[str] = None
    notes: Optional[str] = None


class MatterQuestionRequest(BaseModel):
    query: str
    # falls back to the matter's own jurisdiction / category when omitted
    jurisdiction: Optional[Jurisdiction] = None
    formulation_category: Optional[str] = None


class MatterQuestionResponse(BaseModel):
    matter: Matter
    question: MatterQuestion
    result: QueryResponse
