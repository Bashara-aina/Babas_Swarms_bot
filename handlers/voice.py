"""Voice message handler — transcribes .ogg via Whisper then routes to agent."""
from __future__ import annotations

import logging
import os
import tempfile

from aiogram import F, Router
from aiogram.types import Message

from handlers.shared import _execute_chat, is_allowed

logger = logging.getLogger(__name__)
router = Router()


async def _transcribe(ogg_path: str) -> str:
    """Transcribe audio file using OpenAI Whisper API or local whisper."""
    # Try OpenAI Whisper API first
    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")
    if openai_key and os.getenv("OPENAI_API_KEY"):
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=openai_key)
            with open(ogg_path, "rb") as f:
                result = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="id",  # Indonesian + English auto-detect
                )
            return result.text
        except Exception as e:
            logger.warning("OpenAI Whisper failed: %s", e)

    # Fallback: Groq Whisper (free, fast)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                with open(ogg_path, "rb") as f:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {groq_key}"},
                        files={"file": ("audio.ogg", f, "audio/ogg")},
                        data={"model": "whisper-large-v3", "response_format": "text"},
                    )
                resp.raise_for_status()
                return resp.text.strip()
        except Exception as e:
            logger.warning("Groq Whisper failed: %s", e)

    # Fallback: local whisper
    try:
        import whisper  # pip install openai-whisper
        model = whisper.load_model("base")
        result = model.transcribe(ogg_path)
        return result["text"]
    except ImportError:
        raise RuntimeError("No Whisper available. Set OPENAI_API_KEY or GROQ_API_KEY, or: pip install openai-whisper")


@router.message(F.voice)
async def handle_voice(msg: Message) -> None:
    """Download voice message, transcribe, then route to agent."""
    if not is_allowed(msg):
        return

    status = await msg.answer("🎙 transcribing…")

    try:
        # Download .ogg from Telegram
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp_path = tmp.name

        file = await msg.bot.get_file(msg.voice.file_id)
        await msg.bot.download_file(file.file_path, destination=tmp_path)

        # Transcribe
        text = await _transcribe(tmp_path)
        os.unlink(tmp_path)

        if not text or not text.strip():
            await status.edit_text("❌ Could not transcribe audio — please try again")
            return

        await status.edit_text(f"🎙 <i>{text}</i>", parse_mode="HTML")
        logger.info("Voice transcribed: %s", text[:80])

        # Route to agent exactly like a text message
        await _execute_chat(msg, text)

    except Exception as e:
        logger.error("Voice handler error: %s", e)
        await status.edit_text(f"❌ Voice error: {str(e)[:200]}")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@router.message(F.audio)
async def handle_audio(msg: Message) -> None:
    """Handle audio file uploads (mp3, wav, m4a) — same pipeline."""
    if not is_allowed(msg):
        return
    status = await msg.answer("🎵 transcribing audio file…")
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        file = await msg.bot.get_file(msg.audio.file_id)
        await msg.bot.download_file(file.file_path, destination=tmp_path)
        text = await _transcribe(tmp_path)
        os.unlink(tmp_path)
        if not text.strip():
            await status.edit_text("❌ Empty transcription")
            return
        await status.edit_text(f"🎵 <i>{text}</i>", parse_mode="HTML")
        await _execute_chat(msg, text)
    except Exception as e:
        await status.edit_text(f"❌ Audio error: {str(e)[:200]}")
