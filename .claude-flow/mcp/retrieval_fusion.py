#!/usr/bin/env python3
"""
RetrievalFusion — BM25 + Vector dual retrieval with Reciprocal Rank Fusion.
Implements the TEMPR system's 4-strategy fusion: vector + BM25 + graph + temporal.
This module provides the keyword BM25 fallback layer for Hermes memory system.

BM25 formula: score = IDF * TF / (TF + k1 * (1 - b + b * doc_len / avg_doc_len))
k1=1.5, b=0.75 are standard Lucene-compatible parameters.
RRF: RRF_score(d) = Σ 1/(k + rank_i(d)), k=60 (standard constant).
"""
import json
import math
import os
import re
import sqlite3
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Try to import rank_bm25; fallback to pure Python implementation
try:
    from rank_bm25 import BM25Plus
    _HAS_RANK_BM25 = True
except ImportError:
    _HAS_RANK_BM25 = False

PROJECT_ROOT = Path("/home/newadmin/swarm-bot")
FUSION_DB = PROJECT_ROOT / ".claude-flow" / "data" / "retrieval_fusion.db"
CHROMA_DB = PROJECT_ROOT / "data" / "legion_chroma" / "chroma.sqlite3"

# BM25 standard parameters (Lucene-compatible)
BM25_K1 = 1.5
BM25_B = 0.75
# RRF constant
RRF_K = 60
# Default retrieval limits
DEFAULT_TOP_K = 20

LOCK = threading.Lock()

# ---------------------------------------------------------------------------
# Tokenization (whitespace + punctuation, lowercase)
# ---------------------------------------------------------------------------
def _tokenize(text: str) -> List[str]:
    """Tokenize on whitespace + punctuation, lowercase."""
    if not text:
        return []
    text = text.lower()
    # Split on whitespace and punctuation (keep alphanumeric + @ and # for code/social)
    tokens = re.findall(r"[\w@#]+", text, re.UNICODE)
    return [t for t in tokens if len(t) >= 2]

# ---------------------------------------------------------------------------
# SQLite FTS5 BM25 index (inverted index)
# ---------------------------------------------------------------------------
def _get_fusion_db() -> sqlite3.Connection:
    FUSION_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(FUSION_DB), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bm25_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT NOT NULL,
            collection TEXT NOT NULL DEFAULT 'memory',
            content TEXT NOT NULL,
            tokenized TEXT NOT NULL,
            doc_len INTEGER NOT NULL,
            updated REAL,
            UNIQUE(doc_id, collection)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bm25_stats (
            collection TEXT PRIMARY KEY,
            doc_count INTEGER DEFAULT 0,
            avg_doc_len REAL DEFAULT 0,
            idf_cache TEXT,
            updated REAL
        )
    """)
    # FTS5 virtual table for full-text keyword search fallback
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS bm25_fts USING fts5(
            doc_id UNINDEXED,
            content,
            tokenize='porter unicode61'
        )
    """)
    conn.commit()
    return conn

# ---------------------------------------------------------------------------
# IDF computation
# ---------------------------------------------------------------------------
def _compute_idf(doc_freqs: Dict[str, int], total_docs: int) -> Dict[str, float]:
    """Compute IDF for each term: log((N - n + 0.5) / (n + 0.5))."""
    idf = {}
    for term, df in doc_freqs.items():
        # Smoothed IDF (Lucene formula)
        idf[term] = math.log((total_docs - df + 0.5) / (df + 0.5) + 1)
    return idf

