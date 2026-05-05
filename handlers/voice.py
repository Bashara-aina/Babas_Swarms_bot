"""Voice message handler — transcribes audio and optionally replies with TTS.

Commands (merged from voice_handler.py):
  /voice_on      — enable voice reply mode
  /voice_off     — disable voice reply mode
  /voice_status  — show current voice mode state
  /voice_toggle  — toggle voice reply (legacy alias)
      /vcsearch      — search voice message transcripts

Handles:
  F.voice  — voice note messages (transcribe → LLM → optional TTS reply)
  F.audio  — audio file uploads (same pipeline)
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import tempfile

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from handlers.shared import _execute_chat, is_allowed
from tools.persistence import kv_get, kv_set

logger = logging.getLogger(__name__)
router = Router()

VOICE_REPLY_KEY = "voice_reply_enabled"


async def _voice_reply_enabled() -> bool:
    value = await kv_get(VOICE_REPLY_KEY)
    if value is None:
        return True
    return value.lower() in {"1", "true", "yes", "on"}


async def _set_voice_reply_enabled(enabled: bool) -> None:
    await kv_set(VOICE_REPLY_KEY, "true" if enabled else "false")


async def _transcribe(ogg_path: str) -> str:
    """Transcribe audio file using Groq Whisper API or local whisper."""
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            import httpx

            loop = asyncio.get_running_loop()
            audio_bytes = await loop.run_in_executor(None, lambda: open(ogg_path, "rb").read())
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {groq_key}"},
                    files={"file": ("audio.ogg", audio_bytes, "audio/ogg")},
                    data={"model": "whisper-large-v3", "response_format": "text"},
                )
                resp.raise_for_status()
                return resp.text.strip()
        except Exception as exc:
            logger.warning("Groq Whisper failed: %s", exc)

    # Cached whisper model — load once in thread executor, reuse across calls
    try:
        import whisper  # pip install openai-whisper  # type: ignore[reportMissingImports]
    except ImportError:
        raise RuntimeError(
            " whisper not installed. Install with: pip install openai-whisper"
        )

    _model_key = "_whisper_model"
    if not hasattr(_transcribe, _model_key):
        model = await asyncio.to_thread(whisper.load_model, "base")
        setattr(_transcribe, _model_key, model)

    def _do_transcribe() -> str:
        model = getattr(_transcribe, _model_key)
        result = model.transcribe(ogg_path)
        return result["text"]

    return await asyncio.to_thread(_do_transcribe)


async def _reply_with_optional_tts(msg: Message, response: str) -> None:
    from llm_client import chunk_output

    chunks = chunk_output(response, max_length=4000)
    for chunk in chunks:
        await msg.answer(chunk)
    try:
        from core.utils.multimodal_processor import text_to_speech

        audio = await text_to_speech(response)
        if audio:
            await msg.answer_voice(BufferedInputFile(audio, filename="legion_reply.mp3"))
    except Exception as exc:
        logger.debug("TTS skipped: %s", exc)


# ── Voice mode commands ────────────────────────────────────────────────────────────────────────────────


@router.message(Command("voice_on"))
async def cmd_voice_on(msg: Message) -> None:
    """Enable voice reply mode."""
    if not is_allowed(msg):
        return
    await _set_voice_reply_enabled(True)
    await msg.answer("🎤 Voice mode ON — send voice notes and I'll reply with audio.")


@router.message(Command("voice_off"))
async def cmd_voice_off(msg: Message) -> None:
    """Disable voice reply mode."""
    if not is_allowed(msg):
        return
    await _set_voice_reply_enabled(False)
    await msg.answer("🔇 Voice mode OFF — text only.")


@router.message(Command("voice_status"))
async def cmd_voice_status(msg: Message) -> None:
    """Show current voice mode state."""
    if not is_allowed(msg):
        return
    enabled = await _voice_reply_enabled()
    status = "ON 🎤" if enabled else "OFF 🔇"
    await msg.answer(f"Voice reply mode: <b>{status}</b>", parse_mode="HTML")


@router.message(Command("voice_toggle"))
async def cmd_voice_toggle(msg: Message) -> None:
    """Toggle voice reply on/off (alias for /voice_on / /voice_off)."""
    if not is_allowed(msg):
        return
    enabled = await _voice_reply_enabled()
    new_state = not enabled
    await _set_voice_reply_enabled(new_state)
    await msg.answer(f"Voice replies are now {'enabled 🎤' if new_state else 'disabled 🔇'}.")


@router.message(Command("vcsearch"))
async def cmd_vcsearch(msg: Message) -> None:
    """Search voice message transcripts.
    Usage: /vcsearch <query>
    """
    if not is_allowed(msg):
        return

    query = (msg.text or "").replace("/vcsearch", "").strip()
    if not query:
        await msg.answer("❌ Usage: /vcsearch <query>")
        return

    # Search voice transcripts (implementation depends on storage)
    # For now, return placeholder
    await msg.answer(
        f"🔍 Searching voice transcripts for: <b>{query}</b>\n\n"
        "⚠️ Voice transcript search not yet implemented.\n"
        "This feature requires a transcript storage backend.",
        parse_mode="HTML",
    )


# ── Voice/audio message handlers ──────────────────────────────────────────────────────────────────


@router.message(F.voice)
async def handle_voice(msg: Message) -> None:
    """Download voice message, transcribe, then route to chat with optional TTS."""
    if not is_allowed(msg):
        return

    status = await msg.answer("🎙 transcribing…")
    tmp_path = ""

    try:
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp_path = tmp.name

        assert msg.voice is not None
        file = await msg.bot.get_file(msg.voice.file_id)  # type: ignore[reportOptionalMemberAccess]
        if file is None or file.file_path is None:
            raise RuntimeError("get_file returned None")
        await msg.bot.download_file(file.file_path, destination=tmp_path)  # type: ignore[reportOptionalMemberAccess]
        text = await _transcribe(tmp_path)

        if not text or not text.strip():
            await status.edit_text("❌ Could not transcribe audio — please try again")
            return

        await status.edit_text(f"🎙 <i>{text}</i>", parse_mode="HTML")
        logger.info("Voice transcribed: %s", text[:80])

        if await _voice_reply_enabled():
            from llm_client import chat

            assert msg.from_user is not None
            response, _model = await chat(task=text, user_id=str(msg.from_user.id), show_thinking=False)
            await _reply_with_optional_tts(msg, response)
        else:
            await _execute_chat(msg, text)

    except Exception as exc:
        logger.error("Voice handler error: %s", exc)
        await status.edit_text(f"❌ Voice error: {str(exc)[:200]}")
    finally:
        if tmp_path:
            with contextlib.suppress(Exception):
                os.unlink(tmp_path)


@router.message(F.audio)
async def handle_audio(msg: Message) -> None:
    """Handle audio file uploads (mp3, wav, m4a) — same pipeline."""
    if not is_allowed(msg):
        return

    status = await msg.answer("🎵 transcribing audio file…")
    tmp_path = ""

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        assert msg.audio is not None
        file = await msg.bot.get_file(msg.audio.file_id)  # type: ignore[reportOptionalMemberAccess]
        if file is None or file.file_path is None:
            raise RuntimeError("get_file returned None")
        await msg.bot.download_file(file.file_path, destination=tmp_path)  # type: ignore[reportOptionalMemberAccess]
        text = await _transcribe(tmp_path)
        if not text.strip():
            await status.edit_text("❌ Empty transcription")
            return
        await status.edit_text(f"🎵 <i>{text}</i>", parse_mode="HTML")

        if await _voice_reply_enabled():
            from llm_client import chat

            assert msg.from_user is not None
            response, _model = await chat(task=text, user_id=str(msg.from_user.id), show_thinking=False)
            await _reply_with_optional_tts(msg, response)
        else:
            await _execute_chat(msg, text)
    except Exception as exc:
        await status.edit_text(f"❌ Audio error: {str(exc)[:200]}")
    finally:
        if tmp_path:
            with contextlib.suppress(Exception):
                os.unlink(tmp_path)
