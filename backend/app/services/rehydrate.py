"""Rebuilds the lightweight in-memory shapes the scoring pipeline expects
from the JSON blobs persisted in Postgres, so matching/scoring can run
against a previously-parsed resume/job without re-parsing the source file.
"""

from __future__ import annotations

from types import SimpleNamespace


def resume_from_json(parsed_json: dict) -> SimpleNamespace:
    return SimpleNamespace(
        candidate=SimpleNamespace(**parsed_json.get("candidate", {})),
        sections=parsed_json.get("sections", {}),
        all_skills_flat=parsed_json.get("all_skills_flat", []),
        unmatched_section_headers=parsed_json.get("unmatched_section_headers", []),
        achievement_metrics=parsed_json.get("achievement_metrics", []),
    )


def jd_from_json(parsed_json: dict) -> SimpleNamespace:
    return SimpleNamespace(
        job_title=parsed_json.get("job_title"),
        seniority=parsed_json.get("seniority"),
        required_skills=parsed_json.get("required_skills", []),
        preferred_skills=parsed_json.get("preferred_skills", []),
        experience_requirements=parsed_json.get("experience_requirements", []),
        education_requirements=parsed_json.get("education_requirements", []),
        responsibilities=parsed_json.get("responsibilities", []),
    )
