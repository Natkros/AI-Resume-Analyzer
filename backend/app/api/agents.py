"""Phase 9 API surface: run the full agent pipeline (deterministic agents
always; LLM reasoning agents optionally) against an already-uploaded resume
and job, and return the Phase 64 consolidated report."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.supervisor import run_pipeline
from app.api.deps import get_optional_user, require_ownership
from app.core.database import get_db
from app.core.errors import AppError
from app.models.orm import Job, Resume, User
from app.providers.factory import get_llm_provider
from app.retrieval.knowledge_base import get_knowledge_base
from app.services.rehydrate import resume_from_json

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


class AgentPipelineRequest(BaseModel):
    resume_id: str
    job_id: str
    include_llm_agents: bool = False


@router.post("/analyze")
def analyze_with_agents(
    payload: AgentPipelineRequest, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)
):
    resume_row = db.get(Resume, payload.resume_id)
    if not resume_row:
        raise AppError(404, "RESUME_NOT_FOUND", "Resume not found.")
    require_ownership(resume_row, user)
    job_row = db.get(Job, payload.job_id)
    if not job_row:
        raise AppError(404, "JOB_NOT_FOUND", "Job not found.")

    llm = None
    if payload.include_llm_agents:
        try:
            llm = get_llm_provider()
        except Exception:
            llm = None  # degrade gracefully: report still includes the deterministic sections

    result = run_pipeline(
        resume_preparsed=resume_from_json(resume_row.parsed_json),
        jd_text=job_row.raw_text,
        llm=llm,
        knowledge_base=get_knowledge_base() if llm else None,
        include_llm_agents=payload.include_llm_agents and llm is not None,
    )
    return result.to_report()
