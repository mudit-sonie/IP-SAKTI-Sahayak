"""Routes for the matter workspace (PRODUCT_ROADMAP.md).

    POST   /matters                 create
    GET    /matters                 list summaries
    GET    /matters/{id}            full aggregate
    PATCH  /matters/{id}            update profile fields
    DELETE /matters/{id}            remove
    POST   /matters/{id}/questions  run a grounded question, record it on the matter
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from app.config import get_settings
from app.schemas import (
    ChecklistItemCreateRequest,
    ChecklistItemStatusRequest,
    DeadlineCreateRequest,
    DeadlineDeriveRequest,
    DeadlineDoneRequest,
    DraftCreateRequest,
    MatterDocumentDetail,
    Matter,
    MatterCreateRequest,
    MatterQuestionRequest,
    MatterQuestionResponse,
    MatterSummary,
    MatterUpdateRequest,
)
from app.services import matters
from app.store.repos import get_matter_repo

router = APIRouter(prefix="/matters", tags=["matters"])


def _require_enabled() -> None:
    if not get_settings().matters_enabled:
        raise HTTPException(status_code=404, detail="matters are disabled")


@router.post("", response_model=Matter, status_code=201)
def create_matter(req: MatterCreateRequest) -> Matter:
    _require_enabled()
    return matters.create(req)


@router.get("", response_model=list[MatterSummary])
def list_matters() -> list[MatterSummary]:
    _require_enabled()
    return get_matter_repo().list_summaries(owner=get_settings().local_owner)


@router.get("/{matter_id}", response_model=Matter)
def get_matter(matter_id: str) -> Matter:
    _require_enabled()
    matter = get_matter_repo().get(matter_id)
    if matter is None:
        raise HTTPException(status_code=404, detail="matter not found")
    return matter


@router.patch("/{matter_id}", response_model=Matter)
def update_matter(matter_id: str, req: MatterUpdateRequest) -> Matter:
    _require_enabled()
    try:
        return matters.update(matter_id, req)
    except KeyError:
        raise HTTPException(status_code=404, detail="matter not found")


@router.delete("/{matter_id}", status_code=204)
def delete_matter(matter_id: str) -> None:
    _require_enabled()
    if not matters.delete(matter_id):
        raise HTTPException(status_code=404, detail="matter not found")


@router.post("/{matter_id}/questions", response_model=MatterQuestionResponse)
def ask_in_matter(matter_id: str, req: MatterQuestionRequest) -> MatterQuestionResponse:
    _require_enabled()
    if not req.query.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")
    try:
        matter, question, result = matters.ask(matter_id, req)
    except KeyError:
        raise HTTPException(status_code=404, detail="matter not found")
    return MatterQuestionResponse(matter=matter, question=question, result=result)


@router.get(
    "/{matter_id}/questions/{question_id}/export",
    response_class=PlainTextResponse,
)
def export_question(matter_id: str, question_id: str) -> PlainTextResponse:
    _require_enabled()
    try:
        fname, md = matters.export_question_markdown(matter_id, question_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="matter or question not found")
    return PlainTextResponse(
        md,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.post("/{matter_id}/drafts", response_model=Matter, status_code=201)
def create_draft(matter_id: str, req: DraftCreateRequest) -> Matter:
    _require_enabled()
    try:
        matter, _ref = matters.create_draft(matter_id, req.kind)
    except KeyError:
        raise HTTPException(status_code=404, detail="matter not found")
    return matter


@router.get("/{matter_id}/drafts/{draft_id}", response_class=PlainTextResponse)
def get_draft(matter_id: str, draft_id: str) -> PlainTextResponse:
    _require_enabled()
    try:
        fname, md = matters.get_draft_markdown(matter_id, draft_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="matter or draft not found")
    return PlainTextResponse(
        md,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.delete("/{matter_id}/drafts/{draft_id}", response_model=Matter)
def delete_draft(matter_id: str, draft_id: str) -> Matter:
    _require_enabled()
    try:
        return matters.delete_draft(matter_id, draft_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="matter or draft not found")


@router.post("/{matter_id}/deadlines/derive", response_model=Matter)
def derive_deadlines(matter_id: str, req: DeadlineDeriveRequest) -> Matter:
    _require_enabled()
    try:
        return matters.derive_deadlines(matter_id, req.anchor, req.anchor_date)
    except KeyError:
        raise HTTPException(status_code=404, detail="matter not found")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/{matter_id}/deadlines", response_model=Matter, status_code=201)
def add_deadline(matter_id: str, req: DeadlineCreateRequest) -> Matter:
    _require_enabled()
    if not req.title.strip():
        raise HTTPException(status_code=422, detail="title must not be empty")
    try:
        return matters.add_deadline(matter_id, req)
    except KeyError:
        raise HTTPException(status_code=404, detail="matter not found")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.patch("/{matter_id}/deadlines/{deadline_id}", response_model=Matter)
def set_deadline_done(
    matter_id: str, deadline_id: str, req: DeadlineDoneRequest
) -> Matter:
    _require_enabled()
    try:
        return matters.set_deadline_done(matter_id, deadline_id, req.done)
    except KeyError:
        raise HTTPException(status_code=404, detail="matter or deadline not found")


@router.delete("/{matter_id}/deadlines/{deadline_id}", response_model=Matter)
def delete_deadline(matter_id: str, deadline_id: str) -> Matter:
    _require_enabled()
    try:
        return matters.delete_deadline(matter_id, deadline_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="matter or deadline not found")


@router.post("/{matter_id}/documents", response_model=Matter, status_code=201)
async def add_document(
    matter_id: str,
    background: BackgroundTasks,
    file: UploadFile = File(...),
) -> Matter:
    _require_enabled()
    if not get_settings().matter_docs_enabled:
        raise HTTPException(status_code=404, detail="matter documents are disabled")
    data = await file.read()
    try:
        matter, doc = matters.add_document(
            matter_id, file.filename or "document", data
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="matter not found")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if doc.status == "processing":
        background.add_task(matters.process_document, matter_id, doc.id)
    return matter


@router.get(
    "/{matter_id}/documents/{doc_id}", response_model=MatterDocumentDetail
)
def get_document(matter_id: str, doc_id: str) -> MatterDocumentDetail:
    _require_enabled()
    try:
        return matters.get_document(matter_id, doc_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="document not found")


@router.delete("/{matter_id}/documents/{doc_id}", response_model=Matter)
def delete_document(matter_id: str, doc_id: str) -> Matter:
    _require_enabled()
    try:
        return matters.delete_document(matter_id, doc_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="matter or document not found")


@router.post("/{matter_id}/tkdl-check", response_model=Matter)
def run_tkdl_check(matter_id: str) -> Matter:
    _require_enabled()
    try:
        return matters.run_tkdl_check(matter_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="matter not found")


@router.post("/{matter_id}/checklist", response_model=Matter)
def regenerate_checklist(matter_id: str) -> Matter:
    _require_enabled()
    try:
        return matters.regenerate_checklist(matter_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="matter not found")


@router.post("/{matter_id}/checklist/items", response_model=Matter)
def add_checklist_item(matter_id: str, req: ChecklistItemCreateRequest) -> Matter:
    _require_enabled()
    if not req.title.strip():
        raise HTTPException(status_code=422, detail="title must not be empty")
    try:
        return matters.add_checklist_item(matter_id, req)
    except KeyError:
        raise HTTPException(status_code=404, detail="matter not found")


@router.patch("/{matter_id}/checklist/{item_id}", response_model=Matter)
def set_checklist_status(
    matter_id: str, item_id: str, req: ChecklistItemStatusRequest
) -> Matter:
    _require_enabled()
    try:
        return matters.set_checklist_status(matter_id, item_id, req.status)
    except KeyError:
        raise HTTPException(status_code=404, detail="matter or item not found")
