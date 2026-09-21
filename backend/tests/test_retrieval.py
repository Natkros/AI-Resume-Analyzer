from app.providers.local_embeddings import LocalEmbeddingProvider
from app.retrieval.chunking import chunk_document
from app.retrieval.knowledge_base import KnowledgeBase
from app.retrieval.vector_store import InMemoryVectorStore, VectorRecord


def test_chunk_document_splits_on_headings():
    text = "# Heading One\nSome content here.\n\n# Heading Two\nOther content here."
    chunks = chunk_document(text, source="test.md")
    headings = {c.heading for c in chunks}
    assert "Heading One" in headings
    assert "Heading Two" in headings


def test_chunk_document_windows_long_sections():
    body = "word " * 500
    text = f"# Long Section\n{body}"
    chunks = chunk_document(text, source="test.md", max_chars=200, overlap=20)
    assert len(chunks) > 1
    assert all(len(c.text) <= 220 for c in chunks)


def test_in_memory_vector_store_returns_most_similar_first():
    store = InMemoryVectorStore()
    store.upsert([
        VectorRecord(id="a", text="python", vector=[1.0, 0.0], metadata={}),
        VectorRecord(id="b", text="unrelated", vector=[0.0, 1.0], metadata={}),
    ])
    results = store.search([1.0, 0.0], top_k=2)
    assert results[0].record.id == "a"
    assert results[0].score > results[1].score


def test_knowledge_base_retrieves_relevant_chunk(tmp_path):
    (tmp_path / "docs.md").write_text(
        "# Kubernetes\nKubernetes orchestrates containers across a cluster.\n\n"
        "# Unrelated Topic\nThis document discusses baking bread.",
        encoding="utf-8",
    )
    embedder = LocalEmbeddingProvider(model_name="does-not-exist-forces-fallback")
    kb = KnowledgeBase(knowledge_dir=tmp_path, embedder=embedder)
    kb.build_index()
    results = kb.retrieve("Kubernetes container orchestration", top_k=1)
    assert results
    assert "Kubernetes" in results[0].record.text
