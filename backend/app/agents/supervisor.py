"""Phase 9: supervisor orchestrator. Runs the deterministic agent pipeline
(always) and, if an LLM provider is available and requested, the reasoning
agents on top, then assembles the Phase 64 final report format.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.base import AgentContext
from app.agents.deterministic_agents import (
    ATSAnalysisAgent,
    GapAnalysisAgent,
    JobRequirementAgent,
    ResumeParserAgent,
    ScoringAgent,
    SkillMatchingAgent,
)
from app.agents.llm_agents import InterviewPreparationAgent, RecommendationAgent, ResumeOptimizationAgent, RoadmapAgent
from app.providers.base import LLMProvider
from app.retrieval.knowledge_base import KnowledgeBase


@dataclass
class SupervisorResult:
    context: AgentContext

    def to_report(self) -> dict:
        """Phase 64 final report format."""
        ctx = self.context
        resume = ctx.get("resume")
        job = ctx.get("job")
        score = ctx.get("compatibility_score")
        gap = ctx.get("skill_gap") or {}
        ats = ctx.get("ats_result")

        return {
            "candidate": {
                "name": getattr(resume.candidate, "email", None) if resume else None,
                "target_role": getattr(job, "job_title", None) if job else None,
            },
            "compatibility": score.to_dict() if score else None,
            "strong_matches": gap.get("strong_matches", []),
            "partial_matches": gap.get("partial_matches", []),
            "missing_requirements": gap.get("missing_skills", []),
            "ats_issues": ats.to_dict() if ats else None,
            "resume_improvements": ctx.get("optimization"),
            "recommendations": ctx.get("recommendations"),
            "interview_preparation": ctx.get("interview_questions"),
            "skill_gap_roadmap": ctx.get("roadmap"),
            "agent_errors": ctx.errors,
        }


def run_pipeline(
    resume_file_bytes: bytes | None = None,
    resume_filename: str | None = None,
    resume_preparsed=None,
    jd_text: str = "",
    jd_preparsed=None,
    llm: LLMProvider | None = None,
    knowledge_base: KnowledgeBase | None = None,
    include_llm_agents: bool = False,
) -> SupervisorResult:
    ctx = AgentContext()
    ctx.set("resume_file_bytes", resume_file_bytes)
    ctx.set("resume_filename", resume_filename)
    ctx.set("jd_text", jd_text)
    if resume_preparsed is not None:
        ctx.set("resume", resume_preparsed)
    if jd_preparsed is not None:
        ctx.set("job", jd_preparsed)

    deterministic_pipeline = [
        ResumeParserAgent(),
        JobRequirementAgent(),
        SkillMatchingAgent(),
        ATSAnalysisAgent(),
        GapAnalysisAgent(),
        ScoringAgent(),
    ]
    for agent in deterministic_pipeline:
        ctx = agent.run_safely(ctx)

    if include_llm_agents and llm is not None:
        llm_pipeline = [
            RecommendationAgent(llm, knowledge_base),
            ResumeOptimizationAgent(llm),
            InterviewPreparationAgent(llm, knowledge_base),
            RoadmapAgent(llm, knowledge_base),
        ]
        for agent in llm_pipeline:
            ctx = agent.run_safely(ctx)

    return SupervisorResult(context=ctx)
