"""Autonomous plain-text message handling for Legion v6.

Routes every non-command message through AutonomousRouter (keyword + LLM)
and dispatches to the appropriate handler without requiring /slash commands.
"""

from __future__ import annotations

import html as html_mod
import logging

from aiogram.types import Message

from core.autonomous_router import SKILL_PATTERNS, AutonomousRouter
from .shared import _execute_chat, _run_agent_loop, is_allowed

logger = logging.getLogger(__name__)


async def handle_plain_message(
    msg: Message,
    auto_router: AutonomousRouter,
) -> None:
    """Handle non-command plain text and route autonomously."""
    if not is_allowed(msg):
        return

    user_msg = (msg.text or "").strip()
    if not user_msg or user_msg.startswith("/"):
        return

    # analyze() is async (may call LLM for low-confidence messages)
    skill_match = await auto_router.analyze(user_msg)
    logger.info(
        "[AutoRouter] '%s...' -> %s (%s%%)",
        user_msg[:50],
        skill_match.skill_name,
        int(skill_match.confidence * 100),
    )

    handler_key = SKILL_PATTERNS.get(skill_match.skill_name, {}).get("handler", "chat")

    try:
        # ── conversation / low-confidence fallback ───────────────────────────
        if handler_key == "chat" or skill_match.confidence < 0.4:
            await _execute_chat(msg, user_msg)
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── memory recall ────────────────────────────────────────────────────
        if handler_key == "memory_recall":
            from llm_client import memory

            if memory is not None:
                memories = await memory.search(user_msg, limit=8)
                if memories:
                    mem_context = "\n".join(
                        f"[{str(m.get('created_at', ''))[:10]}] {str(m.get('content', ''))[:300]}"
                        for m in memories[:5]
                    )
                    enriched = (
                        f"{user_msg}\n\n"
                        f"[Memory search results — use these to answer]:\n{mem_context}"
                    )
                    await _execute_chat(msg, enriched)
                    auto_router.record_performance(skill_match.skill_name, True)
                    return
            await _execute_chat(msg, user_msg)
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── desktop / computer control ───────────────────────────────────────
        if handler_key == "/do":
            await _run_agent_loop(msg, user_msg)
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── code generation ──────────────────────────────────────────────────
        if handler_key == "/run":
            await _execute_chat(msg, user_msg, forced_agent="coding")
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── deep reasoning ───────────────────────────────────────────────────
        if handler_key == "/think":
            await _execute_chat(msg, user_msg, forced_agent="think")
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── multi-agent swarm ────────────────────────────────────────────────
        if handler_key == "/swarm":
            await _execute_chat(msg, user_msg, forced_agent="architect")
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── multi-source research ────────────────────────────────────────────
        if handler_key == "/research":
            await _execute_chat(msg, user_msg, forced_agent="researcher")
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── shell command ────────────────────────────────────────────────────
        if handler_key == "/cmd":
            from llm_client import run_shell_command

            output = await run_shell_command(user_msg)
            await msg.answer(
                f"<pre>{html_mod.escape(output[:3800])}</pre>",
                parse_mode="HTML",
            )
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── email management ─────────────────────────────────────────────────
        if handler_key == "email":
            await _handle_email(msg, user_msg, auto_router)
            return

        # ── business / Supabase ──────────────────────────────────────────────
        if handler_key == "business":
            await _handle_business(msg, user_msg, auto_router)
            return

        # ── location-aware recommendations ───────────────────────────────────
        if handler_key == "location":
            await _handle_location(msg, user_msg, auto_router)
            return

        # ── WhatsApp ─────────────────────────────────────────────────────────
        if handler_key == "whatsapp":
            await _handle_whatsapp(msg, user_msg, auto_router)
            return

        # ── GitHub trending intelligence ──────────────────────────────────────
        if handler_key == "github_intel":
            await _handle_github_intel(msg, user_msg, auto_router)
            return

        # ── generic fallback ─────────────────────────────────────────────────
        await _execute_chat(msg, user_msg)
        auto_router.record_performance(skill_match.skill_name, True)

    except Exception as exc:
        auto_router.record_performance(skill_match.skill_name, False)
        await msg.answer(
            f"autonomous routing error: <code>{html_mod.escape(str(exc)[:350])}</code>",
            parse_mode="HTML",
        )


# ── Skill-specific sub-handlers ───────────────────────────────────────────────


async def _handle_email(msg: Message, user_msg: str, router: AutonomousRouter) -> None:
    """Read inbox or compose email based on natural language."""
    try:
        from tools.email_client import EmailClient

        client = EmailClient()
        msg_lower = user_msg.lower()

        if any(kw in msg_lower for kw in ["send", "kirim", "reply", "balas", "forward"]):
            # Compose / reply — delegate to LLM with email context injected
            enriched = (
                f"{user_msg}\n\n"
                "[You have access to the user's email. "
                "Draft a reply or new email as requested. "
                "Use send_email() or reply_email() when ready.]"
            )
            await _execute_chat(msg, enriched, forced_agent="general")
        else:
            # Default: show inbox summary
            summary = await client.summarize_inbox()
            enriched = (
                f"{user_msg}\n\n"
                f"[Current inbox summary]:\n{summary[:2000]}\n\n"
                "Summarise what's important and ask if the user wants to act on anything."
            )
            await _execute_chat(msg, enriched, forced_agent="general")

        router.record_performance("email_management", True)
    except Exception as exc:
        logger.warning("[email handler] %s", exc)
        # Graceful fallback — chat agent handles it
        await _execute_chat(msg, user_msg)
        router.record_performance("email_management", False)


