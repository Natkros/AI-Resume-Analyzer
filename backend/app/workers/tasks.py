"""Phase 39 background tasks. Each task opens its own DB session (workers
run in a separate process from the API, so the FastAPI request-scoped
session cannot be reused) and writes its result to the same tables the
synchronous API endpoints use, so callers can poll via the normal
GET /api/v1/resumes/{id} etc. regardless of whether the work ran sync or
async.
"""

from __future__ import annotations

from app.core.database import SessionLocal
from app.models.orm import Analysis, Job, Resume
from app.pipelines.jd_parser import parse_job_description
from app.pipelines.resume_parser import parse_resume
from app.providers.factory import get_embedding_provider
from app.scoring.ats_analyzer import analyze_ats
from app.scoring.compatibility_score import compute_compatibility_score
from app.scoring.matching_engine import run_matching
from app.services.rehydrate import jd_from_json, resume_from_json
from app.workers.celery_app import celery_app


@celery_app.task(name="tasks.parse_resume_task", bind=True, max_retries=2)
def parse_resume_task(self, resume_id: str, file_bytes: bytes, filename: str):
    db = SessionLocal()
    try:
        parsed = parse_resume(file_bytes, filename)
        resume = db.get(Resume, resume_id)
        if resume is None:
            return {"status": "not_found", "resume_id": resume_id}
        resume.raw_text = parsed.raw_text
        resume.parsed_json = parsed.to_dict()
        resume.used_ocr = parsed.used_ocr
        db.commit()
        return {"status": "done", "resume_id": resume_id}
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=5) from exc
    finally:
        db.close()


@celery_app.task(name="tasks.parse_job_task")
def parse_job_task(job_id: str, text: str):
    db = SessionLocal()
    try:
        parsed = parse_job_description(text)
        job = db.get(Job, job_id)
        if job is None:
            return {"status": "not_found", "job_id": job_id}
        job.title = parsed.job_title
        job.parsed_json = parsed.to_dict()
        db.commit()
        return {"status": "done", "job_id": job_id}
    finally:
        db.close()


@celery_app.task(name="tasks.analyze_match_task", bind=True, max_retries=2)
def analyze_match_task(self, resume_id: str, job_id: str):
    db = SessionLocal()
    try:
        resume_row = db.get(Resume, resume_id)
        job_row = db.get(Job, job_id)
        if resume_row is None or job_row is None:
            return {"status": "not_found"}

        resume = resume_from_json(resume_row.parsed_json)
        jd = jd_from_json(job_row.parsed_json)
        embedder = get_embedding_provider()

        match_result = run_matching(resume, jd, embedder)
        ats_result = analyze_ats(resume)
        score = compute_compatibility_score(resume, jd, match_result, ats_result)

        analysis = Analysis(
            resume_id=resume_id, job_id=job_id, compatibility_score=score.to_dict()["overall"],
            match_json=match_result.to_dict(), score_json=score.to_dict(), ats_json=ats_result.to_dict(),
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return {"status": "done", "analysis_id": analysis.id}
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=5) from exc
    finally:
        db.close()
