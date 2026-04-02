from fastapi import APIRouter, Depends, Query

from app.dependencies import require_role
from app.models.user import UpdateUserRequest
from app.services import user_service

router = APIRouter()


@router.get("")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    role: str | None = Query(None, pattern=r"^(viewer|analyst|admin)$"),
    is_active: bool | None = Query(None),
    current_user: dict = Depends(require_role("admin")),
):
    result = user_service.list_users(page, limit, search, role, is_active)
    return {"success": True, **result}


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    user = user_service.get_user(user_id)
    return {"success": True, "data": user}


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    current_user: dict = Depends(require_role("admin")),
):
    user = user_service.update_user(user_id, body.model_dump(exclude_none=True), current_user["id"])
    return {"success": True, "data": user}


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    user = user_service.deactivate_user(user_id, current_user["id"])
    return {"success": True, "data": user, "message": "User deactivated"}
