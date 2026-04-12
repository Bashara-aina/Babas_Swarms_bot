"""Error humanizer — converts raw exceptions into friendly, conversational messages.

Never show raw Python tracebacks or exception strings to Bashara.
All API errors, rate limits, auth failures, and internal errors are
translated into natural Indonesian/English messages.

Usage:
    from core.error_humanizer import humanize_error
    friendly = humanize_error(exc, context="running /do command")
"""

from __future__ import annotations

import re
from typing import Any


def humanize_error(exc: Exception, context: str = "") -> str | None:
    """Convert a raw exception into a human-readable message.

    Returns None for internal errors that should be retried silently
    (e.g., parameter name mismatches that have been fixed).

    Args:
        exc: The exception to humanize
        context: What Legion was trying to do when this error occurred

    Returns:
        A friendly message string, or None if the error should be suppressed
    """
    msg = str(exc)
    msg_lower = msg.lower()
    context_lower = context.lower()

    # ── Internal / known-fixed errors — retry silently ─────────────────────────
    if "progress_cb" in msg_lower or "progress_fn" in msg_lower:
        return None  # Already fixed, retry silently
    if "unexpected keyword argument" in msg_lower and ("progress_cb" in msg_lower or "progress_fn" in msg_lower):
        return None

    # ── API key / authentication errors ─────────────────────────────────────────
    if any(kw in msg_lower for kw in ("api key", "auth", "authentication", "unauthorized", "401", "403")):
        if "groq" in context_lower or "groq" in msg_lower:
            return "GROQ lagi ada masalah sama auth. Lagi coba cek ulang API key…"
        if "cerebras" in context_lower or "cerebras" in msg_lower:
            return "Cerebras API lagi error auth. Coba retry sebentar…"
        if "gemini" in context_lower or "gemini" in msg_lower:
            return "Gemini API key bermasalah. Lagi coba cek…"
        if "openai" in msg_lower or "anthropic" in msg_lower:
            return "API key lagi bermasalah. Lagi coba dicek…"
        if "z.ai" in msg_lower or "glm" in msg_lower:
            return "Z.AI / GLM-4 API key lagi error. Coba lagi ya…"
        return "Ada masalah sama API key. Lagi coba fallback ke provider lain…"

    # ── Rate limiting ──────────────────────────────────────────────────────────
    if any(kw in msg_lower for kw in ("rate limit", "ratelimit", "429", "too many requests", "quota")):
        return "Rate limited — bentar dulu ya, coba lagi dalam 1-2 menit…"

    # ── Timeout errors ─────────────────────────────────────────────────────────
    if any(kw in msg_lower for kw in ("timeout", "timed out", "deadline", "took too long")):
        return "Koneksi timeout. Lagi retry dengan cara lain…"

    # ── Model not available ─────────────────────────────────────────────────────
    if any(kw in msg_lower for kw in ("model not found", "model not available", "does not exist", "404")):
        return "Model yang dipake lagi unavailable. Lagi switch ke model lain…"

    # ── Bad request / malformed ───────────────────────────────────────────────
    if any(kw in msg_lower for kw in ("bad request", "invalid request", "400", "malformed")):
        if "context" in msg_lower or "window" in msg_lower:
            return "Request terlalu panjang — lagi coba singkatin context…"
        return "Request lagi malformed. Lagi retry…"

    # ── Network / connectivity ─────────────────────────────────────────────────
    if any(kw in msg_lower for kw in ("connection", "network", "connectivity", "dns", "refused", "unreachable", "no internet")):
        return "Koneksi lagi hiccup. Lagi retry…"

    # ── Execution errors (shell, code) ─────────────────────────────────────────
    if "execute" in context_lower or "shell" in context_lower:
        if "permission denied" in msg_lower or "access denied" in msg_lower:
            return "Permission denied — mau coba sudo atau bypass?"
        if "not found" in msg_lower or "command not found" in msg_lower:
            return "Command tidak ketemu. Check lagi typo atau install dulu…"
        if "killed" in msg_lower or "signal" in msg_lower:
            return "Process kebunuh — kemungkinan timeout atau OOM. Mau coba lagi?"
        if "disk" in msg_lower or "space" in msg_lower:
            return "Disk hampir penuh — mau cleanup files?"

    # ── Memory / resource errors ──────────────────────────────────────────────
    if any(kw in msg_lower for kw in ("memory", "oom", "out of memory", "cuda oom", "gpu memory")):
        if "cuda" in msg_lower or "gpu" in msg_lower:
            return "GPU lagi kehabisan memory. Lagi stop model lain dulu…"
        return "RAM hampir penuh. Lagi cleanup proses yang nggak perlu…"

    # ── File errors ───────────────────────────────────────────────────────────
    if any(kw in msg_lower for kw in ("no such file", "not found", "is a directory", "permission denied")):
        return "File tidak ditemukan atau permission error. Check path-nya ya…"

    # ── Empty / null response ─────────────────────────────────────────────────
    if not msg or msg.strip() in ("", "None", "null"):
        return "Lagi dapat response kosong — retry dulu ya…"

    # ── Unknown or suppressed ──────────────────────────────────────────────────
    if context:
        # Generic fallback with context hint — never expose raw exception
        if any(kw in msg_lower for kw in ("error", "exception", "failed", "failed")):
            # Check for known safe-to-ignore patterns
            if any(kw in msg_lower for kw in ("suppress", "internal", "traceback")):
                return None
            return f"Ada error pas {context}. Lagi coba lagi ya…"
    return None


def humanize_error_for_display(exc: Exception, context: str = "") -> str:
    """Humanized error that IS safe to display to Bashara.

    Unlike humanize_error(), this always returns a string — never None.
    Used at the Telegram handler level.
    """
    friendly = humanize_error(exc, context)
    if friendly is not None:
        return friendly

    # Fallback for truly unknown errors
    exc_name = type(exc).__name__
    friendly_fallbacks = {
        "TimeoutError": "Timeout — bentar ya, lagi proses…",
        "RuntimeError": "Runtime error. Coba lagi atau check inputnya.",
        "ValueError": "Input nggak valid. Check formatnya ya.",
        "TypeError": "Type error — ada mismatch tipe data.",
        "AttributeError": "Internal error. Restart bisa bantu.",
        "ConnectionError": "Koneksi gagal. Check internetnya ya.",
        "OSError": "OS-level error. Biasanya bisa solved sendiri.",
    }
    return friendly_fallbacks.get(
        exc_name,
        f"Ada error nih ({exc_name}). Lagi coba lagi…",
    )
