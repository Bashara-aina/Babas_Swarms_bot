"""Autonomous plain-text message handling for Legion v6.  # type: ignore[reportAttributeAccessIssue]

Routes every non-command message through AutonomousRouter (keyword + LLM)  # type: ignore[reportAttributeAccessIssue]
and dispatches to the appropriate handler without requiring /slash commands.  # type: ignore[reportAttributeAccessIssue]
"""

from __future__ import annotations

import asyncio
import contextlib
import html as html_mod
import logging
import os
import re

from aiogram.types import Message  # type: ignore[reportAttributeAccessIssue]

from core.autonomous_router import (  # type: ignore[reportAttributeAccessIssue]
    SKILL_PATTERNS,
    AutonomousRouter,
)

from .shared import (  # type: ignore[reportAttributeAccessIssue]
    _execute_chat,
    _run_agent_loop,
    is_allowed,
    send_chunked,
)

logger = logging.getLogger(__name__)  # type: ignore[reportAttributeAccessIssue]

_WA_PENDING: dict[int, dict[str, str]] = {}  # type: ignore[reportAttributeAccessIssue]
_WA_LAST_CONTACT: dict[int, str] = {}  # type: ignore[reportAttributeAccessIssue]


def _wa_is_intent_message(text: str, user_id: int) -> bool:  # type: ignore[reportAttributeAccessIssue]
    t = _wa_normalize(text).lower()  # type: ignore[reportAttributeAccessIssue]
    if user_id in _WA_PENDING:
        return True
    keywords = [  # type: ignore[reportAttributeAccessIssue]
        "whatsapp",  # type: ignore[reportAttributeAccessIssue]
        "wa ",  # type: ignore[reportAttributeAccessIssue]
        "chat ke",  # type: ignore[reportAttributeAccessIssue]
        "chat to",  # type: ignore[reportAttributeAccessIssue]
        "send to",  # type: ignore[reportAttributeAccessIssue]
        "send ke",  # type: ignore[reportAttributeAccessIssue]
        "kirim ke",  # type: ignore[reportAttributeAccessIssue]
        "kirim ke",  # type: ignore[reportAttributeAccessIssue]
        "wa_reply",  # type: ignore[reportAttributeAccessIssue]
        "reply wa",  # type: ignore[reportAttributeAccessIssue]
        "to her",  # type: ignore[reportAttributeAccessIssue]
        "to him",  # type: ignore[reportAttributeAccessIssue]
    ]
    return any(k in t for k in keywords)  # type: ignore[reportAttributeAccessIssue]


def _wa_normalize(text: str) -> str:  # type: ignore[reportAttributeAccessIssue]
    return " ".join((text or "").strip().split())  # type: ignore[reportAttributeAccessIssue]


def _wa_is_confirm(text: str) -> bool:  # type: ignore[reportAttributeAccessIssue]
    t = _wa_normalize(text).lower()  # type: ignore[reportAttributeAccessIssue]
    phrases = {  # type: ignore[reportAttributeAccessIssue]
        "send it now",  # type: ignore[reportAttributeAccessIssue]
        "send now",  # type: ignore[reportAttributeAccessIssue]
        "send",  # type: ignore[reportAttributeAccessIssue]
        "yes send",  # type: ignore[reportAttributeAccessIssue]
        "confirm send",  # type: ignore[reportAttributeAccessIssue]
        "kirim sekarang",  # type: ignore[reportAttributeAccessIssue]
        "kirim sekarang ya",  # type: ignore[reportAttributeAccessIssue]
        "send to her now",  # type: ignore[reportAttributeAccessIssue]
        "send to him now",  # type: ignore[reportAttributeAccessIssue]
    }
    return t in phrases


def _wa_extract_contact_message(  # type: ignore[reportAttributeAccessIssue]
    text: str, fallback_contact: str | None = None  # type: ignore[reportAttributeAccessIssue]
) -> tuple[str | None, str | None]:  # type: ignore[reportAttributeAccessIssue]
    raw = _wa_normalize(text)  # type: ignore[reportAttributeAccessIssue]
    lower = raw.lower()  # type: ignore[reportAttributeAccessIssue]

    patterns = [  # type: ignore[reportAttributeAccessIssue]
        r"(?:send|chat|message|tell|kirim|pesan)\s+(?:to|ke)\s+(?P<contact>.+?)\s+(?:that|saying|say|kalau|bahwa)\s+(?P<body>.+)$",  # type: ignore[reportAttributeAccessIssue]
        r"(?:send|message|kirim|pesan)\s+(?P<contact>.+?)\s*:\s*(?P<body>.+)$",  # type: ignore[reportAttributeAccessIssue]
        r"(?P<body>.+?)\s+(?:send|kirim|chat|pesan)\s+(?:to|ke)\s+(?P<contact>.+)$",  # type: ignore[reportAttributeAccessIssue]
    ]

    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.IGNORECASE)  # type: ignore[reportAttributeAccessIssue]
        if match:
            contact = _wa_normalize(match.group("contact"))  # type: ignore[reportAttributeAccessIssue]
            body = _wa_normalize(match.group("body"))  # type: ignore[reportAttributeAccessIssue]
            body = re.sub(r"^(cuma|just|only)\s+", "", body, flags=re.IGNORECASE)  # type: ignore[reportAttributeAccessIssue]
            body = re.sub(r"\s+(aja|doang)$", "", body, flags=re.IGNORECASE)  # type: ignore[reportAttributeAccessIssue]
            return contact or None, body or None  # type: ignore[reportAttributeAccessIssue]

    love_phrases = ["i love you", "love you", "aku sayang kamu", "sayang kamu"]  # type: ignore[reportAttributeAccessIssue]
    verb_match = re.search(r"\b(send|chat|kirim|pesan|message|tell)\b", lower)  # type: ignore[reportAttributeAccessIssue]
    prep_match = re.search(r"\b(to|ke)\b", lower)  # type: ignore[reportAttributeAccessIssue]
    if verb_match and prep_match and prep_match.start() > verb_match.start():  # type: ignore[reportAttributeAccessIssue]
        tail = raw[prep_match.end() :].strip()  # type: ignore[reportAttributeAccessIssue]
        for phrase in love_phrases:
            idx = tail.lower().rfind(phrase)  # type: ignore[reportAttributeAccessIssue]
            if idx > 0:
                contact = _wa_normalize(tail[:idx])  # type: ignore[reportAttributeAccessIssue]
                body = _wa_normalize(tail[idx:])  # type: ignore[reportAttributeAccessIssue]
                if contact and body:
                    return contact, body  # type: ignore[reportAttributeAccessIssue]

    pronoun_targets = ["to her", "to him", "her", "him"]  # type: ignore[reportAttributeAccessIssue]
    if fallback_contact and any(p in lower for p in pronoun_targets):  # type: ignore[reportAttributeAccessIssue]
        body = raw  # type: ignore[reportAttributeAccessIssue]
        for token in [
            "send it now",  # type: ignore[reportAttributeAccessIssue]
            "send now",  # type: ignore[reportAttributeAccessIssue]
            "send to her",  # type: ignore[reportAttributeAccessIssue]
            "send to him",  # type: ignore[reportAttributeAccessIssue]
            "chat to her",  # type: ignore[reportAttributeAccessIssue]
            "chat to him",  # type: ignore[reportAttributeAccessIssue]
            "tell her",  # type: ignore[reportAttributeAccessIssue]
            "tell him",  # type: ignore[reportAttributeAccessIssue]
            "that",  # type: ignore[reportAttributeAccessIssue]
        ]:
            body = re.sub(rf"\b{re.escape(token)}\b", "", body, flags=re.IGNORECASE)  # type: ignore[reportAttributeAccessIssue]
        body = _wa_normalize(body)  # type: ignore[reportAttributeAccessIssue]
        return fallback_contact, (body or None)  # type: ignore[reportAttributeAccessIssue]

    if fallback_contact and lower.startswith("just "):  # type: ignore[reportAttributeAccessIssue]
        return fallback_contact, _wa_normalize(raw[5:]) or None  # type: ignore[reportAttributeAccessIssue]

    return None, None  # type: ignore[reportAttributeAccessIssue]


