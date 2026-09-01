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
    # Background on the specific product (from a matter's formulation profile).
    # Used to inform generation only — never mixed into retrieval, and the
    # answer must still come from the corpus passages.
    context: Optional[str] = None
    # Set when the question was asked inside a matter — carried onto an escalation.
    matter_id: Optional[str] = None


class Citation(BaseModel):
    source: str
    section: str
    excerpt_ref: Optional[str] = None
    source_url: Optional[str] = None
    # Amendment awareness (S6): currency date of the passage text, and an
    # amending instrument known to affect this provision (both optional — only
    # set when the amendment overlay is curated).
    as_of: Optional[str] = None
    amended_by: Optional[str] = None


class Claim(BaseModel):
    """One factual statement from the answer plus the passages that back it.

    `citations` holds 1-based indices into the response's `citations[]` array
    (the same `[n]` markers rendered inline in `text`). A claim with an empty
    list is narrative connective tissue, not a grounded assertion.
    """

    text: str
    citations: list[int] = Field(default_factory=list)


class ConflictPosition(BaseModel):
    """One side of a divergence between instruments."""

    summary: str
    citations: list[int] = Field(default_factory=list)  # 1-based into `citations[]`


class Conflict(BaseModel):
    """Two or more retrieved instruments taking divergent positions on one point.
    Surfaced instead of silently picking a winner."""

    topic: str
    positions: list[ConflictPosition] = Field(default_factory=list)


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
    as_of: Optional[str] = None
    amended_by: Optional[str] = None
    in_force: Optional[bool] = None


# --------------------------------------------------------------------------- #
# /corpus — coverage map (what the assistant can and cannot answer from) (S4)
# --------------------------------------------------------------------------- #
class CorpusSource(BaseModel):
    source: str
    source_id: Optional[str] = None
    jurisdiction: Optional[str] = None
    document_type: Optional[str] = None
    organization: Optional[str] = None
    source_url: Optional[str] = None
    year: Optional[int] = None
    as_of: Optional[str] = None
    chunk_count: int = 0
    section_count: int = 0
    sections: list[str] = Field(default_factory=list)
    thin: bool = False  # fewer chunks than the thin-coverage threshold


class CorpusCoverage(BaseModel):
    generated_at: str
    corpus_loaded: bool
    chunk_count: int = 0
    source_count: int = 0
    jurisdictions: dict[str, int] = Field(default_factory=dict)
    sources: list[CorpusSource] = Field(default_factory=list)
    known_gaps: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# /fees — patent & GI fee calculators (S11)
# --------------------------------------------------------------------------- #
class FeeEntity(BaseModel):
    key: str
    label: str


class FeeItem(BaseModel):
    code: str
    label: str
    category: str
    amounts: dict[str, int]  # entity key -> amount
    note: Optional[str] = None


class FeeRenewalBand(BaseModel):
    from_year: int
    to_year: int
    amounts: dict[str, int]  # entity key -> per-year amount


class FeeSchedule(BaseModel):
    track: str  # "patent" | "gi"
    title: str
    currency: str = "INR"
    as_of: str
    source: str
    source_url: Optional[str] = None
    entities: list[FeeEntity] = Field(default_factory=list)
    items: list[FeeItem] = Field(default_factory=list)
    renewal_bands: list[FeeRenewalBand] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class FeesResponse(BaseModel):
    disclaimer: str
    schedules: list[FeeSchedule] = Field(default_factory=list)


class FeeEstimateRequest(BaseModel):
    track: str
    entity: str
    item_codes: list[str] = Field(default_factory=list)
    renewal_from_year: Optional[int] = None
    renewal_to_year: Optional[int] = None


class FeeEstimateLine(BaseModel):
    code: str
    label: str
    amount: int
    detail: Optional[str] = None


class FeeEstimateResponse(BaseModel):
    track: str
    entity: str
    currency: str
    lines: list[FeeEstimateLine] = Field(default_factory=list)
    total: int = 0
    disclaimer: str


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


