# Evaluation

## Gold dataset

`data/evaluation/gold_resumes/*.json` — 3 hand-authored resumes (backend,
ML, frontend profiles) each annotated with the skills, sections, and email
a correct parse should produce. `data/evaluation/gold_jd_matches.json`
pairs each resume with a JD and the expected matched/missing required
skills, for evaluating the matching engine end-to-end.

This is intentionally small (Phase 44 calls for "a small manually
annotated dataset") — it exists to catch regressions in the deterministic
pipeline, not to be a statistically representative benchmark.

## Metrics

`app/evaluation/metrics.py` implements standard, dependency-free
precision/recall/F1 (`precision_recall_f1`, `average_prf1`) plus
`recall_at_k` and `mean_reciprocal_rank` for retrieval-style evaluation
(available for the RAG knowledge base, not currently wired into a gold
retrieval set since the knowledge base is small enough to check by hand).

## Running the harness

```bash
cd backend
python -m app.evaluation.run_eval
```

Prints a JSON report with three sections: `skill_extraction`,
`section_detection`, `skill_matching`, each with an average
precision/recall/F1 and a per-item breakdown.

## Current results (deterministic pipeline, no LLM)

| Metric | F1 |
|---|---|
| Skill extraction | ~0.95 |
| Section detection | ~0.93 |
| Skill matching (required-skill precision/recall) | ~0.92 |

`backend/tests/test_evaluation.py` asserts each of these stays above 0.90,
so a change that regresses extraction/matching quality fails CI, not just a
manual check. This is how the JD-parser bug (a job title like "ML Engineer"
leaking "ML" into required skills via the short `"ml"` alias) was caught and
fixed during development — the eval harness surfaced a precision drop from
1.0 to 0.6 on one gold case that a plain unit test wouldn't have flagged as
clearly.

## What isn't covered yet

- LLM output evaluation (factuality/groundedness/consistency scoring) — the
  anti-hallucination *prompting* is in place (see AI_PIPELINE.md) but there
  is no automated harness scoring actual LLM responses against it, since
  that requires either a live API key in CI or a mocked LLM with fixture
  responses.
- Retrieval quality (recall@k/MRR) against a labeled query set for the RAG
  knowledge base — the metrics functions exist but no gold query set has
  been built yet.
