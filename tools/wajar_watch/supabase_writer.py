"""WAJAR_WATCH — supabase_writer: CRUD helpers with JSON fallback."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tools.wajar_watch.confidence_scorer import ConfidenceResult

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    """Lazy-init Supabase client from CEKWAJAR env vars."""
    global _client
    if _client is not None:
        return _client
    try:
        from supabase import create_client

        url = os.environ["CEKWAJAR_SUPABASE_URL"]
        key = os.environ["CEKWAJAR_SUPABASE_SERVICE_KEY"]
        _client = create_client(url, key)
        return _client
    except KeyError as e:
        logger.error("Missing env var: %s", e)
        raise
    except Exception as e:
        logger.error("Supabase init failed: %s", e)
        raise


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_fallback(run_id: str, data: dict) -> None:
    """Write data to local JSON file when Supabase is unavailable."""
    fallback_dir = Path("logs")
    fallback_dir.mkdir(exist_ok=True)
    path = fallback_dir / f"wajar_watch_fallback_{run_id}.json"
    existing = []
    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except Exception:
            pass
    existing.append({"timestamp": _utcnow_iso(), **data})
    path.write_text(json.dumps(existing, indent=2, default=str))
    logger.warning("Supabase unavailable — wrote fallback to %s", path)


# ── Page hashes ───────────────────────────────────────────────────────────────

async def get_page_hash(source_id: str, url: str) -> dict | None:
    """Get last known hash for a source URL. Returns dict or None."""
    try:
        client = _get_client()
        resp = (
            client.table("regulation_page_hashes")
            .select("*")
            .eq("source_id", source_id)
            .eq("url", url)
            .execute()
        )
        if resp.data:
            return resp.data[0]
        return None
    except Exception as e:
        logger.error("get_page_hash failed: %s", e)
        return None


async def update_page_hash(
    source_id: str, url: str, content_hash: str, snippet: str
) -> bool:
    """Upsert page hash. Returns True on success."""
    try:
        client = _get_client()
        client.table("regulation_page_hashes").upsert(
            {
                "source_id": source_id,
                "url": url,
                "content_hash": content_hash,
                "last_checked": _utcnow_iso(),
                "last_changed": _utcnow_iso(),
                "snippet": snippet[:500],
            },
            on_conflict="source_id,url",
        ).execute()
        return True
    except Exception as e:
        logger.error("update_page_hash failed: %s", e)
        return False


async def update_page_hash_checked_only(source_id: str, url: str) -> bool:
    """Update only last_checked timestamp (no content change)."""
    try:
        client = _get_client()
        client.table("regulation_page_hashes").update(
            {"last_checked": _utcnow_iso()}
        ).eq("source_id", source_id).eq("url", url).execute()
        return True
    except Exception as e:
        logger.error("update_page_hash_checked_only failed: %s", e)
        return False


# ── Regulation constants ─────────────────────────────────────────────────────

async def upsert_constant(key: str, value: float, **kwargs) -> bool:
    """Upsert a regulation constant. Returns True on success."""
    try:
        client = _get_client()
        row = {"key": key, "value": value, "updated_at": _utcnow_iso(), **kwargs}
        client.table("regulation_constants").upsert(
            row, on_conflict="key"
        ).execute()
        return True
    except Exception as e:
        logger.error("upsert_constant failed: %s", e)
        _write_fallback("manual", {"op": "upsert_constant", "key": key, "value": value, **kwargs})
        return False


# ── Change log ────────────────────────────────────────────────────────────────

async def log_change(
    key: str,
    old_value: float,
    new_value: float,
    result: ConfidenceResult,
    pr_url: str | None,
    pr_number: int | None,
    run_id: str,
) -> str | None:
    """Log a detected change. Returns the log entry UUID or None."""
    try:
        client = _get_client()
        row = {
            "key": key,
            "old_value": old_value,
            "new_value": new_value,
            "delta_pct": result.delta_pct,
            "confidence": result.confidence,
            "routing": result.routing,
            "pr_url": pr_url,
            "pr_number": pr_number,
            "legal_basis": result.legal_basis,
            "legal_basis_url": result.legal_basis_url,
            "verbatim_quote": result.verbatim_quotes[0] if result.verbatim_quotes else None,
            "pipeline_run_id": run_id,
        }
        resp = client.table("regulation_change_log").insert(row).execute()
        if resp.data:
            return resp.data[0]["id"]
        return None
    except Exception as e:
        logger.error("log_change failed: %s", e)
        _write_fallback(run_id, {"op": "log_change", "key": key, "old": old_value, "new": new_value})
        return None


async def update_change_status(
    log_id: str, status: str, approved_by: str | None = None
) -> bool:
    """Update the status of a change log entry."""
    try:
        client = _get_client()
        update = {"status": status}
        if approved_by:
            update["approved_by"] = approved_by
            update["approved_at"] = _utcnow_iso()
        client.table("regulation_change_log").update(update).eq("id", log_id).execute()
        return True
    except Exception as e:
        logger.error("update_change_status failed: %s", e)
        return False


async def get_recent_changes(limit: int = 10) -> list[dict]:
    """Get most recent change log entries."""
    try:
        client = _get_client()
        resp = (
            client.table("regulation_change_log")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        logger.error("get_recent_changes failed: %s", e)
        return []


async def get_change_by_id(log_id: str) -> dict | None:
    """Get a single change log entry by ID."""
    try:
        client = _get_client()
        resp = (
            client.table("regulation_change_log")
            .select("*")
            .eq("id", log_id)
            .execute()
        )
        if resp.data:
            return resp.data[0]
        return None
    except Exception as e:
        logger.error("get_change_by_id failed: %s", e)
        return None


# ── Pipeline run log ─────────────────────────────────────────────────────────

async def start_pipeline_run(run_id: str, trigger: str = "cron") -> bool:
    """Log pipeline start."""
    try:
        client = _get_client()
        client.table("pipeline_run_log").insert({
            "run_id": run_id,
            "trigger": trigger,
            "started_at": _utcnow_iso(),
        }).execute()
        return True
    except Exception as e:
        logger.error("start_pipeline_run failed: %s", e)
        return False


async def finish_pipeline_run(run_id: str, result: Any) -> bool:
    """Log pipeline completion with summary stats."""
    try:
        client = _get_client()
        client.table("pipeline_run_log").update({
            "finished_at": _utcnow_iso(),
            "sources_checked": result.sources_checked,
            "changes_detected": result.changes_detected,
            "auto_applied": result.auto_applied,
            "alerted_human": result.alerted_human,
            "blocked": result.blocked,
            "skipped": result.skipped,
            "errors": json.dumps(result.errors),
            "status": "failed" if result.errors else "completed",
        }).eq("run_id", run_id).execute()
        return True
    except Exception as e:
        logger.error("finish_pipeline_run failed: %s", e)
        _write_fallback(run_id, {
            "op": "finish_pipeline_run",
            "sources_checked": result.sources_checked,
            "changes_detected": result.changes_detected,
            "errors": result.errors,
        })
        return False


# ── Fallback import ──────────────────────────────────────────────────────────

async def import_fallback(filepath: str) -> int:
    """Replay a fallback JSON file into Supabase. Returns count of replayed ops."""
    path = Path(filepath)
    if not path.exists():
        logger.warning("Fallback file not found: %s", filepath)
        return 0

    data = json.loads(path.read_text())
    replayed = 0
    for entry in data:
        op = entry.get("op")
        try:
            if op == "upsert_constant":
                key = entry.pop("key")
                entry.pop("op")
                entry.pop("timestamp", None)
                value = entry.pop("value")
                await upsert_constant(key, value, **entry)
                replayed += 1
            elif op == "log_change":
                logger.info("Skipping log_change replay (manual review needed)")
            elif op == "finish_pipeline_run":
                logger.info("Skipping finish_pipeline_run replay")
        except Exception as e:
            logger.error("Fallback replay error: %s", e)

    logger.info("Replayed %d/%d operations from %s", replayed, len(data), filepath)
    return replayed
