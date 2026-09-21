"""Phase 39 API surface: enqueue expensive pipeline steps to Celery instead
of blocking the request. Requires a running worker + Redis broker
(`celery -A app.workers.celery_app worker`); the synchronous endpoints in
resumes.py/jobs.py/matching.py remain available and are what local dev /
the test suite exercise by default.
"""

from fastapi import APIRouter, Depends, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.models.orm import Job, Resume
from app.workers.celery_app import celery_app
from app.workers.tasks import analyze_match_task, parse_job_task, parse_resume_task

router = APIRouter(prefix="/api/v1/async", tags=["async"])


class TaskAccepted(BaseModel):
    task_id: str
    status: str = "queued"
    poll_url: str


class MatchRequest(BaseModel):
    resume_id: str
    job_id: str


class JobRequest(BaseModel):
    text: str


@router.post("/resumes/upload", response_model=TaskAccepted, status_code=status.HTTP_202_ACCEPTED)
async def upload_resume_async(file: UploadFile, db: Session = Depends(get_db)):
    if not file.filename:
        raise AppError(400, "MISSING_FILENAME", "Uploaded file has no filename.")
    file_bytes = await file.read()

    # Create the row immediately (empty parse) so the caller has a stable
    # resume_id to poll/reference right away; the worker fills it in.
    resume = Resume(filename=file.filename, raw_text="", parsed_json={}, used_ocr=False)
    db.add(resume)
    db.commit()
    db.refresh(resume)

    task = parse_resume_task.delay(resume.id, file_bytes, file.filename)
    return TaskAccepted(task_id=task.id, poll_url=f"/api/v1/async/tasks/{task.id}")


@router.post("/jobs/analyze", response_model=TaskAccepted, status_code=status.HTTP_202_ACCEPTED)
def analyze_job_async(payload: JobRequest, db: Session = Depends(get_db)):
    if not payload.text.strip():
        raise AppError(400, "EMPTY_JOB_DESCRIPTION", "Job description text is empty.")
    job = Job(raw_text=payload.text, parsed_json={})
    db.add(job)
    db.commit()
    db.refresh(job)

    task = parse_job_task.delay(job.id, payload.text)
    return TaskAccepted(task_id=task.id, poll_url=f"/api/v1/async/tasks/{task.id}")


@router.post("/matching/analyze", response_model=TaskAccepted, status_code=status.HTTP_202_ACCEPTED)
def analyze_match_async(payload: MatchRequest):
    task = analyze_match_task.delay(payload.resume_id, payload.job_id)
    return TaskAccepted(task_id=task.id, poll_url=f"/api/v1/async/tasks/{task.id}")


@router.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,  # PENDING | STARTED | SUCCESS | FAILURE | RETRY
        "result": result.result if result.successful() else None,
        "error": str(result.result) if result.failed() else None,
    }