async def _handle_business(msg: Message, user_msg: str, router: AutonomousRouter) -> None:
    """Query rumahlabuh.com business data via Supabase."""
    try:
        from tools.supabase_client import get_client

        db = get_client()
        if db is not None and hasattr(db, "query_natural"):
            # Phase 6 implementation: NL→SQL via Supabase
            result = await db.query_natural(user_msg)
            enriched = (
                f"{user_msg}\n\n"
                f"[Supabase query result]:\n{str(result)[:2000]}\n\n"
                "Present this data clearly and suggest what the user might want to do next."
            )
            await _execute_chat(msg, enriched, forced_agent="analyst")
        else:
            # Fallback: researcher with Supabase/business context injected
            enriched = (
                f"{user_msg}\n\n"
                "[Context: You manage rumahlabuh.com — a villa/accommodation rental "
                "business in Indonesia. The database is on Supabase. "
                "Answer using your knowledge of the business, or ask for more detail.]"
            )
            await _execute_chat(msg, enriched, forced_agent="analyst")

        router.record_performance("business_query", True)
    except Exception as exc:
        logger.warning("[business handler] %s", exc)
        await _execute_chat(msg, user_msg)
        router.record_performance("business_query", False)


async def _handle_location(msg: Message, user_msg: str, router: AutonomousRouter) -> None:
    """Location-aware recommendations using user profile location."""
    try:
        from tools.location_advisor import LocationAdvisor
        from core.memory.user_profile import UserProfile

        profile = UserProfile()
        location = profile.get("location", "Tokyo, Japan")
        advisor = LocationAdvisor()
        result = await advisor.recommend_places(user_msg, location)
        await msg.answer(result[:4000], parse_mode="HTML")
        router.record_performance("location_advice", True)
    except Exception as exc:
        logger.warning("[location handler] %s — falling back to enriched chat", exc)
        # Fallback: inject location into researcher prompt
        try:
            from core.memory.user_profile import UserProfile
            location = UserProfile().get("location", "Tokyo, Japan")
        except Exception:
            location = "Tokyo, Japan"
        enriched = (
            f"{user_msg}\n\n"
            f"[User's home location: {location}. "
            "Use this location to give specific, personalised recommendations. "
            "Search online for up-to-date options.]"
        )
        await _execute_chat(msg, enriched, forced_agent="researcher")
        router.record_performance("location_advice", False)


async def _handle_whatsapp(msg: Message, user_msg: str, router: AutonomousRouter) -> None:
    """Read or send WhatsApp messages via the WA bridge."""
    try:
        from bridges.whatsapp_bridge import WhatsAppBridge

        bridge = WhatsAppBridge()
        msg_lower = user_msg.lower()

        if any(kw in msg_lower for kw in ["send", "kirim", "balas", "reply"]):
            enriched = (
                f"{user_msg}\n\n"
                "[You can send WhatsApp messages via WhatsAppBridge.send_message(). "
                "Draft the message and confirm with the user before sending.]"
            )
            await _execute_chat(msg, enriched, forced_agent="general")
        else:
            unread = await bridge.get_unread()
            if not unread:
                await msg.answer("No unread WhatsApp messages right now.", parse_mode="HTML")
                router.record_performance("whatsapp_action", True)
                return
            summary = "\n".join(
                f"<b>{m.get('name', m.get('from', '?'))}</b>: {html_mod.escape(str(m.get('body', ''))[:200])}"
                for m in unread[:10]
            )
            enriched = (
                f"{user_msg}\n\n"
                f"[Unread WhatsApp messages]:\n{summary}\n\n"
                "Summarise and ask if the user wants to reply to any."
            )
            await _execute_chat(msg, enriched, forced_agent="general")

        router.record_performance("whatsapp_action", True)
    except ImportError:
        await msg.answer(
            "WhatsApp bridge not yet set up. Use <code>/wa_qr</code> to get started.",
            parse_mode="HTML",
        )
        router.record_performance("whatsapp_action", False)
    except Exception as exc:
        logger.warning("[whatsapp handler] %s", exc)
        await _execute_chat(msg, user_msg)
        router.record_performance("whatsapp_action", False)


async def _handle_github_intel(msg: Message, user_msg: str, router: AutonomousRouter) -> None:
    """Trigger GitHub trending intelligence scan."""
    try:
        from tools.github_intel import GitHubIntelEngine

        engine = GitHubIntelEngine()
        await msg.answer("Scanning GitHub trending... this takes ~30s.", parse_mode="HTML")
        report = await engine.generate_intel_report(
            await engine.fetch_trending()
        )
        await msg.answer(report[:4000], parse_mode="HTML")
        router.record_performance("github_intel", True)
    except ImportError:
        await msg.answer(
            "GitHub intel engine not yet installed. Use <code>/github_intel</code> to trigger manually.",
            parse_mode="HTML",
        )
        router.record_performance("github_intel", False)
    except Exception as exc:
        logger.warning("[github_intel handler] %s", exc)
        await _execute_chat(msg, user_msg, forced_agent="researcher")
        router.record_performance("github_intel", False)
