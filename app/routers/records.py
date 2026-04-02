from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user, require_role
from app.models.record import CreateRecordRequest, UpdateRecordRequest
from app.services import record_service

router = APIRouter()


@router.get("")
async def list_records(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    type: str | None = Query(None, pattern=r"^(income|expense)$"),
    category: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("date", pattern=r"^(date|amount|created_at)$"),
    order: str = Query("desc", pattern=r"^(asc|desc)$"),
    current_user: dict = Depends(require_role("viewer", "analyst", "admin")),
):
    result = record_service.list_records(
        page, limit, type, category, start_date, end_date, search, sort_by, order
    )
    return {"success": True, **result}


@router.get("/{record_id}")
async def get_record(
    record_id: str,
    current_user: dict = Depends(require_role("viewer", "analyst", "admin")),
):
    record = record_service.get_record(record_id)
    return {"success": True, "data": record}


@router.post("", status_code=201)
async def create_record(
    body: CreateRecordRequest,
    current_user: dict = Depends(require_role("admin")),
):
    record = record_service.create_record(body.model_dump(), current_user["id"])
    return {"success": True, "data": record}


@router.patch("/{record_id}")
async def update_record(
    record_id: str,
    body: UpdateRecordRequest,
    current_user: dict = Depends(require_role("admin")),
):
    record = record_service.update_record(record_id, body.model_dump(exclude_none=True))
    return {"success": True, "data": record}


@router.delete("/{record_id}")
async def delete_record(
    record_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    record = record_service.soft_delete_record(record_id)
    return {"success": True, "data": record, "message": "Record deleted"}