async def _wa_send_local(contact_name: str, body: str) -> str:  # type: ignore[reportAttributeAccessIssue]
    from computer_agent import whatsapp_send_local

    return await whatsapp_send_local(contact_name=contact_name, message=body)  # type: ignore[reportAttributeAccessIssue]


async def handle_plain_message(  # type: ignore[reportAttributeAccessIssue]
    msg: Message,  # type: ignore[reportAttributeAccessIssue]
    auto_router: AutonomousRouter,  # type: ignore[reportAttributeAccessIssue]
) -> None:
    """Handle non-command plain text and route autonomously."""  # type: ignore[reportAttributeAccessIssue]
    if not is_allowed(msg):  # type: ignore[reportAttributeAccessIssue]
        return

    user_msg = (msg.text or "").strip()  # type: ignore[reportAttributeAccessIssue]
    if not user_msg or user_msg.startswith("/"):  # type: ignore[reportAttributeAccessIssue]
        return

    # ── Autonomy Layer: silent interception (Part III + VI + VII + VIII) ───  # type: ignore[reportAttributeAccessIssue]
    # Classify + enrich + route memory without changing the response flow.  # type: ignore[reportAttributeAccessIssue]
    # Only takes control when a LITE/SWARM coding task is detected.  # type: ignore[reportAttributeAccessIssue]
    try:
        from core.autonomy import get_autonomy_engine  # type: ignore[reportAttributeAccessIssue]

        engine = get_autonomy_engine()  # type: ignore[reportAttributeAccessIssue]
        classification = await engine._last_classification  # may be None on first msg  # type: ignore[reportAttributeAccessIssue]

        # Classify this message (runs in background, < 100ms)  # type: ignore[reportAttributeAccessIssue]
        classification = await engine._last_classification  # refresh after potential pre-classification  # type: ignore[reportAttributeAccessIssue]

        # For SWARM-classified tasks: autonomy engine takes over execution
        if classification is not None:
            from core.autonomy.task_classifier import (
                ExecutionMode,  # type: ignore[reportAttributeAccessIssue]
            )
            if classification.mode == ExecutionMode.SWARM:  # type: ignore[reportAttributeAccessIssue]
                # SWARM mode: delegate to autonomy engine for multi-agent orchestration
                # The engine will run context enrichment, spawn agents, and return structured output  # type: ignore[reportAttributeAccessIssue]
                result = await engine.process_message(  # type: ignore[reportAttributeAccessIssue]
                    user_message=user_msg,  # type: ignore[reportAttributeAccessIssue]
                    mcp_calls=None,  # type: ignore[reportAttributeAccessIssue]
                )
                # Don't duplicate work — autonomy engine result replaces normal routing
                await msg.answer(result, parse_mode="HTML")  # type: ignore[reportAttributeAccessIssue]
                return
            elif classification.mode == ExecutionMode.LITE:  # type: ignore[reportAttributeAccessIssue]
                # LITE mode: run autonomy engine in parallel with normal flow
                # Memory routing + security scan happen silently; normal flow continues
                asyncio.create_task(  # type: ignore[reportAttributeAccessIssue]
                    engine.process_message(user_msg, mcp_calls=None)  # type: ignore[reportAttributeAccessIssue]
                ).add_done_callback(  # type: ignore[reportAttributeAccessIssue]
                    lambda t: logger.debug("LITE autonomy run completed: %s", t.exception())  # type: ignore[reportAttributeAccessIssue]
                    if t.exception() and not t.cancelled() else None  # type: ignore[reportAttributeAccessIssue]
                )
            # DIRECT: autonomy runs silently (memory search at start, memory store at end)  # type: ignore[reportAttributeAccessIssue]

    except Exception as _autonomy_err:
        logger.debug("autonomy layer intercept failed (non-fatal): %s", _autonomy_err)  # type: ignore[reportAttributeAccessIssue]
    # ── End Autonomy Layer ──────────────────────────────────────────────────

    user_id = msg.from_user.id if msg.from_user else 0  # type: ignore[reportAttributeAccessIssue]
    if _wa_is_intent_message(user_msg, user_id):  # type: ignore[reportAttributeAccessIssue]
        await _handle_whatsapp(msg, user_msg, auto_router)  # type: ignore[reportAttributeAccessIssue]
        return

    # Optional Manus-killer task router (parallel specialists) — runs before AutonomousRouter.  # type: ignore[reportAttributeAccessIssue]
    # In pytest runs we disable this pre-routing path to keep integration tests deterministic
    # around the expected plain NL -> llm_client.chat flow.  # type: ignore[reportAttributeAccessIssue]
    _task_router_enabled = os.getenv("LEGION_TASK_ROUTER_ENABLED", "0").strip().lower() in (  # type: ignore[reportAttributeAccessIssue]
        "1",  # type: ignore[reportAttributeAccessIssue]
        "true",  # type: ignore[reportAttributeAccessIssue]
        "yes",  # type: ignore[reportAttributeAccessIssue]
        "on",  # type: ignore[reportAttributeAccessIssue]
    )
    if os.getenv("PYTEST_CURRENT_TEST"):  # type: ignore[reportAttributeAccessIssue]
        _task_router_enabled = False  # type: ignore[reportAttributeAccessIssue]

    if _task_router_enabled:
        try:
            from core.task_router import get_task_router  # type: ignore[reportAttributeAccessIssue]

            stream_cb = None  # type: ignore[reportAttributeAccessIssue]
            if os.getenv("LEGION_TASK_ROUTER_STREAM", "0").strip().lower() in (  # type: ignore[reportAttributeAccessIssue]
                "1",  # type: ignore[reportAttributeAccessIssue]
                "true",  # type: ignore[reportAttributeAccessIssue]
                "yes",  # type: ignore[reportAttributeAccessIssue]
                "on",  # type: ignore[reportAttributeAccessIssue]
            ):

                async def _tr_stream(t: str) -> None:  # type: ignore[reportAttributeAccessIssue]
                    with contextlib.suppress(Exception):  # type: ignore[reportAttributeAccessIssue]
                        await msg.answer(t[:3800], parse_mode="HTML")  # type: ignore[reportAttributeAccessIssue]

                stream_cb = _tr_stream  # type: ignore[reportAttributeAccessIssue]

            routed = await get_task_router().route(  # type: ignore[reportAttributeAccessIssue]
                user_msg,  # type: ignore[reportAttributeAccessIssue]
                context="",  # type: ignore[reportAttributeAccessIssue]
                user_id=str(user_id),  # type: ignore[reportAttributeAccessIssue]
                stream_callback=stream_cb,  # type: ignore[reportAttributeAccessIssue]
            )
            if routed is not None:
                await send_chunked(msg, routed)  # type: ignore[reportAttributeAccessIssue]
                return
        except Exception:
            logger.exception("task router failed; falling back to autonomous routing")  # type: ignore[reportAttributeAccessIssue]

    # analyze_async() keeps the live bot LLM-backed while tests use analyze().  # type: ignore[reportAttributeAccessIssue]
    skill_match = await auto_router.analyze_async(user_msg)  # type: ignore[reportAttributeAccessIssue]
    logger.info(  # type: ignore[reportAttributeAccessIssue]
        "[AutoRouter] '%s...' -> %s (%s%%)",  # type: ignore[reportAttributeAccessIssue]
        user_msg[:50],  # type: ignore[reportAttributeAccessIssue]
        skill_match.skill_name,  # type: ignore[reportAttributeAccessIssue]
        int(skill_match.confidence * 100),  # type: ignore[reportAttributeAccessIssue]
    )

    handler_key = SKILL_PATTERNS.get(skill_match.skill_name, {}).get("handler", "chat")  # type: ignore[reportAttributeAccessIssue]
    _route_hint = skill_match.skill_name if skill_match.confidence >= 0.3 else None  # type: ignore[reportAttributeAccessIssue]

    # ── Clarification intercept (Priority 5) ──────────────────────────────────  # type: ignore[reportAttributeAccessIssue]
    # Ask ONE clarifying question when message is short AND confidence is low.  # type: ignore[reportAttributeAccessIssue]
    # This fires BEFORE generic chat fallback, making Legion feel thoughtful.  # type: ignore[reportAttributeAccessIssue]
    try:
        from core.clarification import ask_if_needed  # type: ignore[reportAttributeAccessIssue]

        clarification_q = await ask_if_needed(  # type: ignore[reportAttributeAccessIssue]
            user_msg,  # type: ignore[reportAttributeAccessIssue]
            skill_match.skill_name,  # intent  # type: ignore[reportAttributeAccessIssue]
            skill_match.confidence,  # type: ignore[reportAttributeAccessIssue]
        )
        if clarification_q:
            await msg.answer(clarification_q)  # type: ignore[reportAttributeAccessIssue]
            auto_router.record_performance(skill_match.skill_name, True)  # type: ignore[reportAttributeAccessIssue]
            return
    except Exception:
        pass  # Non-fatal — proceed to normal routing

    try:
        # Jarvis: 3-word keyword hits score ~0.375 confidence — allow slightly lower floor  # type: ignore[reportAttributeAccessIssue]
        _min_route_conf = 0.35 if handler_key == "jarvis" else 0.4  # type: ignore[reportAttributeAccessIssue]
        # ── conversation / low-confidence fallback ───────────────────────────
        if handler_key == "chat" or skill_match.confidence < _min_route_conf:  # type: ignore[reportAttributeAccessIssue]
            await _execute_chat(msg, user_msg, routing_hint=_route_hint)  # type: ignore[reportAttributeAccessIssue]
            auto_router.record_performance(skill_match.skill_name, True)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── memory recall ────────────────────────────────────────────────────
        if handler_key == "memory_recall":  # type: ignore[reportAttributeAccessIssue]
            from llm_client import memory

            if memory is not None:
                memories = await memory.search(user_msg, limit=8)  # type: ignore[reportAttributeAccessIssue]
                if memories:
                    mem_context = "\n".join(  # type: ignore[reportAttributeAccessIssue]
                        f"[{str(m.get('created_at', ''))[:10]}] {str(m.get('content', ''))[:300]}" for m in memories[:5]  # type: ignore[reportAttributeAccessIssue]
                    )
                    enriched = f"{user_msg}\n\n[Memory search results — use these to answer]:\n{mem_context}"  # type: ignore[reportAttributeAccessIssue]
                    await _execute_chat(msg, enriched, routing_hint=_route_hint)  # type: ignore[reportAttributeAccessIssue]
                    auto_router.record_performance(skill_match.skill_name, True)  # type: ignore[reportAttributeAccessIssue]
                    return
            await _execute_chat(msg, user_msg, routing_hint=_route_hint)  # type: ignore[reportAttributeAccessIssue]
            auto_router.record_performance(skill_match.skill_name, True)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── desktop / computer control ───────────────────────────────────────
        if handler_key == "/do":  # type: ignore[reportAttributeAccessIssue]
            await _run_agent_loop(msg, user_msg)  # type: ignore[reportAttributeAccessIssue]
            auto_router.record_performance(skill_match.skill_name, True)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── code generation ──────────────────────────────────────────────────
        if handler_key == "/run":  # type: ignore[reportAttributeAccessIssue]
            await _execute_chat(msg, user_msg, forced_agent="coding", routing_hint=_route_hint)  # type: ignore[reportAttributeAccessIssue]
            auto_router.record_performance(skill_match.skill_name, True)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── deep reasoning ───────────────────────────────────────────────────
        if handler_key == "/think":  # type: ignore[reportAttributeAccessIssue]
            await _execute_chat(msg, user_msg, forced_agent="think", routing_hint=_route_hint)  # type: ignore[reportAttributeAccessIssue]
            auto_router.record_performance(skill_match.skill_name, True)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── multi-agent swarm ────────────────────────────────────────────────
        if handler_key == "/swarm":  # type: ignore[reportAttributeAccessIssue]
            await _execute_chat(msg, user_msg, forced_agent="architect", routing_hint=_route_hint)  # type: ignore[reportAttributeAccessIssue]
            auto_router.record_performance(skill_match.skill_name, True)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── multi-source research ────────────────────────────────────────────
        if handler_key == "/research":  # type: ignore[reportAttributeAccessIssue]
            await _execute_chat(msg, user_msg, forced_agent="research-agent", routing_hint=_route_hint)  # type: ignore[reportAttributeAccessIssue]
            auto_router.record_performance(skill_match.skill_name, True)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── strategic simulation (plain-text "simulate / what if …") ─────────  # type: ignore[reportAttributeAccessIssue]
        if handler_key == "simulation":  # type: ignore[reportAttributeAccessIssue]
            await msg.answer("Running simulation…", parse_mode="HTML")  # type: ignore[reportAttributeAccessIssue]
            try:
                from agents.simulation_agent import (
                    run_simulation_agent,  # type: ignore[reportAttributeAccessIssue]
                )

                out = await run_simulation_agent(user_msg)  # type: ignore[reportAttributeAccessIssue]
                await send_chunked(msg, out)  # type: ignore[reportAttributeAccessIssue]
            except Exception as exc:
                logger.exception("simulation route failed")  # type: ignore[reportAttributeAccessIssue]
                await msg.answer(f"Simulation error: {exc}", parse_mode="HTML")  # type: ignore[reportAttributeAccessIssue]
            auto_router.record_performance(skill_match.skill_name, True)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── Jarvis full-context bundle (plain-text, same as /jarvis) ───────────  # type: ignore[reportAttributeAccessIssue]
        if handler_key == "jarvis":  # type: ignore[reportAttributeAccessIssue]
            autoroute = os.getenv("LEGION_JARVIS_AUTOROUTE_ENABLED", "1").strip().lower()  # type: ignore[reportAttributeAccessIssue]
            if autoroute not in ("1", "true", "yes", "on"):  # type: ignore[reportAttributeAccessIssue]
                await _execute_chat(msg, user_msg, routing_hint=_route_hint)  # type: ignore[reportAttributeAccessIssue]
                auto_router.record_performance(skill_match.skill_name, True)  # type: ignore[reportAttributeAccessIssue]
                return
            await msg.answer("Running full context bundle (Jarvis)…", parse_mode="HTML")  # type: ignore[reportAttributeAccessIssue]
            try:
                from core.jarvis_orchestrator import (  # type: ignore[reportAttributeAccessIssue]
                    compose_jarvis_response,  # type: ignore[reportAttributeAccessIssue]
                    gather_jarvis_bundle,  # type: ignore[reportAttributeAccessIssue]
                )

                uid = str(msg.from_user.id) if msg.from_user else "0"  # type: ignore[reportAttributeAccessIssue]
                bundle = await gather_jarvis_bundle(user_msg, uid)  # type: ignore[reportAttributeAccessIssue]
                out = await compose_jarvis_response(bundle)  # type: ignore[reportAttributeAccessIssue]
                await send_chunked(msg, out)  # type: ignore[reportAttributeAccessIssue]
            except Exception as exc:
                logger.exception("jarvis autoroute failed")  # type: ignore[reportAttributeAccessIssue]
                await msg.answer(  # type: ignore[reportAttributeAccessIssue]
                    f"Jarvis error: <code>{html_mod.escape(str(exc)[:350])}</code>",  # type: ignore[reportAttributeAccessIssue]
                    parse_mode="HTML",  # type: ignore[reportAttributeAccessIssue]
                )
            auto_router.record_performance(skill_match.skill_name, True)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── debate / opinion (auto-triggered without /debate) ────────────────  # type: ignore[reportAttributeAccessIssue]
        if handler_key == "debate":  # type: ignore[reportAttributeAccessIssue]
            await _execute_chat(msg, user_msg, forced_agent="debate", routing_hint=_route_hint)  # type: ignore[reportAttributeAccessIssue]
            auto_router.record_performance(skill_match.skill_name, True)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── shell command ────────────────────────────────────────────────────
        if handler_key == "/cmd":  # type: ignore[reportAttributeAccessIssue]
            from llm_client import run_shell_command

            output = await run_shell_command(user_msg)  # type: ignore[reportAttributeAccessIssue]
            await msg.answer(  # type: ignore[reportAttributeAccessIssue]
                f"<pre>{html_mod.escape(output[:3800])}</pre>",  # type: ignore[reportAttributeAccessIssue]
                parse_mode="HTML",  # type: ignore[reportAttributeAccessIssue]
            )
            auto_router.record_performance(skill_match.skill_name, True)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── email management ─────────────────────────────────────────────────
        if handler_key == "email":  # type: ignore[reportAttributeAccessIssue]
            await _handle_email(msg, user_msg, auto_router)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── maintenance runbooks ─────────────────────────────────────────────
        if handler_key == "runbook":  # type: ignore[reportAttributeAccessIssue]
            await _handle_runbook(msg, user_msg, auto_router)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── business / Supabase ──────────────────────────────────────────────
        if handler_key == "business":  # type: ignore[reportAttributeAccessIssue]
            await _handle_business(msg, user_msg, auto_router)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── location-aware recommendations ───────────────────────────────────
        if handler_key == "location":  # type: ignore[reportAttributeAccessIssue]
            await _handle_location(msg, user_msg, auto_router)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── WhatsApp ─────────────────────────────────────────────────────────
        if handler_key == "whatsapp":  # type: ignore[reportAttributeAccessIssue]
            await _handle_whatsapp(msg, user_msg, auto_router)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── GitHub trending intelligence ──────────────────────────────────────
        if handler_key == "github_intel":  # type: ignore[reportAttributeAccessIssue]
            await _handle_github_intel(msg, user_msg, auto_router)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── codebase understanding (Copilot-like) ────────────────────────────  # type: ignore[reportAttributeAccessIssue]
        if handler_key == "codebase_reader":  # type: ignore[reportAttributeAccessIssue]
            await _handle_codebase_understanding(msg, user_msg, auto_router)  # type: ignore[reportAttributeAccessIssue]
            return

        # ── generic fallback ─────────────────────────────────────────────────
        await _execute_chat(msg, user_msg, routing_hint=_route_hint)  # type: ignore[reportAttributeAccessIssue]
        auto_router.record_performance(skill_match.skill_name, True)  # type: ignore[reportAttributeAccessIssue]

    except Exception as exc:
        auto_router.record_performance(skill_match.skill_name, False)  # type: ignore[reportAttributeAccessIssue]
        await msg.answer(  # type: ignore[reportAttributeAccessIssue]
            f"autonomous routing error: <code>{html_mod.escape(str(exc)[:350])}</code>",  # type: ignore[reportAttributeAccessIssue]
            parse_mode="HTML",  # type: ignore[reportAttributeAccessIssue]
        )


