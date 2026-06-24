#!/usr/bin/env python3
"""
ChromaDB daemon — persistent subprocess for low-latency vector recall.
Reads JSON queries from stdin, writes JSON results to stdout.

Input:  {"id":"1","query":"text","top_k":5,"min_score":0.25}
Output: {"id":"1","results":[...],"error":null}

Keeps ChromaDB + embedder loaded between queries (~2.2s saved per call).
"""
import json
import sys
import os

# Import once at startup (the expensive part)
# Redirect stdout to stderr during import — the embedder prints log messages
# that would flood the JSON protocol stream
_old_stdout = sys.stdout
sys.stdout = sys.stderr
sys.path.insert(0, os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd()))
from core.memory.store import MemoryStore  # noqa: E402
store = MemoryStore()
sys.stdout = _old_stdout

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        req = json.loads(line)
        results = store.recall(
            query=req.get("query", ""),
            top_k=req.get("top_k", 5),
            min_score=req.get("min_score", 0.25),
        )
        out = []
        for r in results:
            if isinstance(r, dict):
                raw_score = r.get("score", r.get("relevance", 0))
                out.append({
                    "content": r.get("content", r.get("text", "")),
                    "score": min(0.35, raw_score * 0.35),
                    "source": "chroma",
                })
            elif isinstance(r, str):
                out.append({"content": r, "score": 0.35, "source": "chroma"})
        response = {"id": req.get("id", "?"), "results": out, "error": None}
    except Exception as e:
        response = {"id": req.get("id", "?"), "results": [], "error": str(e)[:200]}
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()
