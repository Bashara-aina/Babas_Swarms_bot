"""minimax_media.py — MiniMax multi-modal tool wrappers.

Wraps 4 MiniMax tools:
  - understand_image  — analyze photos
  - web_search       — web search
  - generate_image   — text-to-image generation
  - generate_speech  — text-to-speech

These tools require a MiniMax MCP server to be configured in config/mcp_config.json.
When no MCP server is available, functions return clear error messages.
"""

from __future__ import annotations

import base64
import logging
import os
import tempfile
from typing import Any

logger = logging.getLogger(__name__)

# Timeout for MiniMax tool calls (seconds)
_MCP_TIMEOUT = 120.0

# Valid aspect ratios for image generation
_VALID_ASPECT_RATIOS = {"1:1", "16:9", "9:16", "4:3", "3:4"}

# Valid voice IDs for speech generation
_VALID_VOICE_IDS = {
    "English_expressive_narrator",
    "male-qn-qingse",
    "female-shaonv",
}

# MCP server name for MiniMax tools (set via LEGION_MCP_MINIMAX_SERVER env var)
_MCP_SERVER = os.getenv("LEGION_MCP_MINIMAX_SERVER", "minimax")


def _get_mcp_client() -> Any:
    """Return an MCPClient instance, or None if unavailable."""
    try:
        from core.mcp_client import MCPClient

        return MCPClient()
    except Exception:
        return None


# ── Image Understanding ────────────────────────────────────────────────────────


async def understand_image(prompt: str, image_path: str) -> str:
    """Analyze an image and return a text description.

    Args:
        prompt: Question or analysis request about the image.
        image_path: Path to local image file (JPEG, PNG, WebP).

    Returns:
        Text description of the image, or an error string.
    """
    if not os.path.exists(image_path):
        return f"Error: image file not found: {image_path}"

    # Read and encode image
    try:
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }.get(ext, "image/jpeg")

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        image_source = f"data:{mime_type};base64,{image_data}"
    except Exception as exc:
        return f"Error reading image: {exc}"

    client = _get_mcp_client()
    if not client:
        return "Error: MiniMax MCP client not available. Set LEGION_MCP_MINIMAX_SERVER in .env."

    try:
        result = await client.call_tool(
            _MCP_SERVER,
            "CodingPlan_understand_image",
            {"prompt": prompt, "image_source": image_source},
        )
        return result if result else "(no description returned)"
    except Exception as exc:
        logger.warning("understand_image failed: %s", exc)
        return f"Error: {exc}"


# ── Web Search ──────────────────────────────────────────────────────────────────


async def web_search(query: str, max_results: int = 6) -> str:
    """Search the web using MiniMax web search.

    Args:
        query: Search query string.
        max_results: Maximum number of results (default 6).

    Returns:
        Formatted search results string, or an error string.
    """
    client = _get_mcp_client()
    if not client:
        return "Error: MiniMax MCP client not available. Set LEGION_MCP_MINIMAX_SERVER in .env."

    try:
        result = await client.call_tool(
            _MCP_SERVER,
            "CodingPlan_web_search",
            {"query": query, "max_results": max_results},
        )
        return result if result else "(no results returned)"
    except Exception as exc:
        logger.warning("web_search failed: %s", exc)
        return f"Error: {exc}"


# ── Image Generation ────────────────────────────────────────────────────────────


