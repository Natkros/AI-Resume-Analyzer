from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.models.orm import Analysis, Job, Resume
from app.providers.factory import LLMUnavailableError, get_llm_provider
from app.services import recommendation_service as rec

router = APIRouter(prefix="/api/v1", tags=["recommendations"])


class AnalysisRefRequest(BaseModel):
    analysis_id: str


def _load_context(analysis_id: str, db: Session):
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise AppError(404, "ANALYSIS_NOT_FOUND", "Analysis not found.")
    resume = db.get(Resume, analysis.resume_id)
    job = db.get(Job, analysis.job_id)
    matched = [m["skill"] for m in analysis.match_json.get("required_skill_matches", [])]
    missing = analysis.match_json.get("missing_required_skills", [])
    return resume, job, matched, missing


def _llm_or_503():
    try:
        return get_llm_provider()
    except LLMUnavailableError as exc:
        raise AppError(503, "LLM_UNAVAILABLE", str(exc)) from exc


@router.post("/resumes/{analysis_id}/optimize")
def optimize(analysis_id: str, db: Session = Depends(get_db)):
    resume, job, matched, _missing = _load_context(analysis_id, db)
    llm = _llm_or_503()
    return rec.optimize_resume(llm, resume.raw_text, job.raw_text, matched)


@router.post("/interview/generate")
def interview(payload: AnalysisRefRequest, db: Session = Depends(get_db)):
    resume, job, matched, missing = _load_context(payload.analysis_id, db)
    llm = _llm_or_503()
    return rec.generate_interview_questions(llm, resume.raw_text, job.raw_text, missing, matched)


@router.post("/roadmap/generate")
def roadmap(payload: AnalysisRefRequest, db: Session = Depends(get_db)):
    resume, job, _matched, missing = _load_context(payload.analysis_id, db)
    llm = _llm_or_503()
    return rec.generate_learning_roadmap(llm, job.raw_text, missing)


@router.post("/matching/{analysis_id}/recommendations")
def recommendations(analysis_id: str, db: Session = Depends(get_db)):
    resume, job, matched, missing = _load_context(analysis_id, db)
    llm = _llm_or_503()
    return rec.generate_recommendations(llm, resume.raw_text, job.raw_text, missing, matched)