class CompareRequest(BaseModel):
    query: str
    formulation_category: Optional[str] = None
    context: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    # Per-claim breakdown of `answer` with inline `[n]` markers into `citations`.
    # Empty when generation produced no marker-tagged claims (e.g. escalate).
    claims: list[Claim] = Field(default_factory=list)
    # Divergent positions across retrieved instruments, when generation found any.
    conflicts: list[Conflict] = Field(default_factory=list)
    confidence: Confidence
    abs_flag: bool = False
    abs_note: Optional[str] = None
    cached: bool = False
    jurisdiction_note: Optional[str] = None
    retrieval: Optional[RetrievalInfo] = None
    # True when this answer came from a human-reviewed FAQ entry, not the model.
    from_faq: bool = False


class CompareResponse(BaseModel):
    """One question run against both jurisdictions, for side-by-side rendering."""

    query: str
    india: QueryResponse
    international: QueryResponse


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


class MatterProfile(BaseModel):
    """A short description of the actual product. Fed as background into every
    question asked inside the matter (not into retrieval)."""

    dosage_form: Optional[str] = None  # "tablet" | "churna" | "oil" | ...
    key_ingredients: list[str] = Field(default_factory=list)
    intended_use: Optional[str] = None  # what it's marketed / used for
    process_novelty: Optional[str] = None  # new combination / extract / indication?
    source_notes: Optional[str] = None  # biological-resource / origin details

    def as_context(self) -> str:
        parts: list[str] = []
        if self.dosage_form:
            parts.append(f"Dosage form: {self.dosage_form}.")
        if self.key_ingredients:
            parts.append("Key ingredients: " + ", ".join(self.key_ingredients) + ".")
        if self.intended_use:
            parts.append(f"Intended use / claims: {self.intended_use}.")
        if self.process_novelty:
            parts.append(f"Novelty: {self.process_novelty}.")
        if self.source_notes:
            parts.append(f"Biological source: {self.source_notes}.")
        return " ".join(parts)


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
    claims: list[Claim] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    abs_flag: bool = False


class ChecklistItem(BaseModel):
    id: str
    title: str
    detail: Optional[str] = None
    group: Optional[str] = None  # "Licensing" | "ABS" | "Labelling" | ...
    status: ChecklistStatus = ChecklistStatus.todo
    citations: list[Citation] = Field(default_factory=list)
    source_rule: Optional[str] = None  # which generator rule produced this


class DeadlineAnchor(str, Enum):
    patent_filing = "patent_filing"
    patent_priority = "patent_priority"
    tm_application = "tm_application"
    gi_application = "gi_application"


class Deadline(BaseModel):
    id: str
    title: str
    due_date: str  # ISO date
    kind: str = "manual"  # "manual" | "derived"
    detail: Optional[str] = None
    done: bool = False
    source_rule: Optional[str] = None  # derived-rule key, when kind == "derived"
    anchor: Optional[str] = None  # DeadlineAnchor value the derivation used
    citations: list[Citation] = Field(default_factory=list)


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
    profile: MatterProfile = Field(default_factory=MatterProfile)
    abs_status: AbsStatus = AbsStatus.unknown
    # Optional Indian state — drives the ASU&H licensing authority and (later)
    # state-specific rules. Free-form key matched against the state-rules table.
    state: Optional[str] = None
    notes: Optional[str] = None
    questions: list[MatterQuestion] = Field(default_factory=list)
    checklist: list[ChecklistItem] = Field(default_factory=list)
    deadlines: list[Deadline] = Field(default_factory=list)
    # Anchor dates the user has supplied (DeadlineAnchor -> ISO date), used to
    # (re)derive statutory deadlines.
    anchor_dates: dict[str, str] = Field(default_factory=dict)
    drafts: list[DraftRef] = Field(default_factory=list)
    tkdl: Optional[TkdlResult] = None  # last TKDL / prior-art cross-check (S12)
    audit: list[AuditEntry] = Field(default_factory=list)


class TkdlReference(BaseModel):
    title: str
    source: Optional[str] = None
    formulation_ref: Optional[str] = None
    url: Optional[str] = None


