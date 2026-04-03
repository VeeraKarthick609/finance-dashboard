from fastapi import APIRouter, Depends, BackgroundTasks

from app.dependencies import require_role
from app.models.report import CreateReportRequest
from app.services import report_service

router = APIRouter()


@router.post("", status_code=202)
async def submit_report(
    body: CreateReportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role("analyst", "admin")),
):
    job = report_service.submit_job(body.type, body.start_date, body.end_date)
    background_tasks.add_task(report_service.process_job, job["job_id"])
    return {"success": True, "data": job, "message": "Report job queued"}


@router.get("/{job_id}")
async def get_report(
    job_id: str,
    current_user: dict = Depends(require_role("analyst", "admin")),
):
    job = report_service.get_job(job_id)
    return {"success": True, "data": job}
