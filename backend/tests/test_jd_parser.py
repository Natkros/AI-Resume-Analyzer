from app.pipelines.jd_parser import parse_job_description

SAMPLE_JD = """GenAI Engineer

About the role:
We are looking for a GenAI Engineer to build retrieval-augmented generation systems.

Requirements:
- 3+ years of Python experience required.
- Required: strong experience with FastAPI and PostgreSQL.
- Bachelor's degree in Computer Science or related field required.

Preferred:
- Experience with Kubernetes is a plus.
- AWS ECS experience preferred.

Responsibilities:
- Design and build scalable RAG pipelines.
- Collaborate with product teams to ship features.
"""


def test_jd_parser_separates_required_and_preferred():
    jd = parse_job_description(SAMPLE_JD)
    assert "Python" in jd.required_skills
    assert "FastAPI" in jd.required_skills
    assert "Kubernetes" in jd.preferred_skills
    assert "Kubernetes" not in jd.required_skills


def test_jd_parser_extracts_experience_years():
    jd = parse_job_description(SAMPLE_JD)
    years = [r["min_years"] for r in jd.experience_requirements if r["min_years"]]
    assert 3 in years


def test_jd_parser_extracts_education():
    jd = parse_job_description(SAMPLE_JD)
    assert any("bachelor" in e.lower() for e in jd.education_requirements)


def test_jd_parser_extracts_responsibilities():
    jd = parse_job_description(SAMPLE_JD)
    assert any("rag pipelines" in r.lower() for r in jd.responsibilities)


def test_jd_parser_guesses_job_title():
    jd = parse_job_description(SAMPLE_JD)
    assert jd.job_title == "GenAI Engineer"
