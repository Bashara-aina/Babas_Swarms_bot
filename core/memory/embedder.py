"""
Ollama-based embedder using nomic-embed-text.
768 dimensions, served locally at localhost:11434.
Zero extra packages — pure requests to Ollama API.
"""
from __future__ import annotations

import threading
from typing import Any

import requests

_ollama_base = "http://localhost:11434"
_model = "nomic-embed-text"
_embed_lock = threading.Lock()

# Pre-warm: verify Ollama is reachable
try:
    resp = requests.get(f"{_ollama_base}/api/tags", timeout=5)
    if resp.status_code == 200:
        print("[EMBEDDER] Ollama connected — nomic-embed-text ready")
    else:
        print(f"[EMBEDDER] Ollama returned {resp.status_code}")
except Exception as e:
    print(f"[EMBEDDER] Ollama not reachable: {e}")


def _embed_via_ollama(text: str) -> list[float]:
    """Call Ollama /api/embeddings endpoint. Thread-safe."""
    payload: dict[str, Any] = {"model": _model, "prompt": text}
    resp = requests.post(
        f"{_ollama_base}/api/embeddings",
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


class Embedder:
    """Thread-safe singleton. One Ollama call at a time per thread."""

    def embed(self, text: str) -> list[float]:
        with _embed_lock:
            return _embed_via_ollama(text)

    def embed_query(self, text: str) -> list[float]:
        with _embed_lock:
            return _embed_via_ollama(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        with _embed_lock:
            return [_embed_via_ollama(t) for t in texts]


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
