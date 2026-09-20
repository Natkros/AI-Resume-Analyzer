from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user
from app.core.database import get_db
from app.core.errors import AppError
from app.models.orm import Job, User
from app.pipelines.jd_parser import parse_job_description

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


class JobCreateRequest(BaseModel):
    text: str
    company: str | None = None


class JobDetail(BaseModel):
    id: str
    title: str | None
    company: str | None
    parsed: dict

    class Config:
        from_attributes = True


@router.post("/analyze", response_model=JobDetail, status_code=status.HTTP_201_CREATED)
def analyze_job(
    payload: JobCreateRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if not payload.text.strip():
        raise AppError(400, "EMPTY_JOB_DESCRIPTION", "Job description text is empty.")

    parsed = parse_job_description(payload.text)
    job = Job(
        owner_id=user.id if user else None,
        title=parsed.job_title,
        company=payload.company,
        raw_text=payload.text,
        parsed_json=parsed.to_dict(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return JobDetail(id=job.id, title=job.title, company=job.company, parsed=job.parsed_json)


@router.get("/{job_id}", response_model=JobDetail)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise AppError(404, "JOB_NOT_FOUND", "Job not found.")
    return JobDetail(id=job.id, title=job.title, company=job.company, parsed=job.parsed_json)
