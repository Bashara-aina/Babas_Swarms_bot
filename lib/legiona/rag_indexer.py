"""Codebase chunking and embedding indexer for Legiona RAG."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx

EMBED_MODEL = "embo-01"  # [VERIFY BEFORE USE: confirm MiniMax embedding model name]
EMBED_DIM = 1536  # [VERIFY BEFORE USE: confirm MiniMax embo-01 output dimension]
EMBED_URL = "https://api.opencode.ai/zen/go/v1/embeddings"
CHUNK_TOKENS = 2000  # expanded for M3 large context window
CHUNK_OVERLAP = 200  # 10% overlap ensures continuity
SUPPORTED_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".sql", ".md"}


def _approx_tokens(text: str) -> list[str]:
    return text.split()


def _chunk_words(words: list[str], chunk_size: int = CHUNK_TOKENS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(0, end - overlap)
    return chunks


def get_embedding(text: str) -> list[float]:
    """Get embedding vector from MiniMax embo-01 endpoint."""
    api_key = os.getenv("OPENCODE_GO_API_KEY", "")
    if not api_key:
        raise ValueError("OPENCODE_GO_API_KEY not set")
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": EMBED_MODEL, "input": [text]}
    with httpx.Client(timeout=60.0) as client:
        response = client.post(EMBED_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]


def _embed_texts(texts: list[str]) -> list[list[float]]:
    api_key = os.getenv("OPENCODE_GO_API_KEY", "")
    if not api_key:
        raise ValueError("OPENCODE_GO_API_KEY not set")
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": EMBED_MODEL, "input": texts}
    with httpx.Client(timeout=60.0) as client:
        response = client.post(EMBED_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]


def chunk_and_embed(file_path: str) -> list[dict[str, Any]]:
    """Read, chunk (~500 tokens with 50 overlap), and embed one file."""
    path = Path(file_path)
    content = path.read_text(encoding="utf-8", errors="ignore")
    chunks = _chunk_words(_approx_tokens(content))
    if not chunks:
        return []
    embeddings = _embed_texts(chunks)
    records: list[dict[str, Any]] = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
        records.append(
            {
                "file_path": str(path),
                "chunk_index": idx,
                "content": chunk,
                "embedding": embedding,
                "metadata": {"source": "codebase", "model": EMBED_MODEL},
            }
        )
    return records


def index_codebase(root_dir: str, supabase_client: Any) -> int:
    """Walk repo, chunk/embed supported files, and upsert into legiona_embeddings."""
    root = Path(root_dir)
    total = 0
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in SUPPORTED_SUFFIXES:
            continue
        if any(part.startswith(".") for part in path.parts):
            continue
        if "node_modules" in path.parts or "__pycache__" in path.parts:
            continue
        rows = chunk_and_embed(str(path))
        if not rows:
            continue
        supabase_client.table("legiona_embeddings").upsert(rows).execute()
        total += len(rows)
    return total