class TkdlResult(BaseModel):
    """Outcome of a TKDL / prior-art cross-check (S12).

    `status` is "not_connected" until a deployment wires a TKDL connector — the
    library is access-controlled, so this is a scaffold that is honest about it
    and never invents prior art.
    """

    status: str = "not_connected"  # not_connected | no_matches | matches
    checked_at: str
    search_terms: list[str] = Field(default_factory=list)
    note: str = ""
    references: list[TkdlReference] = Field(default_factory=list)


class StateAuthority(BaseModel):
    """ASU&H drug licensing authority for an Indian state (S13)."""

    key: str
    state: str
    authority: str
    portal_url: Optional[str] = None
    note: Optional[str] = None


class StateRulesResponse(BaseModel):
    as_of: str
    note: str
    authorities: list[StateAuthority] = Field(default_factory=list)


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
    profile: Optional[MatterProfile] = None
    state: Optional[str] = None
    notes: Optional[str] = None


class MatterUpdateRequest(BaseModel):
    title: Optional[str] = None
    jurisdiction: Optional[Jurisdiction] = None
    formulation_category: Optional[str] = None
    formulation_label: Optional[str] = None
    classification_rationale: Optional[list[str]] = None
    profile: Optional[MatterProfile] = None
    state: Optional[str] = None
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


class ChecklistItemStatusRequest(BaseModel):
    status: ChecklistStatus


class ChecklistItemCreateRequest(BaseModel):
    title: str
    detail: Optional[str] = None
    group: Optional[str] = None


# --------------------------------------------------------------------------- #
# Facilitator queue + reviewed FAQ (S5)
# --------------------------------------------------------------------------- #
class EscalationStatus(str, Enum):
    open = "open"
    answered = "answered"
    dismissed = "dismissed"


class Escalation(BaseModel):
    id: str
    created_at: str
    query: str
    jurisdiction: Jurisdiction = Jurisdiction.india
    formulation_category: Optional[str] = None
    context: Optional[str] = None  # matter background, if the ask came from a matter
    retrieval_score: float = 0.0
    self_confidence: SelfConfidence = SelfConfidence.low
    reason: Optional[str] = None  # "low_retrieval" | "high_stakes" | "no_gemini" ...
    source: str = "query"  # "query" | "matter"
    matter_id: Optional[str] = None
    status: EscalationStatus = EscalationStatus.open
    answer: Optional[str] = None
    answer_citations: list[Citation] = Field(default_factory=list)
    answered_at: Optional[str] = None
    faq_id: Optional[str] = None


class FaqEntry(BaseModel):
    id: str
    question: str
    jurisdiction: Jurisdiction = Jurisdiction.india
    formulation_category: Optional[str] = None
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    source_escalation_id: Optional[str] = None


class EscalationAnswerRequest(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    publish_faq: bool = True


class FaqCreateRequest(BaseModel):
    question: str
    answer: str
    jurisdiction: Jurisdiction = Jurisdiction.india
    formulation_category: Optional[str] = None
    citations: list[Citation] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Document drafts (S8)
# --------------------------------------------------------------------------- #
class DraftKind(str, Enum):
    form1 = "form1"
    nba_abs = "nba_abs"
    disclosure_of_source = "disclosure_of_source"
    s3p_rebuttal = "s3p_rebuttal"


class DraftKindInfo(BaseModel):
    kind: DraftKind
    title: str
    description: str
    requires_abs: bool = False


class DraftCreateRequest(BaseModel):
    kind: DraftKind


# --------------------------------------------------------------------------- #
# Deadlines (S9)
# --------------------------------------------------------------------------- #
class DeadlineDeriveRequest(BaseModel):
    anchor: DeadlineAnchor
    anchor_date: str  # ISO date (YYYY-MM-DD)


class DeadlineCreateRequest(BaseModel):
    title: str
    due_date: str
    detail: Optional[str] = None


class DeadlineDoneRequest(BaseModel):
    done: bool
