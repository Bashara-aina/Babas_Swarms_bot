"""Resource monitor — RAM + GPU VRAM awareness for local model gating.

Checks system RAM and GPU VRAM before allowing Ollama (local model) use.
If resources are too constrained, bot automatically falls back to cloud API.

Usage:
    from tools.resource_monitor import can_use_local_model, get_resource_snapshot

    if await can_use_local_model():
        # use ollama_chat/gemma3:12b
    else:
        # use cloud fallback

Thresholds (configurable via env vars):
    LOCAL_MIN_FREE_RAM_GB   default 3.0  — minimum free system RAM in GB
    LOCAL_MIN_FREE_VRAM_GB  default 4.0  — minimum free GPU VRAM in GB
    LOCAL_MIN_FREE_VRAM_PCT default 25   — minimum free VRAM as % of total

All checks are cached for 30s to avoid hammering nvidia-smi / psutil.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ── Thresholds (override via .env) ────────────────────────────────────────────
MIN_FREE_RAM_GB:   float = float(os.getenv("LOCAL_MIN_FREE_RAM_GB",   "3.0"))
MIN_FREE_VRAM_GB:  float = float(os.getenv("LOCAL_MIN_FREE_VRAM_GB",  "4.0"))
MIN_FREE_VRAM_PCT: float = float(os.getenv("LOCAL_MIN_FREE_VRAM_PCT", "25"))
CACHE_TTL:         float = 30.0   # seconds between re-polls


@dataclass
class ResourceSnapshot:
    """Point-in-time resource reading."""
    # RAM
    ram_total_gb:    float = 0.0
    ram_used_gb:     float = 0.0
    ram_free_gb:     float = 0.0
    ram_percent:     float = 0.0   # % used

    # GPU VRAM (None if no GPU / nvidia-smi unavailable)
    gpu_name:        Optional[str]   = None
    vram_total_gb:   Optional[float] = None
    vram_used_gb:    Optional[float] = None
    vram_free_gb:    Optional[float] = None
    vram_percent:    Optional[float] = None   # % used
    gpu_util_pct:    Optional[float] = None   # GPU compute utilisation %

    # Decision
    local_allowed:   bool = True
    block_reason:    str  = ""     # human-readable reason if blocked

    # Meta
    timestamp:       float = field(default_factory=time.time)
    psutil_ok:       bool  = True
    nvml_ok:         bool  = False   # True if nvidia-smi / pynvml worked


# ── Cache ─────────────────────────────────────────────────────────────────────
_cache: Optional[ResourceSnapshot] = None
_cache_lock = asyncio.Lock()


def _read_ram() -> tuple[float, float, float, float]:
    """Returns (total_gb, used_gb, free_gb, percent_used). Never raises."""
    try:
        import psutil
        vm = psutil.virtual_memory()
        total = vm.total / 1024 ** 3
        used  = vm.used  / 1024 ** 3
        free  = vm.available / 1024 ** 3   # 'available' is more accurate than 'free'
        pct   = vm.percent
        return total, used, free, pct
    except Exception as e:
        logger.warning("psutil RAM read failed: %s", e)
        return 0.0, 0.0, 0.0, 0.0


def _read_gpu() -> tuple[Optional[str], Optional[float], Optional[float], Optional[float], Optional[float], Optional[float]]:
    """
    Returns (name, total_gb, used_gb, free_gb, vram_pct_used, gpu_util_pct).
    Tries pynvml first (faster, no subprocess), falls back to nvidia-smi subprocess.
    Returns all-None on failure (no GPU or driver issue).
    """
    # --- Try pynvml (preferred) ---
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        name   = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode()
        mem    = pynvml.nvmlDeviceGetMemoryInfo(handle)
        util   = pynvml.nvmlDeviceGetUtilizationRates(handle)
        total  = mem.total / 1024 ** 3
        used   = mem.used  / 1024 ** 3
        free   = mem.free  / 1024 ** 3
        pct    = (mem.used / mem.total * 100) if mem.total else 0.0
        gpu_u  = float(util.gpu)
        pynvml.nvmlShutdown()
        return name, total, used, free, pct, gpu_u
    except Exception:
        pass

    # --- Fallback: nvidia-smi subprocess ---
    try:
        import subprocess
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            timeout=5,
            stderr=subprocess.DEVNULL,
        ).decode().strip().splitlines()[0]
        parts = [p.strip() for p in out.split(",")]
        if len(parts) >= 5:
            name   = parts[0]
            total  = float(parts[1]) / 1024   # MiB -> GiB
            used   = float(parts[2]) / 1024
            free_v = float(parts[3]) / 1024
            pct    = (used / total * 100) if total else 0.0
            gpu_u  = float(parts[4])
            return name, total, used, free_v, pct, gpu_u
    except Exception as e:
        logger.debug("nvidia-smi fallback failed: %s", e)

    return None, None, None, None, None, None


def _build_snapshot() -> ResourceSnapshot:
    """Synchronous snapshot build — called from asyncio thread pool."""
    snap = ResourceSnapshot()

    # RAM
    snap.ram_total_gb, snap.ram_used_gb, snap.ram_free_gb, snap.ram_percent = _read_ram()
    snap.psutil_ok = snap.ram_total_gb > 0

    # GPU
    (
        snap.gpu_name,
        snap.vram_total_gb,
        snap.vram_used_gb,
        snap.vram_free_gb,
        snap.vram_percent,
        snap.gpu_util_pct,
    ) = _read_gpu()
    snap.nvml_ok = snap.gpu_name is not None

    # ── Decision logic ────────────────────────────────────────────────────────
    reasons: list[str] = []

    # 1. RAM check
    if snap.psutil_ok and snap.ram_free_gb < MIN_FREE_RAM_GB:
        reasons.append(
            f"RAM too low: {snap.ram_free_gb:.1f}GB free "
            f"(need {MIN_FREE_RAM_GB}GB, {snap.ram_percent:.0f}% used)"
        )

    # 2. VRAM checks (only if GPU was detected)
    if snap.nvml_ok and snap.vram_free_gb is not None:
        if snap.vram_free_gb < MIN_FREE_VRAM_GB:
            reasons.append(
                f"VRAM too low: {snap.vram_free_gb:.1f}GB free "
                f"(need {MIN_FREE_VRAM_GB}GB)"
            )
        free_pct = 100.0 - (snap.vram_percent or 0.0)
        if free_pct < MIN_FREE_VRAM_PCT:
            reasons.append(
                f"VRAM {free_pct:.0f}% free "
                f"(need {MIN_FREE_VRAM_PCT:.0f}%)"
            )

    snap.local_allowed = len(reasons) == 0
    snap.block_reason  = "; ".join(reasons)
    snap.timestamp     = time.time()

    logger.debug(
        "Resource snap: RAM %.1f/%.1fGB free | VRAM %s | local=%s",
        snap.ram_free_gb, snap.ram_total_gb,
        f"{snap.vram_free_gb:.1f}GB" if snap.vram_free_gb is not None else "N/A",
        snap.local_allowed,
    )
    return snap


async def get_resource_snapshot(force: bool = False) -> ResourceSnapshot:
    """Return a cached snapshot, refreshing if older than CACHE_TTL seconds.

    Thread-safe via asyncio.Lock — concurrent callers wait for one poll
    instead of all spawning their own subprocess.
    """
    global _cache
    async with _cache_lock:
        now = time.time()
        if not force and _cache is not None and (now - _cache.timestamp) < CACHE_TTL:
            return _cache
        # Run blocking I/O in thread pool so event loop isn't blocked
        loop = asyncio.get_event_loop()
        _cache = await loop.run_in_executor(None, _build_snapshot)
        return _cache


async def can_use_local_model(force: bool = False) -> tuple[bool, str]:
    """Quick check: can we safely run Ollama right now?

    Returns:
        (True, "")               — local model is fine to use
        (False, "reason string") — too constrained, use cloud instead
    """
    snap = await get_resource_snapshot(force=force)
    return snap.local_allowed, snap.block_reason


def format_resource_html(snap: ResourceSnapshot) -> str:
    """Telegram HTML summary of current resource state."""
    lines = ["<b>\U0001f5a5\ufe0f System Resources</b>\n"]

    # RAM
    ram_bar = _bar(snap.ram_percent)
    lines.append(
        f"\U0001f9e0 <b>RAM</b>  {snap.ram_used_gb:.1f} / {snap.ram_total_gb:.1f} GB "
        f"({snap.ram_percent:.0f}%) {ram_bar}"
    )
    lines.append(
        f"   free: <b>{snap.ram_free_gb:.1f} GB</b> "
        + ("\u2705" if snap.ram_free_gb >= MIN_FREE_RAM_GB else f"\u26a0\ufe0f &lt; {MIN_FREE_RAM_GB}GB threshold")
    )

    # GPU
    lines.append("")
    if snap.nvml_ok and snap.vram_total_gb is not None:
        vram_bar  = _bar(snap.vram_percent or 0)
        free_pct  = 100.0 - (snap.vram_percent or 0.0)
        vram_ok   = (
            snap.vram_free_gb >= MIN_FREE_VRAM_GB
            and free_pct >= MIN_FREE_VRAM_PCT
        )
        lines.append(
            f"\U0001f3ae <b>GPU</b>  {snap.gpu_name}"
        )
        lines.append(
            f"   VRAM: {snap.vram_used_gb:.1f} / {snap.vram_total_gb:.1f} GB "
            f"({snap.vram_percent:.0f}%) {vram_bar}"
        )
        lines.append(
            f"   free: <b>{snap.vram_free_gb:.1f} GB</b> ({free_pct:.0f}% free) "
            + ("\u2705" if vram_ok else f"\u26a0\ufe0f below threshold")
        )
        if snap.gpu_util_pct is not None:
            lines.append(f"   compute util: <b>{snap.gpu_util_pct:.0f}%</b>")
    else:
        lines.append("\U0001f3ae <b>GPU</b>  not detected (pynvml / nvidia-smi unavailable)")

    # Local model decision
    lines.append("")
    if snap.local_allowed:
        lines.append("\U0001f916 <b>Local Ollama</b>: \u2705 <b>ENABLED</b>")
        lines.append("   gemma3:12b will be used for vision tasks")
    else:
        lines.append("\U0001f916 <b>Local Ollama</b>: \u274c <b>BYPASSED \u2192 cloud fallback</b>")
        lines.append(f"   reason: <i>{snap.block_reason}</i>")

    # Thresholds
    lines.append("")
    lines.append(
        f"<i>thresholds: RAM \u2265{MIN_FREE_RAM_GB}GB free | "
        f"VRAM \u2265{MIN_FREE_VRAM_GB}GB free &amp; \u2265{MIN_FREE_VRAM_PCT:.0f}% free</i>"
    )
    lines.append(
        "<i>override via .env: LOCAL_MIN_FREE_RAM_GB, LOCAL_MIN_FREE_VRAM_GB, LOCAL_MIN_FREE_VRAM_PCT</i>"
    )

    return "\n".join(lines)


def _bar(pct: float, width: int = 8) -> str:
    """ASCII progress bar. pct = 0..100."""
    filled = round(pct / 100 * width)
    filled = max(0, min(width, filled))
    bar = "\u2588" * filled + "\u2591" * (width - filled)
    return f"[{bar}]"
