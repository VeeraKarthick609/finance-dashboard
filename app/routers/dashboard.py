from fastapi import APIRouter, Depends, Query

from app.dependencies import require_role
from app.services import dashboard_service

router = APIRouter()


@router.get("/summary")
async def summary(
    current_user: dict = Depends(require_role("viewer", "analyst", "admin")),
):
    result = dashboard_service.get_summary()
    return {"success": True, "data": result}


@router.get("/categories")
async def category_totals(
    current_user: dict = Depends(require_role("viewer", "analyst", "admin")),
):
    result = dashboard_service.get_category_totals()
    return {"success": True, **result}


@router.get("/recent")
async def recent_records(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(require_role("viewer", "analyst", "admin")),
):
    result = dashboard_service.get_recent(limit)
    return {"success": True, **result}