async def generate_image(prompt: str, aspect_ratio: str = "1:1") -> str:
    """Generate an image from a text prompt using MiniMax image generation.

    Args:
        prompt: Text description of the desired image.
        aspect_ratio: One of "1:1", "16:9", "9:16", "4:3", "3:4" (default "1:1").

    Returns:
        Path to saved image file, or an error string.
    """
    if aspect_ratio not in _VALID_ASPECT_RATIOS:
        return (
            f"Error: invalid aspect_ratio '{aspect_ratio}'. Must be one of: {', '.join(sorted(_VALID_ASPECT_RATIOS))}"
        )

    client = _get_mcp_client()
    if not client:
        return "Error: MiniMax MCP client not available. Set LEGION_MCP_MINIMAX_SERVER in .env."

    try:
        result = await client.call_tool(
            _MCP_SERVER,
            "TokenPlan_image_generation",
            {"prompt": prompt, "aspect_ratio": aspect_ratio},
        )
        result_str = str(result) if result else "(empty result)"

        # If result is a URL, download and save to temp file
        if result_str.startswith("http"):
            try:
                import httpx

                async with httpx.AsyncClient(timeout=60.0) as client_http:
                    r = await client_http.get(result_str)
                    r.raise_for_status()
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(r.content)
                    return tmp.name
            except Exception as exc:
                logger.warning("Failed to download generated image: %s", exc)
                return f"Generated at {result_str} but download failed: {exc}"

        # If result is base64 data, save to temp file
        if "base64," in result_str:
            try:
                _, data = result_str.split("base64,", 1)
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(base64.b64decode(data))
                    return tmp.name
            except Exception as exc:
                logger.warning("Failed to save base64 image: %s", exc)
                return f"Generated but save failed: {exc}"

        return result_str
    except Exception as exc:
        logger.warning("generate_image failed: %s", exc)
        return f"Error: {exc}"


# ── Speech Generation ───────────────────────────────────────────────────────────


async def understand_audio(audio_path: str) -> str:
    """Transcribe an audio file using faster-whisper (GPU-accelerated).

    This function delegates to core.utils.multimodal_processor.transcribe_voice.
    Keeping it here maintains backward compatibility with existing import sites.

    Args:
        audio_path: Path to local audio file (MP3, WAV, OGG, M4A, etc.).

    Returns:
        Transcript text, or an error string.
    """
    try:
        import os

        from core.utils.multimodal_processor import transcribe_voice

        with open(audio_path, "rb") as f:
            audio_data = f.read()
        return await transcribe_voice(audio_data, extension=os.path.splitext(audio_path)[1] or ".mp3")
    except Exception as exc:
        logger.warning("understand_audio failed for %s: %s", audio_path, exc)
        return f"Error: transcription failed — {exc}"


async def generate_speech(
    text: str,
    voice_id: str = "English_expressive_narrator",
    speed: float = 1.0,
) -> str:
    """Convert text to speech using MiniMax speech generation.

    Args:
        text: Text to convert to speech.
        voice_id: Voice ID (default "English_expressive_narrator").
                  Other options: "male-qn-qingse", "female-shaonv".
        speed: Speech speed from 0.5 to 2.0 (default 1.0).

    Returns:
        Path to saved audio file, or an error string.
    """
    if voice_id not in _VALID_VOICE_IDS:
        return f"Error: invalid voice_id '{voice_id}'. Must be one of: {', '.join(sorted(_VALID_VOICE_IDS))}"

    if not 0.5 <= speed <= 2.0:
        return f"Error: speed must be between 0.5 and 2.0, got {speed}"

    client = _get_mcp_client()
    if not client:
        return "Error: MiniMax MCP client not available. Set LEGION_MCP_MINIMAX_SERVER in .env."

    try:
        result = await client.call_tool(
            _MCP_SERVER,
            "TokenPlan_speech_generation",
            {"text": text, "voice_id": voice_id, "speed": speed},
        )
        result_str = str(result) if result else "(empty result)"

        # If result is a URL, download and save to temp file
        if result_str.startswith("http"):
            try:
                import httpx

                async with httpx.AsyncClient(timeout=60.0) as client_http:
                    r = await client_http.get(result_str)
                    r.raise_for_status()
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp.write(r.content)
                    return tmp.name
            except Exception as exc:
                logger.warning("Failed to download generated speech: %s", exc)
                return f"Generated at {result_str} but download failed: {exc}"

        # If result is base64 data, save to temp file
        if "base64," in result_str:
            try:
                _, data = result_str.split("base64,", 1)
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp.write(base64.b64decode(data))
                    return tmp.name
            except Exception as exc:
                logger.warning("Failed to save base64 audio: %s", exc)
                return f"Generated but save failed: {exc}"

        return result_str
    except Exception as exc:
        logger.warning("generate_speech failed: %s", exc)
        return f"Error: {exc}"
