"""Phase 1 + 2: end-to-end resume parsing -> structured candidate profile.

Pipeline: raw bytes -> text extraction (OCR fallback) -> section detection ->
entity extraction -> skill extraction/normalization -> structured JSON.
Everything here is deterministic; no LLM call is required to get a usable
structured profile (LLM-based deepening happens later in the optional
Phase 7 reasoning layer, on top of this, never replacing it).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from app.pipelines.document_extractor import ExtractionResult, extract_text
from app.pipelines.entity_extractor import ContactInfo, extract_achievement_metrics, extract_contact_info
from app.pipelines.section_detector import ResumeSections, detect_sections
from app.services.skill_taxonomy import get_skill_taxonomy


@dataclass
class SkillsBlock:
    programming_languages: list[str] = field(default_factory=list)
    frameworks_backend: list[str] = field(default_factory=list)
    frameworks_frontend: list[str] = field(default_factory=list)
    databases: list[str] = field(default_factory=list)
    cloud: list[str] = field(default_factory=list)
    devops: list[str] = field(default_factory=list)
    ai_ml: list[str] = field(default_factory=list)
    other: list[str] = field(default_factory=list)


@dataclass
class ParsedResume:
    candidate: ContactInfo
    sections: dict[str, str]
    skills: SkillsBlock
    all_skills_flat: list[str]
    achievement_metrics: list[dict]
    unmatched_section_headers: list[str]
    used_ocr: bool
    raw_text: str

    def to_dict(self) -> dict:
        return {
            "candidate": asdict(self.candidate),
            "sections": self.sections,
            "skills": asdict(self.skills),
            "all_skills_flat": self.all_skills_flat,
            "achievement_metrics": self.achievement_metrics,
            "unmatched_section_headers": self.unmatched_section_headers,
            "used_ocr": self.used_ocr,
        }


_CATEGORY_TO_FIELD = {
    "programming_languages": "programming_languages",
    "frameworks_backend": "frameworks_backend",
    "frameworks_frontend": "frameworks_frontend",
    "databases": "databases",
    "cloud": "cloud",
    "devops": "devops",
    "ai_ml": "ai_ml",
}


def _bucket_skills(skills: list[str]) -> SkillsBlock:
    taxonomy = get_skill_taxonomy()
    block = SkillsBlock()
    for skill in skills:
        category = taxonomy.category_of(skill)
        field_name = _CATEGORY_TO_FIELD.get(category or "", "other")
        getattr(block, field_name).append(skill)
    return block


def parse_resume(file_bytes: bytes, filename: str) -> ParsedResume:
    extraction: ExtractionResult = extract_text(file_bytes, filename)
    text = extraction.text

    sections: ResumeSections = detect_sections(text)
    contact = extract_contact_info(text)

    taxonomy = get_skill_taxonomy()
    # Prefer the dedicated skills section when present, but always fall back
    # to scanning the whole resume so skills mentioned only in project/
    # experience bullets are still captured.
    skills_section_text = sections.get("skills") or ""
    skills_from_section = taxonomy.extract_from_text(skills_section_text)
    skills_from_whole_doc = taxonomy.extract_from_text(text)
    all_skills = sorted(set(skills_from_section) | set(skills_from_whole_doc))

    metrics = extract_achievement_metrics(text)

    return ParsedResume(
        candidate=contact,
        sections=sections.sections,
        skills=_bucket_skills(all_skills),
        all_skills_flat=all_skills,
        achievement_metrics=[asdict(m) for m in metrics],
        unmatched_section_headers=sections.unmatched_headers,
        used_ocr=extraction.used_ocr,
        raw_text=text,
    )
