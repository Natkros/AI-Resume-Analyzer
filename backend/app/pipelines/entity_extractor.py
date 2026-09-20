"""Phase 1: deterministic entity extraction (contact info) + achievement metrics.

Regex-based on purpose: emails, phone numbers, URLs, and "reduced X by Y%"
style metrics have a small, well-defined grammar and do not benefit from an
LLM call. Reserve the LLM for genuinely ambiguous reasoning (see
app/services/llm_extraction.py, Phase 7).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:(?:\+?\d{1,3}[\s.\-]?)?(?:\(\d{2,4}\)[\s.\-]?)?\d{3,4}[\s.\-]?\d{3,4}[\s.\-]?\d{0,4})")
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-_/]+", re.IGNORECASE)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-_/]+", re.IGNORECASE)
GENERIC_URL_RE = re.compile(r"https?://[^\s,]+")

METRIC_RE = re.compile(
    r"(?P<verb>reduc\w*|decreas\w*|increas\w*|improv\w*|boost\w*|grew|grow\w*|sav\w*|cut|optimi[sz]\w*|accelerat\w*|process\w*|scal\w*|handl\w*|generat\w*|achiev\w*)"
    r"[^.\n%$]{0,60}?"
    r"(?P<value>\d[\d,\.]*)\s*(?P<unit>%|percent|x|k|m|ms|s|seconds|minutes|hours|users|requests|records|documents)?",
    re.IGNORECASE,
)


@dataclass
class ContactInfo:
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    github: str | None = None
    other_links: list[str] | None = None


@dataclass
class AchievementMetric:
    sentence: str
    verb: str
    value: str
    unit: str | None


def extract_contact_info(text: str) -> ContactInfo:
    email_match = EMAIL_RE.search(text)
    linkedin_match = LINKEDIN_RE.search(text)
    github_match = GITHUB_RE.search(text)

    phone = None
    for candidate in PHONE_RE.findall(text):
        digits = re.sub(r"\D", "", candidate)
        if 7 <= len(digits) <= 15:
            phone = candidate.strip()
            break

    all_urls = set(GENERIC_URL_RE.findall(text))
    if linkedin_match:
        all_urls.discard(linkedin_match.group(0))
    if github_match:
        all_urls.discard(github_match.group(0))

    return ContactInfo(
        email=email_match.group(0) if email_match else None,
        phone=phone,
        linkedin=linkedin_match.group(0) if linkedin_match else None,
        github=github_match.group(0) if github_match else None,
        other_links=sorted(all_urls) or None,
    )


def extract_achievement_metrics(text: str) -> list[AchievementMetric]:
    results: list[AchievementMetric] = []
    for sentence in re.split(r"(?<=[.\n])", text):
        sentence = sentence.strip()
        if not sentence:
            continue
        m = METRIC_RE.search(sentence)
        if m:
            results.append(
                AchievementMetric(
                    sentence=sentence,
                    verb=m.group("verb"),
                    value=m.group("value"),
                    unit=m.group("unit"),
                )
            )
    return results
