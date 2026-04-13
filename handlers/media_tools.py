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

import aiofiles
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
            async with aiofiles.open(result, "rb") as f:
                image_data = await f.read()
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

        # Concern 4 fix: Synthesize search results through LLM before returning to user.
        # Self-awareness gate only triggers on "I don't know" responses, so we proactively
        # inject search results into the LLM context here so the response is natural/synthesized.
        logger.info("Search completed for '%s', synthesizing via LLM...", text)
        try:
            from llm_client import chat

            synthesis_prompt = (
                f"User asked: {text}\n\n"
                f"Here are web search results for '{text}':\n\n"
                f"{result}\n\n"
                f"Sintesiskan hasil pencarian di atas menjadi jawaban natural dalam Bahasa Indonesia. "
                f"Jawab dengan ringkas dan jelas."
            )
            synthesized, _model_used = await chat(
                task=synthesis_prompt,
                agent_key="general",
                run_post_hooks=False,
            )
            # If synthesis succeeded and is not empty/error, use it
            if synthesized and not synthesized.startswith("[") and len(synthesized) > 10:
                await status.delete()
                await send_chunked(
                    msg,
                    f"🔍 <b>Results for:</b> {_clean_html(text)}\n\n{synthesized}",
                    parse_mode="HTML",
                )
                logger.info("Search synthesis successful, model used: %s", _model_used)
                return
            # Fall through to raw results if synthesis failed or was too short
            logger.warning("Search synthesis returned weak result, falling back to raw")
        except Exception as synth_err:
            logger.warning("Search synthesis failed, using raw results: %s", synth_err)

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
            async with aiofiles.open(result, "rb") as f:
                audio_data = await f.read()
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

        is_error = (
            result.startswith("Error:")
            or "not in config" in result
            or "is disabled" in result
            or "no command configured" in result
            or "MCP error" in result
            or "not available" in result
            or result.startswith("MCP ")
        )
        if is_error:
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


# ── Video handling (F.video) ─────────────────────────────────────────────────


@router.message(F.video)
async def handle_video(msg: Message) -> None:
    """Analyze a video sent by the user.

    Extracts keyframes using ffmpeg and transcribes audio.
    User can add a caption/prompt: "What's in this video?" or "Summarize this."
    """
    if not is_allowed(msg):
        return

    caption = (msg.caption or "").strip()
    text = (msg.text or "").strip()
    prompt = caption or text or "Describe what happens in this video clip."

    status = await msg.answer("🎬 Analyzing video… this may take a moment.")

    tmp_video_path = ""
    tmp_frames_dir = ""
    try:
        # Download video
        video = msg.video
        if video is None:
            await status.edit_text("❌ No video found in message.")
            return

        if video.file_size and video.file_size > 100 * 1024 * 1024:
            await status.edit_text("❌ Video too large (max 100 MB).")
            return

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_video_path = tmp.name

        file = await msg.bot.get_file(video.file_id)
        await msg.bot.download_file(file.file_path, destination=tmp_video_path)

        # Extract keyframes using ffmpeg (1 frame every 10 seconds, max 8 frames)
        import subprocess
        import shutil

        tmp_frames_dir = tempfile.mkdtemp(prefix="video_frames_")
        frame_pattern = os.path.join(tmp_frames_dir, "frame_%03d.jpg")

        # Get video duration
        duration_proc = await asyncio.create_subprocess_shell(
            f'ffprobe -v error -show_entries format=duration -of csv=p=0 "{tmp_video_path}"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        duration_out, _ = await duration_proc.communicate()
        try:
            duration_sec = float(duration_out.decode().strip())
        except Exception:
            duration_sec = 60

        # Extract frames: 1 every 10s, max 8
        interval_sec = min(10, max(1, duration_sec / 8))
        n_frames = min(8, max(1, int(duration_sec / interval_sec)))

        extract_cmd = (
            f'ffmpeg -i "{tmp_video_path}" -vf "fps=1/{interval_sec},scale=640:-1" '
            f'-q:v 2 -frames:v {n_frames} "{frame_pattern}" -y'
        )
        extract_proc = await asyncio.create_subprocess_shell(
            extract_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await extract_proc.communicate()

        # Transcribe audio using faster-whisper if available
        audio_transcript = ""
        try:
            from tools.minimax_media import understand_audio

            audio_tmp = tempfile.mktemp(suffix=".mp3")
            conv_proc = await asyncio.create_subprocess_shell(
                f'ffmpeg -i "{tmp_video_path}" -vn -acodec libmp3lame -q:a 2 "{audio_tmp}" -y',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await conv_proc.communicate()
            audio_transcript = await understand_audio(audio_tmp)
            try:
                os.unlink(audio_tmp)
            except Exception:
                pass
        except Exception as exc:
            logger.debug("Audio transcription skipped: %s", exc)

        # Analyze keyframes
        frame_results: list[str] = []
        import glob as glob_mod

        frame_files = sorted(glob_mod.glob(os.path.join(tmp_frames_dir, "frame_*.jpg")))
        for frame_path in frame_files[:4]:
            try:
                from tools.minimax_media import understand_image

                frame_desc = await understand_image(
                    prompt="Describe what you see in this frame from a video. Be brief.",
                    image_path=frame_path,
                )
                frame_results.append(frame_desc)
            except Exception as exc:
                logger.debug("Frame analysis failed: %s", exc)

        # Build response
        lines = [f"🎬 <b>Video Analysis</b>", "", f"<i>Prompt: {_clean_html(prompt)}</i>", ""]

        if frame_results:
            lines.append("<b>Key frames:</b>")
            for i, fr in enumerate(frame_results, 1):
                lines.append(f"  {i}. {fr}")
            lines.append("")

        if audio_transcript and not audio_transcript.startswith("Error"):
            snippet = audio_transcript[:500]
            if len(audio_transcript) > 500:
                snippet += "…"
            lines.append(f"<b>Audio transcript:</b> {snippet}")

        await status.delete()
        await send_chunked(msg, "\n".join(lines), parse_mode="HTML")

    except Exception as exc:
        logger.exception("video analysis failed")
        await status.edit_text(f"❌ Error analyzing video: {str(exc)[:200]}")
    finally:
        if tmp_video_path and os.path.exists(tmp_video_path):
            try:
                os.unlink(tmp_video_path)
            except Exception:
                pass
        if tmp_frames_dir and os.path.exists(tmp_frames_dir):
            try:
                shutil.rmtree(tmp_frames_dir)
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
