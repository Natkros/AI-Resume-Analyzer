from app.pipelines.resume_parser import parse_resume

SAMPLE_RESUME = """Kritarth Saxena
kritarth@example.com | +1 555-123-4567
linkedin.com/in/kritarthsaxena | github.com/kritarth

SUMMARY
AI Engineer focused on NLP and retrieval-augmented generation systems.

SKILLS
Python, FastAPI, PyTorch, PostgreSQL, Docker, React, AWS S3

PROFESSIONAL EXPERIENCE
Backend Engineer Intern, Acme Corp
- Built REST APIs using FastAPI for a production data platform.
- Reduced query latency by 35% through PostgreSQL index tuning.

PROJECTS
Production Multimodal RAG Platform
- Developed a production multimodal RAG platform using vector search, embeddings and LLM orchestration.
- Processed 100K documents with a Qdrant-backed retrieval pipeline.

EDUCATION
Bachelor of Technology in Computer Science, XYZ University, 2024

CERTIFICATIONS
AWS Certified Cloud Practitioner
"""


def test_parse_resume_extracts_contact_info():
    parsed = parse_resume(SAMPLE_RESUME.encode("utf-8"), "resume.txt")
    assert parsed.candidate.email == "kritarth@example.com"
    assert parsed.candidate.linkedin is not None
    assert parsed.candidate.github is not None


def test_parse_resume_detects_sections():
    parsed = parse_resume(SAMPLE_RESUME.encode("utf-8"), "resume.txt")
    assert "skills" in parsed.sections
    assert "experience" in parsed.sections
    assert "projects" in parsed.sections
    assert "education" in parsed.sections


def test_parse_resume_extracts_skills():
    parsed = parse_resume(SAMPLE_RESUME.encode("utf-8"), "resume.txt")
    assert "Python" in parsed.all_skills_flat
    assert "FastAPI" in parsed.all_skills_flat
    assert "PostgreSQL" in parsed.all_skills_flat
    assert "React" in parsed.all_skills_flat


def test_parse_resume_extracts_metrics():
    parsed = parse_resume(SAMPLE_RESUME.encode("utf-8"), "resume.txt")
    values = [m["value"] for m in parsed.achievement_metrics]
    assert "35" in values or any("35" in v for v in values)


def test_parse_resume_no_ocr_for_text_file():
    parsed = parse_resume(SAMPLE_RESUME.encode("utf-8"), "resume.txt")
    assert parsed.used_ocr is False
