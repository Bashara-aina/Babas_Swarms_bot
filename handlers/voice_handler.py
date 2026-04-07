"""
Voice handler — Phase 7.
Receives Telegram voice notes → transcribes → LLM → replies with voice.
Commands: /voice_on, /voice_off, /voice_status
"""
from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, Voice, BufferedInputFile

logger = logging.getLogger(__name__)
router = Router(name="voice")

_voice_enabled: bool = True


@router.message(Command("voice_on"))
async def cmd_voice_on(message: Message) -> None:
    global _voice_enabled
    _voice_enabled = True
    await message.answer("🎙️ Voice mode ON — send voice notes and I'll reply with audio.")


@router.message(Command("voice_off"))
async def cmd_voice_off(message: Message) -> None:
    global _voice_enabled
    _voice_enabled = False
    await message.answer("🔇 Voice mode OFF — text only.")


@router.message(Command("voice_status"))
async def cmd_voice_status(message: Message) -> None:
    status = "ON" if _voice_enabled else "OFF"
    await message.answer(f"Voice mode: {status}")


@router.message(F.voice)
async def handle_voice_note(message: Message) -> None:
    """Transcribe incoming voice note, run through LLM, reply with voice."""
    if not _voice_enabled:
        await message.answer("(Voice mode is off — use /voice_on to enable)")
        return

    status_msg = await message.answer("🎙️ Transcribing...")
    try:
        from tools.voice_engine import transcribe_voice, synthesize_speech
        from llm_client import chat

        # Download voice file
        voice: Voice = message.voice
        file_info = await message.bot.get_file(voice.file_id)
        voice_bytes = await message.bot.download_file(file_info.file_path)
        audio_bytes = voice_bytes.read()

        # Transcribe
        text = await transcribe_voice(audio_bytes, file_ext="ogg")
        if not text:
            await status_msg.edit_text("❌ Could not transcribe voice note.")
            return

        await status_msg.edit_text(f"📝 Heard: {text[:200]}\n⏳ Thinking...")

        # LLM
        user_id = message.from_user.id if message.from_user else 0
        response_text = await chat(
            task=text,
            user_id=user_id,
            agent_name="general",
        )

        # Synthesize reply
        audio_out = await synthesize_speech(response_text)
        if audio_out:
            await status_msg.delete()
            await message.answer_voice(
                BufferedInputFile(audio_out, filename="legion_reply.wav"),
                caption=f"💬 {response_text[:300]}",
            )
        else:
            await status_msg.edit_text(response_text)

    except Exception as e:
        logger.error("voice handler error: %s", e)
        await status_msg.edit_text(f"❌ Voice error: {e}")