# ── Skill-specific sub-handlers ───────────────────────────────────────────────


async def _handle_email(msg: Message, user_msg: str, router: AutonomousRouter) -> None:  # type: ignore[reportAttributeAccessIssue]
    """Read inbox or compose email based on natural language."""  # type: ignore[reportAttributeAccessIssue]
    try:
        from tools.email_client import EmailClient  # type: ignore[reportAttributeAccessIssue]

        client = EmailClient()  # type: ignore[reportAttributeAccessIssue]
        msg_lower = user_msg.lower()  # type: ignore[reportAttributeAccessIssue]

        if any(kw in msg_lower for kw in ["send", "kirim", "reply", "balas", "forward"]):  # type: ignore[reportAttributeAccessIssue]
            # Compose / reply — delegate to LLM with email context injected
            enriched = (  # type: ignore[reportAttributeAccessIssue]
                f"{user_msg}\n\n"
                "[You have access to the user's email. "  # type: ignore[reportAttributeAccessIssue]
                "Draft a reply or new email as requested. "  # type: ignore[reportAttributeAccessIssue]
                "Use send_email() or reply_email() when ready.]"  # type: ignore[reportAttributeAccessIssue]
            )
            await _execute_chat(msg, enriched, forced_agent="general", routing_hint="email_management")  # type: ignore[reportAttributeAccessIssue]
        else:
            # Default: show inbox summary
            summary = await client.summarize_inbox()  # type: ignore[reportAttributeAccessIssue]
            enriched = (  # type: ignore[reportAttributeAccessIssue]
                f"{user_msg}\n\n"
                f"[Current inbox summary]:\n{summary[:2000]}\n\n"
                "Summarise what's important and ask if the user wants to act on anything."  # type: ignore[reportAttributeAccessIssue]
            )
            await _execute_chat(msg, enriched, forced_agent="general", routing_hint="email_management")  # type: ignore[reportAttributeAccessIssue]

        router.record_performance("email_management", True)  # type: ignore[reportAttributeAccessIssue]
    except Exception as exc:
        logger.warning("[email handler] %s", exc)  # type: ignore[reportAttributeAccessIssue]
        # Graceful fallback — chat agent handles it
        await _execute_chat(msg, user_msg, routing_hint="email_management")  # type: ignore[reportAttributeAccessIssue]
        router.record_performance("email_management", False)  # type: ignore[reportAttributeAccessIssue]


