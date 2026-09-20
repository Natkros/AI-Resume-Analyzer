"""Phase 6 + 20: ATS-style structural/content analysis and resume quality.

Deterministic heuristics only — this never claims to replicate any specific
vendor's ATS parser (Workday, Greenhouse, Taleo, etc. all differ), only to
flag common, well-known risk patterns: missing contact info, weak/passive
bullet phrasing, missing metrics, non-standard section headers.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from app.pipelines.resume_parser import ParsedResume

WEAK_VERBS = {"worked", "helped", "responsible", "involved", "assisted", "participated", "did", "handled"}
STRONG_VERB_HINT = {
    "built", "designed", "led", "developed", "implemented", "architected", "optimized",
    "reduced", "increased", "launched", "created", "automated", "deployed", "improved",
}
PASSIVE_RE = re.compile(r"\b(was|were|is|are|been)\s+\w+ed\b", re.IGNORECASE)
METRIC_RE = re.compile(r"\d")


@dataclass
class ATSIssue:
    severity: str  # issue | warning
    area: str  # formatting | content | structure
    message: str


@dataclass
class ATSResult:
    ats_score: int
    issues: list[ATSIssue]
    warnings: list[ATSIssue]
    recommendations: list[str]

    def to_dict(self) -> dict:
        return {
            "ats_score": self.ats_score,
            "issues": [asdict(i) for i in self.issues],
            "warnings": [asdict(w) for w in self.warnings],
            "recommendations": self.recommendations,
            "disclaimer": "This score approximates common ATS parsing risk patterns; "
            "it does not represent how any specific ATS vendor will actually score this resume.",
        }


def analyze_ats(resume: ParsedResume) -> ATSResult:
    issues: list[ATSIssue] = []
    warnings: list[ATSIssue] = []
    recommendations: list[str] = []
    deductions = 0

    # --- structure: contact info ---
    if not resume.candidate.email:
        issues.append(ATSIssue("issue", "structure", "No email address detected."))
        recommendations.append("Add a clearly formatted email address near the top of the resume.")
        deductions += 15
    if not resume.candidate.phone:
        warnings.append(ATSIssue("warning", "structure", "No phone number detected."))
        deductions += 5

    # --- structure: expected sections present ---
    if not resume.sections.get("skills"):
        issues.append(ATSIssue("issue", "structure", "No dedicated Skills section detected."))
        recommendations.append("Add an explicit 'Skills' section listing key technologies.")
        deductions += 10
    if not resume.sections.get("experience") and not resume.sections.get("projects"):
        issues.append(ATSIssue("issue", "structure", "No Experience or Projects section detected."))
        deductions += 15

    if resume.unmatched_section_headers:
        warnings.append(
            ATSIssue(
                "warning", "structure",
                f"{len(resume.unmatched_section_headers)} section header(s) not recognized: "
                f"{', '.join(resume.unmatched_section_headers[:5])}. Consider using standard headings.",
            )
        )
        deductions += 3

    # --- content: bullet quality ---
    bullet_source = "\n".join(
        resume.sections.get(k, "") for k in ("experience", "projects") if resume.sections.get(k)
    )
    bullets = [b.strip() for b in bullet_source.splitlines() if b.strip()]
    weak_count = 0
    metric_count = 0
    long_bullets = 0
    for bullet in bullets:
        lowered = bullet.lower()
        first_word = lowered.split()[0] if lowered.split() else ""
        if first_word in WEAK_VERBS or PASSIVE_RE.search(bullet):
            weak_count += 1
        if METRIC_RE.search(bullet):
            metric_count += 1
        if len(bullet) > 220:
            long_bullets += 1

    if bullets:
        weak_ratio = weak_count / len(bullets)
        metric_ratio = metric_count / len(bullets)
        if weak_ratio > 0.3:
            warnings.append(
                ATSIssue("warning", "content", f"{weak_count}/{len(bullets)} bullets use weak or passive phrasing.")
            )
            recommendations.append("Rewrite weak bullets to start with a strong action verb (e.g. 'built', 'led', 'optimized').")
            deductions += min(15, int(weak_ratio * 20))
        if metric_ratio < 0.2:
            warnings.append(
                ATSIssue("warning", "content", "Few bullets contain quantifiable metrics.")
            )
            recommendations.append("Add measurable outcomes to bullets where genuinely available (e.g. '35% latency reduction').")
            deductions += 8
        if long_bullets:
            warnings.append(ATSIssue("warning", "content", f"{long_bullets} bullet(s) are unusually long (>220 chars)."))
            deductions += 3

    if not recommendations:
        recommendations.append("No major ATS issues detected; consider a final proofread for consistency.")

    score = max(0, min(100, 100 - deductions))
    return ATSResult(ats_score=score, issues=issues, warnings=warnings, recommendations=recommendations)
