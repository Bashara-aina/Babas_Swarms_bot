"""Declarative maintenance runbooks (HTTP, Supabase, notes).

Config: config/runbooks.json
Env: RUNBOOK_SUPABASE_TABLE — optional table name for supabase_probe (default bookings).
"""

from __future__ import annotations

import html
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CONFIG = Path(__file__).resolve().parent.parent / "config" / "runbooks.json"


def _load() -> dict[str, Any]:
    if not _CONFIG.exists():
        return {"runbooks": {}}
    try:
        return json.loads(_CONFIG.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("[runbook] load failed: %s", e)
        return {"runbooks": {}}


def list_runbook_summaries() -> str:
    data = _load()
    books = data.get("runbooks") or {}
    if not books:
        return "No runbooks in config/runbooks.json"
    lines = ["<b>Available runbooks</b>"]
    for rid, meta in books.items():
        title = html.escape(str(meta.get("title", rid)))
        desc = html.escape(str(meta.get("description", ""))[:200])
        lines.append(f"• <code>{html.escape(rid)}</code> — {title}")
        if desc:
            lines.append(f"  <i>{desc}</i>")
    return "\n".join(lines)


def match_runbook_from_text(message: str) -> str | None:
    """Return runbook id if triggers match (substring, case-insensitive)."""
    low = (message or "").lower().strip()
    data = _load()
    for rid, meta in (data.get("runbooks") or {}).items():
        for trig in meta.get("triggers") or []:
            if trig.lower() in low:
                return rid
    if "runbook" in low:
        # "runbook rumahlabuh_stack_health" style
        parts = low.split()
        for i, p in enumerate(parts):
            if p == "runbook" and i + 1 < len(parts):
                cand = parts[i + 1].strip()
                if cand in (data.get("runbooks") or {}):
                    return cand
    return None


async def _step_http_get(step: dict[str, Any]) -> str:
    import aiohttp

    url = str(step.get("url", "")).strip()
    name = html.escape(str(step.get("name", url)))
    timeout = float(step.get("timeout_sec", 10))
    if not url:
        return f"• {name}: <b>skip</b> (no url)"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                allow_redirects=True,
            ) as resp:
                ok = resp.status < 400
                icon = "✅" if ok else "❌"
                return f"• {name}: {icon} HTTP {resp.status}"
    except Exception as e:
        return f"• {name}: ❌ <code>{html.escape(str(e)[:200])}</code>"


async def _step_supabase_probe(step: dict[str, Any]) -> str:
    env_key = str(step.get("table_env", "RUNBOOK_SUPABASE_TABLE"))
    table = os.getenv(env_key, "").strip() or str(step.get("fallback_table", "bookings"))
    limit = int(step.get("limit", 1))
    try:
        from tools.supabase_client import get_client, is_configured

        if not is_configured():
            return "• Supabase: ⚠️ not configured (set SUPABASE_URL + keys)"
        db = get_client()
        if db is None:
            return "• Supabase: ⚠️ client unavailable"
        rows = await db.query(table, select="*", limit=limit)
        return f"• Supabase table <code>{html.escape(table)}</code>: ✅ OK ({len(rows)} row sample)"
    except Exception as e:
        return (
            f"• Supabase table <code>{html.escape(table)}</code>: ❌ "
            f"<code>{html.escape(str(e)[:220])}</code>"
        )


def _step_note(step: dict[str, Any]) -> str:
    txt = str(step.get("text", "")).strip()
    if not txt:
        return ""
    return f"• <i>{html.escape(txt[:500])}</i>"


async def execute_runbook(runbook_id: str) -> str:
    data = _load()
    books = data.get("runbooks") or {}
    meta = books.get(runbook_id)
    if not meta:
        return f"Unknown runbook <code>{html.escape(runbook_id)}</code>. Try /runbook"

    title = html.escape(str(meta.get("title", runbook_id)))
    lines = [f"<b>Runbook: {title}</b>", ""]
    for step in meta.get("steps") or []:
        stype = str(step.get("type", "")).lower()
        try:
            if stype == "http_get":
                lines.append(await _step_http_get(step))
            elif stype == "supabase_probe":
                lines.append(await _step_supabase_probe(step))
            elif stype == "note":
                n = _step_note(step)
                if n:
                    lines.append(n)
            else:
                lines.append(f"• ⚠️ unknown step type <code>{html.escape(stype)}</code>")
        except Exception as e:
            lines.append(f"• ❌ step error: <code>{html.escape(str(e)[:200])}</code>")
    lines.append("")
    lines.append("<i>Tip: extend config/runbooks.json for more sites/tables.</i>")
    return "\n".join(lines)
