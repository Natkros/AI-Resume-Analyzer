# Security

## Authentication

JWT bearer tokens (`python-jose`), issued on register/login, expiring after
`ACCESS_TOKEN_EXPIRE_MINUTES` (default 60). Passwords are hashed with
`bcrypt` directly (see note below) — never stored or logged in plaintext.

**Note on the bcrypt/passlib incident**: the original implementation used
`passlib.CryptContext(schemes=["bcrypt"])`, which is incompatible with
`bcrypt>=4.1` (passlib's backend-detection code calls an API bcrypt removed)
and crashes on the very first password hash. This was caught by an
end-to-end smoke test, not a unit test (unit tests never exercised
`hash_password`). Fixed by calling the `bcrypt` library directly in
`app/core/security.py`, with the input explicitly truncated to bcrypt's
72-byte limit rather than letting the library raise on long passwords.

## Authorization

Every resource with an owner (`Resume.owner_id`, `Job.owner_id`) is
access-controlled via `require_ownership()` in `app/api/deps.py`: if a
resource has an owner, only that owner (by JWT subject) may read/delete it;
anonymous access to an owned resource returns 403. Resources created
without authentication (`owner_id is None`) remain accessible to anyone
holding the ID — this matches the product's "try without an account" flow
and is a deliberate choice, not an oversight; it means an anonymous
resume's ID functions like a capability token, so treat those IDs as
sensitive.

## Input validation

- File uploads: extension allowlist (`.pdf`/`.docx`/`.txt`), size cap
  (`MAX_FILE_SIZE_MB`), MIME/extension mismatches surfaced as parse errors
  rather than crashing the process.
- All request bodies are validated by Pydantic models; unexpected fields are
  ignored, missing required fields are rejected with 422.
- SQL is entirely via SQLAlchemy's ORM (parameterized) — no raw string SQL
  anywhere in the codebase.

## Secrets

No API key or credential is hardcoded. `.env.example` documents every
required variable; a missing `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` degrades
the LLM-dependent endpoints to a clear 503 (`LLM_UNAVAILABLE`) rather than
throwing an unhandled exception or silently using a default key.

## Privacy

- `DELETE /api/v1/resumes/{id}` lets an authenticated owner remove their
  uploaded resume data on request (Phase 41).
- Resume/JD text is logged only as opaque IDs in structured logs
  (`app/core/logging.py`) — raw resume content is never written to logs.
- Uploaded files are not persisted to disk; only the extracted structured
  JSON and raw text are stored in Postgres.

## Known gaps

- No rate limiting yet on `/resumes/upload` or the LLM-backed endpoints —
  worth adding before any public deployment, since both are the most
  expensive endpoints (OCR and LLM tokens respectively).
- CORS is configured via a single `CORS_ORIGINS` env var; production
  deployments should restrict this to the actual frontend origin rather
  than the default `http://localhost:3000`.
- No CSRF protection is needed today since the API is bearer-token
  authenticated (not cookie-based), but this assumption should be revisited
  if cookie-based sessions are ever added.