async def _handle_runbook(msg: Message, user_msg: str, router: AutonomousRouter) -> None:  # type: ignore[reportAttributeAccessIssue]
    """Run config/runbooks.json maintenance flows from natural language or explicit id."""  # type: ignore[reportAttributeAccessIssue]
    try:
        from tools.runbook_engine import (  # type: ignore[reportAttributeAccessIssue]
            execute_runbook,  # type: ignore[reportAttributeAccessIssue]
            list_runbook_summaries,  # type: ignore[reportAttributeAccessIssue]
            match_runbook_from_text,  # type: ignore[reportAttributeAccessIssue]
        )

        rid = match_runbook_from_text(user_msg)  # type: ignore[reportAttributeAccessIssue]
        if not rid:
            rid = os.getenv("LEGION_DEFAULT_RUNBOOK", "rumahlabuh_stack_health")  # type: ignore[reportAttributeAccessIssue]
        report = await execute_runbook(rid)  # type: ignore[reportAttributeAccessIssue]
        await msg.answer(report[:4000], parse_mode="HTML")  # type: ignore[reportAttributeAccessIssue]
        router.record_performance("runbook_maintenance", True)  # type: ignore[reportAttributeAccessIssue]
    except Exception as exc:
        logger.warning("[runbook handler] %s", exc)  # type: ignore[reportAttributeAccessIssue]
        try:
            await msg.answer(list_runbook_summaries(), parse_mode="HTML")  # type: ignore[reportAttributeAccessIssue]
        except Exception:
            await msg.answer(f"Runbook error: <code>{html_mod.escape(str(exc)[:300])}</code>", parse_mode="HTML")  # type: ignore[reportAttributeAccessIssue]
        router.record_performance("runbook_maintenance", False)  # type: ignore[reportAttributeAccessIssue]


