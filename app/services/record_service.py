from app.database import supabase
from app.exceptions import AppError


def _record_response(record: dict) -> dict:
    return {k: v for k, v in record.items() if k != "is_deleted"}


def list_records(
    page: int = 1,
    limit: int = 20,
    type: str | None = None,
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    search: str | None = None,
    sort_by: str = "date",
    order: str = "desc",
) -> dict:
    query = supabase.table("records").select(
        "id, amount, type, category, date, notes, user_id, created_at, updated_at",
        count="exact",
    )

    # Always exclude soft-deleted
    query = query.eq("is_deleted", False)

    if type:
        query = query.eq("type", type)
    if category:
        query = query.ilike("category", f"%{category}%")
    if start_date:
        query = query.gte("date", start_date)
    if end_date:
        query = query.lte("date", end_date)
    if search:
        query = query.or_(f"notes.ilike.%{search}%,category.ilike.%{search}%")

    # Sorting
    desc = order == "desc"
    if sort_by in ("date", "amount", "created_at"):
        query = query.order(sort_by, desc=desc)
    else:
        query = query.order("date", desc=True)

    # Pagination
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
            "total_pages": max(1, -(-total // limit)),
        },
    }


def get_record(record_id: str) -> dict:
    response = (
        supabase.table("records")
        .select("id, amount, type, category, date, notes, user_id, created_at, updated_at")
        .eq("id", record_id)
        .eq("is_deleted", False)
        .execute()
    )

    if not response.data:
        raise AppError(404, "Record not found")

    return response.data[0]


def create_record(data: dict, user_id: str) -> dict:
    record_data = {
        **data,
        "date": str(data["date"]),
        "user_id": user_id,
    }

    response = supabase.table("records").insert(record_data).execute()
    return _record_response(response.data[0])


def update_record(record_id: str, data: dict) -> dict:
    # Check exists and not deleted
    get_record(record_id)

    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        raise AppError(400, "No fields to update")

    # Convert date to string if present
    if "date" in update_data:
        update_data["date"] = str(update_data["date"])

    response = (
        supabase.table("records")
        .update(update_data)
        .eq("id", record_id)
        .execute()
    )

    return _record_response(response.data[0])


def bulk_create_records(records: list[dict], user_id: str) -> list[dict]:
    records_data = [
        {**r, "date": str(r["date"]), "user_id": user_id}
        for r in records
    ]
    response = supabase.table("records").insert(records_data).execute()
    return [_record_response(r) for r in response.data]


def soft_delete_record(record_id: str) -> dict:
    get_record(record_id)

    response = (
        supabase.table("records")
        .update({"is_deleted": True})
        .eq("id", record_id)
        .execute()
    )

    return _record_response(response.data[0])
