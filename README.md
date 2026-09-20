# AI Resume Analyzer & Job Matcher

Explainable resume-job compatibility analysis: deterministic resume/JD parsing, a
normalized skill taxonomy, multi-layer matching (exact/alias/semantic), an
itemized "Resume-Job Compatibility Score" with evidence for every subscore, an
ATS risk analyzer, and an optional grounded LLM layer for recommendations,
resume optimization, interview prep, and learning roadmaps.

This is a real, incrementally-built project — see **Build status** below for
exactly what is implemented vs. scaffolded, so nothing here is oversold.

## Architecture

```
Frontend (Next.js/React/TS/Tailwind)
        │
        ▼
FastAPI backend (/api/v1)
        │
   ┌────┼─────────────────────────────────────┐
   ▼    ▼                                      ▼
Resume   JD Parser                    Auth (JWT)
Parser   (app/pipelines/jd_parser.py)
(app/pipelines/resume_parser.py)
   │        │
   └───┬────┘
       ▼
Skill Taxonomy (deterministic, data/skills/*.json)
       ▼
Matching Engine (app/scoring/matching_engine.py)
 exact/alias match + semantic similarity (embeddings) + evidence lookup
       ▼
Compatibility Score (app/scoring/compatibility_score.py)
 required skills 30% / preferred 10% / experience 20% / projects 15% /
 semantic 10% / education 5% / certifications 5% / ATS 5% — weights configurable
       ▼
ATS Analyzer (app/scoring/ats_analyzer.py)
       ▼
(optional) LLM layer (app/services/recommendation_service.py)
 recommendations / resume optimization / interview questions / learning roadmap
 — grounded in resume+JD text only, structured JSON output, never fabricates
       ▼
PostgreSQL (resumes, jobs, analyses, recommendations, users, audit_logs)
```

Everything through the Compatibility Score is **deterministic** — no LLM call
required to get a full, explainable match result. The LLM is used only where
genuine reasoning is needed (Phase 7: recommendations/optimization/interview
prep/roadmap), and every prompt is grounded in the actual resume/JD text with
an explicit no-fabrication instruction.

## What's implemented (real, tested code)

- **Resume parsing** (PDF/DOCX/TXT, OCR fallback for scanned PDFs): [backend/app/pipelines/document_extractor.py](backend/app/pipelines/document_extractor.py), [section_detector.py](backend/app/pipelines/section_detector.py), [entity_extractor.py](backend/app/pipelines/entity_extractor.py), [resume_parser.py](backend/app/pipelines/resume_parser.py)
- **Skill taxonomy & normalization** (aliases, categories): [backend/app/services/skill_taxonomy.py](backend/app/services/skill_taxonomy.py), data in [data/skills/](data/skills/)
- **JD parsing** (required vs. preferred, experience/education requirements, responsibilities): [backend/app/pipelines/jd_parser.py](backend/app/pipelines/jd_parser.py)
- **Matching engine** (exact/alias + semantic similarity + evidence): [backend/app/scoring/matching_engine.py](backend/app/scoring/matching_engine.py)
- **Explainable compatibility score**: [backend/app/scoring/compatibility_score.py](backend/app/scoring/compatibility_score.py)
- **ATS analyzer**: [backend/app/scoring/ats_analyzer.py](backend/app/scoring/ats_analyzer.py)
- **Swappable LLM/embedding providers** (Anthropic/OpenAI/local, with an offline-safe embedding fallback): [backend/app/providers/](backend/app/providers/)
- **Grounded LLM recommendation layer**: [backend/app/services/recommendation_service.py](backend/app/services/recommendation_service.py)
- **FastAPI app** with auth (JWT), resume upload, JD analysis, matching, multi-job comparison, recommendation endpoints, structured error responses, request-ID logging: [backend/app/main.py](backend/app/main.py), [backend/app/api/](backend/app/api/)
- **SQLAlchemy models** for users/resumes/jobs/analyses/recommendations/audit_logs: [backend/app/models/orm.py](backend/app/models/orm.py)
- **24 passing unit tests** for the deterministic pipeline (parser, taxonomy, JD parsing, matching, scoring, ATS): [backend/tests/](backend/tests/)
- **Next.js frontend**: landing page, resume upload, JD input, and a full analysis dashboard (score breakdown, matched/missing skills with evidence, ATS issues) wired to the real API: [frontend/app/](frontend/app/)
- **Docker Compose** (Postgres, Redis, backend, frontend) and per-service **Dockerfiles**
- **GitHub Actions CI** (backend lint+test, frontend typecheck+build): [.github/workflows/ci.yml](.github/workflows/ci.yml)

## Scaffolded / not yet built (honest gaps)

These are structurally planned for (provider abstractions, DB tables, folders
exist) but not fully implemented — future work:

- RAG knowledge base + vector retrieval (Qdrant/pgvector wiring, chunking, knowledge docs)
- Multi-agent orchestration layer (`app/agents/`)
- Celery background job processing for resume parsing (currently synchronous)
- Frontend: dashboard/comparison/optimization/interview/roadmap/settings pages
- Full auth-gated ownership checks on every endpoint (auth exists; not all routes enforce it yet)
- AI evaluation framework (gold dataset, precision/recall/nDCG harness)
- Resume versioning, semantic career graph
- Full docs set (ARCHITECTURE.md/API.md/SECURITY.md beyond this README)

## Local setup

### Backend
```bash
cd backend
python -m venv .venv
.venv/Scripts/activate   # or source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp ../.env.example ../.env   # fill in DATABASE_URL / API keys
uvicorn app.main:app --reload
```

Run tests (no live Postgres required — they exercise the deterministic pipeline directly):
```bash
pytest -q
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

### Full stack with Docker
```bash
cp .env.example .env
docker compose up --build
```

## API examples

```bash
curl -X POST http://localhost:8000/api/v1/resumes/upload -F "file=@resume.pdf"

curl -X POST http://localhost:8000/api/v1/jobs/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "GenAI Engineer... Required: Python, FastAPI..."}'

curl -X POST http://localhost:8000/api/v1/matching/analyze \
  -H "Content-Type: application/json" \
  -d '{"resume_id": "...", "job_id": "..."}'
```

## Safety principles enforced in code

- The overall score is always labeled **"Resume-Job Compatibility Score"**, never a hiring probability ([compatibility_score.py](backend/app/scoring/compatibility_score.py)).
- Every matched skill carries an evidence snippet or an explicit "no evidence found" ([matching_engine.py](backend/app/scoring/matching_engine.py)).
- LLM prompts explicitly forbid inventing employers/projects/metrics/certifications not present in the source resume text ([recommendation_service.py](backend/app/services/recommendation_service.py)).
- Structured LLM output is requested via JSON schema and validated before use; malformed output surfaces raw text rather than being silently accepted.

## License

MIT (see [LICENSE](LICENSE)).
