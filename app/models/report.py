from typing import Optional, Any

from pydantic import BaseModel, Field


class CreateReportRequest(BaseModel):
    type: str = Field(pattern=r"^(monthly_trends|weekly_trends|category_breakdown|income_vs_expense)$")
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ReportJobResponse(BaseModel):
    job_id: str
    status: str  # pending | processing | completed | failed
    type: str
    params: dict
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str
