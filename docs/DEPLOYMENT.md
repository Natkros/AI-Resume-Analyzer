# Deployment

## Local (Docker Compose)

```bash
cp .env.example .env   # fill in ANTHROPIC_API_KEY/OPENAI_API_KEY if you want the LLM endpoints
docker compose up --build
```

Starts Postgres, Redis, the FastAPI backend (port 8000), and the Next.js
frontend (port 3000). The backend's `Dockerfile` builds from the repo root
(context: `.`, dockerfile: `backend/Dockerfile`) so it can `COPY data ./data`
— the skill taxonomy and knowledge base ship inside the image.

## Environment variables

See `.env.example` for the full list. The ones that change behavior most:

| Variable | Effect |
|---|---|
| `MODEL_PROVIDER` / `MODEL_NAME` | Which LLM backs recommendations/optimization/interview/roadmap. Unset -> those endpoints return 503, everything else still works. |
| `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL` | Semantic matching quality. Falls back to a dependency-free hashed embedding if the model can't load (e.g. no internet in a sandboxed build). |
| `VECTOR_DB_PROVIDER` | `pgvector` (default, unused today — in-memory store is used) or `qdrant` (requires `QDRANT_URL` reachable). |
| `DATABASE_URL` | Any SQLAlchemy-compatible Postgres URL. |
| `CORS_ORIGINS` | Comma-separated list; must include the deployed frontend origin. |

## Database migrations

The project currently creates tables via `Base.metadata.create_all()` (see
any of the smoke-test scripts) rather than Alembic migrations — `alembic`
is in `requirements.txt` and a `migrations/` directory is expected by the
structure in the original spec, but no migration has been authored yet.
For a first deploy, running `create_all()` once against a fresh database is
sufficient; introduce Alembic before the schema needs to evolve against
existing data.

## Background workers

The synchronous endpoints (`/api/v1/resumes/upload`, `/api/v1/jobs/analyze`,
`/api/v1/matching/analyze`) work without any worker process — this is what
local dev and CI use. For production, expensive steps (OCR-heavy PDF
parsing, embedding generation) can be moved off the request path via the
`/api/v1/async/*` endpoints, which require a Celery worker:

```bash
celery -A app.workers.celery_app worker --loglevel=info
```

pointed at the same `REDIS_URL` as the API process.

## Frontend

`npm run build && npm start`, or the provided `frontend/Dockerfile`. Set
`NEXT_PUBLIC_API_BASE_URL` to the backend's public URL at build time (it's
inlined into the client bundle, so it must be set before `next build`, not
just at runtime).

## CI

`.github/workflows/ci.yml` runs on every push/PR to `main`: backend lint
(`ruff`) + the deterministic-pipeline test suite (no Postgres/Redis
required — see `docs/EVALUATION.md` for why those tests don't need live
infra), and a frontend typecheck + production build. Neither job needs any
API key.
