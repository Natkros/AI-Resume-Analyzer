# Contributing

## Principles (see docs/ARCHITECTURE.md for the full rationale)

1. Prefer deterministic code over an LLM call wherever the task has a
   well-defined grammar (parsing, matching, scoring). Reserve the LLM for
   genuinely open-ended generation.
2. Every LLM-backed function must be grounded (resume/JD text passed in
   explicitly) and must never fabricate candidate experience — extend
   `SAFETY_PREAMBLE` in `recommendation_service.py` rather than writing a
   new ungrounded prompt.
3. Business logic (`pipelines/`, `services/`, `scoring/`) must depend only
   on `app/providers/base.py` interfaces, never a vendor SDK directly.
4. A new skill goes in `data/skills/<category>.json` with its aliases —
   never hardcode skill strings in Python.

## Running checks locally before opening a PR

```bash
cd backend
pip install -r requirements.txt ruff
ruff check app tests
pytest -q
python -m app.evaluation.run_eval   # confirm no regression vs. gold dataset

cd ../frontend
npm install
npx tsc --noEmit
npm run build
```

## Adding a new skill

Edit the relevant file in `data/skills/` (or add a new category file — it's
picked up automatically by `SkillTaxonomy._load()`):

```json
{"canonical": "Terraform", "aliases": ["terraform iac"]}
```

Aliases are matched case-insensitively with word boundaries, so `"iac"`
alone should not be added as an alias if it's ambiguous with other
technologies.

## Adding a new LLM provider

1. Create `app/providers/<name>_provider.py` implementing `LLMProvider`
   (see `anthropic_provider.py` for the JSON-repair pattern to reuse).
2. Register it in `app/providers/factory.py::get_llm_provider()`.
3. No caller code changes — `recommendation_service.py` and the agents in
   `app/agents/llm_agents.py` only depend on the `LLMProvider` interface.

## Tests

- Deterministic pipeline changes (parsing, matching, scoring, ATS) need a
  unit test in `backend/tests/` — these run without any API key or live
  database.
- Changes to `jd_parser.py` or `skill_taxonomy.py` should also be checked
  against `python -m app.evaluation.run_eval` — a precision/recall
  regression there can indicate a subtle bug even if the targeted unit
  tests still pass (this caught a real bug during development: a job
  title leaking into required skills — see `docs/EVALUATION.md`).
- API-layer changes (new endpoint, changed auth behavior) don't currently
  have a pytest suite (no DB fixture is wired up); validate manually with
  `TestClient` against a throwaway SQLite DB, as demonstrated in this
  project's development smoke tests.
