"""media_tools.py — MiniMax multi-modal media handlers.

Commands:
  /imagine <prompt> [aspect_ratio] — generate an image
  /search <query>                  — web search
  /speak <text>                    — text to speech
  /mcp_status                      — show MiniMax MCP tool status

Photo handling:
  F.photo                          — analyze sent photo

Auto-routing via SKILL_PATTERNS:
  media_imagine  — image generation
  media_search   — web search
  media_speak    — speech generation
  media_photo    — image understanding
"""

from __future__ import annotations

import html as html_mod
import logging
import os
import tempfile
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message, PhotoSize

from handlers.shared import is_allowed, send_chunked
from tools.minimax_media import (
    generate_image,
    generate_speech,
    understand_image,
    web_search,
)

logger = logging.getLogger(__name__)
router = Router()

MAX_PHOTO_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


# ── Helpers ────────────────────────────────────────────────────────────────────


def _clean_html(text: str) -> str:
    """Escape HTML special characters."""
    return html_mod.escape(text or "")


async def _download_photo(msg: Message) -> Optional[str]:
    """Download photo to a temp file, return path or None."""
    photo: PhotoSize | None = None
    for p in msg.photo:
        if photo is None or p.file_size > photo.file_size:
            photo = p

    if photo is None:
        return None

    if photo.file_size > MAX_PHOTO_SIZE_BYTES:
        logger.warning("Photo too large: %d bytes", photo.file_size)
        return None

    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name

        file = await msg.bot.get_file(photo.file_id)
        await msg.bot.download_file(file.file_path, destination=tmp_path)
        return tmp_path
    except Exception as exc:
        logger.error("Failed to download photo: %s", exc)
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        return None


def _aspect_ratio_from_text(text: str) -> tuple[str, str]:
    """Extract aspect ratio from command text if present. Returns (prompt, aspect_ratio)."""
    text = (text or "").strip()
    parts = text.rsplit(None, 1)
    if len(parts) == 2 and parts[1] in {"1:1", "16:9", "9:16", "4:3", "3:4"}:
        return parts[0], parts[1]
    return text, "1:1"


# ── /imagine ──────────────────────────────────────────────────────────────────


@router.message(Command("imagine", "genimage", "draw"))
async def cmd_imagine(msg: Message) -> None:
    """Generate an image from a text prompt.

    Usage: /imagine <prompt> [aspect_ratio]
    Examples:
      /imagine a sunset over mountains
      /imagine a cat 16:9
      /genimage futuristic city 9:16
    """
    if not is_allowed(msg):
        return

    text = (msg.text or "").replace("/imagine", "").replace("/genimage", "").replace("/draw", "").strip()
    if not text:
        await msg.answer(
            "Usage: <code>/imagine &lt;prompt&gt; [aspect_ratio]</code>\n\n"
            "Aspect ratios: 1:1 (default), 16:9, 9:16, 4:3, 3:4\n\n"
            "Examples:\n"
            "  /imagine a sunset over mountains\n"
            "  /imagine futuristic city 16:9",
            parse_mode="HTML",
        )
        return

    prompt, aspect_ratio = _aspect_ratio_from_text(text)
    if not prompt:
        await msg.answer("Please provide a prompt, e.g. <code>/imagine a beautiful garden</code>", parse_mode="HTML")
        return

    status = await msg.answer("🎨 Generating image…")

    try:
        result = await generate_image(prompt=prompt, aspect_ratio=aspect_ratio)

        if result.startswith("Error:"):
            await status.edit_text(f"❌ {result}")
            return

        # Send the image back
        try:
            with open(result, "rb") as f:
                image_data = f.read()
            await msg.answer_document(
                BufferedInputFile(image_data, filename="generated.png"),
                caption=f"✨ <b>{_clean_html(prompt)}</b>\nAspect ratio: {aspect_ratio}",
                parse_mode="HTML",
            )
            await status.delete()
        except Exception as exc:
            await status.edit_text(f"❌ Failed to send image: {exc}")
    except Exception as exc:
        logger.exception("imagine failed")
        await status.edit_text(f"❌ Error: {str(exc)[:200]}")
    finally:
        if result and not result.startswith("Error:") and os.path.exists(result):
            try:
                os.unlink(result)
            except Exception:
                pass


# ── /search ───────────────────────────────────────────────────────────────────


