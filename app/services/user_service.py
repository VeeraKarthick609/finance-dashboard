from app.database import supabase
from app.exceptions import AppError


def _user_without_password(user: dict) -> dict:
    return {k: v for k, v in user.items() if k != "password"}


def list_users(
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> dict:
    query = supabase.table("users").select(
        "id, email, name, role, is_active, created_at, updated_at", count="exact"
    )

    if search:
        query = query.or_(f"name.ilike.%{search}%,email.ilike.%{search}%")
    if role:
        query = query.eq("role", role)
    if is_active is not None:
        query = query.eq("is_active", is_active)

    query = query.order("created_at", desc=True)
    offset = (page - 1) * limit
    query = query.range(offset, offset + limit - 1)

    response = query.execute()
    total = response.count or 0

    return {
        "data": response.data,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": max(1, -(-total // limit)),  # ceiling division
        },
    }


def get_user(user_id: str) -> dict:
    response = (
        supabase.table("users")
        .select("id, email, name, role, is_active, created_at, updated_at")
        .eq("id", user_id)
        .execute()
    )

    if not response.data:
        raise AppError(404, "User not found")

    return response.data[0]


def update_user(user_id: str, data: dict, current_user_id: str) -> dict:
    # Prevent admin from demoting themselves
    if user_id == current_user_id and "role" in data:
        raise AppError(400, "Cannot change your own role")

    # Check user exists
    get_user(user_id)

    # Filter out None values
    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        raise AppError(400, "No fields to update")

    response = (
        supabase.table("users")
        .update(update_data)
        .eq("id", user_id)
        .execute()
    )

    return _user_without_password(response.data[0])


def deactivate_user(user_id: str, current_user_id: str) -> dict:
    if user_id == current_user_id:
        raise AppError(400, "Cannot deactivate your own account")

    get_user(user_id)

    response = (
        supabase.table("users")
        .update({"is_active": False})
        .eq("id", user_id)
        .execute()
    )

    return _user_without_password(response.data[0])
