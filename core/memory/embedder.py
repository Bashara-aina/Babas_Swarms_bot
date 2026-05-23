"""
Ollama-based embedder using nomic-embed-text.
768 dimensions, served locally at localhost:11434.
Zero extra packages — pure requests to Ollama API.

P0 fix: Removed global _embed_lock — caused 10x slowdown on concurrent recall.
Embedding is naturally idempotent; the only shared state is the liveness cache
which is already atomic (bool + expiry, updated under monotonic compare-and-swap).
"""
from __future__ import annotations

import threading
import time
from typing import Any

import requests

_ollama_base = "http://localhost:11434"
_model = "nomic-embed-text"

# ── Liveness cache (atomic, no lock needed) ─────────────────────────────────

_ollama_live: bool | None = None
_ollama_live_expiry: float = 0.0
_LIVE_TTL: float = 10.0  # seconds before re-checking

# ── Embedding cache (LRU, thread-safe) ───────────────────────────────────────

_embed_cache: dict[str, list[float]] = {}
_cache_lock = threading.Lock()
_CACHE_MAX = 512  # entries — more than enough for recall queries


def _check_ollama_live() -> bool:
    """Fast liveness check with 10s TTL cache. Thread-safe, no lock needed."""
    global _ollama_live, _ollama_live_expiry
    now = time.monotonic()
    if _ollama_live is not None and now < _ollama_live_expiry:
        return _ollama_live
    try:
        resp = requests.get(f"{_ollama_base}/api/tags", timeout=3)
        _ollama_live = resp.status_code == 200
    except Exception:
        _ollama_live = False
    _ollama_live_expiry = now + _LIVE_TTL
    return _ollama_live


def _embed_via_ollama(text: str) -> list[float] | None:
    """Call Ollama /api/embeddings. Thread-safe. Caches results. Returns None if dead."""
    # Check cache first — no lock needed for reads
    cache_key = text[:256]  # truncate long texts for cache key
    cached = _embed_cache.get(cache_key)
    if cached is not None:
        return cached

    if not _check_ollama_live():
        return None
    payload: dict[str, Any] = {"model": _model, "prompt": text}
    try:
        resp = requests.post(
            f"{_ollama_base}/api/embeddings",
            json=payload,
            timeout=5,
        )
        resp.raise_for_status()
        embedding = resp.json()["embedding"]
    except Exception:
        # Mark as dead so next calls fail fast
        global _ollama_live, _ollama_live_expiry
        _ollama_live = False
        _ollama_live_expiry = time.monotonic() + _LIVE_TTL
        return None

    # Cache result — lock only for write
    with _cache_lock:
        if len(_embed_cache) < _CACHE_MAX:
            _embed_cache[cache_key] = embedding

    return embedding


# Pre-warm: verify Ollama is reachable
if _check_ollama_live():
    print("[EMBEDDER] Ollama connected — nomic-embed-text ready (cache enabled)")
else:
    print("[EMBEDDER] Ollama not reachable — embedding disabled (will use keyword fallback)")


class Embedder:
    """Thread-safe singleton. Embeddings cached per text."""

    def embed(self, text: str) -> list[float]:
        result = _embed_via_ollama(text)
        if result is None:
            # Return zero vector so calling code doesn't crash
            return [0.0] * 768
        return result

    def embed_query(self, text: str) -> list[float]:
        result = _embed_via_ollama(text)
        if result is None:
            return [0.0] * 768
        return result

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


# ── Re-embed existing ChromaDB store ────────────────────────────────────────
def reembed_store():
    """
    Re-embed all memories from the old 384-dim space → new 768-dim space.
    Deletes old collection and re-stores everything.
    """
    import chromadb
    from chromadb.config import Settings

    from .embedder import Embedder

    old_client = chromadb.PersistentClient(
        path=str(__import__("pathlib").Path.home() / ".swarms_memory"),
        settings=Settings(anonymized_telemetry=False),
    )
    old_col = old_client.get_collection("babas_swarms")
    all_items = old_col.get(include=["documents", "metadatas"])

    if not all_items.get("documents"):
        print("[REEMBED] Nothing to re-embed — collection is empty")
        return

    print(f"[REEMBED] Re-embedding {len(all_items['documents'])} chunks with nomic-embed-text...")

    # Delete and recreate collection
    try:
        old_client.delete_collection("babas_swarms")
    except Exception:
        pass

    new_client = chromadb.PersistentClient(
        path=str(__import__("pathlib").Path.home() / ".swarms_memory"),
        settings=Settings(anonymized_telemetry=False),
    )
    new_col = new_client.create_collection(
        name="babas_swarms",
        metadata={"hnsw:space": "cosine"},
    )

    embedder = Embedder()
    ids = all_items.get("ids", [])
    docs = all_items["documents"]
    metas = all_items.get("metadatas", [{}] * len(docs))

    embeddings = embedder.embed_batch(docs)
    new_col.add(
        documents=docs,
        embeddings=embeddings,
        metadatas=metas,
        ids=ids,
    )
    print(f"[REEMBED] Done — {new_col.count()} chunks stored with 768-dim nomic-embed-text")


if __name__ == "__main__":
    reembed_store()
