"""Memory and self-awareness commands for Legion v6."""

from __future__ import annotations

from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from .shared import is_allowed

router = Router()


@router.message(Command("memory"))
async def cmd_memory_stats(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from llm_client import memory

    if memory is None:
        await msg.answer("memory system is not initialized yet.")
        return

    stats = memory.get_memory_stats()
    core_facts = memory.core.all()

    lines = [
        "<b>🧠 Legion's Memory</b>",
        "",
        f"<b>Archival:</b> {stats['archival_total']} memories stored",
        f"<b>Core:</b> {stats['core_keys']} high-priority facts",
        f"<b>Known facts about you:</b> {stats['profile_facts']}",
        f"<b>Observed patterns:</b> {stats['profile_patterns']}",
        "",
    ]
    if core_facts:
        lines.append("<b>Core memory right now:</b>")
        for key, value in list(core_facts.items())[:5]:
            lines.append(f"  • {key}: {value[:80]}")

    await msg.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("remember"))
async def cmd_remember(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from llm_client import memory

    text = (msg.text or "").removeprefix("/remember").strip()
    if not text:
        await msg.answer("Usage: /remember <what to remember>")
        return
    if memory is None:
        await msg.answer("memory system is not initialized yet.")
        return

    mem_id = await memory.save(
        content=text,
        summary=f"User explicitly asked to remember: {text[:100]}",
        tags=["explicit", "user-request"],
        importance=0.95,
        source="user-explicit",
    )
    memory.core.set(f"explicit_{mem_id}", text[:200])
    memory.profile.add_known_fact(text[:200])
    try:
        from tools.mem0_client import mem0_add

        await mem0_add(user_id=str(msg.from_user.id), content=text, metadata={"source": "explicit", "memory_id": mem_id})
    except Exception:
        pass
    await msg.answer("Got it. That's saved permanently — I won't forget.")


@router.message(Command("recall"))
async def cmd_recall(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from llm_client import memory

    query = (msg.text or "").removeprefix("/recall").strip()
    if not query:
        await msg.answer("Usage: /recall <what to search for>")
        return
    if memory is None:
        await msg.answer("memory system is not initialized yet.")
        return

    results = await memory.search(query, limit=6)
    try:
        from tools.mem0_client import mem0_search, build_mem0_context

        mem0_results = await mem0_search(user_id=str(msg.from_user.id), query=query, limit=8)
        mem0_ctx = build_mem0_context(mem0_results, query=query)
    except Exception:
        mem0_results = []
        mem0_ctx = ""
    if not results:
        if mem0_ctx:
            await msg.answer(mem0_ctx, parse_mode="HTML")
            return
        await msg.answer("Nothing found in memory for that.")
        return

    lines = [f"<b>🔍 Memory search: '{query}'</b>", ""]
    for item in results:
        date = str(item.get("created_at", ""))[:10]
        content = str(item.get("content", ""))[:200]
        lines.append(f"<b>[{date}]</b> {content}")
        lines.append("")

    if mem0_ctx:
        lines.append("<b>Mem0 context</b>")
        lines.append(mem0_ctx)

    await msg.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("emotion"))
async def cmd_emotion(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from core.emotion_modulator import get_emotion_profile
    from tools.letta_personality import get_persona_state

    state = get_persona_state()
    emotion_name = state.get("dominant_emotion", "neutral")
    profile = get_emotion_profile(str(emotion_name))
    events = state.get("recent_emotional_events", []) or []
    events_text = "\n".join(
        f"• {item.get('emotion', 'neutral')}: {item.get('event', '')}" for item in events[:3] if isinstance(item, dict)
    ) or "• none"
    await msg.answer(
        (
            f"<b>🧠 Legion Emotional State</b>\n\n"
            f"Emotion: <code>{emotion_name}</code>\n"
            f"Energy: <code>{state.get('energy_level', 'high')}</code>\n"
            f"Mood: <code>{state.get('mood_notes', '—')}</code>\n"
            f"Tone: <code>{profile.tone}</code> | Length: <code>{profile.length_bias}</code>\n"
            f"Directness: <code>{profile.directness:.0%}</code> | Enthusiasm: <code>{profile.enthusiasm:.0%}</code>\n\n"
            f"<b>Recent emotional events</b>\n<pre>{events_text}</pre>"
        ),
        parse_mode="HTML",
    )


@router.message(Command("opinions"))
async def cmd_opinions(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from llm_client import reflection

    if reflection is None:
        await msg.answer("reflection engine is not initialized yet.")
        return

    opinions_block = reflection.get_opinions_block()
    if not opinions_block:
        await msg.answer("I haven't formed strong opinions yet. Give me more conversations.")
        return
    await msg.answer(f"<b>🧠 What I currently think</b>\n\n<pre>{opinions_block}</pre>", parse_mode="HTML")


@router.message(Command("forget"))
async def cmd_forget(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from llm_client import memory

    key = (msg.text or "").removeprefix("/forget").strip()
    if not key:
        await msg.answer("Usage: /forget <core memory key>")
        return
    if memory is None:
        await msg.answer("memory system is not initialized yet.")
        return

    memory.core.delete(key)
    await msg.answer(f"Removed '{key}' from core memory.")


@router.message(Command("profile"))
async def cmd_profile(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from llm_client import memory

    if memory is None:
        await msg.answer("memory system is not initialized yet.")
        return

    block = memory.profile.to_prompt_block()
    await msg.answer(
        f"<b>👤 Your Profile (what I know about you)</b>\n\n<pre>{block}</pre>",
        parse_mode="HTML",
    )


@router.message(Command("teach"))
async def cmd_teach(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from llm_client import memory, reflection

    text = (msg.text or "").removeprefix("/teach").strip()
    if not text:
        await msg.answer("Usage: /teach <correct me about something>")
        return
    if memory is None:
        await msg.answer("memory system is not initialized yet.")
        return

    memory.profile.add_known_fact(text)
    await memory.save(
        content=f"User corrected/taught: {text}",
        tags=["user-correction", "explicit-teaching"],
        importance=0.95,
        source="user-teach",
    )
    if reflection is not None:
        reflection._opinions["lessons"].append(
            f"[{datetime.now():%Y-%m-%d}] User taught me: {text}"
        )
        reflection._save_opinions()
    await msg.answer("Got it — updating my understanding. I'll factor that in going forward.")
