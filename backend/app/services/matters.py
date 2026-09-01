"""Matter lifecycle — create, record a grounded question, keep derived state fresh.

A matter is the persistent formulation profile the workspace is built around.
Storage is a single JSON document per matter (app/store).
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.core.logging import get_logger
from app.schemas import (
    AbsStatus,
    AuditEntry,
    ChecklistItem,
    ChecklistItemCreateRequest,
    ChecklistStatus,
    DraftKind,
    DraftRef,
    Jurisdiction,
    Matter,
    MatterCreateRequest,
    MatterProfile,
    MatterQuestion,
    MatterQuestionRequest,
    MatterUpdateRequest,
    QueryRequest,
    QueryResponse,
)
from app.services import checklist as checklist_svc
from app.services import drafts as drafts_svc
from app.services import pipeline
from app.store.repos import get_matter_repo, new_id

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _audit(matter: Matter, action: str, detail: str | None = None) -> None:
    matter.audit.append(AuditEntry(at=_now(), action=action, detail=detail))
    matter.updated_at = _now()


def create(req: MatterCreateRequest) -> Matter:
    now = _now()
    matter = Matter(
        id=new_id(),
        owner=get_settings().local_owner,
        title=req.title.strip() or "Untitled matter",
        created_at=now,
        updated_at=now,
        jurisdiction=req.jurisdiction,
        formulation_category=req.formulation_category,
        formulation_label=req.formulation_label,
        classification_rationale=req.classification_rationale,
        profile=req.profile or MatterProfile(),
        notes=req.notes,
    )
    _audit(matter, "matter.created", matter.title)
    if matter.formulation_category:
        matter.checklist = checklist_svc.generate(matter)
        _audit(matter, "checklist.generated", f"{len(matter.checklist)} items")
    get_matter_repo().save(matter)
    logger.info("matter created: %s (%s)", matter.id, matter.title)
    return matter


def update(matter_id: str, req: MatterUpdateRequest) -> Matter:
    repo = get_matter_repo()
    with repo.mutate(matter_id) as matter:
        before_cat = matter.formulation_category
        for field in ("title", "jurisdiction", "formulation_category",
                      "formulation_label", "classification_rationale",
                      "profile", "notes"):
            val = getattr(req, field)
            if val is not None:
                setattr(matter, field, val)
        _audit(matter, "matter.updated")
        # A new / changed classification changes which checklist rules apply.
        if matter.formulation_category and matter.formulation_category != before_cat:
            matter.checklist = checklist_svc.generate(matter)
            _audit(
                matter,
                "checklist.generated",
                f"{len(matter.checklist)} items (classification changed)",
            )
        return matter


def delete(matter_id: str) -> bool:
    return get_matter_repo().delete(matter_id)


def _recompute_abs_status(matter: Matter) -> None:
    """flagged wins once seen; else clear if any question ran clean; else unknown."""
    if any(q.abs_flag for q in matter.questions):
        matter.abs_status = AbsStatus.flagged
    elif matter.questions:
        matter.abs_status = AbsStatus.clear
    else:
        matter.abs_status = AbsStatus.unknown


def ask(matter_id: str, req: MatterQuestionRequest) -> tuple[Matter, MatterQuestion, QueryResponse]:
    repo = get_matter_repo()
    # Run the grounded pipeline outside the store lock (it can be slow).
    with repo.mutate(matter_id) as matter:
        jurisdiction = req.jurisdiction or matter.jurisdiction
        category = req.formulation_category or matter.formulation_category
        product_context = matter.profile.as_context()

    query_req = QueryRequest(
        query=req.query,
        jurisdiction=Jurisdiction(jurisdiction),
        formulation_category=category,
        context=product_context or None,
    )
    result = pipeline.run_query(query_req)

    question = MatterQuestion(
        id=new_id("q_"),
        query=req.query,
        jurisdiction=Jurisdiction(jurisdiction),
        formulation_category=category,
        asked_at=_now(),
        answer=result.answer,
        status=result.confidence.status,
        self_confidence=result.confidence.self_confidence,
        retrieval_score=result.confidence.retrieval_score,
        citations=result.citations,
        claims=result.claims,
        conflicts=result.conflicts,
        abs_flag=result.abs_flag,
    )

    with repo.mutate(matter_id) as matter:
        was = matter.abs_status
        matter.questions.append(question)
        _recompute_abs_status(matter)
        _audit(
            matter,
            "question.asked",
            f"{req.query[:80]} → {question.status.value}",
        )
        # ABS just turned on, or the checklist exists — refresh it so ABS items
        # appear / disappear in step with the matter's real state.
        if matter.checklist or matter.formulation_category:
            if matter.abs_status != was or matter.checklist:
                matter.checklist = checklist_svc.generate(matter)
        saved = matter

    return saved, question, result


# --------------------------------------------------------------------------- #
# Compliance checklist
# --------------------------------------------------------------------------- #
def regenerate_checklist(matter_id: str) -> Matter:
    repo = get_matter_repo()
    with repo.mutate(matter_id) as matter:
        matter.checklist = checklist_svc.generate(matter)
        _audit(matter, "checklist.generated", f"{len(matter.checklist)} items")
        return matter


def set_checklist_status(
    matter_id: str, item_id: str, status: ChecklistStatus
) -> Matter:
    repo = get_matter_repo()
    with repo.mutate(matter_id) as matter:
        for item in matter.checklist:
            if item.id == item_id:
                item.status = status
                _audit(matter, "checklist.item", f"{item.title[:60]} → {status.value}")
                return matter
        raise KeyError(item_id)


def export_question_markdown(matter_id: str, question_id: str) -> tuple[str, str]:
    """Return (filename, markdown) for a single grounded answer — a record the
    user can keep with their filing. Verbatim answer + citations, timestamped."""
    matter = get_matter_repo().get(matter_id)
    if matter is None:
        raise KeyError(matter_id)
    q = next((x for x in matter.questions if x.id == question_id), None)
    if q is None:
        raise KeyError(question_id)

    lines = [
        f"# IP-SAKTI Sahayak — grounded answer",
        "",
        f"**Matter:** {matter.title}  ",
        f"**Question asked:** {q.asked_at}  ",
        f"**Jurisdiction:** {q.jurisdiction.value}  ",
        f"**Formulation:** {matter.formulation_label or 'not classified'}  ",
        f"**Status:** {q.status.value} (retrieval score "
        f"{q.retrieval_score:.2f}, model self-confidence {q.self_confidence.value})",
        "",
        "## Question",
        "",
        q.query,
        "",
        "## Answer",
        "",
        q.answer or "_(escalated — no grounded answer)_",
        "",
        "## Citations",
        "",
    ]
    if q.citations:
        for c in q.citations:
            url = f" — {c.source_url}" if c.source_url else ""
            lines.append(f"- {c.source}, Section {c.section}{url}")
            if c.as_of:
                lines.append(f"  - source text as of {c.as_of}")
            if c.amended_by:
                lines.append(
                    f"  - ⚠ may have been amended by {c.amended_by}; verify "
                    f"against the official source"
                )
    else:
        lines.append("_No passage met the citation bar._")
    lines += [
        "",
        "---",
        "",
        "_Generated by IP-SAKTI Sahayak. Educational and informational use only "
        "— not legal advice. Verify against the official source text._",
        "",
    ]
    fname = f"ip-sakti-{matter_id}-{question_id}.md"
    return fname, "\n".join(lines)


def _drafts_root() -> Path:
    return Path(get_settings().drafts_dir)


def create_draft(matter_id: str, kind: DraftKind) -> tuple[Matter, DraftRef]:
    """Render a document draft from the matter and persist it under data/drafts/."""
    matter = get_matter_repo().get(matter_id)
    if matter is None:
        raise KeyError(matter_id)

    rendered = drafts_svc.render(matter, kind)
    draft_id = new_id("d_")
    rel_path = f"{matter_id}/{draft_id}.md"
    out = _drafts_root() / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered.markdown, encoding="utf-8")

    ref = DraftRef(
        id=draft_id,
        kind=kind.value,
        title=rendered.title,
        created_at=_now(),
        rel_path=rel_path,
    )
    with get_matter_repo().mutate(matter_id) as m:
        m.drafts.append(ref)
        _audit(m, "draft.generated", f"{rendered.title} ({len(rendered.citations)} cited)")
        saved = m
    return saved, ref


def get_draft_markdown(matter_id: str, draft_id: str) -> tuple[str, str]:
    matter = get_matter_repo().get(matter_id)
    if matter is None:
        raise KeyError(matter_id)
    ref = next((d for d in matter.drafts if d.id == draft_id), None)
    if ref is None:
        raise KeyError(draft_id)
    path = _drafts_root() / (ref.rel_path or f"{matter_id}/{draft_id}.md")
    if path.exists():
        md = path.read_text(encoding="utf-8")
    else:  # file lost (e.g. data/ cleaned) — re-render from the matter
        md = drafts_svc.render(matter, DraftKind(ref.kind)).markdown
    fname = f"ip-sakti-{ref.kind}-{matter_id}-{draft_id}.md"
    return fname, md


def delete_draft(matter_id: str, draft_id: str) -> Matter:
    with get_matter_repo().mutate(matter_id) as m:
        ref = next((d for d in m.drafts if d.id == draft_id), None)
        if ref is None:
            raise KeyError(draft_id)
        m.drafts = [d for d in m.drafts if d.id != draft_id]
        _audit(m, "draft.deleted", ref.title)
        if ref.rel_path:
            (_drafts_root() / ref.rel_path).unlink(missing_ok=True)
        return m


def add_checklist_item(
    matter_id: str, req: ChecklistItemCreateRequest
) -> Matter:
    repo = get_matter_repo()
    with repo.mutate(matter_id) as matter:
        matter.checklist.append(
            ChecklistItem(
                id=new_id("c_"),
                title=req.title.strip(),
                detail=req.detail,
                group=req.group or "Other",
            )
        )
        _audit(matter, "checklist.item.added", req.title[:60])
        return matter
