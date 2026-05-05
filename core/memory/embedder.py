"""
Local embedder using all-MiniLM-L6-v2.
384 dimensions, fast CPU, well-tested for semantic search.
~20ms CPU per embed, loads once, reuses forever.
Zero API calls, zero cost, works offline.
"""
from __future__ import annotations

import threading

_lock = threading.Lock()
_model = None
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"


def _load():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                print(f"[MEMORY] Loading embedder: {MODEL_ID} (first run only)...")
                _model = SentenceTransformer(
                    MODEL_ID,
                    device="cpu",
                    local_files_only=True,
                )
                print("[MEMORY] Embedder ready.")
    return _model


class Embedder:
    """Thread-safe singleton. Load once, use forever."""

    def embed(self, text: str) -> list[float]:
        model = _load()
        prefixed = f"search_document: {text}"
        return model.encode(
            prefixed,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

    def embed_query(self, text: str) -> list[float]:
        """Use different prefix for queries vs documents."""
        model = _load()
        prefixed = f"search_query: {text}"
        return model.encode(
            prefixed,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        model = _load()
        prefixed = [f"search_document: {t}" for t in texts]
        vecs = model.encode(
            prefixed,
            normalize_embeddings=True,
            batch_size=16,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vecs]