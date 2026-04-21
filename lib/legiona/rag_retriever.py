"""Supabase pgvector retriever for Legiona grounded context."""

from __future__ import annotations

import os

from supabase import create_client

from lib.legiona.rag_indexer import get_embedding


def retrieve_context(query: str, top_k: int = 5) -> list[str]:
    """Embed query via MiniMax and return top-k matching chunks from Supabase."""
    supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_KEY")
    )
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not set (SUPABASE_URL + service key)")

    client = create_client(supabase_url, supabase_key)
    query_embedding = get_embedding(query)
    response = client.rpc(
        "match_legiona_embeddings",
        {"query_embedding": query_embedding, "match_count": top_k},
    ).execute()
    rows = response.data or []
    return [row.get("content", "") for row in rows if row.get("content")]
