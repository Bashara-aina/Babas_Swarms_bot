"""Mem0 vector backend selection: local Chroma vs Supabase (PostgreSQL + pgvector).

Set ``MEM0_USE_SUPABASE=1`` and provide ``SUPABASE_DB_URL`` (or ``DATABASE_URL``)
with a Postgres connection string from Supabase **Settings → Database**.

``MEM0_EMBEDDING_DIMS`` must match your embedder (e.g. 768 for ``nomic-embed-text``,
1536 for many OpenAI-compatible models). Align with the vector column in Supabase.
"""

from __future__ import annotations

import os
from typing import Any


def mem0_vector_store_config() -> dict[str, Any]:
    """Return the ``vector_store`` fragment for :func:`mem0.Memory.from_config`."""
    use_sb = os.getenv("MEM0_USE_SUPABASE", "").strip().lower() in ("1", "true", "yes", "on")
    conn = (os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL") or "").strip()
    # Only use Supabase if explicitly enabled AND connection is a postgres:// URI
    # (not a REST API URL like https://xxx.supabase.co)
    if use_sb and conn and conn.startswith("postgres"):
        return {
            "provider": "supabase",
            "config": {
                "connection_string": conn,
                "collection_name": os.getenv("MEM0_COLLECTION_NAME", "legion_memories"),
                "embedding_model_dims": int(os.getenv("MEM0_EMBEDDING_DIMS", "768")),
                "index_method": os.getenv("MEM0_INDEX_METHOD", "hnsw"),
                "index_measure": os.getenv("MEM0_INDEX_MEASURE", "cosine_distance"),
            },
        }
    # Default: local ChromaDB (always works, no external deps)
    chroma_path = os.path.expanduser(os.getenv("MEM0_CHROMA_PATH", "~/.legion/mem0_chroma"))
    return {
        "provider": "chroma",
        "config": {
            "collection_name": os.getenv("MEM0_CHROMA_COLLECTION", "legion_memory"),
            "path": chroma_path,
        },
    }
