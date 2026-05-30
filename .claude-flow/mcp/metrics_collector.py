#!/usr/bin/env python3
"""
MetricsCollector — Hermes MCP server metrics tracking.
Tracks: tool_name, call_count, total_latency_ms, error_count, last_called.
Percentiles: p50, p95, p99 per tool.
Persists to /tmp/hermes_metrics.db SQLite.
"""
import json
import os
import sqlite3
import statistics
import threading
import time
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional

METRICS_DB = Path("/tmp/hermes_metrics.db")
METRICS_DIR = METRICS_DB.parent
LOCK = threading.Lock()

def _get_db() -> sqlite3.Connection:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(METRICS_DB), check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tool_metrics (
            tool_name TEXT PRIMARY KEY,
            call_count INTEGER DEFAULT 0,
            total_latency_ms REAL DEFAULT 0.0,
            error_count INTEGER DEFAULT 0,
            last_called REAL,
            latency_samples TEXT DEFAULT '[]'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_name TEXT,
            latency_ms REAL,
            success INTEGER,
            ts REAL
        )
    """)
    conn.commit()
    return conn

def track_metrics(tool_name: str):
    """Decorator to track metrics for any _run_cmd call."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            error = False
            result = None
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                error = True
                raise
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                _record_metric(tool_name, elapsed_ms, error)
        return wrapper
    return decorator

def _record_metric(tool_name: str, latency_ms: float, is_error: bool):
    with LOCK:
        conn = _get_db()
        now = time.time()
        # Update tool_metrics table
        conn.execute("""
            INSERT INTO tool_metrics (tool_name, call_count, total_latency_ms, error_count, last_called, latency_samples)
            VALUES (?, 1, ?, ?, ?, '[]')
            ON CONFLICT(tool_name) DO UPDATE SET
                call_count = call_count + 1,
                total_latency_ms = total_latency_ms + ?,
                error_count = error_count + ?,
                last_called = ?
        """, (tool_name, latency_ms, 1 if is_error else 0, now,
              latency_ms, 1 if is_error else 0, now))
        # Log individual call
        conn.execute("""
            INSERT INTO metrics_log (tool_name, latency_ms, success, ts)
            VALUES (?, ?, ?, ?)
        """, (tool_name, latency_ms, 0 if is_error else 1, now))
        conn.commit()
        conn.close()

