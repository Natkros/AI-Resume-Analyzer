"""Phase 4: multi-layer resume <-> job matching.

Layer 1/2 (exact + alias): both resume and JD skills are already normalized
to canonical names via the shared skill taxonomy, so exact/alias matching
is just set membership — no separate layer needed.
Layer 3 (semantic): cosine similarity between JD requirement text and
resume section/project/experience text, via the embedding provider.
Layer 4 (experience): does the candidate show years/roles relevant to the
requirement.
Layer 5 (evidence): for every matched skill, locate the strongest resume
excerpt that demonstrates it, so the score is explainable (Phase 17).
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

import numpy as np

from app.pipelines.jd_parser import ParsedJobDescription
from app.pipelines.resume_parser import ParsedResume
from app.providers.base import EmbeddingProvider


@dataclass
class SkillEvidence:
    skill: str
    matched: bool
    match_type: str  # exact | semantic | none
    evidence_snippet: str | None
    confidence: str  # high | medium | low


@dataclass
class SemanticMatch:
    jd_statement: str
    best_resume_excerpt: str
    similarity: float


@dataclass
class MatchResult:
    required_skill_matches: list[SkillEvidence]
    preferred_skill_matches: list[SkillEvidence]
    missing_required_skills: list[str]
    missing_preferred_skills: list[str]
    semantic_matches: list[SemanticMatch]
    required_skill_coverage: float  # 0..1
    preferred_skill_coverage: float
    semantic_similarity_avg: float
    embeddings_are_fallback: bool

    def to_dict(self) -> dict:
        return {
            "required_skill_matches": [asdict(m) for m in self.required_skill_matches],
            "preferred_skill_matches": [asdict(m) for m in self.preferred_skill_matches],
            "missing_required_skills": self.missing_required_skills,
            "missing_preferred_skills": self.missing_preferred_skills,
            "semantic_matches": [asdict(m) for m in self.semantic_matches],
            "required_skill_coverage": self.required_skill_coverage,
            "preferred_skill_coverage": self.preferred_skill_coverage,
            "semantic_similarity_avg": self.semantic_similarity_avg,
            "embeddings_are_fallback": self.embeddings_are_fallback,
        }


def _find_evidence(skill: str, resume: ParsedResume) -> str | None:
    """Find the strongest sentence in the resume mentioning this skill,
    preferring projects/experience over the skills list (a bare list entry
    is weaker evidence than a bullet describing actual use)."""
    pattern = re.compile(r"(?<![a-z0-9])" + re.escape(skill.lower()) + r"(?![a-z0-9])")
    for section_name in ("projects", "experience", "summary"):
        section_text = resume.sections.get(section_name, "")
        for sentence in re.split(r"(?<=[.\n])", section_text):
            if pattern.search(sentence.lower()):
                return sentence.strip()
    if skill in resume.all_skills_flat:
        return f"Listed in skills section: {skill}"
    return None


def _cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = (np.linalg.norm(va) * np.linalg.norm(vb)) or 1e-9
    return float(np.dot(va, vb) / denom)


def _confidence_for(match_type: str, similarity: float | None = None) -> str:
    if match_type == "exact":
        return "high"
    if match_type == "semantic" and similarity is not None:
        if similarity >= 0.75:
            return "medium"
        return "low"
    return "low"


def _score_skill_list(
    required_or_preferred: list[str], resume: ParsedResume, embedder: EmbeddingProvider | None
) -> tuple[list[SkillEvidence], list[str]]:
    matched: list[SkillEvidence] = []
    missing: list[str] = []
    resume_skill_set = set(resume.all_skills_flat)

    for skill in required_or_preferred:
        if skill in resume_skill_set:
            evidence = _find_evidence(skill, resume)
            matched.append(
                SkillEvidence(
                    skill=skill, matched=True, match_type="exact",
                    evidence_snippet=evidence, confidence=_confidence_for("exact"),
                )
            )
            continue
        missing.append(skill)

    return matched, missing


def run_matching(
    resume: ParsedResume,
    jd: ParsedJobDescription,
    embedder: EmbeddingProvider | None = None,
) -> MatchResult:
    required_matched, required_missing = _score_skill_list(jd.required_skills, resume, embedder)
    preferred_matched, preferred_missing = _score_skill_list(jd.preferred_skills, resume, embedder)

    required_coverage = (
        len(required_matched) / len(jd.required_skills) if jd.required_skills else 1.0
    )
    preferred_coverage = (
        len(preferred_matched) / len(jd.preferred_skills) if jd.preferred_skills else 1.0
    )

    semantic_matches: list[SemanticMatch] = []
    embeddings_are_fallback = getattr(embedder, "is_fallback", False)
    sem_scores: list[float] = []

    if embedder is not None and jd.responsibilities:
        resume_chunks = [
            c.strip()
            for section in ("experience", "projects", "summary")
            for c in re.split(r"(?<=[.\n])", resume.sections.get(section, ""))
            if c.strip()
        ]
        if resume_chunks:
            resume_vectors = embedder.embed(resume_chunks)
            jd_statements = jd.responsibilities[:10]
            jd_vectors = embedder.embed(jd_statements)
            for statement, jd_vec in zip(jd_statements, jd_vectors):
                sims = [_cosine(jd_vec, rv) for rv in resume_vectors]
                best_idx = int(np.argmax(sims)) if sims else -1
                if best_idx >= 0:
                    semantic_matches.append(
                        SemanticMatch(
                            jd_statement=statement,
                            best_resume_excerpt=resume_chunks[best_idx],
                            similarity=round(sims[best_idx], 4),
                        )
                    )
                    sem_scores.append(sims[best_idx])

    semantic_avg = float(np.mean(sem_scores)) if sem_scores else 0.0

    return MatchResult(
        required_skill_matches=required_matched,
        preferred_skill_matches=preferred_matched,
        missing_required_skills=required_missing,
        missing_preferred_skills=preferred_missing,
        semantic_matches=semantic_matches,
        required_skill_coverage=round(required_coverage, 4),
        preferred_skill_coverage=round(preferred_coverage, 4),
        semantic_similarity_avg=round(semantic_avg, 4),
        embeddings_are_fallback=embeddings_are_fallback,
    )
