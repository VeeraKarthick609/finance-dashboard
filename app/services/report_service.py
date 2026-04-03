"""
DungBeetle-inspired async report engine.

Pattern (from Zerodha's DungBeetle):
  1. Client POSTs a report request → gets a job_id immediately (202 Accepted)
  2. Job is stored in Redis with status "pending" and pushed onto a Redis list queue
  3. A FastAPI BackgroundTask picks it up and runs the report query
  4. Result is written back to Redis; client polls GET /api/reports/{job_id}
"""

import json
import uuid
import datetime
from collections import defaultdict
from typing import Optional

from app.database import supabase
from app.exceptions import AppError
from app.redis import redis

QUEUE_KEY = "reports:queue"
JOB_TTL = 3600  # 1 hour


def _job_key(job_id: str) -> str:
    return f"reports:job:{job_id}"


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def submit_job(report_type: str, start_date: Optional[str], end_date: Optional[str]) -> dict:
    """Create a new report job, enqueue it, and return the job record."""
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "status": "pending",
        "type": report_type,
        "params": {"start_date": start_date, "end_date": end_date},
        "result": None,
        "error": None,
        "created_at": _now(),
        "updated_at": _now(),
    }
    redis.set(_job_key(job_id), json.dumps(job), ex=JOB_TTL)
    redis.rpush(QUEUE_KEY, job_id)
    return job


def get_job(job_id: str) -> dict:
    """Fetch a job's current state from Redis."""
    raw = redis.get(_job_key(job_id))
    if not raw:
        raise AppError(404, "Report job not found or expired")
    return json.loads(raw)


def process_job(job_id: str) -> None:
    """Background worker: run the report and persist the result."""
    raw = redis.get(_job_key(job_id))
    if not raw:
        return

    job = json.loads(raw)

    # Mark processing
    job["status"] = "processing"
    job["updated_at"] = _now()
    redis.set(_job_key(job_id), json.dumps(job), ex=JOB_TTL)

    try:
        job["result"] = _run_report(job["type"], job["params"])
        job["status"] = "completed"
    except Exception as exc:
        job["status"] = "failed"
        job["error"] = str(exc)

    job["updated_at"] = _now()
    redis.set(_job_key(job_id), json.dumps(job), ex=JOB_TTL)


# ---------------------------------------------------------------------------
# Report runners
# ---------------------------------------------------------------------------

def _run_report(report_type: str, params: dict) -> dict:
    start_date = params.get("start_date")
    end_date = params.get("end_date")

    query = (
        supabase.table("records")
        .select("amount, type, category, date")
        .eq("is_deleted", False)
    )
    if start_date:
        query = query.gte("date", start_date)
    if end_date:
        query = query.lte("date", end_date)

    records = query.execute().data

    runners = {
        "monthly_trends": _monthly_trends,
        "weekly_trends": _weekly_trends,
        "category_breakdown": _category_breakdown,
        "income_vs_expense": _income_vs_expense,
    }
    return runners[report_type](records)


def _monthly_trends(records: list) -> dict:
    buckets: dict = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for r in records:
        month = r["date"][:7]  # "YYYY-MM"
        buckets[month][r["type"]] += r["amount"]

    return {
        "trends": [
            {
                "period": month,
                "income": round(buckets[month]["income"], 2),
                "expense": round(buckets[month]["expense"], 2),
                "net": round(buckets[month]["income"] - buckets[month]["expense"], 2),
            }
            for month in sorted(buckets)
        ]
    }


def _weekly_trends(records: list) -> dict:
    buckets: dict = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for r in records:
        d = datetime.date.fromisoformat(r["date"])
        iso = d.isocalendar()
        week = f"{iso.year}-W{iso.week:02d}"
        buckets[week][r["type"]] += r["amount"]

    return {
        "trends": [
            {
                "period": week,
                "income": round(buckets[week]["income"], 2),
                "expense": round(buckets[week]["expense"], 2),
                "net": round(buckets[week]["income"] - buckets[week]["expense"], 2),
            }
            for week in sorted(buckets)
        ]
    }


def _category_breakdown(records: list) -> dict:
    buckets: dict = defaultdict(lambda: {"income": 0.0, "expense": 0.0, "count": 0})
    for r in records:
        buckets[r["category"]][r["type"]] += r["amount"]
        buckets[r["category"]]["count"] += 1

    return {
        "breakdown": [
            {
                "category": cat,
                "income": round(data["income"], 2),
                "expense": round(data["expense"], 2),
                "total": round(data["income"] + data["expense"], 2),
                "count": data["count"],
            }
            for cat, data in sorted(
                buckets.items(), key=lambda x: x[1]["income"] + x[1]["expense"], reverse=True
            )
        ]
    }


def _income_vs_expense(records: list) -> dict:
    total_income = sum(r["amount"] for r in records if r["type"] == "income")
    total_expense = sum(r["amount"] for r in records if r["type"] == "expense")
    income_count = sum(1 for r in records if r["type"] == "income")
    expense_count = sum(1 for r in records if r["type"] == "expense")

    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net": round(total_income - total_expense, 2),
        "income_count": income_count,
        "expense_count": expense_count,
        "avg_income": round(total_income / income_count, 2) if income_count else 0.0,
        "avg_expense": round(total_expense / expense_count, 2) if expense_count else 0.0,
    }