def get_tool_metrics(tool_name: str) -> dict[str, Any]:
    """Return metrics for a specific tool."""
    conn = _get_db()
    row = conn.execute("SELECT * FROM tool_metrics WHERE tool_name = ?", (tool_name,)).fetchone()
    conn.close()
    if not row:
        return {"tool_name": tool_name, "error": "not found"}
    cols = ["tool_name", "call_count", "total_latency_ms", "error_count", "last_called", "latency_samples"]
    data = dict(zip(cols, row))
    avg_latency = data["total_latency_ms"] / data["call_count"] if data["call_count"] > 0 else 0
    error_rate = data["error_count"] / data["call_count"] if data["call_count"] > 0 else 0
    # Compute percentiles from log
    conn = _get_db()
    samples = conn.execute("""
        SELECT latency_ms FROM metrics_log
        WHERE tool_name = ? AND success = 1
        ORDER BY latency_ms
    """, (tool_name,)).fetchall()
    conn.close()
    latencies = [s[0] for s in samples]
    p50 = statistics.median(latencies) if latencies else 0
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else (max(latencies) if latencies else 0)
    p99 = statistics.quantiles(latencies, n=100)[97] if len(latencies) >= 100 else (max(latencies) if latencies else 0)
    return {
        "tool_name": tool_name,
        "call_count": data["call_count"],
        "total_latency_ms": round(data["total_latency_ms"], 2),
        "avg_latency_ms": round(avg_latency, 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "error_count": data["error_count"],
        "error_rate": round(error_rate * 100, 2),
        "last_called": data["last_called"],
    }

def get_top_tools(limit: int = 10, by: str = "call_count") -> list[dict[str, Any]]:
    """List most-used tools."""
    conn = _get_db()
    order_col = "call_count" if by == "call_count" else "total_latency_ms"
    rows = conn.execute(f"""
        SELECT tool_name, call_count, total_latency_ms, error_count
        FROM tool_metrics ORDER BY {order_col} DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [
        {"tool_name": r[0], "call_count": r[1], "total_latency_ms": round(r[2], 2), "error_count": r[3]}
        for r in rows
    ]

def get_slowest_tools(limit: int = 10) -> list[dict[str, Any]]:
    """Tools with highest p95 latency."""
    conn = _get_db()
    rows = conn.execute("""
        SELECT tool_name, call_count, total_latency_ms / call_count as avg_ms
        FROM tool_metrics WHERE call_count >= 5
        ORDER BY avg_ms DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [
        {"tool_name": r[0], "call_count": r[1], "p95_ms": round(r[2], 2)}
        for r in rows
    ]

def get_error_prone_tools(limit: int = 10) -> list[dict[str, Any]]:
    """Tools with highest error rate."""
    conn = _get_db()
    rows = conn.execute("""
        SELECT tool_name, call_count, error_count,
               CAST(error_count AS REAL) * 100 / call_count as error_rate
        FROM tool_metrics WHERE call_count >= 3
        ORDER BY error_rate DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [
        {"tool_name": r[0], "call_count": r[1], "error_count": r[2], "error_rate": round(r[3], 2)}
        for r in rows
    ]

def metrics_export_csv(path: str) -> dict[str, Any]:
    """Export all metrics to CSV file."""
    import csv
    conn = _get_db()
    rows = conn.execute("SELECT * FROM tool_metrics ORDER BY call_count DESC").fetchall()
    conn.close()
    cols = ["tool_name", "call_count", "total_latency_ms", "error_count", "last_called", "latency_samples"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols[:5])
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row[i] for i, c in enumerate(cols[:5])})
    return {"success": True, "path": path, "rows_exported": len(rows)}

def cache_clear(tool_name: str | None = None) -> dict[str, Any]:
    """Clear metrics for a tool or all tools."""
    with LOCK:
        conn = _get_db()
        if tool_name:
            conn.execute("DELETE FROM tool_metrics WHERE tool_name = ?", (tool_name,))
            conn.execute("DELETE FROM metrics_log WHERE tool_name = ?", (tool_name,))
        else:
            conn.execute("DELETE FROM tool_metrics")
            conn.execute("DELETE FROM metrics_log")
        conn.commit()
        conn.close()
    return {"success": True, "tool_name": tool_name}

# ── MCP Tool Schema ─────────────────────────────────────────────────────────

def handle_metrics(args: dict[str, Any]) -> str:
    """Handle all metrics tools."""
    action = args.get("action", "status")
    if action == "get_tool":
        result = get_tool_metrics(args.get("tool_name", ""))
    elif action == "top":
        result = get_top_tools(args.get("limit", 10), args.get("by", "call_count"))
    elif action == "slowest":
        result = get_slowest_tools(args.get("limit", 10))
    elif action == "error_prone":
        result = get_error_prone_tools(args.get("limit", 10))
    elif action == "export_csv":
        result = metrics_export_csv(args.get("path", "/tmp/hermes_metrics_export.csv"))
    elif action == "clear":
        result = cache_clear(args.get("tool_name"))
    else:
        conn = _get_db()
        total_calls = conn.execute("SELECT SUM(call_count) FROM tool_metrics").fetchone()[0] or 0
        total_errors = conn.execute("SELECT SUM(error_count) FROM tool_metrics").fetchone()[0] or 0
        conn.close()
        result = {"total_calls": total_calls, "total_errors": total_errors, "status": "ok"}
    return json.dumps(result, indent=2)

METRICS_SCHEMA = {
    "name": "metrics_collector",
    "description": "Track Hermes MCP tool usage frequency, latency percentiles, error rates.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["status", "get_tool", "top", "slowest", "error_prone", "export_csv", "clear"],
            },
            "tool_name": {"type": "string"},
            "limit": {"type": "integer", "default": 10},
            "by": {"type": "string", "enum": ["call_count", "total_latency_ms"]},
            "path": {"type": "string"},
        },
    },
}
