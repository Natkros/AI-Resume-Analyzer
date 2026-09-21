# AI Pipeline

## Where AI is, and isn't, used

| Task | Approach | Why |
|---|---|---|
| Text extraction (PDF/DOCX/TXT) | Deterministic (`pdfplumber`, `python-docx`) + OCR fallback | Well-defined file formats |
| Section detection | Rule-based alias matching | Small, stable vocabulary of headings |
| Contact info / metric extraction | Regex | Fixed grammar (emails, "reduced X by Y%") |
| Skill extraction/normalization | Deterministic taxonomy lookup | Skills have known canonical names + aliases |
| JD requirement classification | Rule-based (required/preferred markers, "N+ years") | Formulaic JD language |
| Skill matching (exact/alias) | Set membership post-normalization | No ambiguity once both sides are normalized |
| Skill matching (semantic) | Embeddings + cosine similarity | Captures paraphrase (e.g. "built a RAG platform" vs. "retrieval augmented generation") |
| Compatibility scoring | Deterministic weighted formula | Must be auditable and reproducible |
| ATS risk analysis | Deterministic heuristics | No ATS vendor's actual parser is available to call |
| Recommendations / resume rewrite / interview questions / roadmap | LLM, RAG-grounded | Genuinely open-ended generation |

Everything in the left column above the LLM row runs with **zero API calls**
and is covered by unit tests that don't need any key configured.

## Provider abstraction

`app/providers/base.py` defines `LLMProvider` and `EmbeddingProvider`.
Concrete adapters (`anthropic_provider.py`, `openai_provider.py`,
`local_embeddings.py`) are selected in `app/providers/factory.py` from
`MODEL_PROVIDER` / `EMBEDDING_PROVIDER` in `.env`. Business logic
(`recommendation_service.py`, `matching_engine.py`) only imports the
interfaces, never a vendor SDK, so adding a new provider means writing one
adapter file, not touching callers.

`LocalEmbeddingProvider` wraps `sentence-transformers` but falls back to a
dependency-free hashed bag-of-words vector if the model can't be loaded
(no internet, package missing). The fallback is clearly flagged
(`embeddings_are_fallback` / `is_fallback`) in every response that uses it,
rather than silently degrading quality.

## Structured output & validation

`LLMProvider.generate(prompt, schema=...)` appends the JSON schema to the
prompt and asks for JSON-only output. The Anthropic adapter attempts to
parse the raw response, then a fenced-code-block-stripped version, then a
brace-extracted substring, in that order (`_parse_json_with_repair`). If all
three fail, the caller gets `raw_json=None` and the raw text is preserved
(`raw_text` key) rather than crashing — callers check for this and surface
an empty-but-valid structure instead of propagating a parse error to the
user.

## Anti-hallucination measures (Phase 28)

Every LLM-backed function in `recommendation_service.py` starts its prompt
with `SAFETY_PREAMBLE`, which:
- Restricts the model to only the resume text, JD text, and matched/missing
  skill lists actually passed in.
- Explicitly forbids inventing employers, degrees, certifications, projects,
  or metrics.
- Requires explicit "no evidence found" statements instead of filling gaps.
- Forbids framing the output as a hiring prediction.

The resume optimization prompt additionally states: "Do NOT add any
technology, employer, project, or metric that is not already present in the
original resume text — only rephrase, reorder, and sharpen wording."

## RAG grounding

`_rag_context()` in `recommendation_service.py` retrieves up to 3-4 passages
from the knowledge base per call, prefixes them as "use only if genuinely
applicable, do not force it", and returns the sources used
(`retrieved_sources`) alongside the LLM's JSON output, so a caller can see
exactly which knowledge-base passage (if any) informed a given
recommendation — this is what makes the recommendations grounded rather than
purely relying on the base model's general knowledge.
