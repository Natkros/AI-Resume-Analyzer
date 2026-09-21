from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_user, require_ownership
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


@router.get("", response_model=list[JobDetail])
def list_my_jobs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    jobs = db.query(Job).filter(Job.owner_id == user.id).order_by(Job.created_at.desc()).all()
    return [JobDetail(id=j.id, title=j.title, company=j.company, parsed=j.parsed_json) for j in jobs]


@router.get("/{job_id}", response_model=JobDetail)
def get_job(job_id: str, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    job = db.get(Job, job_id)
    if not job:
        raise AppError(404, "JOB_NOT_FOUND", "Job not found.")
    require_ownership(job, user)
    return JobDetail(id=job.id, title=job.title, company=job.company, parsed=job.parsed_json)
