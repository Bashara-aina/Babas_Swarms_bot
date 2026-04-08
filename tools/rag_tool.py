"""Query ChromaDB HTTP (docker-compose chromadb:8000) or optional RAGFlow retrieval API."""

from __future__ import annotations

import asyncio
import logging
import os

import httpx

logger = logging.getLogger(__name__)


async def _ragflow_query_async(collection_name: str, query: str, n: int) -> str:
    base = (os.getenv("RAGFLOW_API_BASE") or "").strip().rstrip("/")
    dataset = (os.getenv("RAGFLOW_DATASET_ID") or collection_name or "").strip()
    if not base or not dataset:
        return ""
    path = (os.getenv("RAGFLOW_RETRIEVAL_PATH") or "/api/v1/retrieval").strip()
    if not path.startswith("/"):
        path = "/" + path
    key = (os.getenv("RAGFLOW_API_KEY") or "").strip()
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    payload = {
        "question": query,
        "dataset_ids": [dataset],
        "page_size": max(1, min(n, 32)),
    }
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            r = await client.post(f"{base}{path}", json=payload, headers=headers)
            if r.status_code >= 400:
                logger.debug("ragflow HTTP %s: %s", r.status_code, r.text[:200])
                return ""
            data = r.json()
    except Exception as exc:
        logger.debug("ragflow query failed: %s", exc)
        return ""

    chunks: list[str] = []
    if isinstance(data, dict):
        ref = data.get("data") or data.get("chunks") or data.get("reference") or []
        if isinstance(ref, dict):
            ref = ref.get("chunks") or ref.get("doc_aggs") or []
        for item in ref[:n] if isinstance(ref, list) else []:
            if isinstance(item, str):
                chunks.append(item[:900])
            elif isinstance(item, dict):
                t = item.get("content") or item.get("text") or item.get("chunk") or ""
                chunks.append(str(t)[:900])
    if not chunks:
        return ""
    return "## RAG (RAGFlow)\n" + "\n".join(chunks)


def _query_sync(collection_name: str, query: str, n: int) -> str:
    import chromadb  # type: ignore

    host = os.getenv("CHROMADB_HOST", "127.0.0.1")
    port = int(os.getenv("CHROMADB_PORT", "8000"))
    client = chromadb.HttpClient(host=host, port=port)
    try:
        col = client.get_collection(collection_name)
    except Exception:
        return ""
    res = col.query(query_texts=[query], n_results=n)
    docs = (res.get("documents") or [[]])[0]
    dist = (res.get("distances") or [[]])[0]
    if not docs:
        return ""
    lines = [f"## RAG ({collection_name})"]
    for i, doc in enumerate(docs):
        d = str(dist[i]) if i < len(dist) else "?"
        lines.append(f"[{d}] {str(doc)[:900]}")
    return "\n".join(lines)


async def rag_query(collection_name: str, query: str, n_results: int = 5) -> str:
    if os.getenv("LEGION_RAG_ENABLED", "0").strip().lower() not in ("1", "true", "yes", "on"):
        return ""
    name = collection_name or os.getenv("LEGION_RAG_COLLECTION", "legion_rag")
    backend = (os.getenv("LEGION_RAG_BACKEND") or "chroma").strip().lower()
    try:
        if backend == "ragflow":
            return await _ragflow_query_async(name, query, n_results)
        return await asyncio.to_thread(_query_sync, name, query, n_results)
    except Exception as exc:
        logger.debug("rag_query failed: %s", exc)
        return ""
