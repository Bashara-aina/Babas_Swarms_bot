"""Autonomous plain-text message handling for Legion v6.

Routes every non-command message through AutonomousRouter (keyword + LLM)
and dispatches to the appropriate handler without requiring /slash commands.
"""

from __future__ import annotations

import html as html_mod
import logging
import os
import re
from typing import Optional

from aiogram.types import Message

from core.autonomous_router import SKILL_PATTERNS, AutonomousRouter
from .shared import _execute_chat, _run_agent_loop, is_allowed, send_chunked

logger = logging.getLogger(__name__)

_WA_PENDING: dict[int, dict[str, str]] = {}
_WA_LAST_CONTACT: dict[int, str] = {}


def _wa_is_intent_message(text: str, user_id: int) -> bool:
    t = _wa_normalize(text).lower()
    if user_id in _WA_PENDING:
        return True
    keywords = [
        "whatsapp",
        "wa ",
        "chat ke",
        "chat to",
        "send to",
        "send ke",
        "kirim ke",
        "kirim ke",
        "wa_reply",
        "reply wa",
        "to her",
        "to him",
    ]
    return any(k in t for k in keywords)


def _wa_normalize(text: str) -> str:
    return " ".join((text or "").strip().split())


def _wa_is_confirm(text: str) -> bool:
    t = _wa_normalize(text).lower()
    phrases = {
        "send it now",
        "send now",
        "send",
        "yes send",
        "confirm send",
        "kirim sekarang",
        "kirim sekarang ya",
        "send to her now",
        "send to him now",
    }
    return t in phrases


