"""Video URL handler — understand and extract info from video URLs.

Supports YouTube, Twitter/X video, and general video URLs.
Uses yt-dlp for metadata extraction and audio transcription.

Usage:
    from tools.video import understand_video_url
    result = await understand_video_url("https://youtube.com/watch?v=...")
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

_VIDEO_DOMAINS = {
    "youtube.com",
    "youtu.be",
    "youtube-nocookie.com",
    "twitter.com",
    "x.com",
    "xvideos.com",
    "pornhub.com",
    "tiktok.com",
    "instagram.com",
    "facebook.com",
    "vimeo.com",
}


def is_video_url(url: str) -> bool:
    """Return True if the URL appears to be a video URL."""
    if not url:
        return False
    url_lower = url.lower()
    return any(domain in url_lower for domain in _VIDEO_DOMAINS)


async def understand_video_url(url: str) -> str:
    """Extract metadata and optional audio transcript from a video URL.

    Args:
        url: A video URL (YouTube, Twitter, TikTok, etc.)

    Returns:
        A string summary of the video: title, duration, description, and
        audio transcript if available.
    """
    if not url or not url.strip():
        return "Error: No URL provided."

    url = url.strip()

    try:
        # Use yt-dlp for metadata + audio extraction
        # --dump-json: output JSON with all metadata
        # --no-playlist: don't download playlists
        # --no-check-certificates: skip SSL verification if needed
        # --socket-timeout: avoid hanging
        proc = await asyncio.create_subprocess_shell(
            f'yt-dlp --dump-json --no-playlist --no-check-certificates --socket-timeout 30 "{url}"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

        if proc.returncode != 0:
            err = stderr.decode("utf-8", errors="replace").strip()
            logger.warning("[video] yt-dlp failed for %s: %s", url, err[:200])
            return "Error: Could not extract video info (yt-dlp failed). The URL may be unsupported or private."

        try:
            import json

            data = json.loads(stdout.decode("utf-8", errors="replace"))
        except Exception as exc:
            logger.warning("[video] failed to parse yt-dlp JSON for %s: %s", url, exc)
            return f"Error: Could not parse video metadata for {url}."

        # Build summary
        title = data.get("title", "Unknown title")
        duration_sec = data.get("duration", 0)
        description = data.get("description", "")
        uploader = data.get("uploader", data.get("channel", "Unknown uploader"))
        view_count = data.get("view_count", 0)
        like_count = data.get("like_count", 0)
        tags = data.get("tags", [])[:10]

        if duration_sec:
            mins, secs = divmod(int(duration_sec), 60)
            hours, mins = divmod(mins, 60)
            if hours:
                duration_str = f"{hours}h {mins}m {secs}s"
            elif mins:
                duration_str = f"{mins}m {secs}s"
            else:
                duration_str = f"{secs}s"
        else:
            duration_str = "Unknown"

        lines = [
            f"🎬 <b>{title}</b>",
            "",
            f"👤 Uploader: {uploader}",
            f"⏱ Duration: {duration_str}",
            f"👁 Views: {view_count:,}" if view_count else "",
            f"👍 Likes: {like_count:,}" if like_count else "",
        ]

        if tags:
            lines.append(f"🏷 Tags: {', '.join(str(t) for t in tags)}")

        if description and description.strip():
            desc_snippet = description.strip()[:500]
            if len(description) > 500:
                desc_snippet += "…"
            lines.extend(["", f"📝 Description: {desc_snippet}"])

        # Try to extract audio and transcribe (if whisper is available)
        audio_transcript = await _transcribe_video_audio(url)
        if audio_transcript and not audio_transcript.startswith("Error"):
            snippet = audio_transcript[:800]
            if len(audio_transcript) > 800:
                snippet += "…"
            lines.extend(["", "📝 <b>Transcript:</b>", snippet])

        return "\n".join(line for line in lines if line)

    except TimeoutError:
        return f"Error: Timeout extracting video info for {url}."
    except Exception as exc:
        logger.exception("[video] understand_video_url failed for %s", url)
        return f"Error: Could not extract video info: {str(exc)[:200]}"


async def _transcribe_video_audio(url: str) -> str:
    """Download audio and transcribe using faster-whisper if available."""
    try:
        # Download audio to temp file
        import tempfile

        tmp_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp_path = tmp_audio.name
        tmp_audio.close()

        proc = await asyncio.create_subprocess_shell(
            f'yt-dlp -x --audio-format mp3 --audio-quality 0 -o "{tmp_path}.%(ext)s" --no-playlist --no-check-certificates --socket-timeout 30 "{url}"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

        if proc.returncode != 0:
            logger.debug("[video] audio download failed: %s", stderr.decode()[:200])
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            return ""

        # Find the actual file with extension
        import glob as glob_mod

        audio_files = glob_mod.glob(f"{tmp_path}.*")
        actual_path = next((f for f in audio_files if os.path.getsize(f) > 1000), None)

        if not actual_path:
            return ""

        try:
            from tools.minimax_media import understand_audio

            transcript = await understand_audio(actual_path)
            return transcript
        except Exception as exc:
            logger.debug("[video] audio transcription skipped: %s", exc)
            return ""
        finally:
            try:
                for f in audio_files:
                    os.unlink(f)
            except Exception:
                pass

    except Exception as exc:
        logger.debug("[video] _transcribe_video_audio failed: %s", exc)
        return ""