@router.message(Command("search", "websearch", "google"))
async def cmd_search(msg: Message) -> None:
    """Search the web.

    Usage: /search <query>
    Examples:
      /search latest AI news
      /websearch Python 3.13 release date
    """
    if not is_allowed(msg):
        return

    text = msg.text or ""
    for cmd in ("/search", "/websearch", "/google"):
        text = text.replace(cmd, "", 1).strip()

    if not text:
        await msg.answer(
            "Usage: <code>/search &lt;query&gt;</code>\n\n"
            "Examples:\n"
            "  /search latest AI news\n"
            "  /search Python best practices 2025",
            parse_mode="HTML",
        )
        return

    status = await msg.answer("🔍 Searching…")

    try:
        result = await web_search(query=text)

        if result.startswith("Error:"):
            await status.edit_text(f"❌ {result}")
            return

        await status.delete()
        await send_chunked(msg, f"🔍 <b>Results for:</b> {_clean_html(text)}\n\n{result}", parse_mode="HTML")
    except Exception as exc:
        logger.exception("search failed")
        await status.edit_text(f"❌ Error: {str(exc)[:200]}")


# ── /speak ─────────────────────────────────────────────────────────────────────


@router.message(Command("speak", "tts", "voice_gen", "say"))
async def cmd_speak(msg: Message) -> None:
    """Convert text to speech.

    Usage: /speak <text>
    Voice options: English_expressive_narrator (default), male-qn-qingse, female-shaonv
    Speed: 0.5 - 2.0 (default 1.0)

    Examples:
      /speak Hello, how are you today?
      /tts The meeting starts at 3 PM
    """
    if not is_allowed(msg):
        return

    text = msg.text or ""
    for cmd in ("/speak", "/tts", "/voice_gen", "/say"):
        text = text.replace(cmd, "", 1).strip()

    if not text:
        await msg.answer(
            "Usage: <code>/speak &lt;text&gt;</code>\n\n"
            "Voices: English_expressive_narrator (default), male-qn-qingse, female-shaonv\n"
            "Speed: 0.5 - 2.0 (default 1.0)\n\n"
            "Examples:\n"
            "  /speak Hello, how are you today?\n"
            "  /tts The meeting starts at 3 PM",
            parse_mode="HTML",
        )
        return

    status = await msg.answer("🗣️ Generating speech…")

    try:
        result = await generate_speech(text=text)

        if result.startswith("Error:"):
            await status.edit_text(f"❌ {result}")
            return

        # Send as voice message
        try:
            with open(result, "rb") as f:
                audio_data = f.read()
            await msg.answer_voice(
                BufferedInputFile(audio_data, filename="speech.mp3"),
            )
            await status.delete()
        except Exception as exc:
            await status.edit_text(f"❌ Failed to send audio: {exc}")
    except Exception as exc:
        logger.exception("speak failed")
        await status.edit_text(f"❌ Error: {str(exc)[:200]}")
    finally:
        if result and not result.startswith("Error:") and os.path.exists(result):
            try:
                os.unlink(result)
            except Exception:
                pass


# ── Photo handling ────────────────────────────────────────────────────────────


@router.message(F.photo)
async def handle_photo(msg: Message) -> None:
    """Analyze a photo sent by the user.

    User can add a text prompt after the photo, e.g.:
      "What's in this image?" or "Describe this photo"
    """
    if not is_allowed(msg):
        return

    # Get caption or text after photo
    caption = (msg.caption or "").strip()
    text = (msg.text or "").strip()

    # Determine the prompt
    if caption:
        prompt = caption
    elif text:
        prompt = text
    else:
        prompt = "Describe what you see in this image in detail."

    status = await msg.answer("🖼️ Analyzing image…")

    tmp_path = ""
    try:
        tmp_path = await _download_photo(msg)
        if not tmp_path:
            await status.edit_text("❌ Failed to download image")
            return

        result = await understand_image(prompt=prompt, image_path=tmp_path)

        if result.startswith("Error:"):
            await status.edit_text(f"❌ {result}")
            return

        await status.delete()
        await send_chunked(
            msg,
            f"🖼️ <b>Image Analysis</b>\n\n{result}",
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.exception("photo analysis failed")
        await status.edit_text(f"❌ Error: {str(exc)[:200]}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# ── /mcp_status ───────────────────────────────────────────────────────────────


@router.message(Command("mcp_status", "mm_status"))
async def cmd_mcp_status(msg: Message) -> None:
    """Show MiniMax MCP tool status and available capabilities."""
    if not is_allowed(msg):
        return

    lines = [
        "<b>MiniMax MCP Tools</b>",
        "",
        "✅ understand_image — analyze photos",
        "✅ web_search       — search the web",
        "✅ generate_image   — create images from text",
        "✅ generate_speech  — text to speech",
        "",
        "<b>Commands:</b>",
        "  /imagine &lt;prompt&gt; [aspect_ratio] — generate image",
        "  /search &lt;query&gt;               — web search",
        "  /speak &lt;text&gt;                 — text to speech",
        "  (send a photo)               — analyze image",
        "",
        "<b>Aspect ratios:</b> 1:1, 16:9, 9:16, 4:3, 3:4",
        "<b>Voices:</b> English_expressive_narrator, male-qn-qingse, female-shaonv",
    ]

    await msg.answer("\n".join(lines), parse_mode="HTML")
