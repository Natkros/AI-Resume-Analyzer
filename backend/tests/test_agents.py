from app.agents.supervisor import run_pipeline
from app.pipelines.resume_parser import parse_resume

RESUME_TEXT = """Jane Doe
jane@example.com

SKILLS
Python, FastAPI, PostgreSQL

PROFESSIONAL EXPERIENCE
Backend Engineer, Acme Corp
- Built REST APIs using FastAPI.
"""

JD_TEXT = """Backend Engineer

Requirements:
- Required: Python
- Required: FastAPI
- Required: Kubernetes
"""


def test_supervisor_deterministic_pipeline_produces_report():
    resume = parse_resume(RESUME_TEXT.encode(), "resume.txt")
    result = run_pipeline(resume_preparsed=resume, jd_text=JD_TEXT, include_llm_agents=False)
    report = result.to_report()

    assert report["compatibility"] is not None
    assert "Python" in report["strong_matches"]
    assert "Kubernetes" in report["missing_requirements"]
    assert report["ats_issues"] is not None
    # LLM-dependent sections are absent when include_llm_agents=False
    assert report["recommendations"] is None
    assert report["agent_errors"] == []


def test_supervisor_pipeline_from_raw_bytes():
    result = run_pipeline(
        resume_file_bytes=RESUME_TEXT.encode(), resume_filename="resume.txt", jd_text=JD_TEXT,
    )
    report = result.to_report()
    assert report["compatibility"]["overall"] >= 0
