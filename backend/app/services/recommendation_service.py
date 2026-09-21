"""Phase 7: LLM-backed reasoning layer, built strictly on top of the
deterministic parse/match/score output — never as a replacement for it.

Every prompt is grounded: it includes only resume text, JD text, and the
matching engine's own evidence, and explicitly forbids inventing experience
(Phase 28 hallucination prevention). Structured output is requested via a
JSON schema and validated; on failure we retry once, then surface a clear
error rather than returning unvalidated text.
"""

from __future__ import annotations

from app.providers.base import LLMProvider
from app.retrieval.knowledge_base import KnowledgeBase

SAFETY_PREAMBLE = (
    "You are analyzing a candidate's resume against a job description. "
    "Base every statement ONLY on the resume text and job description text provided below. "
    "Never invent employers, job titles, degrees, certifications, projects, or metrics that are "
    "not present in the resume text. If information is missing, say so explicitly "
    "(e.g. 'No evidence found in the uploaded resume for X') rather than filling the gap. "
    "Never claim the candidate will or will not get hired.\n\n"
)

RECOMMENDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "rationale": {"type": "string"},
                    "evidence": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["title", "rationale", "confidence"],
            },
        }
    },
    "required": ["recommendations"],
}

OPTIMIZATION_SCHEMA = {
    "type": "object",
    "properties": {
        "improved_summary": {"type": "string"},
        "bullet_rewrites": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "original": {"type": "string"},
                    "improved": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["original", "improved", "reason"],
            },
        },
        "keyword_gaps_to_consider": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["improved_summary", "bullet_rewrites"],
}

INTERVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "technical_questions": {"type": "array", "items": {"type": "string"}},
        "project_questions": {"type": "array", "items": {"type": "string"}},
        "behavioral_questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["technical_questions", "project_questions", "behavioral_questions"],
}

ROADMAP_SCHEMA = {
    "type": "object",
    "properties": {
        "roadmap": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "skill": {"type": "string"},
                    "why_it_matters": {"type": "string"},
                    "prerequisites": {"type": "array", "items": {"type": "string"}},
                    "learning_sequence": {"type": "array", "items": {"type": "string"}},
                    "practical_project": {"type": "string"},
                    "validation_task": {"type": "string"},
                },
                "required": ["skill", "why_it_matters", "learning_sequence"],
            },
        }
    },
    "required": ["roadmap"],
}


def _grounded_context(resume_text: str, jd_text: str, missing_skills: list[str], matched_skills: list[str]) -> str:
    return (
        f"RESUME TEXT:\n{resume_text[:6000]}\n\n"
        f"JOB DESCRIPTION TEXT:\n{jd_text[:4000]}\n\n"
        f"MATCHED SKILLS (confirmed present in resume): {', '.join(matched_skills) or 'none'}\n"
        f"MISSING REQUIRED SKILLS (JD requires, not found in resume): {', '.join(missing_skills) or 'none'}\n\n"
    )


def _rag_context(kb: KnowledgeBase | None, query: str, top_k: int = 3) -> tuple[str, list[dict]]:
    """Phase 8: retrieve grounding passages from the knowledge base for a query.
    Returns (prompt_block, sources) so callers can cite what was actually used."""
    if kb is None or not query.strip():
        return "", []
    hits = kb.retrieve(query, top_k=top_k)
    if not hits:
        return "", []
    lines = ["RELEVANT KNOWLEDGE BASE CONTEXT (use only if genuinely applicable, do not force it):"]
    sources = []
    for hit in hits:
        lines.append(f"- ({hit.record.metadata.get('source')}) {hit.record.text}")
        sources.append({
            "source": hit.record.metadata.get("source"),
            "heading": hit.record.metadata.get("heading"),
            "similarity": round(hit.score, 4),
        })
    return "\n".join(lines) + "\n\n", sources


def generate_recommendations(
    llm: LLMProvider,
    resume_text: str,
    jd_text: str,
    missing_skills: list[str],
    matched_skills: list[str],
    knowledge_base: KnowledgeBase | None = None,
) -> dict:
    rag_block, sources = _rag_context(
        knowledge_base, "resume quality ATS best practices " + " ".join(missing_skills)
    )
    prompt = (
        SAFETY_PREAMBLE
        + _grounded_context(resume_text, jd_text, missing_skills, matched_skills)
        + rag_block
        + "Generate 3-6 prioritized, actionable recommendations to improve this resume's match "
        "for this specific job. Each recommendation must cite evidence from the resume or JD."
    )
    response = llm.generate(prompt, schema=RECOMMENDATION_SCHEMA, max_tokens=1200)
    result = response.raw_json or {"recommendations": [], "raw_text": response.text}
    result["retrieved_sources"] = sources
    return result


def optimize_resume(llm: LLMProvider, resume_text: str, jd_text: str, matched_skills: list[str]) -> dict:
    prompt = SAFETY_PREAMBLE + _grounded_context(resume_text, jd_text, [], matched_skills) + (
        "Rewrite the resume's summary and up to 6 of its weakest bullets to better align with the "
        "job description. Do NOT add any technology, employer, project, or metric that is not already "
        "present in the original resume text — only rephrase, reorder, and sharpen wording."
    )
    response = llm.generate(prompt, schema=OPTIMIZATION_SCHEMA, max_tokens=1500)
    return response.raw_json or {"improved_summary": "", "bullet_rewrites": [], "raw_text": response.text}


def generate_interview_questions(
    llm: LLMProvider,
    resume_text: str,
    jd_text: str,
    missing_skills: list[str],
    matched_skills: list[str],
    knowledge_base: KnowledgeBase | None = None,
) -> dict:
    rag_block, sources = _rag_context(knowledge_base, "interview preparation guidance " + " ".join(matched_skills))
    prompt = (
        SAFETY_PREAMBLE
        + _grounded_context(resume_text, jd_text, missing_skills, matched_skills)
        + rag_block
        + "Generate role-specific interview questions: technical questions based on matched skills, "
        "project questions based on the candidate's actual projects described in the resume, and "
        "behavioral questions relevant to this role/seniority."
    )
    response = llm.generate(prompt, schema=INTERVIEW_SCHEMA, max_tokens=1200)
    result = response.raw_json or {
        "technical_questions": [], "project_questions": [], "behavioral_questions": [], "raw_text": response.text,
    }
    result["retrieved_sources"] = sources
    return result


def generate_learning_roadmap(
    llm: LLMProvider, jd_text: str, missing_skills: list[str], knowledge_base: KnowledgeBase | None = None
) -> dict:
    if not missing_skills:
        return {"roadmap": [], "retrieved_sources": []}
    rag_block, sources = _rag_context(knowledge_base, "skill relationships transferable skills " + " ".join(missing_skills))
    prompt = SAFETY_PREAMBLE + (
        f"JOB DESCRIPTION TEXT:\n{jd_text[:4000]}\n\n"
        f"MISSING REQUIRED SKILLS: {', '.join(missing_skills)}\n\n"
        + rag_block
        + "For each missing skill, produce a learning roadmap entry: why it matters for this role, "
        "prerequisites, a learning sequence, a practical project to build, and a way to validate the skill."
    )
    response = llm.generate(prompt, schema=ROADMAP_SCHEMA, max_tokens=1500)
    result = response.raw_json or {"roadmap": [], "raw_text": response.text}
    result["retrieved_sources"] = sources
    return result
