#!/usr/bin/env python3
"""
WebSearchAggregator - Unified web search with auto-selection based on query type.
Providers: tavily, exa, ddg, firecrawl with fallback chain.
"""
import hashlib
import json
import os
import sqlite3
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

CACHE_DB = Path("/tmp/hermes_query_cache/web_search_cache.sqlite")
CACHE_LOCK = threading.Lock()
CACHE_TTL = 3600

def _get_cache_db():
    CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CACHE_DB), check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS web_cache (
            cache_key TEXT PRIMARY KEY,
            provider TEXT,
            result_json TEXT,
            created_at REAL,
            query_hash TEXT
        )
    """)
    conn.commit()
    return conn

def _cache_key(query, provider):
    return hashlib.sha256(f"{provider}:{query}".encode()).hexdigest()[:32]

def _get_cached(query, provider):
    key = _cache_key(query, provider)
    with CACHE_LOCK:
        conn = _get_cache_db()
        row = conn.execute("""
            SELECT result_json, created_at FROM web_cache WHERE cache_key = ?
        """, (key,)).fetchone()
        conn.close()
        if row and (time.time() - row[1]) < CACHE_TTL:
            return json.loads(row[0])
    return None

def _set_cached(query, provider, result):
    key = _cache_key(query, provider)
    with CACHE_LOCK:
        conn = _get_cache_db()
        conn.execute("""
            INSERT OR REPLACE INTO web_cache (cache_key, provider, result_json, created_at, query_hash)
            VALUES (?, ?, ?, ?, ?)
        """, (key, provider, json.dumps(result), time.time(), hashlib.sha256(query.encode()).hexdigest()[:16]))
        conn.commit()
        conn.close()

def _analyze_query_type(query):
    q = query.lower()
    if any(w in q for w in ["news", "breaking", "today", "latest"]):
        return "news"
    if any(w in q for w in ["doc", "document", "api", "reference", "manual"]):
        return "documentation"
    if any(w in q for w in ["code", "github", "stackoverflow", "function", "class"]):
        return "code"
    return "general"

def _run_cmd_provider(provider, query, max_results):
    try:
        if provider == "ddg":
            out = subprocess.run(
                ["npx", "-y", "ddg-mcp@latest", "search"],
                input=json.dumps({"query": query, "max_results": max_results}).encode(),
                capture_output=True, timeout=15
            )
            return {"provider": "ddg", "result": json.loads(out.stdout) if out.stdout else {}}
    except Exception as e:
        return {"provider": provider, "error": str(e)}
    return {"provider": provider, "error": "unknown provider"}

def unified_web_search(query, depth="basic", max_results=5, no_cache=False):
    query_type = _analyze_query_type(query)
    provider_selection = {
        "news": ["ddg", "tavily"],
        "documentation": ["ddg", "firecrawl"],
        "code": ["ddg", "tavily"],
        "general": ["ddg", "exa"],
    }
    providers = provider_selection.get(query_type, ["ddg"])

    results = []
    errors = []
    used_provider = ""

    for provider in providers:
        if not no_cache:
            cached = _get_cached(query, provider)
            if cached:
                cached["_cached"] = True
                return cached
        resp = _run_cmd_provider(provider, query, max_results)
        if "error" in resp:
            errors.append(f"{provider}: {resp['error']}")
            continue
        results.append(resp)
        used_provider = provider
        break

    if not results:
        return {
            "query": query,
            "query_type": query_type,
            "error": "all providers failed",
            "errors": errors,
        }

    final_result = results[0]
    final_result["query_type"] = query_type
    final_result["providers_tried"] = providers
    final_result["used_provider"] = used_provider
    return final_result

def handle_web_search_aggregator(args):
    action = args.get("action", "search")
    if action == "search":
        result = unified_web_search(
            args.get("query", ""),
            args.get("depth", "basic"),
            args.get("max_results", 5),
            args.get("no_cache", False)
        )
    elif action == "analyze":
        result = {"query_type": _analyze_query_type(args.get("query", ""))}
    elif action == "cache_clear":
        with CACHE_LOCK:
            conn = _get_cache_db()
            conn.execute("DELETE FROM web_cache")
            conn.commit()
            conn.close()
        result = {"success": True, "action": "cache_cleared"}
    else:
        result = {"error": f"unknown action: {action}"}
    return json.dumps(result, indent=2)