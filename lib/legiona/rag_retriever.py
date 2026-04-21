"""Supabase pgvector retriever for Legiona grounded context."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from supabase import create_client

from lib.legiona.rag_indexer import get_embedding


def retrieve_context(query: str, top_k: int = 10) -> list[str]:
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
        {"query_embedding": query_embedding, "match_count": top_k, "match_threshold": 0.72},
    ).execute()
    rows = response.data or []
    return [row.get("content", "") for row in rows if row.get("content")]


def retrieve_context_as_messages(query: str, top_k: int = 10) -> list[dict]:
    """
    Return RAG context as a cache-controlled user message.
    Embeds the query, retrieves top-k chunks, wraps as <context> block.
    Marked ephemeral for prompt caching.
    """
    chunks = retrieve_context(query, top_k)
    context_text = "\n\n---\n\n".join(chunks)
    return [{
        "role": "user",
        "content": f"<context>\n{context_text}\n</context>",
        "cache_control": {"type": "ephemeral"},
    }]


def retrieve(query: str, top_k: int = 10) -> list[dict]:
    """
    Retrieve top-k chunks and return structured format with metadata.
    
    Returns list of dicts with keys:
        content (str): The chunk text
        source (str): Source document/path
        score (float): Similarity score from vector search
        retrieved_at (str): ISO timestamp of retrieval
    
    Args:
        query: Natural language query to embed and search
        top_k: Number of top results to return (default 10)
    
    Returns:
        List of dicts: [{content, source, score, retrieved_at}, ...]
    """
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
        {"query_embedding": query_embedding, "match_count": top_k, "match_threshold": 0.72},
    ).execute()
    rows = response.data or []
    
    now = datetime.now(timezone.utc).isoformat()
    results = []
    for row in rows:
        if not row.get("content"):
            continue
        results.append({
            "content": row.get("content", ""),
            "source": row.get("source", row.get("file_path", "unknown")),
            "score": row.get("similarity", row.get("score", 0.0)),
            "retrieved_at": now,
        })
    
    return results