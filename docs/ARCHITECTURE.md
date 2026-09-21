# Architecture

## Layering

The backend is organized so business logic never depends on a specific
vendor SDK or transport:

```
app/api/          FastAPI routers — request/response shaping, auth, ownership checks only
app/pipelines/     Deterministic extraction: document -> text -> sections -> entities -> skills
app/services/      Cross-cutting logic: skill taxonomy, LLM-backed recommendations, rehydration
app/scoring/       Matching engine, compatibility score, ATS analyzer
app/providers/     LLMProvider / EmbeddingProvider interfaces + Anthropic/OpenAI/local adapters
app/retrieval/     RAG: chunking, vector store abstraction, knowledge base
app/agents/        Thin orchestration layer over pipelines/services (Phase 9)
app/workers/       Celery tasks mirroring the synchronous endpoints, for async processing
app/models/        SQLAlchemy ORM models
app/core/          Config, DB session, security (JWT/password hashing), logging, error types
```

A route handler in `app/api/` never calls a vendor SDK directly — it calls a
function in `pipelines/`, `services/`, or `scoring/`, which itself only
depends on the `LLMProvider`/`EmbeddingProvider` interfaces in
`app/providers/base.py`. This is what makes the model/embedding provider
swappable via `MODEL_PROVIDER`/`EMBEDDING_PROVIDER` in `.env` without
touching business logic.

## Data flow: one match analysis

```
1. POST /api/v1/resumes/upload
   -> document_extractor.extract_text()        (PDF/DOCX/TXT, OCR fallback)
   -> section_detector.detect_sections()
   -> entity_extractor.extract_contact_info() / extract_achievement_metrics()
   -> skill_taxonomy.extract_from_text()
   => stored as Resume.parsed_json

2. POST /api/v1/jobs/analyze
   -> jd_parser.parse_job_description()         (required vs preferred, experience, education)
   => stored as Job.parsed_json

3. POST /api/v1/matching/analyze
   -> rehydrate.resume_from_json() / jd_from_json()   (JSON -> lightweight objects)
   -> matching_engine.run_matching()             (exact/alias + semantic + evidence)
   -> ats_analyzer.analyze_ats()
   -> compatibility_score.compute_compatibility_score()
   => stored as Analysis row; response includes full evidence, never a bare score

4. (optional) POST /api/v1/matching/{id}/recommendations, /interview/generate, /roadmap/generate
   -> knowledge_base.retrieve()                  (RAG grounding passages)
   -> recommendation_service.*(llm, resume_text, jd_text, missing_skills, matched_skills, kb)
   -> LLMProvider.generate(prompt, schema=...)    (structured JSON, validated)
```

Steps 1-3 never call an LLM. Step 4 is the only LLM-dependent path, and it
degrades explicitly (503 `LLM_UNAVAILABLE`) rather than silently, when no
provider is configured.

## Why deterministic-first

Resume/JD parsing, skill matching, and scoring have small, well-defined
grammars (section headings, "N+ years", skill names/aliases). An LLM call
for these would be slower, non-reproducible, and harder to audit than a
rule-based pass — so Phases 0-6 are 100% deterministic and covered by unit
tests that don't require any API key. The LLM is reserved for genuinely
open-ended generation (rewriting prose, generating novel interview
questions), where determinism isn't the goal.

## Agent layer (Phase 9)

`app/agents/supervisor.py` runs a fixed pipeline of `Agent` objects against
a shared `AgentContext`. Six of them (`ResumeParserAgent`,
`JobRequirementAgent`, `SkillMatchingAgent`, `ATSAnalysisAgent`,
`GapAnalysisAgent`, `ScoringAgent`) are deterministic wrappers around the
pipelines above and always run. Four (`RecommendationAgent`,
`ResumeOptimizationAgent`, `InterviewPreparationAgent`, `RoadmapAgent`) call
an LLM and only run when `include_llm_agents=true` and a provider is
configured. Each agent catches its own exceptions (`run_safely`) so one
agent failing doesn't take down the whole report — errors surface in the
`agent_errors` field of the final report instead.

## RAG (Phase 8)

`data/knowledge/*.md` are chunked on headings (`app/retrieval/chunking.py`),
embedded, and indexed into a `VectorStore` (in-memory by default, or Qdrant
via `VECTOR_DB_PROVIDER=qdrant`). `KnowledgeBase.retrieve()` does a cosine
similarity search and returns the top-k passages, which are appended to LLM
prompts as explicit "use only if genuinely applicable" context, with sources
cited back in the response (`retrieved_sources`) so a consumer can verify
what grounded a given recommendation.
