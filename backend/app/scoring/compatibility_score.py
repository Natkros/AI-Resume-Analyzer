"""Phase 5: explainable Resume-Job Compatibility Score.

Combines the matching engine's output, experience/education checks, and
ATS score into one weighted, fully-itemized breakdown. Every subscore is
traceable back to the evidence that produced it (Phase 17) — this module
never emits a bare number.

IMPORTANT (Phase 63 safety rule): this score is a "Resume-Job Compatibility
Score", not a probability of being hired. Never rename or reframe it as such.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from app.pipelines.jd_parser import ParsedJobDescription
from app.pipelines.resume_parser import ParsedResume
from app.scoring.ats_analyzer import ATSResult
from app.scoring.matching_engine import MatchResult

DEFAULT_WEIGHTS = {
    "required_skills": 0.30,
    "preferred_skills": 0.10,
    "experience": 0.20,
    "projects": 0.15,
    "semantic": 0.10,
    "education": 0.05,
    "certifications": 0.05,
    "ats": 0.05,
}


@dataclass
class ScoreComponent:
    name: str
    weight: float
    raw_score: float  # 0..1
    weighted_points: float  # 0..100 scale contribution
    explanation: str


@dataclass
class CompatibilityScore:
    overall: float  # 0..100
    components: list[ScoreComponent]
    label: str = "Resume-Job Compatibility Score"

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "overall": self.overall,
            "components": [asdict(c) for c in self.components],
            "disclaimer": (
                "This score reflects textual and semantic alignment between the "
                "resume and job description. It is not a prediction of interview "
                "outcomes or hiring probability."
            ),
        }


def _experience_score(resume: ParsedResume, jd: ParsedJobDescription) -> tuple[float, str]:
    if not jd.experience_requirements:
        return 1.0, "Job description specified no explicit experience requirement."
    required_years = [r["min_years"] for r in jd.experience_requirements if r.get("min_years") and r.get("is_required")]
    if not required_years:
        return 0.7, "Experience mentioned in JD but no specific year threshold detected."
    min_required = max(required_years)
    exp_text = resume.sections.get("experience", "")
    # crude proxy: does the resume mention >= required years anywhere near "experience"
    has_matching_years = str(min_required) in exp_text or any(
        str(y) in exp_text for y in range(min_required, min_required + 6)
    )
    if has_matching_years:
        return 0.85, f"Resume experience section references a duration compatible with the required {min_required}+ years."
    return 0.4, f"Could not confirm {min_required}+ years of relevant experience from resume text."


def _education_score(resume: ParsedResume, jd: ParsedJobDescription) -> tuple[float, str]:
    if not jd.education_requirements:
        return 1.0, "No explicit education requirement in job description."
    edu_text = resume.sections.get("education", "").lower()
    if not edu_text:
        return 0.3, "Job requires education credentials but no Education section was found in resume."
    keywords = ["bachelor", "master", "phd", "b.s", "m.s", "b.tech", "associate"]
    if any(k in edu_text for k in keywords):
        return 0.9, "Resume Education section contains a degree matching common requirement phrasing."
    return 0.5, "Education section present but degree level unclear relative to requirement."


def _certifications_score(resume: ParsedResume, jd: ParsedJobDescription) -> tuple[float, str]:
    cert_text = resume.sections.get("certifications", "")
    if not cert_text:
        return 0.5, "No certifications section found; treated as neutral (JD did not explicitly require certifications)."
    return 1.0, "Certifications section present."


def _project_relevance_score(match: MatchResult) -> tuple[float, str]:
    if not match.semantic_matches:
        return match.required_skill_coverage, "No project-level semantic comparisons available; using skill coverage as proxy."
    avg_sim = sum(m.similarity for m in match.semantic_matches) / len(match.semantic_matches)
    return max(0.0, min(1.0, avg_sim)), f"Averaged similarity across {len(match.semantic_matches)} JD responsibility statements vs. resume project/experience text."


def compute_compatibility_score(
    resume: ParsedResume,
    jd: ParsedJobDescription,
    match: MatchResult,
    ats: ATSResult,
    weights: dict[str, float] | None = None,
) -> CompatibilityScore:
    weights = weights or DEFAULT_WEIGHTS
    exp_score, exp_reason = _experience_score(resume, jd)
    edu_score, edu_reason = _education_score(resume, jd)
    cert_score, cert_reason = _certifications_score(resume, jd)
    proj_score, proj_reason = _project_relevance_score(match)

    raw_scores = {
        "required_skills": match.required_skill_coverage,
        "preferred_skills": match.preferred_skill_coverage,
        "experience": exp_score,
        "projects": proj_score,
        "semantic": match.semantic_similarity_avg,
        "education": edu_score,
        "certifications": cert_score,
        "ats": ats.ats_score / 100.0,
    }
    explanations = {
        "required_skills": f"{len(match.required_skill_matches)}/{len(match.required_skill_matches) + len(match.missing_required_skills)} required skills matched.",
        "preferred_skills": f"{len(match.preferred_skill_matches)}/{len(match.preferred_skill_matches) + len(match.missing_preferred_skills)} preferred skills matched.",
        "experience": exp_reason,
        "projects": proj_reason,
        "semantic": f"Average semantic similarity of {match.semantic_similarity_avg:.2f} between JD responsibilities and resume text."
        + (" (fallback lexical embedding — install sentence-transformers for full semantic quality)" if match.embeddings_are_fallback else ""),
        "education": edu_reason,
        "certifications": cert_reason,
        "ats": f"ATS structural/content score: {ats.ats_score}/100.",
    }

    components = []
    total = 0.0
    for key, weight in weights.items():
        raw = raw_scores.get(key, 0.0)
        points = round(raw * weight * 100, 2)
        total += points
        components.append(
            ScoreComponent(
                name=key, weight=weight, raw_score=round(raw, 4),
                weighted_points=points, explanation=explanations.get(key, ""),
            )
        )

    return CompatibilityScore(overall=round(total, 2), components=components)
