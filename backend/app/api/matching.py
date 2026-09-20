from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.models.orm import Analysis, Job, Resume
from app.providers.factory import get_embedding_provider
from app.scoring.ats_analyzer import analyze_ats
from app.scoring.compatibility_score import compute_compatibility_score
from app.scoring.matching_engine import run_matching
from app.services.rehydrate import jd_from_json, resume_from_json

router = APIRouter(prefix="/api/v1/matching", tags=["matching"])


class MatchRequest(BaseModel):
    resume_id: str
    job_id: str


class MatchResponse(BaseModel):
    id: str
    resume_id: str
    job_id: str
    compatibility: dict
    match: dict
    ats: dict


def _run_analysis(resume_row: Resume, job_row: Job) -> tuple[dict, dict, dict]:
    resume = resume_from_json(resume_row.parsed_json)
    jd = jd_from_json(job_row.parsed_json)

    embedder = get_embedding_provider()
    match_result = run_matching(resume, jd, embedder)
    ats_result = analyze_ats(resume)
    score = compute_compatibility_score(resume, jd, match_result, ats_result)

    return score.to_dict(), match_result.to_dict(), ats_result.to_dict()


@router.post("/analyze", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
def analyze_match(payload: MatchRequest, db: Session = Depends(get_db)):
    resume_row = db.get(Resume, payload.resume_id)
    if not resume_row:
        raise AppError(404, "RESUME_NOT_FOUND", "Resume not found.")
    job_row = db.get(Job, payload.job_id)
    if not job_row:
        raise AppError(404, "JOB_NOT_FOUND", "Job not found.")

    score_dict, match_dict, ats_dict = _run_analysis(resume_row, job_row)

    analysis = Analysis(
        resume_id=resume_row.id,
        job_id=job_row.id,
        compatibility_score=score_dict["overall"],
        match_json=match_dict,
        score_json=score_dict,
        ats_json=ats_dict,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return MatchResponse(
        id=analysis.id, resume_id=resume_row.id, job_id=job_row.id,
        compatibility=score_dict, match=match_dict, ats=ats_dict,
    )


@router.get("/{analysis_id}", response_model=MatchResponse)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise AppError(404, "ANALYSIS_NOT_FOUND", "Analysis not found.")
    return MatchResponse(
        id=analysis.id, resume_id=analysis.resume_id, job_id=analysis.job_id,
        compatibility=analysis.score_json, match=analysis.match_json, ats=analysis.ats_json,
    )


@router.post("/compare", status_code=status.HTTP_200_OK)
def compare_jobs(resume_id: str, job_ids: list[str], db: Session = Depends(get_db)):
    """Phase 32: compare one resume against multiple jobs, ranked but with
    full criteria breakdown shown (never a bare ranked list)."""
    resume_row = db.get(Resume, resume_id)
    if not resume_row:
        raise AppError(404, "RESUME_NOT_FOUND", "Resume not found.")

    results = []
    for job_id in job_ids:
        job_row = db.get(Job, job_id)
        if not job_row:
            continue
        score_dict, match_dict, _ats = _run_analysis(resume_row, job_row)
        results.append({
            "job_id": job_id,
            "job_title": job_row.title,
            "overall": score_dict["overall"],
            "required_skill_coverage": match_dict["required_skill_coverage"],
            "missing_required_skills": match_dict["missing_required_skills"],
        })

    results.sort(key=lambda r: r["overall"], reverse=True)
    return {"resume_id": resume_id, "comparisons": results}
