"""Business management handler for rumahlabuh.com + Supabase.

Commands:
  /db <query>              — Natural language Supabase query
  /site_health             — Ping website + Supabase connection
  /bookings [today|week|month]  — Booking summary
  /db_schema               — Regenerate the rumahlabuh skill file from live schema
"""

from __future__ import annotations

import html
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.shared import is_allowed

router = Router()
logger = logging.getLogger(__name__)


def _get_db():
    """Return Supabase client or None."""
    try:
        from tools.supabase_client import get_client, is_configured

        if not is_configured():
            return None
        return get_client()
    except Exception:
        return None


@router.message(Command("db"))
async def cmd_db(msg: Message) -> None:
    """Natural language query against the business database."""
    if not is_allowed(msg):
        return
    query = (msg.text or "").replace("/db", "", 1).strip()
    if not query:
        await msg.answer(
            "Usage: <code>/db ada berapa booking minggu ini?</code>",
            parse_mode="HTML",
        )
        return

    db = _get_db()
    if db is None:
        await msg.answer(
            "Supabase not configured. Add <code>SUPABASE_URL</code> and "
            "<code>SUPABASE_ANON_KEY</code> to your .env file.",
            parse_mode="HTML",
        )
        return

    await msg.answer("Querying database...", parse_mode="HTML")
    try:
        result = await db.query_natural(query)
        await msg.answer(result[:4000], parse_mode="HTML")
    except Exception as exc:
        await msg.answer(
            f"Query failed: <code>{html.escape(str(exc)[:300])}</code>",
            parse_mode="HTML",
        )


@router.message(Command("site_health"))
async def cmd_site_health(msg: Message) -> None:
    """Check rumahlabuh.com website + Supabase connection health."""
    if not is_allowed(msg):
        return

    lines: list[str] = ["<b>Site Health Check</b>"]

    # Check website
    try:
        from tools.rumahlabuh_http import get_resilient_session

        async with get_resilient_session() as session:
            async with session.get("https://rumahlabuh.com") as resp:
                status = resp.status
                lines.append(f"rumahlabuh.com: {'✅' if status < 400 else '❌'} HTTP {status}")

                # Trigger schema bootstrap if skill file is missing
                from pathlib import Path

                if not Path("skills/rumahlabuh-manager.md").exists():
                    db = _get_db()
                    if db is not None:
                        try:
                            path = await db.generate_skill_file()
                            lines.append(f"✅ Schema bootstrapped → {path}")
                        except Exception as se:
                            lines.append(f"⚠️ Schema bootstrap failed: {se}")
    except Exception as exc:
        lines.append(f"rumahlabuh.com: ❌ {exc}")

    # Check Supabase
    db = _get_db()
    if db is not None:
        try:
            health = await db.health_check()
            ok = health.get("ok", False)
            latency = health.get("latency_ms", "?")
            lines.append(f"Supabase: {'✅' if ok else '❌'} {latency}ms")
        except Exception as exc:
            lines.append(f"Supabase: ❌ {exc}")
    else:
        lines.append("Supabase: ⚠️ not configured")

    await msg.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("bookings"))
async def cmd_bookings(msg: Message) -> None:
    """Show booking summary for today / this week / this month."""
    if not is_allowed(msg):
        return

    args = (msg.text or "").replace("/bookings", "", 1).strip().lower()
    period = args if args in ("today", "week", "month") else "week"

    db = _get_db()
    if db is None:
        await msg.answer(
            "Supabase not configured. Add <code>SUPABASE_URL</code> to .env.",
            parse_mode="HTML",
        )
        return

    period_query = {
        "today": "booking untuk hari ini",
        "week": "booking minggu ini",
        "month": "booking bulan ini",
    }
    nl = period_query.get(period, "booking minggu ini")

    await msg.answer(f"Fetching {period} bookings...", parse_mode="HTML")
    try:
        result = await db.query_natural(nl)
        await msg.answer(result[:4000], parse_mode="HTML")
    except Exception as exc:
        await msg.answer(
            f"Failed: <code>{html.escape(str(exc)[:300])}</code>",
            parse_mode="HTML",
        )


@router.message(Command("db_schema"))
async def cmd_db_schema(msg: Message) -> None:
    """Regenerate skills/rumahlabuh-manager.md from live Supabase schema."""
    if not is_allowed(msg):
        return

    db = _get_db()
    if db is None:
        await msg.answer(
            "Supabase not configured. Add <code>SUPABASE_URL</code> and "
            "<code>SUPABASE_SERVICE_ROLE_KEY</code> to .env.",
            parse_mode="HTML",
        )
        return

    await msg.answer("Introspecting Supabase schema...", parse_mode="HTML")
    try:
        path = await db.generate_skill_file()
        await msg.answer(
            f"✅ Skill file generated: <code>{html.escape(path)}</code>\n"
            "Legion now knows your database schema. Try: <code>/db ada berapa booking?</code>",
            parse_mode="HTML",
        )
    except Exception as exc:
        await msg.answer(
            f"Schema generation failed: <code>{html.escape(str(exc)[:300])}</code>",
            parse_mode="HTML",
        )


@router.message(Command("biz"))
async def cmd_biz_summary(msg: Message) -> None:
    """Business metrics dashboard — rumahlabuh + cekwajar + Vercel."""
    if not is_allowed(msg):
        return

    status = await msg.answer("📊 Fetching business metrics...")
    from tools.business_ops import check_vercel_deployments, get_business_summary

    summary = await get_business_summary()
    deployments = await check_vercel_deployments()
    full = summary + "\n\n" + deployments
    await status.edit_text(full, parse_mode="HTML")
