from app.pipelines.jd_parser import parse_job_description
from app.pipelines.resume_parser import parse_resume
from app.scoring.ats_analyzer import analyze_ats
from app.scoring.compatibility_score import compute_compatibility_score
from app.scoring.matching_engine import run_matching

RESUME_TEXT = """Jane Doe
jane@example.com | 555-000-1111

SKILLS
Python, FastAPI, PostgreSQL, Docker

PROFESSIONAL EXPERIENCE
Backend Engineer, Acme Corp
- Built REST APIs using FastAPI for a production data platform.
- Reduced query latency by 35% through PostgreSQL index tuning.

PROJECTS
RAG Platform
- Built a retrieval-augmented generation platform with vector search and embeddings.

EDUCATION
Bachelor of Science in Computer Science, State University, 2022
"""

JD_TEXT = """Backend Engineer

Requirements:
- Required: Python
- Required: FastAPI
- Required: PostgreSQL
- Required: Kubernetes
- 2+ years of experience required.

Preferred:
- AWS is a plus.

Responsibilities:
- Build and maintain REST APIs.
"""


def _parsed_pair():
    resume = parse_resume(RESUME_TEXT.encode(), "resume.txt")
    jd = parse_job_description(JD_TEXT)
    return resume, jd


def test_matching_engine_finds_exact_matches_with_evidence():
    resume, jd = _parsed_pair()
    match = run_matching(resume, jd, embedder=None)
    matched_skills = {m.skill for m in match.required_skill_matches}
    assert {"Python", "FastAPI", "PostgreSQL"} <= matched_skills
    for m in match.required_skill_matches:
        assert m.evidence_snippet is not None


def test_matching_engine_reports_missing_required_skill():
    resume, jd = _parsed_pair()
    match = run_matching(resume, jd, embedder=None)
    assert "Kubernetes" in match.missing_required_skills


def test_matching_engine_coverage_between_0_and_1():
    resume, jd = _parsed_pair()
    match = run_matching(resume, jd, embedder=None)
    assert 0.0 <= match.required_skill_coverage <= 1.0


def test_ats_analyzer_flags_missing_email():
    resume, _jd = _parsed_pair()
    resume.candidate.email = None
    result = analyze_ats(resume)
    assert result.ats_score < 100
    assert any("email" in i.message.lower() for i in result.issues)


def test_ats_analyzer_full_resume_scores_reasonably():
    resume, _jd = _parsed_pair()
    result = analyze_ats(resume)
    assert 0 <= result.ats_score <= 100


def test_compatibility_score_never_claims_hiring_probability():
    resume, jd = _parsed_pair()
    match = run_matching(resume, jd, embedder=None)
    ats = analyze_ats(resume)
    score = compute_compatibility_score(resume, jd, match, ats)
    payload = score.to_dict()
    assert "hire" not in payload["disclaimer"].lower() or "not a prediction" in payload["disclaimer"].lower()
    assert payload["label"] == "Resume-Job Compatibility Score"
    assert 0 <= payload["overall"] <= 100


def test_compatibility_score_components_sum_to_overall():
    resume, jd = _parsed_pair()
    match = run_matching(resume, jd, embedder=None)
    ats = analyze_ats(resume)
    score = compute_compatibility_score(resume, jd, match, ats)
    total = round(sum(c.weighted_points for c in score.components), 2)
    assert abs(total - score.overall) < 0.05
