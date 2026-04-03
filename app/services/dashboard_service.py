import json

from app.database import supabase
from app.redis import redis

CACHE_TTL = 300  # 5 minutes


def get_summary() -> dict:
    cache_key = "dashboard:summary"
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)

    response = (
        supabase.table("records")
        .select("amount, type")
        .eq("is_deleted", False)
        .execute()
    )
    records = response.data

    total_income = sum(r["amount"] for r in records if r["type"] == "income")
    total_expense = sum(r["amount"] for r in records if r["type"] == "expense")

    result = {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_balance": round(total_income - total_expense, 2),
        "record_count": len(records),
    }

    redis.set(cache_key, json.dumps(result), ex=CACHE_TTL)
    return result


def get_category_totals() -> dict:
    cache_key = "dashboard:categories"
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)

    response = (
        supabase.table("records")
        .select("category, type, amount")
        .eq("is_deleted", False)
        .execute()
    )

    totals: dict = {}
    for r in response.data:
        key = (r["category"], r["type"])
        if key not in totals:
            totals[key] = {"category": r["category"], "type": r["type"], "total": 0.0, "count": 0}
        totals[key]["total"] += r["amount"]
        totals[key]["count"] += 1

    result = {
        "data": [
            {**v, "total": round(v["total"], 2)}
            for v in sorted(totals.values(), key=lambda x: x["total"], reverse=True)
        ]
    }

    redis.set(cache_key, json.dumps(result), ex=CACHE_TTL)
    return result


def get_recent(limit: int = 10) -> dict:
    cache_key = f"dashboard:recent:{limit}"
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)

    response = (
        supabase.table("records")
        .select("id, amount, type, category, date, notes, user_id")
        .eq("is_deleted", False)
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )

    result = {"data": response.data}
    redis.set(cache_key, json.dumps(result), ex=CACHE_TTL)
    return result