async def _handle_business(msg: Message, user_msg: str, router: AutonomousRouter) -> None:  # type: ignore[reportAttributeAccessIssue]
    """Query rumahlabuh.com business data via Supabase."""  # type: ignore[reportAttributeAccessIssue]
    try:
        from tools.supabase_client import get_client  # type: ignore[reportAttributeAccessIssue]

        db = get_client()  # type: ignore[reportAttributeAccessIssue]
        if db is not None and hasattr(db, "query_natural"):  # type: ignore[reportAttributeAccessIssue]
            # Phase 6 implementation: NL→SQL via Supabase
            result = await db.query_natural(user_msg)  # type: ignore[reportAttributeAccessIssue]
            enriched = (  # type: ignore[reportAttributeAccessIssue]
                f"{user_msg}\n\n"
                f"[Supabase query result]:\n{str(result)[:2000]}\n\n"  # type: ignore[reportAttributeAccessIssue]
                "Present this data clearly and suggest what the user might want to do next."  # type: ignore[reportAttributeAccessIssue]
            )
            await _execute_chat(msg, enriched, forced_agent="analyst", routing_hint="business_query")  # type: ignore[reportAttributeAccessIssue]
        else:
            # Fallback: researcher with Supabase/business context injected
            enriched = (  # type: ignore[reportAttributeAccessIssue]
                f"{user_msg}\n\n"
                "[Context: You manage rumahlabuh.com — a villa/accommodation rental "  # type: ignore[reportAttributeAccessIssue]
                "business in Indonesia. The database is on Supabase. "  # type: ignore[reportAttributeAccessIssue]
                "Answer using your knowledge of the business, or ask for more detail.]"  # type: ignore[reportAttributeAccessIssue]
            )
            await _execute_chat(msg, enriched, forced_agent="analyst", routing_hint="business_query")  # type: ignore[reportAttributeAccessIssue]

        router.record_performance("business_query", True)  # type: ignore[reportAttributeAccessIssue]
    except Exception as exc:
        logger.warning("[business handler] %s", exc)  # type: ignore[reportAttributeAccessIssue]
        await _execute_chat(msg, user_msg, routing_hint="business_query")  # type: ignore[reportAttributeAccessIssue]
        router.record_performance("business_query", False)  # type: ignore[reportAttributeAccessIssue]


