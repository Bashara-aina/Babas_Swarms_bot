"""Business operations tools for Bashara's projects.

Allows Legion to check metrics, run DB queries, manage deployments
via natural language — no Supabase dashboard needed.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")


async def supabase_query(
    table: str,
    query_type: str = "select",
    filters: dict | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Run a Supabase query via REST API. Supports: select, count."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return [{"error": "SUPABASE_URL or SUPABASE_SERVICE_KEY not set"}]
    try:
        import aiohttp

        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
        }
        url = f"{SUPABASE_URL}/rest/v1/{table}"
        params: dict[str, Any] = {"limit": limit}
        if filters:
            for k, v in filters.items():
                params[f"{k}"] = f"eq.{v}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                return [{"error": f"HTTP {resp.status}", "detail": await resp.text()}]
    except Exception as e:
        return [{"error": str(e)}]


async def get_business_summary() -> str:
    """Get a combined business summary for morning briefing."""
    lines = ["📊 **Business Snapshot**\n"]

    try:
        listings = await supabase_query("listings", limit=1, filters={"status": "active"})
        if listings and "error" not in listings[0]:
            lines.append(f"**rumahlabuh.com**")
            lines.append(f"  Active listings: {len(listings)}")
        else:
            lines.append("**rumahlabuh.com**: query failed")
    except Exception as e:
        lines.append(f"**rumahlabuh.com**: {e}")

    try:
        calcs = await supabase_query("salary_checks", limit=1)
        if calcs and "error" not in calcs[0]:
            lines.append(f"**cekwajar.id**")
            lines.append(f"  Recent checks: {len(calcs)}")
        else:
            lines.append("**cekwajar.id**: query failed")
    except Exception as e:
        lines.append(f"**cekwajar.id**: {e}")

    return "\n".join(lines)


async def check_vercel_deployments() -> str:
    """Check latest deployment status on Vercel."""
    vercel_token = os.getenv("VERCEL_TOKEN", "")
    if not vercel_token:
        return "VERCEL_TOKEN not set"
    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.vercel.com/v6/deployments",
                headers={"Authorization": f"Bearer {vercel_token}"},
                params={"limit": "5"},
            ) as resp:
                if resp.status != 200:
                    return f"Vercel API error: {resp.status}"
                data = await resp.json()
                deployments = data.get("deployments", [])
                lines = ["**Recent Vercel Deployments:**"]
                for d in deployments[:3]:
                    state = d.get("state", "unknown")
                    name = d.get("name", "unknown")
                    url = d.get("url", "")
                    emoji = "✅" if state == "READY" else "❌" if state == "ERROR" else "🔄"
                    lines.append(f"  {emoji} {name} — {state} | https://{url}")
                return "\n".join(lines)
    except Exception as e:
        return f"Vercel check failed: {e}"
