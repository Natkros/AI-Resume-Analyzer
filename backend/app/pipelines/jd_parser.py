"""Phase 3: job description parsing -> structured requirements.

Splits a JD into sentences/bullets, classifies each as required vs.
preferred (the single most important distinction for scoring — see
app/scoring/), extracts skills via the same taxonomy used for resumes,
and pulls out experience/education requirements with regex.

Deterministic by design: JD requirement language is formulaic enough
("3+ years", "required", "nice to have", "bachelor's degree") that rules
outperform an LLM call here on cost, latency, and auditability. LLM
reasoning is reserved for JD statements that don't fit any rule.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from app.services.skill_taxonomy import get_skill_taxonomy

REQUIRED_MARKERS = [
    r"\brequired\b", r"\bmust have\b", r"\bmust be\b", r"\bminimum qualifications\b",
    r"\bneeds to\b", r"\brequirement[s]?\b", r"\byou have\b", r"\byou must\b",
]
PREFERRED_MARKERS = [
    r"\bpreferred\b", r"\bnice to have\b", r"\bbonus\b", r"\bplus\b",
    r"\bis a plus\b", r"\bideally\b", r"\bwould be great\b", r"\bdesired\b",
]

EXPERIENCE_RE = re.compile(
    r"(?P<years>\d+)\+?\s*(?:-\s*\d+\s*)?(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)?",
    re.IGNORECASE,
)
EDUCATION_RE = re.compile(
    r"\b(bachelor'?s?|master'?s?|phd|doctorate|b\.?s\.?|m\.?s\.?|associate'?s?)\b[^.\n]*",
    re.IGNORECASE,
)
SENIORITY_KEYWORDS = {
    "intern": "internship",
    "junior": "junior",
    "entry level": "entry_level",
    "entry-level": "entry_level",
    "associate": "associate",
    "mid level": "mid_level",
    "mid-level": "mid_level",
    "senior": "senior",
    "staff": "staff",
    "principal": "principal",
    "lead": "lead",
    "director": "director",
    "vp": "vp",
    "head of": "head",
}


@dataclass
class RequirementItem:
    text: str
    category: str  # required_skill | preferred_skill | required_experience | ... | responsibility | other
    is_required: bool
    skills: list[str] = field(default_factory=list)
    min_years: int | None = None


@dataclass
class ParsedJobDescription:
    job_title: str | None
    seniority: str | None
    required_skills: list[str]
    preferred_skills: list[str]
    experience_requirements: list[dict]
    education_requirements: list[str]
    responsibilities: list[str]
    requirement_items: list[dict]
    all_skills_mentioned: list[str]

    def to_dict(self) -> dict:
        return {
            "job_title": self.job_title,
            "seniority": self.seniority,
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "experience_requirements": self.experience_requirements,
            "education_requirements": self.education_requirements,
            "responsibilities": self.responsibilities,
            "requirement_items": self.requirement_items,
            "all_skills_mentioned": self.all_skills_mentioned,
        }


def _split_statements(text: str) -> list[str]:
    lines = [ln.strip(" \t-*•").strip() for ln in text.splitlines()]
    statements: list[str] = []
    for line in lines:
        if not line:
            continue
        # further split long paragraph lines into sentences
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            sentence = sentence.strip()
            if len(sentence) >= 3:
                statements.append(sentence)
    return statements


def _guess_job_title(text: str) -> str | None:
    first_lines = [ln.strip() for ln in text.splitlines() if ln.strip()][:5]
    for line in first_lines:
        if 3 <= len(line) <= 80 and not line.lower().startswith(("about", "we are", "company")):
            return line
    return None


def _guess_seniority(text: str) -> str | None:
    lowered = text.lower()
    for keyword, label in SENIORITY_KEYWORDS.items():
        if keyword in lowered:
            return label
    return None


def _classify_statement(statement: str) -> tuple[str, bool]:
    lowered = statement.lower()
    is_required = any(re.search(p, lowered) for p in REQUIRED_MARKERS)
    is_preferred = any(re.search(p, lowered) for p in PREFERRED_MARKERS)

    if EDUCATION_RE.search(lowered):
        category = "preferred_education" if is_preferred and not is_required else "required_education"
        return category, not (is_preferred and not is_required)
    if EXPERIENCE_RE.search(lowered) and ("year" in lowered or "yr" in lowered):
        category = "preferred_experience" if is_preferred and not is_required else "required_experience"
        return category, not (is_preferred and not is_required)
    if any(w in lowered for w in ("responsible for", "you will", "own the", "build", "design", "collaborate", "lead the")):
        return "responsibility", True
    if is_preferred and not is_required:
        return "preferred_skill", False
    return "required_skill", True


def parse_job_description(text: str) -> ParsedJobDescription:
    taxonomy = get_skill_taxonomy()
    statements = _split_statements(text)
    job_title = _guess_job_title(text)

    items: list[RequirementItem] = []
    required_skills: set[str] = set()
    preferred_skills: set[str] = set()
    experience_reqs: list[dict] = []
    education_reqs: list[str] = []
    responsibilities: list[str] = []

    for statement in statements:
        # The job title line (e.g. "ML Engineer") is a heading, not a
        # requirement statement — classifying it as one lets short skill
        # aliases like "ML" leak into required_skills.
        if job_title and statement.strip().lower() == job_title.strip().lower():
            continue
        category, is_required = _classify_statement(statement)
        skills_in_statement = taxonomy.extract_from_text(statement)

        years_match = EXPERIENCE_RE.search(statement)
        min_years = int(years_match.group("years")) if years_match and "year" in statement.lower() else None

        item = RequirementItem(
            text=statement,
            category=category,
            is_required=is_required,
            skills=skills_in_statement,
            min_years=min_years,
        )
        items.append(item)

        if category in ("required_skill", "preferred_skill"):
            target = required_skills if category == "required_skill" else preferred_skills
            target.update(skills_in_statement)
        elif skills_in_statement:
            # skills mentioned inside an experience/education/responsibility line
            # still count as required unless explicitly marked preferred
            target = preferred_skills if not is_required else required_skills
            target.update(skills_in_statement)

        if category in ("required_experience", "preferred_experience"):
            experience_reqs.append({
                "text": statement, "min_years": min_years, "is_required": is_required,
                "skills": skills_in_statement,
            })
        if category in ("required_education", "preferred_education"):
            education_reqs.append(statement)
        if category == "responsibility":
            responsibilities.append(statement)

    # A skill should not be both required and preferred; required wins.
    preferred_skills -= required_skills

    all_skills_mentioned = sorted(set(taxonomy.extract_from_text(text)))

    return ParsedJobDescription(
        job_title=job_title,
        seniority=_guess_seniority(text),
        required_skills=sorted(required_skills),
        preferred_skills=sorted(preferred_skills),
        experience_requirements=experience_reqs,
        education_requirements=education_reqs,
        responsibilities=responsibilities,
        requirement_items=[asdict(i) for i in items],
        all_skills_mentioned=all_skills_mentioned,
    )