def _wa_extract_contact_message(
    text: str, fallback_contact: Optional[str] = None
) -> tuple[Optional[str], Optional[str]]:
    raw = _wa_normalize(text)
    lower = raw.lower()

    patterns = [
        r"(?:send|chat|message|tell|kirim|pesan)\s+(?:to|ke)\s+(?P<contact>.+?)\s+(?:that|saying|say|kalau|bahwa)\s+(?P<body>.+)$",
        r"(?:send|message|kirim|pesan)\s+(?P<contact>.+?)\s*:\s*(?P<body>.+)$",
        r"(?P<body>.+?)\s+(?:send|kirim|chat|pesan)\s+(?:to|ke)\s+(?P<contact>.+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.IGNORECASE)
        if match:
            contact = _wa_normalize(match.group("contact"))
            body = _wa_normalize(match.group("body"))
            body = re.sub(r"^(cuma|just|only)\s+", "", body, flags=re.IGNORECASE)
            body = re.sub(r"\s+(aja|doang)$", "", body, flags=re.IGNORECASE)
            return contact or None, body or None

    love_phrases = ["i love you", "love you", "aku sayang kamu", "sayang kamu"]
    verb_match = re.search(r"\b(send|chat|kirim|pesan|message|tell)\b", lower)
    prep_match = re.search(r"\b(to|ke)\b", lower)
    if verb_match and prep_match and prep_match.start() > verb_match.start():
        tail = raw[prep_match.end() :].strip()
        for phrase in love_phrases:
            idx = tail.lower().rfind(phrase)
            if idx > 0:
                contact = _wa_normalize(tail[:idx])
                body = _wa_normalize(tail[idx:])
                if contact and body:
                    return contact, body

    pronoun_targets = ["to her", "to him", "her", "him"]
    if fallback_contact and any(p in lower for p in pronoun_targets):
        body = raw
        for token in [
            "send it now",
            "send now",
            "send to her",
            "send to him",
            "chat to her",
            "chat to him",
            "tell her",
            "tell him",
            "that",
        ]:
            body = re.sub(rf"\b{re.escape(token)}\b", "", body, flags=re.IGNORECASE)
        body = _wa_normalize(body)
        return fallback_contact, (body or None)

    if fallback_contact and lower.startswith("just "):
        return fallback_contact, _wa_normalize(raw[5:]) or None

    return None, None


async def _wa_send_local(contact_name: str, body: str) -> str:
    from computer_agent import whatsapp_send_local

    return await whatsapp_send_local(contact_name=contact_name, message=body)


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

    user_id = msg.from_user.id if msg.from_user else 0
    if _wa_is_intent_message(user_msg, user_id):
        await _handle_whatsapp(msg, user_msg, auto_router)
        return

    # Optional Manus-killer task router (parallel specialists) — runs before AutonomousRouter.
    # In pytest runs we disable this pre-routing path to keep integration tests deterministic
    # around the expected plain NL -> llm_client.chat flow.
    _task_router_enabled = os.getenv("LEGION_TASK_ROUTER_ENABLED", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if os.getenv("PYTEST_CURRENT_TEST"):
        _task_router_enabled = False

    if _task_router_enabled:
        try:
            from core.task_router import get_task_router

            stream_cb = None
            if os.getenv("LEGION_TASK_ROUTER_STREAM", "0").strip().lower() in (
                "1",
                "true",
                "yes",
                "on",
            ):

                async def _tr_stream(t: str) -> None:
                    try:
                        await msg.answer(t[:3800], parse_mode="HTML")
                    except Exception:
                        pass

                stream_cb = _tr_stream

            routed = await get_task_router().route(
                user_msg,
                context="",
                user_id=str(user_id),
                stream_callback=stream_cb,
            )
            if routed is not None:
                await send_chunked(msg, routed)
                return
        except Exception:
            logger.exception("task router failed; falling back to autonomous routing")

    # analyze_async() keeps the live bot LLM-backed while tests use analyze().
    skill_match = await auto_router.analyze_async(user_msg)
    logger.info(
        "[AutoRouter] '%s...' -> %s (%s%%)",
        user_msg[:50],
        skill_match.skill_name,
        int(skill_match.confidence * 100),
    )

    handler_key = SKILL_PATTERNS.get(skill_match.skill_name, {}).get("handler", "chat")
    _route_hint = skill_match.skill_name if skill_match.confidence >= 0.3 else None

    # ── Clarification intercept (Priority 5) ──────────────────────────────────
    # Ask ONE clarifying question when message is short AND confidence is low.
    # This fires BEFORE generic chat fallback, making Legion feel thoughtful.
    try:
        from core.clarification import ask_if_needed

        clarification_q = await ask_if_needed(
            user_msg,
            skill_match.skill_name,  # intent
            skill_match.confidence,
        )
        if clarification_q:
            await msg.answer(clarification_q)
            auto_router.record_performance(skill_match.skill_name, True)
            return
    except Exception:
        pass  # Non-fatal — proceed to normal routing

    try:
        # Jarvis: 3-word keyword hits score ~0.375 confidence — allow slightly lower floor
        _min_route_conf = 0.35 if handler_key == "jarvis" else 0.4
        # ── conversation / low-confidence fallback ───────────────────────────
        if handler_key == "chat" or skill_match.confidence < _min_route_conf:
            await _execute_chat(msg, user_msg, routing_hint=_route_hint)
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── memory recall ────────────────────────────────────────────────────
        if handler_key == "memory_recall":
            from llm_client import memory

            if memory is not None:
                memories = await memory.search(user_msg, limit=8)
                if memories:
                    mem_context = "\n".join(
                        f"[{str(m.get('created_at', ''))[:10]}] {str(m.get('content', ''))[:300]}" for m in memories[:5]
                    )
                    enriched = f"{user_msg}\n\n[Memory search results — use these to answer]:\n{mem_context}"
                    await _execute_chat(msg, enriched, routing_hint=_route_hint)
                    auto_router.record_performance(skill_match.skill_name, True)
                    return
            await _execute_chat(msg, user_msg, routing_hint=_route_hint)
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── desktop / computer control ───────────────────────────────────────
        if handler_key == "/do":
            await _run_agent_loop(msg, user_msg)
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── code generation ──────────────────────────────────────────────────
        if handler_key == "/run":
            await _execute_chat(msg, user_msg, forced_agent="coding", routing_hint=_route_hint)
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── deep reasoning ───────────────────────────────────────────────────
        if handler_key == "/think":
            await _execute_chat(msg, user_msg, forced_agent="think", routing_hint=_route_hint)
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── multi-agent swarm ────────────────────────────────────────────────
        if handler_key == "/swarm":
            await _execute_chat(msg, user_msg, forced_agent="architect", routing_hint=_route_hint)
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── multi-source research ────────────────────────────────────────────
        if handler_key == "/research":
            await _execute_chat(msg, user_msg, forced_agent="researcher", routing_hint=_route_hint)
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── strategic simulation (plain-text "simulate / what if …") ─────────
        if handler_key == "simulation":
            await msg.answer("Running simulation…", parse_mode="HTML")
            try:
                from agents.simulation_agent import run_simulation_agent

                out = await run_simulation_agent(user_msg)
                await send_chunked(msg, out)
            except Exception as exc:
                logger.exception("simulation route failed")
                await msg.answer(f"Simulation error: {exc}", parse_mode="HTML")
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── Jarvis full-context bundle (plain-text, same as /jarvis) ───────────
        if handler_key == "jarvis":
            autoroute = os.getenv("LEGION_JARVIS_AUTOROUTE_ENABLED", "1").strip().lower()
            if autoroute not in ("1", "true", "yes", "on"):
                await _execute_chat(msg, user_msg, routing_hint=_route_hint)
                auto_router.record_performance(skill_match.skill_name, True)
                return
            await msg.answer("Running full context bundle (Jarvis)…", parse_mode="HTML")
            try:
                from core.jarvis_orchestrator import (
                    compose_jarvis_response,
                    gather_jarvis_bundle,
                )

                uid = str(msg.from_user.id) if msg.from_user else "0"
                bundle = await gather_jarvis_bundle(user_msg, uid)
                out = await compose_jarvis_response(bundle)
                await send_chunked(msg, out)
            except Exception as exc:
                logger.exception("jarvis autoroute failed")
                await msg.answer(
                    f"Jarvis error: <code>{html_mod.escape(str(exc)[:350])}</code>",
                    parse_mode="HTML",
                )
            auto_router.record_performance(skill_match.skill_name, True)
            return

        # ── debate / opinion (auto-triggered without /debate) ────────────────
        if handler_key == "debate":
            await _execute_chat(msg, user_msg, forced_agent="debate", routing_hint=_route_hint)
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

        # ── maintenance runbooks ─────────────────────────────────────────────
        if handler_key == "runbook":
            await _handle_runbook(msg, user_msg, auto_router)
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

        # ── codebase understanding (Copilot-like) ────────────────────────────
        if handler_key == "codebase_reader":
            await _handle_codebase_understanding(msg, user_msg, auto_router)
            return

        # ── generic fallback ─────────────────────────────────────────────────
        await _execute_chat(msg, user_msg, routing_hint=_route_hint)
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
            await _execute_chat(msg, enriched, forced_agent="general", routing_hint="email_management")
        else:
            # Default: show inbox summary
            summary = await client.summarize_inbox()
            enriched = (
                f"{user_msg}\n\n"
                f"[Current inbox summary]:\n{summary[:2000]}\n\n"
                "Summarise what's important and ask if the user wants to act on anything."
            )
            await _execute_chat(msg, enriched, forced_agent="general", routing_hint="email_management")

        router.record_performance("email_management", True)
    except Exception as exc:
        logger.warning("[email handler] %s", exc)
        # Graceful fallback — chat agent handles it
        await _execute_chat(msg, user_msg, routing_hint="email_management")
        router.record_performance("email_management", False)


async def _handle_runbook(msg: Message, user_msg: str, router: AutonomousRouter) -> None:
    """Run config/runbooks.json maintenance flows from natural language or explicit id."""
    try:
        from tools.runbook_engine import execute_runbook, list_runbook_summaries, match_runbook_from_text

        rid = match_runbook_from_text(user_msg)
        if not rid:
            rid = os.getenv("LEGION_DEFAULT_RUNBOOK", "rumahlabuh_stack_health")
        report = await execute_runbook(rid)
        await msg.answer(report[:4000], parse_mode="HTML")
        router.record_performance("runbook_maintenance", True)
    except Exception as exc:
        logger.warning("[runbook handler] %s", exc)
        try:
            await msg.answer(list_runbook_summaries(), parse_mode="HTML")
        except Exception:
            await msg.answer(f"Runbook error: <code>{html_mod.escape(str(exc)[:300])}</code>", parse_mode="HTML")
        router.record_performance("runbook_maintenance", False)


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
            await _execute_chat(msg, enriched, forced_agent="analyst", routing_hint="business_query")
        else:
            # Fallback: researcher with Supabase/business context injected
            enriched = (
                f"{user_msg}\n\n"
                "[Context: You manage rumahlabuh.com — a villa/accommodation rental "
                "business in Indonesia. The database is on Supabase. "
                "Answer using your knowledge of the business, or ask for more detail.]"
            )
            await _execute_chat(msg, enriched, forced_agent="analyst", routing_hint="business_query")

        router.record_performance("business_query", True)
    except Exception as exc:
        logger.warning("[business handler] %s", exc)
        await _execute_chat(msg, user_msg, routing_hint="business_query")
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
        await _execute_chat(msg, enriched, forced_agent="researcher", routing_hint="location_advice")
        router.record_performance("location_advice", False)


async def _handle_whatsapp(msg: Message, user_msg: str, router: AutonomousRouter) -> None:
    """Read or send WhatsApp messages via the WA bridge."""
    try:
        from bridges.whatsapp_bridge import WhatsAppBridge

        bridge = WhatsAppBridge()
        msg_lower = user_msg.lower()
        user_id = msg.from_user.id if msg.from_user else 0

        pending = _WA_PENDING.get(user_id)

        if pending and _wa_is_confirm(user_msg):
            result = await _wa_send_local(pending["contact"], pending["body"])
            if "sent" in result.lower() and "failed" not in result.lower():
                await msg.answer(
                    f"✅ Sent to <b>{html_mod.escape(pending['contact'])}</b>: "
                    f"<i>{html_mod.escape(pending['body'])}</i>",
                    parse_mode="HTML",
                )
                _WA_LAST_CONTACT[user_id] = pending["contact"]
                _WA_PENDING.pop(user_id, None)
                router.record_performance("whatsapp_action", True)
                return
            await msg.answer(
                f"❌ Send failed: <code>{html_mod.escape(result[:320])}</code>",
                parse_mode="HTML",
            )
            router.record_performance("whatsapp_action", False)
            return

        fallback_contact = (pending or {}).get("contact") or _WA_LAST_CONTACT.get(user_id)
        contact, body = _wa_extract_contact_message(user_msg, fallback_contact=fallback_contact)
        if contact and body:
            _WA_LAST_CONTACT[user_id] = contact
            if re.match(r"^(send|kirim|pesan|message)\b", msg_lower):
                result = await _wa_send_local(contact, body)
                if "sent" in result.lower() and "failed" not in result.lower():
                    await msg.answer(
                        f"✅ Sent to <b>{html_mod.escape(contact)}</b>: <i>{html_mod.escape(body)}</i>",
                        parse_mode="HTML",
                    )
                    _WA_PENDING.pop(user_id, None)
                    router.record_performance("whatsapp_action", True)
                    return
                await msg.answer(
                    f"❌ Send failed: <code>{html_mod.escape(result[:320])}</code>",
                    parse_mode="HTML",
                )
                router.record_performance("whatsapp_action", False)
                return

            _WA_PENDING[user_id] = {"contact": contact, "body": body}
            await msg.answer(
                "Draft ready:\n"
                f"To: <b>{html_mod.escape(contact)}</b>\n"
                f"Message: <i>{html_mod.escape(body)}</i>\n\n"
                "Reply <b>send it now</b> to send.",
                parse_mode="HTML",
            )
            router.record_performance("whatsapp_action", True)
            return

        if pending and body and not _wa_is_confirm(user_msg):
            pending["body"] = body
            _WA_PENDING[user_id] = pending
            await msg.answer(
                "Updated draft:\n"
                f"To: <b>{html_mod.escape(pending['contact'])}</b>\n"
                f"Message: <i>{html_mod.escape(pending['body'])}</i>\n\n"
                "Reply <b>send it now</b> to send.",
                parse_mode="HTML",
            )
            router.record_performance("whatsapp_action", True)
            return

        if any(kw in msg_lower for kw in ["send", "kirim", "balas", "reply"]):
            if pending:
                await msg.answer(
                    "Pending draft found. Reply <b>send it now</b> to send it, "
                    "or provide a new message in format: "
                    "<code>send to &lt;contact&gt; that &lt;message&gt;</code>",
                    parse_mode="HTML",
                )
            else:
                await msg.answer(
                    "Send format: <code>send to &lt;contact&gt; that &lt;message&gt;</code>\n"
                    "Example: <code>send to pwiti little hani that i love you</code>",
                    parse_mode="HTML",
                )
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
            await _execute_chat(msg, enriched, forced_agent="general", routing_hint="whatsapp_action")

        router.record_performance("whatsapp_action", True)
    except ImportError:
        await msg.answer(
            "WhatsApp bridge not yet set up. Use <code>/wa_qr</code> to get started.",
            parse_mode="HTML",
        )
        router.record_performance("whatsapp_action", False)
    except Exception as exc:
        logger.warning("[whatsapp handler] %s", exc)
        await _execute_chat(msg, user_msg, routing_hint="whatsapp_action")
        router.record_performance("whatsapp_action", False)


async def _handle_github_intel(msg: Message, user_msg: str, router: AutonomousRouter) -> None:
    """Trigger GitHub trending intelligence scan."""
    try:
        from tools.github_intel import GitHubIntelEngine

        engine = GitHubIntelEngine()
        await msg.answer("Scanning GitHub trending... this takes ~30s.", parse_mode="HTML")
        report = await engine.generate_intel_report(await engine.fetch_trending())
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
        await _execute_chat(msg, user_msg, forced_agent="researcher", routing_hint="github_intel")
        router.record_performance("github_intel", False)


async def _handle_codebase_understanding(msg: Message, user_msg: str, router: AutonomousRouter) -> None:
    """Understand project codebase structure — Copilot/Cursor-like code exploration."""
    try:
        from tools.codebase_reader import explain_codebase, find_in_code

        # Detect if it's a "find/locate" query or an "explain" query
        find_triggers = ["where is", "find ", "locate ", "where does", "dimana ada", "cari fungsi"]
        is_find = any(t in user_msg.lower() for t in find_triggers)

        if is_find:
            result = await find_in_code(user_msg)
        else:
            result = await explain_codebase(user_msg)

        # Enrich result with LLM explanation
        enriched = (
            f"{user_msg}\n\n"
            f"[Codebase search results from the Legion project]:\n{result[:3000]}\n\n"
            "Use these results to answer the question. Reference file paths and line numbers. "
            "If the results are incomplete, say so and suggest a more specific search."
        )
        await _execute_chat(msg, enriched, forced_agent="coding", routing_hint="codebase_reader")
        router.record_performance("codebase_understanding", True)
    except Exception as exc:
        logger.warning("[codebase_reader handler] %s", exc)
        # Fallback: just ask the coding agent
        await _execute_chat(msg, user_msg, forced_agent="coding", routing_hint="codebase_reader")
        router.record_performance("codebase_understanding", False)