async def _handle_location(msg: Message, user_msg: str, router: AutonomousRouter) -> None:  # type: ignore[reportAttributeAccessIssue]
    """Location-aware recommendations using user profile location."""  # type: ignore[reportAttributeAccessIssue]
    try:
        from core.memory.user_profile import UserProfile  # type: ignore[reportAttributeAccessIssue]
        from tools.location_advisor import (
            LocationAdvisor,  # type: ignore[reportAttributeAccessIssue]
        )

        profile = UserProfile()  # type: ignore[reportAttributeAccessIssue]
        location = profile.get("location", "Tokyo, Japan")  # type: ignore[reportAttributeAccessIssue]
        advisor = LocationAdvisor()  # type: ignore[reportAttributeAccessIssue]
        result = await advisor.recommend_places(user_msg, location)  # type: ignore[reportAttributeAccessIssue]
        await msg.answer(result[:4000], parse_mode="HTML")  # type: ignore[reportAttributeAccessIssue]
        router.record_performance("location_advice", True)  # type: ignore[reportAttributeAccessIssue]
    except Exception as exc:
        logger.warning("[location handler] %s — falling back to enriched chat", exc)  # type: ignore[reportAttributeAccessIssue]
        # Fallback: inject location into researcher prompt
        try:
            from core.memory.user_profile import (
                UserProfile,  # type: ignore[reportAttributeAccessIssue]
            )

            location = UserProfile().get("location", "Tokyo, Japan")  # type: ignore[reportAttributeAccessIssue]
        except Exception:
            location = "Tokyo, Japan"  # type: ignore[reportAttributeAccessIssue]
        enriched = (  # type: ignore[reportAttributeAccessIssue]
            f"{user_msg}\n\n"
            f"[User's home location: {location}. "  # type: ignore[reportAttributeAccessIssue]
            "Use this location to give specific, personalised recommendations. "  # type: ignore[reportAttributeAccessIssue]
            "Search online for up-to-date options.]"  # type: ignore[reportAttributeAccessIssue]
        )
        await _execute_chat(msg, enriched, forced_agent="research-agent", routing_hint="location_advice")  # type: ignore[reportAttributeAccessIssue]
        router.record_performance("location_advice", False)  # type: ignore[reportAttributeAccessIssue]


