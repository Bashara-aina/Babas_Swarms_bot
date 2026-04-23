"""
Persona handler — manage Legion's personality and emotion state.
Commands: /persona, /mood, /persona_reset, /persona_note
"""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)
router = Router(name="persona")


@router.message(Command("persona"))
async def cmd_persona(message: Message) -> None:
    """Show Legion's current personality state."""
    try:
        from tools.letta_personality import load_persona
        state = load_persona()
        em = state["emotion"]
        rel = state["relationship"]
        ocean = state["ocean"]
        notes = state.get("personality_notes", [])
        text = (
            f"<b>🧠 Legion Persona State</b>\n\n"
            f"Mood: <b>{em['current_mood']}</b> "
            f"(valence={em['valence']:.2f}, arousal={em['arousal']:.2f})\n"
            f"OCEAN: O={ocean['openness']:.2f} C={ocean['conscientiousness']:.2f} "
            f"E={ocean['extraversion']:.2f} A={ocean['agreeableness']:.2f} N={ocean['neuroticism']:.2f}\n"
            f"Trust: {rel['trust_level']:.2f} | Familiarity: {rel['familiarity']:.2f}\n"
            f"Total interactions: {rel['interactions_total']}\n\n"
            f"<b>Personality notes:</b>\n"
        )
        if notes:
            text += "\n".join(f"• {n}" for n in notes[-10:])
        else:
            text += "(none yet)"
        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Persona error: {e}")


@router.message(Command("mood"))
async def cmd_mood(message: Message) -> None:
    """Show or manually set mood. Usage: /mood [excited|content|neutral|frustrated|melancholy]"""
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        from tools.letta_personality import load_persona
        state = load_persona()
        mood = state["emotion"]["current_mood"]
        await message.answer(f"Current mood: <b>{mood}</b>", parse_mode="HTML")
        return
    target_mood = args[1].strip().lower()
    valid = {"excited", "content", "neutral", "frustrated", "melancholy"}
    if target_mood not in valid:
        await message.answer(f"Valid moods: {', '.join(sorted(valid))}")
        return
    try:
        from tools.letta_personality import load_persona, save_persona
        state = load_persona()
        state["emotion"]["current_mood"] = target_mood
        save_persona(state)
        await message.answer(f"Mood set to <b>{target_mood}</b>", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ {e}")


@router.message(Command("persona_reset"))
async def cmd_persona_reset(message: Message) -> None:
    """Reset persona to defaults."""
    try:
        import copy

        from tools.letta_personality import DEFAULT_PERSONA, save_persona
        save_persona(copy.deepcopy(DEFAULT_PERSONA))
        await message.answer("✅ Persona reset to defaults.")
    except Exception as e:
        await message.answer(f"❌ {e}")


@router.message(Command("persona_note"))
async def cmd_persona_note(message: Message) -> None:
    """Add a personality note. Usage: /persona_note Bashara prefers concise answers"""
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: /persona_note <note about Bashara's preferences>")
        return
    note = args[1].strip()
    try:
        from tools.letta_personality import add_personality_note
        add_personality_note(note)
        await message.answer(f"✅ Noted: {note}")
    except Exception as e:
        await message.answer(f"❌ {e}")
