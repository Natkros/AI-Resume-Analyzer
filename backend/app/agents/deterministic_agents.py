"""Deterministic pipeline steps wrapped as agents: parser, JD analyzer,
matcher, ATS analyzer, gap analyzer. No LLM calls here — see
app/agents/llm_agents.py for the reasoning agents."""

from __future__ import annotations

from app.agents.base import Agent, AgentContext
from app.pipelines.jd_parser import parse_job_description
from app.pipelines.resume_parser import parse_resume
from app.providers.factory import get_embedding_provider
from app.scoring.ats_analyzer import analyze_ats
from app.scoring.compatibility_score import compute_compatibility_score
from app.scoring.matching_engine import run_matching


class ResumeParserAgent(Agent):
    name = "resume_parser"

    def run(self, ctx: AgentContext) -> AgentContext:
        file_bytes = ctx.get("resume_file_bytes")
        filename = ctx.get("resume_filename")
        if file_bytes is not None:
            parsed = parse_resume(file_bytes, filename)
            ctx.set("resume", parsed)
        return ctx


class JobRequirementAgent(Agent):
    name = "job_requirement_analyzer"

    def run(self, ctx: AgentContext) -> AgentContext:
        jd_text = ctx.get("jd_text")
        if jd_text:
            ctx.set("job", parse_job_description(jd_text))
        return ctx


class SkillMatchingAgent(Agent):
    name = "skill_matcher"

    def run(self, ctx: AgentContext) -> AgentContext:
        resume, job = ctx.get("resume"), ctx.get("job")
        if resume and job:
            embedder = get_embedding_provider()
            ctx.set("match_result", run_matching(resume, job, embedder))
        return ctx


class ATSAnalysisAgent(Agent):
    name = "ats_analyzer"

    def run(self, ctx: AgentContext) -> AgentContext:
        resume = ctx.get("resume")
        if resume:
            ctx.set("ats_result", analyze_ats(resume))
        return ctx


class GapAnalysisAgent(Agent):
    """Consolidates the matcher's output into strong/partial/missing skill
    buckets, per Phase 18. Deterministic: it only reclassifies data the
    matching engine already produced."""

    name = "gap_analyzer"

    def run(self, ctx: AgentContext) -> AgentContext:
        match_result = ctx.get("match_result")
        if not match_result:
            return ctx
        strong = [m.skill for m in match_result.required_skill_matches if m.confidence == "high"]
        partial = [m.skill for m in match_result.required_skill_matches if m.confidence != "high"] + [
            m.skill for m in match_result.preferred_skill_matches
        ]
        missing = match_result.missing_required_skills
        ctx.set("skill_gap", {"strong_matches": strong, "partial_matches": partial, "missing_skills": missing})
        return ctx


class ScoringAgent(Agent):
    name = "scoring_agent"

    def run(self, ctx: AgentContext) -> AgentContext:
        resume, job = ctx.get("resume"), ctx.get("job")
        match_result, ats_result = ctx.get("match_result"), ctx.get("ats_result")
        if resume and job and match_result and ats_result:
            ctx.set("compatibility_score", compute_compatibility_score(resume, job, match_result, ats_result))
        return ctx