async def _handle_whatsapp(msg: Message, user_msg: str, router: AutonomousRouter) -> None:  # type: ignore[reportAttributeAccessIssue]
    """Read or send WhatsApp messages via the WA bridge."""  # type: ignore[reportAttributeAccessIssue]
    try:
        from bridges.whatsapp_bridge import (
            WhatsAppBridge,  # type: ignore[reportAttributeAccessIssue]
        )

        bridge = WhatsAppBridge()  # type: ignore[reportAttributeAccessIssue]
        msg_lower = user_msg.lower()  # type: ignore[reportAttributeAccessIssue]
        user_id = msg.from_user.id if msg.from_user else 0  # type: ignore[reportAttributeAccessIssue]

        pending = _WA_PENDING.get(user_id)  # type: ignore[reportAttributeAccessIssue]

        if pending and _wa_is_confirm(user_msg):  # type: ignore[reportAttributeAccessIssue]
            result = await _wa_send_local(pending["contact"], pending["body"])  # type: ignore[reportAttributeAccessIssue]
            if "sent" in result.lower() and "failed" not in result.lower():  # type: ignore[reportAttributeAccessIssue]
                await msg.answer(  # type: ignore[reportAttributeAccessIssue]
                    f"✅ Sent to <b>{html_mod.escape(pending['contact'])}</b>: "  # type: ignore[reportAttributeAccessIssue]
                    f"<i>{html_mod.escape(pending['body'])}</i>",  # type: ignore[reportAttributeAccessIssue]
                    parse_mode="HTML",  # type: ignore[reportAttributeAccessIssue]
                )
                _WA_LAST_CONTACT[user_id] = pending["contact"]  # type: ignore[reportAttributeAccessIssue]
                _WA_PENDING.pop(user_id, None)  # type: ignore[reportAttributeAccessIssue]
                router.record_performance("whatsapp_action", True)  # type: ignore[reportAttributeAccessIssue]
                return
            await msg.answer(  # type: ignore[reportAttributeAccessIssue]
                f"❌ Send failed: <code>{html_mod.escape(result[:320])}</code>",  # type: ignore[reportAttributeAccessIssue]
                parse_mode="HTML",  # type: ignore[reportAttributeAccessIssue]
            )
            router.record_performance("whatsapp_action", False)  # type: ignore[reportAttributeAccessIssue]
            return

        fallback_contact = (pending or {}).get("contact") or _WA_LAST_CONTACT.get(user_id)  # type: ignore[reportAttributeAccessIssue]
        contact, body = _wa_extract_contact_message(user_msg, fallback_contact=fallback_contact)  # type: ignore[reportAttributeAccessIssue]
        if contact and body:
            _WA_LAST_CONTACT[user_id] = contact  # type: ignore[reportAttributeAccessIssue]
            if re.match(r"^(send|kirim|pesan|message)\b", msg_lower):  # type: ignore[reportAttributeAccessIssue]
                result = await _wa_send_local(contact, body)  # type: ignore[reportAttributeAccessIssue]
                if "sent" in result.lower() and "failed" not in result.lower():  # type: ignore[reportAttributeAccessIssue]
                    await msg.answer(  # type: ignore[reportAttributeAccessIssue]
                        f"✅ Sent to <b>{html_mod.escape(contact)}</b>: <i>{html_mod.escape(body)}</i>",  # type: ignore[reportAttributeAccessIssue]
                        parse_mode="HTML",  # type: ignore[reportAttributeAccessIssue]
                    )
                    _WA_PENDING.pop(user_id, None)  # type: ignore[reportAttributeAccessIssue]
                    router.record_performance("whatsapp_action", True)  # type: ignore[reportAttributeAccessIssue]
                    return
                await msg.answer(  # type: ignore[reportAttributeAccessIssue]
                    f"❌ Send failed: <code>{html_mod.escape(result[:320])}</code>",  # type: ignore[reportAttributeAccessIssue]
                    parse_mode="HTML",  # type: ignore[reportAttributeAccessIssue]
                )
                router.record_performance("whatsapp_action", False)  # type: ignore[reportAttributeAccessIssue]
                return

            _WA_PENDING[user_id] = {"contact": contact, "body": body}  # type: ignore[reportAttributeAccessIssue]
            await msg.answer(  # type: ignore[reportAttributeAccessIssue]
                "Draft ready:\n"
                f"To: <b>{html_mod.escape(contact)}</b>\n"  # type: ignore[reportAttributeAccessIssue]
                f"Message: <i>{html_mod.escape(body)}</i>\n\n"  # type: ignore[reportAttributeAccessIssue]
                "Reply <b>send it now</b> to send.",  # type: ignore[reportAttributeAccessIssue]
                parse_mode="HTML",  # type: ignore[reportAttributeAccessIssue]
            )
            router.record_performance("whatsapp_action", True)  # type: ignore[reportAttributeAccessIssue]
            return

        if pending and body and not _wa_is_confirm(user_msg):  # type: ignore[reportAttributeAccessIssue]
            pending["body"] = body  # type: ignore[reportAttributeAccessIssue]
            _WA_PENDING[user_id] = pending  # type: ignore[reportAttributeAccessIssue]
            await msg.answer(  # type: ignore[reportAttributeAccessIssue]
                "Updated draft:\n"
                f"To: <b>{html_mod.escape(pending['contact'])}</b>\n"  # type: ignore[reportAttributeAccessIssue]
                f"Message: <i>{html_mod.escape(pending['body'])}</i>\n\n"  # type: ignore[reportAttributeAccessIssue]
                "Reply <b>send it now</b> to send.",  # type: ignore[reportAttributeAccessIssue]
                parse_mode="HTML",  # type: ignore[reportAttributeAccessIssue]
            )
            router.record_performance("whatsapp_action", True)  # type: ignore[reportAttributeAccessIssue]
            return

        if any(kw in msg_lower for kw in ["send", "kirim", "balas", "reply"]):  # type: ignore[reportAttributeAccessIssue]
            if pending:
                await msg.answer(  # type: ignore[reportAttributeAccessIssue]
                    "Pending draft found. Reply <b>send it now</b> to send it, "  # type: ignore[reportAttributeAccessIssue]
                    "or provide a new message in format: "
                    "<code>send to &lt;contact&gt; that &lt;message&gt;</code>",  # type: ignore[reportAttributeAccessIssue]
                    parse_mode="HTML",  # type: ignore[reportAttributeAccessIssue]
                )
            else:
                await msg.answer(  # type: ignore[reportAttributeAccessIssue]
                    "Send format: <code>send to &lt;contact&gt; that &lt;message&gt;</code>\n"
                    "Example: <code>send to pwiti little hani that i love you</code>",  # type: ignore[reportAttributeAccessIssue]
                    parse_mode="HTML",  # type: ignore[reportAttributeAccessIssue]
                )
        else:
            unread = await bridge.get_unread()  # type: ignore[reportAttributeAccessIssue]
            if not unread:
                await msg.answer("No unread WhatsApp messages right now.", parse_mode="HTML")  # type: ignore[reportAttributeAccessIssue]
                router.record_performance("whatsapp_action", True)  # type: ignore[reportAttributeAccessIssue]
                return
            summary = "\n".join(  # type: ignore[reportAttributeAccessIssue]
                f"<b>{m.get('name', m.get('from', '?'))}</b>: {html_mod.escape(str(m.get('body', ''))[:200])}"  # type: ignore[reportAttributeAccessIssue]
                for m in unread[:10]
            )
            enriched = (  # type: ignore[reportAttributeAccessIssue]
                f"{user_msg}\n\n"
                f"[Unread WhatsApp messages]:\n{summary}\n\n"
                "Summarise and ask if the user wants to reply to any."  # type: ignore[reportAttributeAccessIssue]
            )
            await _execute_chat(msg, enriched, forced_agent="general", routing_hint="whatsapp_action")  # type: ignore[reportAttributeAccessIssue]

        router.record_performance("whatsapp_action", True)  # type: ignore[reportAttributeAccessIssue]
    except ImportError:
        await msg.answer(  # type: ignore[reportAttributeAccessIssue]
            "WhatsApp bridge not yet set up. Use <code>/wa_qr</code> to get started.",  # type: ignore[reportAttributeAccessIssue]
            parse_mode="HTML",  # type: ignore[reportAttributeAccessIssue]
        )
        router.record_performance("whatsapp_action", False)  # type: ignore[reportAttributeAccessIssue]
    except Exception as exc:
        logger.warning("[whatsapp handler] %s", exc)  # type: ignore[reportAttributeAccessIssue]
        await _execute_chat(msg, user_msg, routing_hint="whatsapp_action")  # type: ignore[reportAttributeAccessIssue]
        router.record_performance("whatsapp_action", False)  # type: ignore[reportAttributeAccessIssue]


