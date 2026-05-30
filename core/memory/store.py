"""
ChromaDB-based persistent vector store.
Data lives at ~/.swarms_memory/ — survives restarts, zero Docker needed.
"""
from __future__ import annotations

import hashlib
import re
import threading
from pathlib import Path

import chromadb
from chromadb.config import Settings

from .embedder import Embedder


def _keyword_score(text: str, query: str) -> float:
    """Keyword overlap score 0..1."""
    if not query or not text:
        return 0.0
    q_words = set(query.lower().split())
    t_words = set(text.lower().split())
    if not q_words:
        return 0.0
    return sum(1 for w in q_words if w in t_words) / len(q_words)

MEMORY_DIR = Path.home() / ".swarms_memory"
COLLECTION_NAME = "babas_swarms"
embedder = Embedder()


_client_singleton: chromadb.PersistentClient | None = None  # type: ignore[reportGeneralTypeIssues]
_client_lock = threading.Lock()


def _get_client() -> chromadb.PersistentClient:  # type: ignore[reportGeneralTypeIssues]
    global _client_singleton
    if _client_singleton is None:
        with _client_lock:
            if _client_singleton is None:
                MEMORY_DIR.mkdir(parents=True, exist_ok=True)
                _client_singleton = chromadb.PersistentClient(
                    path=str(MEMORY_DIR),
                    settings=Settings(anonymized_telemetry=False),
                )
    return _client_singleton


_collection_singleton: chromadb.Collection | None = None
_collection_lock = threading.Lock()


def _get_collection() -> chromadb.Collection:
    global _collection_singleton
    if _collection_singleton is None:
        with _collection_lock:
            if _collection_singleton is None:
                _collection_singleton = _get_client().get_or_create_collection(
                    name=COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"},
                )
    return _collection_singleton  # type: ignore[return-value]


def _chunk(text: str, min_len: int = 60) -> list[str]:
    """
    Split text into atomic fact-chunks.
    Each chunk = 1-3 sentences. Smaller = more precise recall.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks, current = [], []
    current_len = 0

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        current.append(sent)
        current_len += len(sent)
        if current_len >= 300 or len(current) >= 3:
            chunk = " ".join(current)
            if len(chunk) >= min_len:
                chunks.append(chunk)
            current, current_len = [], 0

    if current:
        chunk = " ".join(current)
        if len(chunk) >= min_len:
            chunks.append(chunk)

    return chunks if chunks else [text[:500]]


_store_lock = threading.Lock()


class MemoryStore:
    def remember(
        self,
        content: str,
        agent_id: str = "shared",
        session_id: str | None = None,
        memory_type: str = "episodic",
        importance: float = 1.0,
    ) -> int:
        """
        Store content as atomic chunks with deduplication.
        Returns number of NEW chunks stored (0 = all duplicates).
        """
        col = _get_collection()
        chunks = _chunk(content)
        stored = 0

        for chunk in chunks:
            doc_id = hashlib.md5(chunk.strip().lower().encode(), usedforsecurity=False).hexdigest()
            embedding = embedder.embed(chunk)  # now always returns 768-dim list
            if not embedding or len(embedding) != 768:
                continue  # skip bad embeddings (Ollama dead / zero vector)
            with _store_lock:
                count_before = col.count()
                col.add(
                    documents=[chunk],
                    embeddings=[embedding],
                    metadatas=[{
                        "agent_id": agent_id,
                        "session_id": session_id or "none",
                        "memory_type": memory_type,
                        "importance": importance,
                    }],
                    ids=[doc_id],
                )
                if col.count() > count_before:
                    stored += 1

        return stored

    def recall(
        self,
        query: str,
        agent_id: str | None = None,
        top_k: int = 10,
        min_score: float = 0.25,
        memory_type: str | None = None,
    ) -> list[str]:
        """
        Semantic search. Returns list of relevant memory strings.
        Searches agent's own memories + shared memories.
        """
        col = _get_collection()
        total = col.count()
        if total == 0:
            return []

        query_embedding = embedder.embed_query(query)
        if query_embedding is None:
            # Ollama embedder is down — fall back to keyword-only chunk scan
            all_chunks: list[tuple[str, float]] = []
            try:
                col = _get_collection()
                all_docs = col.get(include=["documents"])["documents"]
                for doc in all_docs:
                    if not doc or len(doc) < 20:
                        continue
                    score = _keyword_score(doc, query)
                    if score > 0:
                        all_chunks.append((doc, score))
                all_chunks.sort(key=lambda x: x[1], reverse=True)
                return [doc for doc, _ in all_chunks[:top_k]]
            except Exception:
                return []

        n = min(top_k, total)
        where = None
        if agent_id and agent_id != "shared":
            where = {"agent_id": {"$in": [agent_id, "shared"]}}
        if memory_type:
            type_filter = {"memory_type": {"$eq": memory_type}}
            where = {**where, **type_filter} if where else type_filter

        if where:
            results = col.query(
                query_embeddings=[query_embedding],
                n_results=n,
                include=["documents", "distances", "metadatas"],  # type: ignore[arg-type]
                where=where,  # type: ignore[arg-type]
            )
        else:
            results = col.query(
                query_embeddings=[query_embedding],
                n_results=n,
                include=["documents", "distances", "metadatas"],  # type: ignore[arg-type]
            )

        docs = results.get("documents", [[]])[0] if results.get("documents") else []  # type: ignore[reportOptionalSubscript]
        distances = results.get("distances", [[]])[0] if results.get("distances") else []  # type: ignore[reportOptionalSubscript]

        filtered = [
            doc for doc, dist in zip(docs, distances, strict=False)
            if (1 - dist / 2) >= min_score
        ]
        return filtered

    def recall_formatted(
        self,
        query: str,
        agent_id: str | None = None,
        top_k: int = 10,
    ) -> str:
        """Returns memory block ready to inject into any system prompt."""
        memories = self.recall(query, agent_id=agent_id, top_k=top_k)
        if not memories:
            return ""
        lines = [
            "━━━ LONG-TERM MEMORY (recalled from persistent store) ━━━"
        ]
        for i, m in enumerate(memories, 1):
            lines.append(f"{i}. {m}")
        lines.append("━━━ END MEMORY — treat as reliable prior context ━━━")
        return "\n".join(lines)

    def count(self) -> int:
        return _get_collection().count()

    def status(self) -> dict:
        n = self.count()
        return {
            "total_memories": n,
            "storage_path": str(MEMORY_DIR),
            "embedder": "nomic-embed-text (Ollama, 768-dim)",
            "collection": COLLECTION_NAME,
            "status": "healthy",
        }