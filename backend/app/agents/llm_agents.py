"""LLM-backed agents: recommendations, resume optimization, interview prep,
learning roadmap. Each wraps the corresponding function in
app/services/recommendation_service.py — the agent's only job is to pull
its inputs from the shared AgentContext and write its output back, so the
Supervisor can run these interchangeably with the deterministic agents."""

from __future__ import annotations

from app.agents.base import Agent, AgentContext
from app.providers.base import LLMProvider
from app.retrieval.knowledge_base import KnowledgeBase
from app.services import recommendation_service as rec


class RecommendationAgent(Agent):
    name = "recommendation_agent"

    def __init__(self, llm: LLMProvider, knowledge_base: KnowledgeBase | None = None):
        self.llm = llm
        self.knowledge_base = knowledge_base

    def run(self, ctx: AgentContext) -> AgentContext:
        resume, job, gap = ctx.get("resume"), ctx.get("job"), ctx.get("skill_gap")
        if not (resume and job and gap):
            return ctx
        result = rec.generate_recommendations(
            self.llm, resume.raw_text, job.raw_text if hasattr(job, "raw_text") else ctx.get("jd_text", ""),
            gap["missing_skills"], gap["strong_matches"] + gap["partial_matches"], self.knowledge_base,
        )
        ctx.set("recommendations", result)
        return ctx


class ResumeOptimizationAgent(Agent):
    name = "resume_optimization_agent"

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def run(self, ctx: AgentContext) -> AgentContext:
        resume, gap = ctx.get("resume"), ctx.get("skill_gap")
        jd_text = ctx.get("jd_text", "")
        if not (resume and gap):
            return ctx
        result = rec.optimize_resume(self.llm, resume.raw_text, jd_text, gap["strong_matches"] + gap["partial_matches"])
        ctx.set("optimization", result)
        return ctx


class InterviewPreparationAgent(Agent):
    name = "interview_preparation_agent"

    def __init__(self, llm: LLMProvider, knowledge_base: KnowledgeBase | None = None):
        self.llm = llm
        self.knowledge_base = knowledge_base

    def run(self, ctx: AgentContext) -> AgentContext:
        resume, gap = ctx.get("resume"), ctx.get("skill_gap")
        jd_text = ctx.get("jd_text", "")
        if not (resume and gap):
            return ctx
        result = rec.generate_interview_questions(
            self.llm, resume.raw_text, jd_text, gap["missing_skills"],
            gap["strong_matches"] + gap["partial_matches"], self.knowledge_base,
        )
        ctx.set("interview_questions", result)
        return ctx


class RoadmapAgent(Agent):
    name = "roadmap_agent"

    def __init__(self, llm: LLMProvider, knowledge_base: KnowledgeBase | None = None):
        self.llm = llm
        self.knowledge_base = knowledge_base

    def run(self, ctx: AgentContext) -> AgentContext:
        gap = ctx.get("skill_gap")
        jd_text = ctx.get("jd_text", "")
        if not gap:
            return ctx
        result = rec.generate_learning_roadmap(self.llm, jd_text, gap["missing_skills"], self.knowledge_base)
        ctx.set("roadmap", result)
        return ctx
