"""Phase 8: builds the RAG knowledge base index from data/knowledge/*.md
(chunk -> embed -> upsert into a vector store), and exposes retrieval.

Built lazily and cached in-process: the knowledge base is small and static
relative to a single deployment's lifetime, so re-indexing on every request
would be wasted embedding calls.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.providers.base import EmbeddingProvider
from app.providers.factory import get_embedding_provider
from app.retrieval.chunking import chunk_document
from app.retrieval.vector_store import InMemoryVectorStore, ScoredRecord, VectorRecord, VectorStore


class KnowledgeBase:
    def __init__(self, knowledge_dir: Path, embedder: EmbeddingProvider, store: VectorStore | None = None):
        self.knowledge_dir = knowledge_dir
        self.embedder = embedder
        self.store = store or InMemoryVectorStore()
        self._indexed = False

    def build_index(self) -> int:
        if not self.knowledge_dir.exists():
            self._indexed = True
            return 0

        all_chunks = []
        for path in sorted(self.knowledge_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            all_chunks.extend(chunk_document(text, source=path.name))

        if not all_chunks:
            self._indexed = True
            return 0

        vectors = self.embedder.embed([c.text for c in all_chunks])
        records = [
            VectorRecord(
                id=f"{c.source}:{i}",
                text=c.text,
                vector=vec,
                metadata={"source": c.source, "heading": c.heading},
            )
            for i, (c, vec) in enumerate(zip(all_chunks, vectors))
        ]
        self.store.upsert(records)
        self._indexed = True
        return len(records)

    def retrieve(self, query: str, top_k: int = 4) -> list[ScoredRecord]:
        if not self._indexed:
            self.build_index()
        query_vector = self.embedder.embed([query])[0]
        return self.store.search(query_vector, top_k=top_k)


@lru_cache
def get_knowledge_base() -> KnowledgeBase:
    settings = get_settings()
    embedder = get_embedding_provider()
    knowledge_dir = settings.skills_data_dir.parent / "knowledge"
    kb = KnowledgeBase(knowledge_dir=knowledge_dir, embedder=embedder)
    kb.build_index()
    return kb
