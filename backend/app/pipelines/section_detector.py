"""Phase 1: resume section detection.

Resumes use inconsistent headings for the same semantic section
("Professional Experience" / "Work History" / "Employment" all mean the
same thing). This module maps many header spellings to a small set of
canonical section keys, then splits the raw text into those sections.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

CANONICAL_SECTIONS = [
    "summary",
    "skills",
    "experience",
    "projects",
    "education",
    "certifications",
    "achievements",
    "publications",
    "leadership",
    "volunteering",
    "languages",
    "interests",
]

# canonical -> header aliases (matched case-insensitively, whole line)
SECTION_ALIASES: dict[str, list[str]] = {
    "summary": ["summary", "professional summary", "objective", "profile", "about me", "career objective"],
    "skills": ["skills", "technical skills", "core competencies", "key skills", "skills & tools", "technologies"],
    "experience": [
        "experience", "professional experience", "work experience", "work history",
        "employment", "employment history", "career history", "relevant experience",
    ],
    "projects": ["projects", "personal projects", "academic projects", "key projects", "notable projects"],
    "education": ["education", "academic background", "education & training", "educational background"],
    "certifications": ["certifications", "certificates", "licenses & certifications", "professional certifications"],
    "achievements": ["achievements", "accomplishments", "honors & awards", "awards", "honors"],
    "publications": ["publications", "research publications", "papers"],
    "leadership": ["leadership", "leadership experience"],
    "volunteering": ["volunteering", "volunteer experience", "community service"],
    "languages": ["languages", "spoken languages"],
    "interests": ["interests", "hobbies", "hobbies & interests"],
}

_ALIAS_TO_CANONICAL: dict[str, str] = {
    alias.lower(): canonical for canonical, aliases in SECTION_ALIASES.items() for alias in aliases
}

_HEADER_LINE_RE = re.compile(r"^\s{0,4}([A-Za-z][A-Za-z &/'\-]{1,40})\s*:?\s*$")


@dataclass
class ResumeSections:
    sections: dict[str, str]
    unmatched_headers: list[str]

    def get(self, canonical: str, default: str = "") -> str:
        return self.sections.get(canonical, default)


def _match_header(line: str) -> str | None:
    m = _HEADER_LINE_RE.match(line)
    if not m:
        return None
    candidate = m.group(1).strip().lower()
    return _ALIAS_TO_CANONICAL.get(candidate)


def detect_sections(text: str) -> ResumeSections:
    lines = text.splitlines()
    sections: dict[str, list[str]] = {}
    unmatched_headers: list[str] = []

    current_key = "summary"  # content before the first recognized header
    buffer: list[str] = []

    def flush():
        if buffer:
            sections.setdefault(current_key, [])
            sections[current_key].extend(buffer)

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            buffer.append(line)
            continue

        canonical = _match_header(line)
        # Heuristic: an ALL-CAPS short line that isn't a known alias is
        # probably a section header we don't recognize yet.
        looks_like_unknown_header = (
            canonical is None
            and stripped.isupper()
            and 2 <= len(stripped.split()) <= 5
            and len(stripped) < 40
        )

        if canonical:
            flush()
            buffer = []
            current_key = canonical
            continue
        if looks_like_unknown_header:
            flush()
            buffer = []
            unmatched_headers.append(stripped)
            current_key = "summary" if current_key not in sections else current_key
            continue

        buffer.append(line)

    flush()

    joined = {key: "\n".join(v).strip() for key, v in sections.items() if "\n".join(v).strip()}
    return ResumeSections(sections=joined, unmatched_headers=unmatched_headers)
