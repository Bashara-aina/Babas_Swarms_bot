"""
lib/legiona/tools/mmx_tools.py
MiniMax MMX-CLI tool wrappers — 7 modalities accessible via subprocess.
These let Legiona's tool loop invoke multimodal tasks natively.
Requires: mmx-cli (npm install -g mmx-cli)
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

MMX_TIMEOUT = int(os.getenv("MMX_TIMEOUT", "120"))


def _run_mmx(args: list[str], timeout: int = MMX_TIMEOUT) -> str:
    """Run mmx CLI and return stdout."""
    try:
        result = subprocess.run(
            ["mmx", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "NO_COLOR": "1", "NON_INTERACTIVE": "1"},
        )
        if result.returncode != 0:
            return f"ERROR: mmx {' '.join(args)} returned {result.returncode}: {result.stderr}"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return f"ERROR: mmx command timed out after {timeout}s"
    except FileNotFoundError:
        return "ERROR: mmx-cli not found. Run: npm install -g mmx-cli"
    except Exception as exc:
        return f"ERROR: {exc}"


def mmx_vision(image_path: str, prompt: str) -> str:
    """
    Describe an image using MiniMax VLM (vision modality).

    Args:
        image_path: Absolute or relative path to the image file
        prompt: Question or instruction about the image
    Returns:
        Model's description/analysis as string.
    """
    abs_path = str(Path(image_path).resolve())
    if not Path(abs_path).exists():
        return f"ERROR: Image not found: {image_path}"
    # Use non-interactive mode
    result = _run_mmx(
        ["vision", "describe", abs_path, "--prompt", prompt, "--non-interactive"],
        timeout=60,
    )
    return result


def mmx_search(query: str) -> str:
    """
    Search the web via MiniMax search modality.

    Args:
        query: The search query string
    Returns:
        Search results as string.
    """
    result = _run_mmx(["search", "query", query, "--non-interactive"], timeout=30)
    return result


def mmx_speech(text: str, voice: str | None = None) -> str:
    """
    Synthesize speech from text using MiniMax TTS.

    Args:
        text: The text to synthesize
        voice: Voice name (default from env MMX_DEFAULT_VOICE or 'English_Expressive_narrator')
    Returns:
        Path to the generated audio file, or error string.
    """
    voice = voice or os.getenv("MMX_DEFAULT_VOICE", "English_Expressive_narrator")
    # mmx speech synthesize requires --text and --voice flags
    result = _run_mmx(
        ["speech", "synthesize", "--text", text, "--voice", voice, "--non-interactive"],
        timeout=60,
    )
    return result


def mmx_text_chat(message: str) -> str:
    """
    Quick text chat via MiniMax M2.7.

    Args:
        message: The user message to send
    Returns:
        Model's response as string.
    """
    result = _run_mmx(["text", "chat", "--message", message, "--non-interactive"], timeout=60)
    return result


# ── Tool schemas for OpenAI-compatible registry ──────────────────────────────

MMX_TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "mmx_vision",
            "description": "Describe or analyze an image using MiniMax VLM (vision modality). Use this before shell_exec for screenshot analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Absolute or relative path to the image file to analyze",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Question or instruction about the image (e.g. 'What does this screenshot show?')",
                    },
                },
                "required": ["image_path", "prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mmx_search",
            "description": "Search the web via MiniMax search modality. Use for fresh data when RAG doesn't have the answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query string",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mmx_speech",
            "description": "Synthesize speech from text using MiniMax TTS. Returns path to the audio file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to synthesize into speech",
                    },
                    "voice": {
                        "type": "string",
                        "description": "Voice name from mmx speech voices list (default: English_Expressive_narrator)",
                    },
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mmx_text_chat",
            "description": "Quick text chat via MiniMax M2.7. For simple queries that don't need the full tool loop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The user message to send to the model",
                    },
                },
                "required": ["message"],
            },
        },
    },
]
