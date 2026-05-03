"""
core/cognition_boot.py
======================
OpenCode Cognitive Boot Sequence — Legion's thinking startup.

PART 1 of the Ultimate Internal Master Prompt:
  STEP 1 — IDENTITY LOAD
  STEP 2 — MEMORY HYDRATION
  STEP 3 — CONTEXT HEALTH ASSESSMENT
  STEP 4 — TASK CLASSIFICATION

This module is the OpenCode-specific boot (runs before ruflo's boot_sequence.py).
ruflo's boot_sequence.py handles the agent/worker/swarm boot.
This module handles the cognitive/perception boot for the primary LLM.

All steps run silently. No status messages to Bashara.
Total target: < 5 seconds.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path("/home/newadmin/swarm-bot")
SOUL_MD = REPO_ROOT / "SOUL.md"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
MEMORY_BOOTSTRAP = REPO_ROOT / ".claude" / "memory_bootstrap.md"
WIKI_HEALTH_SCRIPT = REPO_ROOT / ".claude" / "scripts" / "wiki_health.py"

TMP_ROOT = Path("/tmp")

# HOT memory files (TIER 1)
SESSION_CONTEXT   = TMP_ROOT / "legion_session_context.txt"
HERMES_SKILLS    = TMP_ROOT / "legion_hermes_skills.txt"
TEMPORAL_CTX     = TMP_ROOT / "legion_temporal_context.txt"
AVAILABLE_SKILLS = TMP_ROOT / "legion_available_skills.txt"
SESSION_SUMMARY  = TMP_ROOT / "legion_session_summary.txt"

CONTEXT_LIMIT = 22000

# ── Boot Result ────────────────────────────────────────────────────────────────


@dataclass
class CognitionBootResult:
    identity_loaded: bool = False
    soul_content: str = ""
    memory_hydrated: bool = False
    skills_loaded: bool = False
    context_health: str = "🟢"
    context_pct: float = 0.0
    task_type: str = "UNKNOWN"
    errors: list[str] = field(default_factory=list)
    boot_time_ms: float = 0.0


# ── STEP 1: Identity Load ─────────────────────────────────────────────────────

SOUL_CACHE: str | None = None
CLAUDE_SECTION0_CACHE: str | None = None


def _load_identity() -> tuple[str, str]:
    """Load SOUL.md and CLAUDE.md Section 0. Cached after first read."""
    global SOUL_CACHE, CLAUDE_SECTION0_CACHE

    if SOUL_CACHE is None:
        try:
            SOUL_CACHE = SOUL_MD.read_text() if SOUL_MD.exists() else ""
        except Exception as e:
            logger.warning("Could not read SOUL.md: %s", e)
            SOUL_CACHE = ""

    if CLAUDE_SECTION0_CACHE is None:
        try:
            text = CLAUDE_MD.read_text() if CLAUDE_MD.exists() else ""
            # Section 0 is everything up to "## SECTION 1"
            idx = text.find("\n## SECTION 1")
            CLAUDE_SECTION0_CACHE = text[:idx] if idx > 0 else text[:2000]
        except Exception as e:
            logger.warning("Could not read CLAUDE.md Section 0: %s", e)
            CLAUDE_SECTION0_CACHE = ""

    return SOUL_CACHE, CLAUDE_SECTION0_CACHE


# ── STEP 2: Memory Hydration ──────────────────────────────────────────────────

_hermes_client = None


def _get_hermes_client():
    """Lazy-load hermes MCP client."""
    global _hermes_client
    if _hermes_client is None:
        try:
            from core.mcp_client import MCPClient
            _hermes_client = MCPClient()
        except Exception as e:
            logger.debug("Hermes MCP unavailable: %s", e)
            _hermes_client = False
    return _hermes_client if _hermes_client else None


async def _hydrate_memory() -> dict[str, Any]:
    """
    Hydrate HOT memory (TIER 1) from persistent stores (TIER 4-5).
    Reads existing /tmp/ files first; refreshes stale ones from source.
    Returns dict with hydration status.
    """
    results: dict[str, Any] = {}

    # Check age of existing HOT files
    stale_threshold = 4 * 3600  # 4 hours
    now = time.time()

    def is_stale(path: Path) -> bool:
        if not path.exists():
            return True
        return (now - path.stat().st_mtime) > stale_threshold

    # SESSION_CONTEXT: hydrate from mem0 if stale
    if is_stale(SESSION_CONTEXT):
        client = _get_hermes_client()
        if client:
            try:
                mem_lines = await _fetch_mem0_context(limit=10)
                SESSION_CONTEXT.write_text("\n".join(mem_lines))
                results["session_context_refreshed"] = True
            except Exception as e:
                logger.debug("mem0 hydration failed: %s", e)
                results["session_context_refreshed"] = False

    # HERMES_SKILLS: refresh from hermes
    if is_stale(HERMES_SKILLS):
        try:
            skill_lines = await _fetch_hermes_skills()
            HERMES_SKILLS.write_text("\n".join(skill_lines))
            results["hermes_skills_refreshed"] = True
        except Exception as e:
            logger.debug("hermes skills refresh failed: %s", e)
            results["hermes_skills_refreshed"] = False

    # TEMPORAL_CTX: git log if stale
    if is_stale(TEMPORAL_CTX):
        try:
            import subprocess
            git_lines = subprocess.run(
                ["git", "-C", str(REPO_ROOT), "log", "--oneline", "-20",
                 "--since=2 weeks ago"],
                capture_output=True, text=True, timeout=5
            ).stdout.splitlines()
            TEMPORAL_CTX.write_text("\n".join(git_lines))
            results["temporal_ctx_refreshed"] = True
        except Exception as e:
            logger.debug("git temporal context failed: %s", e)
            results["temporal_ctx_refreshed"] = False

    # AVAILABLE_SKILLS: refresh from skill indexer
    if is_stale(AVAILABLE_SKILLS):
        try:
            from core.legion_skill_indexer import index_skills
            await index_skills()
            results["skills_index_refreshed"] = True
        except Exception as e:
            logger.debug("skill index refresh failed: %s", e)
            results["skills_index_refreshed"] = False

    return results


async def _fetch_mem0_context(limit: int = 10) -> list[str]:
    """Fetch recent mem0 memories about Bashara."""
    lines: list[str] = []
    try:
        from tools.mem0_client import get_mem0
        mem = get_mem0()
        if mem:
            results = mem.search("recent session context preferences", limit=limit)
            lines = [f"- {r.get('text', '')}" for r in results if r.get('text')]
    except Exception:
        pass
    return lines


async def _fetch_hermes_skills() -> list[str]:
    """Fetch hermes skill list."""
    lines: list[str] = []
    try:
        client = _get_hermes_client()
        if client:
            result = await client.call_tool("hermes", "hermes_list_skills", {})
            # Parse output — skill lines format: "SKILL: title | TAGS: ..."
            if isinstance(result, list) and result:
                for item in result:
                    text = getattr(item, 'text', str(result))
                    for line in text.splitlines():
                        if line.strip() and ":" in line:
                            lines.append(line.strip())
    except Exception:
        pass
    return lines[:20]  # top 20


# ── STEP 3: Context Health ─────────────────────────────────────────────────────


def assess_context(context_chars: int) -> tuple[str, float]:
    """Return (health_emoji, pct) for context usage."""
    pct = context_chars / CONTEXT_LIMIT
    if pct < 0.40:
        return "🟢", pct
    elif pct < 0.60:
        return "🟡", pct
    elif pct < 0.80:
        return "🔴", pct
    return "💀", pct


def _estimate_context_chars() -> int:
    """Rough estimate of context size in characters."""
    try:
        import psutil
        proc = psutil.Process()
        mem_info = proc.memory_info()
        return int(mem_info.rss / 4)
    except Exception:
        return 0


# ── STEP 4: Task Classification ───────────────────────────────────────────────


def classify_task(message: str) -> str:
    """
    Fast keyword-based task classification.
    Returns: MEMORY | CODE | RESEARCH | MULTI_STEP | ARCHITECTURAL | UNKNOWN
    """
    msg = message.lower()
    memory_kw = ["remember", "save", "note for later", "do you remember",
                 "what did we", "what have we", "recall"]
    if any(k in msg for k in memory_kw):
        return "MEMORY"
    code_kw = ["fix", "implement", "add", "remove", "change", "update",
               "write code", "edit", "refactor"]
    if any(k in msg for k in code_kw):
        return "CODE"
    research_kw = ["research", "find out", "look up", "search", "what is",
                   "how does", "explain", "tell me about"]
    if any(k in msg for k in research_kw):
        return "RESEARCH"
    step_indicators = [" then ", " next ", " after that ", " step ",
                       " phases", " stages", " first", " second"]
    if sum(msg.count(s) for s in step_indicators) >= 2:
        return "MULTI_STEP"
    arch_kw = ["refactor", "architecture", "design", "system",
               "restructure", "redesign"]
    if any(k in msg for k in arch_kw):
        return "ARCHITECTURAL"
    return "UNKNOWN"


# ── MAIN BOOT FUNCTION ────────────────────────────────────────────────────────


async def cognition_boot(first_message: str = "") -> CognitionBootResult:
    """
    Run the full cognitive boot sequence.

    This is called at OpenCode session start, before processing any message.
    It is separate from ruflo's boot_sequence.py (which handles agent/worker boot).

    Args:
        first_message: Bashara's first message (used for task classification)

    Returns:
        CognitionBootResult with identity, memory, and context state
    """
    start = time.monotonic()
    result = CognitionBootResult()

    # STEP 1 — Identity Load (fast, cached)
    soul_content, _claude0 = _load_identity()
    result.identity_loaded = bool(soul_content)
    result.soul_content = soul_content[:500]  # first 500 chars for context

    # STEP 2 — Memory Hydration (parallel with identity)
    hydration_results = await asyncio.gather(
        _hydrate_memory(),
        return_exceptions=True,
    )
    mem_results = hydration_results[0] if isinstance(hydration_results[0], dict) else {}
    result.memory_hydrated = bool(mem_results)
    result.skills_loaded = AVAILABLE_SKILLS.exists()

    # STEP 3 — Context Health
    context_chars = _estimate_context_chars()
    result.context_health, result.context_pct = assess_context(context_chars)

    # STEP 4 — Task Classification
    if first_message:
        result.task_type = classify_task(first_message)

    result.boot_time_ms = (time.monotonic() - start) * 1000
    logger.info(
        "Cognition boot: identity=%s memory=%s skills=%s health=%s%.0f task=%s %.0fms",
        result.identity_loaded,
        result.memory_hydrated,
        result.skills_loaded,
        result.context_health,
        result.context_pct * 100,
        result.task_type,
        result.boot_time_ms,
    )

    return result


# ── HOT MEMORY READERS (used by agents after boot) ────────────────────────────


def read_hot_memory(key: str) -> str:
    """
    Read a HOT memory file by key name.
    key: session_context | hermes_skills | temporal_ctx | available_skills | ...
    """
    file_map = {
        "session_context":   SESSION_CONTEXT,
        "hermes_skills":    HERMES_SKILLS,
        "temporal_ctx":    TEMPORAL_CTX,
        "available_skills": AVAILABLE_SKILLS,
        "session_summary":  SESSION_SUMMARY,
        "plan":             TMP_ROOT / "legion_plan.md",
        "build_result":     TMP_ROOT / "legion_build_result.md",
        "review":           TMP_ROOT / "legion_review.md",
        "verify":           TMP_ROOT / "legion_verify.md",
        "research":          TMP_ROOT / "legion_research.md",
    }
    path = file_map.get(key)
    if path is None:
        return ""
    try:
        return path.read_text() if path.exists() else ""
    except Exception:
        return ""


def write_hot_memory(key: str, content: str) -> bool:
    """Write to a HOT memory file. Returns True on success."""
    file_map = {
        "session_context":   SESSION_CONTEXT,
        "hermes_skills":    HERMES_SKILLS,
        "temporal_ctx":    TEMPORAL_CTX,
        "available_skills": AVAILABLE_SKILLS,
        "session_summary":  SESSION_SUMMARY,
        "plan":             TMP_ROOT / "legion_plan.md",
        "build_result":     TMP_ROOT / "legion_build_result.md",
        "review":           TMP_ROOT / "legion_review.md",
        "verify":           TMP_ROOT / "legion_verify.md",
        "research":          TMP_ROOT / "legion_research.md",
        "precompact":        TMP_ROOT / "legion_precompact_checkpoint.md",
    }
    path = file_map.get(key)
    if path is None:
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return True
    except Exception:
        return False