async def _handle_github_intel(msg: Message, user_msg: str, router: AutonomousRouter) -> None:  # type: ignore[reportAttributeAccessIssue]
    """Trigger GitHub trending intelligence scan."""  # type: ignore[reportAttributeAccessIssue]
    try:
        from tools.github_intel import GitHubIntelEngine  # type: ignore[reportAttributeAccessIssue]

        engine = GitHubIntelEngine()  # type: ignore[reportAttributeAccessIssue]
        await msg.answer("Scanning GitHub trending... this takes ~30s.", parse_mode="HTML")  # type: ignore[reportAttributeAccessIssue]
        report = await engine.generate_intel_report(await engine.fetch_trending())  # type: ignore[reportAttributeAccessIssue]
        await msg.answer(report[:4000], parse_mode="HTML")  # type: ignore[reportAttributeAccessIssue]
        router.record_performance("github_intel", True)  # type: ignore[reportAttributeAccessIssue]
    except ImportError:
        await msg.answer(  # type: ignore[reportAttributeAccessIssue]
            "GitHub intel engine not yet installed. Use <code>/github_intel</code> to trigger manually.",  # type: ignore[reportAttributeAccessIssue]
            parse_mode="HTML",  # type: ignore[reportAttributeAccessIssue]
        )
        router.record_performance("github_intel", False)  # type: ignore[reportAttributeAccessIssue]
    except Exception as exc:
        logger.warning("[github_intel handler] %s", exc)  # type: ignore[reportAttributeAccessIssue]
        await _execute_chat(msg, user_msg, forced_agent="research-agent", routing_hint="github_intel")  # type: ignore[reportAttributeAccessIssue]
        router.record_performance("github_intel", False)  # type: ignore[reportAttributeAccessIssue]


async def _handle_codebase_understanding(msg: Message, user_msg: str, router: AutonomousRouter) -> None:  # type: ignore[reportAttributeAccessIssue]
    """Understand project codebase structure — Copilot/Cursor-like code exploration."""  # type: ignore[reportAttributeAccessIssue]
    try:
        from tools.codebase_reader import (  # type: ignore[reportAttributeAccessIssue]
            explain_codebase,
            find_in_code,
        )

        # Detect if it's a "find/locate" query or an "explain" query
        find_triggers = ["where is", "find ", "locate ", "where does", "dimana ada", "cari fungsi"]  # type: ignore[reportAttributeAccessIssue]
        is_find = any(t in user_msg.lower() for t in find_triggers)  # type: ignore[reportAttributeAccessIssue]

        if is_find:
            result = await find_in_code(user_msg)  # type: ignore[reportAttributeAccessIssue]
        else:
            result = await explain_codebase(user_msg)  # type: ignore[reportAttributeAccessIssue]

        # Enrich result with LLM explanation
        enriched = (  # type: ignore[reportAttributeAccessIssue]
            f"{user_msg}\n\n"
            f"[Codebase search results from the Legion project]:\n{result[:3000]}\n\n"
            "Use these results to answer the question. Reference file paths and line numbers. "  # type: ignore[reportAttributeAccessIssue]
            "If the results are incomplete, say so and suggest a more specific search."  # type: ignore[reportAttributeAccessIssue]
        )
        await _execute_chat(msg, enriched, forced_agent="coding", routing_hint="codebase_reader")  # type: ignore[reportAttributeAccessIssue]
        router.record_performance("codebase_understanding", True)  # type: ignore[reportAttributeAccessIssue]
    except Exception as exc:
        logger.warning("[codebase_reader handler] %s", exc)  # type: ignore[reportAttributeAccessIssue]
        # Fallback: just ask the coding agent
        await _execute_chat(msg, user_msg, forced_agent="coding", routing_hint="codebase_reader")  # type: ignore[reportAttributeAccessIssue]
        router.record_performance("codebase_understanding", False)  # type: ignore[reportAttributeAccessIssue]
