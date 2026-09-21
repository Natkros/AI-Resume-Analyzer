# API Reference

Base path: `/api/v1`. Interactive docs at `/docs` (Swagger UI) once the
backend is running. All endpoints accept/return JSON except file upload
(`multipart/form-data`). Authenticated requests use `Authorization: Bearer
<token>`.

Errors follow one shape everywhere:
```json
{ "error": { "code": "RESUME_NOT_FOUND", "message": "...", "request_id": "..." } }
```

## Auth

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/auth/register` | — | `{email, password, full_name?, role?}` -> `{access_token}` |
| POST | `/auth/login` | — | `{email, password}` -> `{access_token}` |

## Resumes

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/resumes/upload` | optional | `multipart/form-data` file. If a token is sent, the resume is owned by that user. |
| GET | `/resumes` | required | List the current user's resumes. |
| GET | `/resumes/{id}` | optional | 403 if the resume is owned by someone else. |
| DELETE | `/resumes/{id}` | required | Owner-only. |

## Jobs

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/jobs/analyze` | optional | `{text, company?}` -> parsed JD. |
| GET | `/jobs` | required | List the current user's jobs. |
| GET | `/jobs/{id}` | optional | 403 if owned by someone else. |

## Matching

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/matching/analyze` | optional | `{resume_id, job_id}` -> compatibility + match + ATS. Enforces ownership on both inputs. |
| GET | `/matching/{analysis_id}` | optional | Re-fetch a stored analysis. |
| POST | `/matching/compare?resume_id=...` | optional | Body: `["job_id", ...]`. Phase 32 multi-job comparison — always returns full per-job criteria, never a bare rank. |

## Recommendations (require an LLM provider configured; 503 otherwise)

| Method | Path | Notes |
|---|---|---|
| POST | `/resumes/{analysis_id}/optimize` | Rewritten summary + bullet-level before/after. |
| POST | `/interview/generate` | Body: `{analysis_id}`. Technical/project/behavioral questions. |
| POST | `/roadmap/generate` | Body: `{analysis_id}`. Per-missing-skill learning roadmap. |
| POST | `/matching/{analysis_id}/recommendations` | Prioritized, evidence-cited recommendations. |

## Agents

| Method | Path | Notes |
|---|---|---|
| POST | `/agents/analyze` | `{resume_id, job_id, include_llm_agents}` -> Phase-64-style consolidated report. LLM agents degrade gracefully (omitted, not errored) if no provider is configured. |

## Async processing (optional, requires a running Celery worker + Redis)

| Method | Path | Notes |
|---|---|---|
| POST | `/async/resumes/upload` | 202 + `{task_id, poll_url}`. |
| POST | `/async/jobs/analyze` | 202 + `{task_id, poll_url}`. |
| POST | `/async/matching/analyze` | 202 + `{task_id, poll_url}`. |
| GET | `/async/tasks/{task_id}` | `{status, result, error}` — poll until `status == "SUCCESS"`. |

## Example: full flow

```bash
RESUME_ID=$(curl -s -X POST localhost:8000/api/v1/resumes/upload -F file=@resume.pdf | jq -r .id)
JOB_ID=$(curl -s -X POST localhost:8000/api/v1/jobs/analyze -H 'Content-Type: application/json' \
  -d '{"text":"..."}' | jq -r .id)
curl -s -X POST localhost:8000/api/v1/matching/analyze -H 'Content-Type: application/json' \
  -d "{\"resume_id\":\"$RESUME_ID\",\"job_id\":\"$JOB_ID\"}" | jq .
```