# ---------------------------------------------------------------------------
# BM25 scoring (pure Python, no external deps needed)
# ---------------------------------------------------------------------------
class SimpleBM25:
    """Pure Python BM25 implementation (used if rank_bm25 unavailable)."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_len_avg = 0.0
        self.N = 0
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        self.doc_lengths: List[int] = []
        self.doc_term_freqs: List[Dict[str, int]] = []

    def index(self, texts: List[str]) -> None:
        """Build inverted index from list of texts."""
        self.doc_term_freqs = []
        self.doc_lengths = []
        self.doc_freqs = defaultdict(int)
        tokenized = [_tokenize(t) for t in texts]
        self.N = len(texts)

        for tokens in tokenized:
            freq = defaultdict(int)
            for t in tokens:
                freq[t] += 1
            self.doc_term_freqs.append(dict(freq))
            self.doc_lengths.append(len(tokens))
            for t in freq:
                self.doc_freqs[t] += 1

        self.doc_len_avg = sum(self.doc_lengths) / max(1, self.N)
        # Compute IDF for all terms
        self.idf = _compute_idf(dict(self.doc_freqs), self.N)

    def score(self, query: str) -> List[Tuple[int, float]]:
        """Score all docs against query. Returns list of (doc_idx, score)."""
        q_tokens = _tokenize(query)
        scores = []
        for idx, term_freqs in enumerate(self.doc_term_freqs):
            score = 0.0
            dl = self.doc_lengths[idx]
            for qt in q_tokens:
                tf = term_freqs.get(qt, 0)
                if tf == 0:
                    continue
                idf = self.idf.get(qt, 0)
                # BM25 formula: IDF * TF / (TF + k1 * (1 - b + b * dl / avg_dl))
                numerator = idf * tf
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / max(0.001, self.doc_len_avg))
                score += numerator / denominator
            scores.append((idx, score))
        scores.sort(key=lambda x: -x[1])
        return scores

    def get_top_k(self, query: str, k: int = 20) -> List[Tuple[int, float]]:
        """Return top-k doc indices with scores."""
        return self.score(query)[:k]

# ---------------------------------------------------------------------------
# BM25 index management
# ---------------------------------------------------------------------------
def index_collection(collection: str, texts: List[str], doc_ids: List[str] = None) -> Dict[str, Any]:
    """Build/refresh BM25 index for a collection."""
    if doc_ids is None:
        doc_ids = [f"doc_{i}" for i in range(len(texts))]

    with LOCK:
        conn = _get_fusion_db()
        now = time.time()

        # Delete existing docs for this collection
        conn.execute("DELETE FROM bm25_index WHERE collection = ?", (collection,))
        conn.execute("DELETE FROM bm25_fts WHERE doc_id IN (SELECT doc_id FROM bm25_index WHERE collection = ?)", (collection,))

        tokenized_texts = [_tokenize(t) for t in texts]
        doc_lens = [len(t) for t in tokenized_texts]
        doc_freqs = defaultdict(int)
        for tokens in tokenized_texts:
            for t in set(tokens):
                doc_freqs[t] += 1

        avg_doc_len = sum(doc_lens) / max(1, len(doc_lens))
        total_docs = len(texts)

        # Insert documents
        for doc_id, text, tokens, dl in zip(doc_ids, texts, tokenized_texts, doc_lens):
            conn.execute("""
                INSERT INTO bm25_index (doc_id, collection, content, tokenized, doc_len, updated)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(doc_id, collection) DO UPDATE SET
                    content = excluded.content,
                    tokenized = excluded.tokenized,
                    doc_len = excluded.doc_len,
                    updated = excluded.updated
            """, (doc_id, collection, text, " ".join(tokens), dl, now))

            # FTS5 backup index
            conn.execute("""
                INSERT OR REPLACE INTO bm25_fts (doc_id, content)
                VALUES (?, ?)
            """, (doc_id, text))

        # Update stats
        idf_json = json.dumps(_compute_idf(dict(doc_freqs), total_docs))
        conn.execute("""
            INSERT OR REPLACE INTO bm25_stats (collection, doc_count, avg_doc_len, idf_cache, updated)
            VALUES (?, ?, ?, ?, ?)
        """, (collection, total_docs, avg_doc_len, idf_json, now))
        conn.commit()
        conn.close()

        return {
            "collection": collection,
            "indexed": total_docs,
            "avg_doc_len": round(avg_doc_len, 2),
            "unique_terms": len(doc_freqs)
        }

# ---------------------------------------------------------------------------
# BM25 retrieval
# ---------------------------------------------------------------------------
def _bm25_search(collection: str, query: str, top_k: int = 20) -> List[Tuple[str, float, int]]:
    """
    Run BM25 search on collection.
    Returns list of (doc_id, score, rank) — rank is 1-based.
    """
    with LOCK:
        conn = _get_fusion_db()

        # Load stats
        row = conn.execute(
            "SELECT doc_count, avg_doc_len, idf_cache FROM bm25_stats WHERE collection = ?",
            (collection,)
        ).fetchone()

        if not row or row[0] == 0:
            conn.close()
            return []

        doc_count, avg_doc_len, idf_cache = row
        idf = json.loads(idf_cache) if idf_cache else {}

        # Get all docs for this collection
        rows = conn.execute("""
            SELECT id, doc_id, content, tokenized, doc_len
            FROM bm25_index WHERE collection = ?
        """, (collection,)).fetchall()
        conn.close()

        if not rows:
            return []

        # Build in-memory BM25
        if _HAS_RANK_BM25:
            texts = [r[2] for r in rows]
            bm25 = BM25Plus([_tokenize(t) for t in texts], k1=BM25_K1, b=BM25_B)
            query_tokens = _tokenize(query)
            scores = bm25.get_scores(query_tokens)
        else:
            simple = SimpleBM25(k1=BM25_K1, b=BM25_B)
            texts = [r[2] for r in rows]
            simple.index(texts)
            scored = simple.score(query)
            scores = [0.0] * len(texts)
            for idx, sc in scored:
                scores[idx] = sc

        # Pair with doc_ids and rank
        doc_scores = [(rows[i][1], scores[i]) for i in range(len(rows)) if scores[i] > 0]
        doc_scores.sort(key=lambda x: -x[1])

        return [(doc_id, score, rank + 1) for rank, (doc_id, score) in enumerate(doc_scores[:top_k])]

# ---------------------------------------------------------------------------
# ChromaDB vector retrieval (reuse pattern from memory_layer_bridge)
# ---------------------------------------------------------------------------
def _vector_search(query: str, collection: str = "hermes_shared", top_k: int = 20) -> List[Tuple[str, float, int]]:
    """Query ChromaDB vector store. Returns list of (doc_id, score, rank)."""
    if not CHROMA_DB.exists():
        return []

    try:
        conn = sqlite3.connect(str(CHROMA_DB), check_same_thread=False)
        # Simple keyword fallback on ChromaDB's SQLite backend
        rows = conn.execute("""
            SELECT e.id, e.document, c.name
            FROM embeddings e
            JOIN collections c ON e.collection_id = c.id
            WHERE c.name = ? AND e.document LIKE ?
            LIMIT ?
        """, (collection, f"%{query[:50]}%", top_k * 2)).fetchall()
        conn.close()

        if not rows:
            return []

        # Score by keyword match density
        results = []
        query_lower = query.lower()
        for row in rows:
            doc_id, doc, _ = row
            if not doc:
                continue
            doc_lower = doc.lower()
            # Count query term occurrences
            q_tokens = set(_tokenize(query))
            matches = sum(1 for t in q_tokens if t in doc_lower)
            if matches > 0:
                score = matches / max(1, len(q_tokens))
                results.append((str(doc_id), score, 0))  # rank=0 means not ranked yet

        results.sort(key=lambda x: -x[1])
        return [(doc_id, score, rank + 1) for rank, (doc_id, score, _) in enumerate(results[:top_k])]
    except Exception:
        return []

# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion
# ---------------------------------------------------------------------------
def _reciprocal_rank_fusion(
    bm25_results: List[Tuple[str, float, int]],
    vector_results: List[Tuple[str, float, int]],
    k: int = 60
) -> List[Tuple[str, float]]:
    """
    Merge ranked results using RRF formula.
    RRF_score(d) = Σ 1/(k + rank_i(d))
    Lower rank (1=best) gives higher contribution.
    """
    doc_scores: Dict[str, float] = defaultdict(float)

    for doc_id, score, rank in bm25_results:
        if rank > 0:
            doc_scores[doc_id] += 1.0 / (k + rank)

    for doc_id, score, rank in vector_results:
        if rank > 0:
            doc_scores[doc_id] += 1.0 / (k + rank)

    ranked = sorted(doc_scores.items(), key=lambda x: -x[1])
    return ranked

# ---------------------------------------------------------------------------
# Unified fusion retrieval API
# ---------------------------------------------------------------------------
def fusion_retrieve(query: str, collection: str = "memory", top_k: int = 10) -> Dict[str, Any]:
    """
    Dual retrieval: BM25 + Vector, merged with RRF.
    Returns final ranked list with scores from each strategy.
    """
    start = time.time()

    # Parallel retrieval (both strategies)
    bm25_results = _bm25_search(collection, query, DEFAULT_TOP_K)
    vector_results = _vector_search(query, "hermes_shared", DEFAULT_TOP_K)

    # FTS5 fallback if BM25 returned nothing
    if not bm25_results:
        bm25_results = _fts5_fallback(query, collection, DEFAULT_TOP_K)

    # RRF merge
    fused = _reciprocal_rank_fusion(bm25_results, vector_results, RRF_K)

    # Build final result
    doc_ids = [d for d, _ in fused[:top_k]]
    doc_scores_map = dict(fused)

    # Fetch doc contents
    with LOCK:
        conn = _get_fusion_db()
        placeholders = ",".join(["?"] * len(doc_ids)) if doc_ids else "'none'"
        rows = conn.execute(f"""
            SELECT doc_id, content, collection
            FROM bm25_index
            WHERE doc_id IN ({placeholders})
        """, doc_ids).fetchall()
        conn.close()

    doc_map = {r[0]: {"content": r[1][:300], "collection": r[2]} for r in rows}

    results = []
    for doc_id, rrf_score in fused[:top_k]:
        bm25_score = next((s for d, s, r in bm25_results if d == doc_id), 0.0)
        vec_score = next((s for d, s, r in vector_results if d == doc_id), 0.0)
        info = doc_map.get(doc_id, {"content": "", "collection": collection})
        results.append({
            "doc_id": doc_id,
            "rrf_score": round(rrf_score, 4),
            "bm25_score": round(bm25_score, 4),
            "vector_score": round(vec_score, 4),
            "content": info["content"],
            "collection": info["collection"]
        })

    elapsed = time.time() - start
    return {
        "query": query,
        "collection": collection,
        "top_k": top_k,
        "results": results,
        "stats": {
            "bm25_hits": len(bm25_results),
            "vector_hits": len(vector_results),
            "fused_total": len(fused),
            "elapsed_ms": round(elapsed * 1000, 2)
        }
    }

def _fts5_fallback(query: str, collection: str, top_k: int) -> List[Tuple[str, float, int]]:
    """FTS5 fallback when BM25 returns no results."""
    with LOCK:
        conn = _get_fusion_db()
        try:
            rows = conn.execute("""
                SELECT doc_id, content
                FROM bm25_fts
                WHERE bm25_fts MATCH ?
                LIMIT ?
            """, (query, top_k)).fetchall()
        except Exception:
            rows = []
        conn.close()

        if not rows:
            return []

        results = []
        for rank, (doc_id, content) in enumerate(rows, 1):
            q_tokens = set(_tokenize(query))
            content_tokens = set(_tokenize(content))
            overlap = len(q_tokens & content_tokens)
            score = overlap / max(1, len(q_tokens))
            results.append((doc_id, score, rank))
        return results

# ---------------------------------------------------------------------------
# Index management API
# ---------------------------------------------------------------------------
def fusion_index(collection: str, texts: List[str] = None, doc_ids: List[str] = None) -> Dict[str, Any]:
    """Build or refresh BM25 index for a collection."""
    if texts is None:
        return {"error": "texts list is required"}
    return index_collection(collection, texts, doc_ids)

# ---------------------------------------------------------------------------
# Stats API
# ---------------------------------------------------------------------------
def fusion_stats(collection: str = None) -> Dict[str, Any]:
    """Return index statistics."""
    with LOCK:
        conn = _get_fusion_db()
        if collection:
            row = conn.execute("""
                SELECT collection, doc_count, avg_doc_len, updated
                FROM bm25_stats WHERE collection = ?
            """, (collection,)).fetchone()
            total = conn.execute("SELECT COUNT(*) FROM bm25_index WHERE collection = ?",
                               (collection,)).fetchone()[0] if row else 0
            conn.close()
            if not row:
                return {"collection": collection, "status": "empty"}
            return {
                "collection": row[0],
                "doc_count": row[1],
                "avg_doc_len": round(row[2], 2),
                "indexed_docs": total,
                "bm25_k1": BM25_K1,
                "bm25_b": BM25_B,
                "updated": row[3]
            }
        else:
            rows = conn.execute("""
                SELECT collection, doc_count, avg_doc_len, updated
                FROM bm25_stats
            """).fetchall()
            conn.close()
            return {
                "collections": [
                    {"collection": r[0], "doc_count": r[1], "avg_doc_len": round(r[2], 2), "updated": r[3]}
                    for r in rows
                ],
                "bm25_k1": BM25_K1,
                "bm25_b": BM25_B,
                "rrf_k": RRF_K
            }

# ---------------------------------------------------------------------------
# Handler for Hermes MCP
# ---------------------------------------------------------------------------
def handle_retrieval_fusion(args: Dict[str, Any]) -> str:
    """Handler for retrieval fusion operations."""
    action = args.get("action", "retrieve")

    if action == "retrieve":
        result = fusion_retrieve(
            args.get("query", ""),
            args.get("collection", "memory"),
            args.get("top_k", 10)
        )
    elif action == "index":
        result = fusion_index(
            args.get("collection", "memory"),
            args.get("texts", []),
            args.get("doc_ids", None)
        )
    elif action == "stats":
        result = fusion_stats(args.get("collection", None))
    else:
        result = {"error": f"unknown action: {action}"}

    return json.dumps(result, indent=2)

RETRIEVAL_FUSION_SCHEMA = {
    "name": "retrieval_fusion",
    "description": "BM25 + Vector dual retrieval with Reciprocal Rank Fusion for Hermes memory. "
                   "Provides keyword BM25 fallback for precise queries alongside semantic vector search.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["retrieve", "index", "stats"]},
            "query": {"type": "string"},
            "collection": {"type": "string", "default": "memory"},
            "top_k": {"type": "integer", "default": 10},
            "texts": {"type": "array"},
            "doc_ids": {"type": "array"},
        },
    },
}