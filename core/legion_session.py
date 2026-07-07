"""
core/legion_session.py
======================
Session lifecycle manager for LEGION. Integrates with the existing
core/autonomy/ boot_sequence and session_teardown, and provides
OpenCode-specific lifecycle hooks.

Handles:
- Boot: memory hydration, context assessment, task classification
- During-session: tool call counting, pre-compaction triggers
- End-of-session: summary generation, skill writes, wiki updates, git commit
"""

from __future__ import annotations

import time

from core.legion_state import (
    AVAILABLE_SKILLS,
    HERMES_SKILLS,
    SESSION_CONTEXT,
    SESSION_SUMMARY,
    TEMPORAL_CONTEXT,
    append_state,
    write_session_summary,
    write_state,
)
from core.self_evolution import get_self_evolution_engine

CONTEXT_LIMIT = 4_194_304  # 1,048,576 tokens * 4 chars/token = deepseek-v4-flash native window
COMPACTION_TRIGGER_PCT = 0.60
CRITICAL_COMPACTION_PCT = 0.80


def assess_context_health(context_chars: int) -> str:
    """
    Return health status string based on context usage.
    🟢 <40% | 🟡 40-60% | 🔴 60-80% | 💀 >80%
    """
    ratio = context_chars / CONTEXT_LIMIT
    if ratio < 0.40:
        return "🟢"
    elif ratio < 0.60:
        return "🟡"
    elif ratio < 0.80:
        return "🔴"
    return "💀"


def should_compact(context_chars: int) -> tuple[bool, str]:
    """
    Returns (should_compact, reason).
    Checks both percentage thresholds and stale memory files.
    """
    ratio = context_chars / CONTEXT_LIMIT
    if ratio >= CRITICAL_COMPACTION_PCT:
        return True, f"Context {ratio:.0%} > 80% — compact IMMEDIATELY"
    if ratio >= COMPACTION_TRIGGER_PCT:
        return True, f"Context {ratio:.0%} > 60% — start pre-compaction checkpoint"
    if _stale_memory():
        return True, "Memory files stale >4h — refresh before new task"
    return False, ""


def _stale_memory() -> bool:
    """Check if any /tmp/legion_ memory file is stale."""
    for path in (SESSION_CONTEXT, TEMPORAL_CONTEXT, AVAILABLE_SKILLS, HERMES_SKILLS):
        if path.exists():
            age = time.time() - path.stat().st_mtime
            if age > 4 * 3600:
                return True
    return False


async def session_boot() -> dict:
    """
    Run at OpenCode session start. Returns dict with:
    - context_health: str (🟢🟡🔴💀)
    - skills_loaded: bool
    - memory_hydrated: bool
    - recent_tasks: list[str]
    """
    from core.autonomy.boot_sequence import run_boot_sequence

    result = await run_boot_sequence()
    _refresh_stale_memory_files()
    context_chars = _estimate_context_chars()
    return {
        "context_health": assess_context_health(context_chars),
        "context_pct": f"{context_chars / CONTEXT_LIMIT:.0%}",
        "skills_loaded": AVAILABLE_SKILLS.exists(),
        "memory_hydrated": SESSION_CONTEXT.exists(),
        "ruflo_healthy": result.healthy,
        "session_restored": result.session_restored,
    }


def _refresh_stale_memory_files() -> None:
    """Refresh stale /tmp/legion_*.txt files from hermes if needed."""
    from tools.mem0_client import get_mem0

    if _stale_memory():
        mem = get_mem0()
        if mem:
            try:
                results = mem.search("recent session context", limit=10)
                if results:
                    lines = [f"- {r['text']}" for r in results[:10]]
                    write_state("session_context", "\n".join(lines))
            except Exception:
                pass


def _estimate_context_chars() -> int:
    """Estimate current conversation context in characters.

    Reads actual session data instead of using process RSS (which was meaningless).
    Checks: session messages, session.json, or /tmp/legion_* files in order.
    """
    import json
    from pathlib import Path

    # Method 1: session_messages.json (ContextCompactor tracking)
    msgs_path = Path(".claude-flow/data/session_messages.json")
    if msgs_path.exists():
        try:
            msgs = json.loads(msgs_path.read_text())
            if msgs:
                return sum(len(m.get("content", "")) for m in msgs[-50:])
        except Exception:
            pass

    # Method 2: current.json (session.js tracking)
    sess_path = Path(".claude-flow/data/current.json")
    if sess_path.exists():
        try:
            data = json.loads(sess_path.read_text())
            ctx = data.get("context", {})
            query = ctx.get("lastUserQuery", "")
            decisions = ctx.get("decisions", [])
            files = ctx.get("filesChanged", [])
            return len(query) + sum(len(d) for d in decisions) + sum(len(f) for f in files) + data.get("metrics", {}).get("edits", 0) * 500
        except Exception:
            pass

    # Method 3: /tmp/legion_* files
    total = 0
    for path in (SESSION_CONTEXT, TEMPORAL_CONTEXT, AVAILABLE_SKILLS, HERMES_SKILLS):
        if path.exists():
            try:
                total += len(path.read_text())
            except Exception:
                pass
    return total


class SessionMetrics:
    """Tracks metrics during a session for end-of-session summary."""

    def __init__(self) -> None:
        self.tool_calls = 0
        self.files_changed: list[str] = []
        self.decisions: list[str] = []
        self.errors: list[str] = []
        self.accomplished: list[str] = []
        self.start_time = time.time()
        self._last_compaction_check = time.time()

    def record_tool_call(self, tool_name: str) -> None:
        self.tool_calls += 1
        if self.tool_calls % 5 == 0:
            self._check_compaction()

    def record_file_change(self, path: str) -> None:
        if path not in self.files_changed:
            self.files_changed.append(path)

    def record_decision(self, decision: str) -> None:
        if decision not in self.decisions:
            self.decisions.append(decision)

    def record_error(self, error: str) -> None:
        self.errors.append(error)

    def record_accomplished(self, item: str) -> None:
        if item not in self.accomplished:
            self.accomplished.append(item)

    def _check_compaction(self) -> None:
        now = time.time()
        if now - self._last_compaction_check < 60:
            return
        self._last_compaction_check = now
        context_chars = _estimate_context_chars()
        if should_compact(context_chars)[0]:
            append_state(
                "session_context",
                f"[COMPACTION WARNING] {assess_context_health(context_chars)} at tool call {self.tool_calls}",
            )

    async def end_session(self) -> dict:
        """
        Run at session end. Writes summary, calls self-evolution,
        triggers async workers.
        """
        duration = time.time() - self.start_time
        write_session_summary(
            accomplished=self.accomplished,
            decisions=self.decisions,
            files_changed=self.files_changed,
            errors=self.errors,
            open_questions=[],
            tool_calls=self.tool_calls,
        )
        try:
            engine = get_self_evolution_engine("/home/newadmin/swarm-bot")
            await engine.record_decision(
                title=f"session-{time.strftime('%Y-%m-%d')}",
                context=f"Duration: {duration:.0f}s, Tool calls: {self.tool_calls}",
                decision="; ".join(self.accomplished[:5]) if self.accomplished else "no tasks completed",
                rationale="end-of-session",
            )
        except Exception:
            pass
        return {
            "duration_seconds": round(duration),
            "tool_calls": self.tool_calls,
            "files_changed": len(self.files_changed),
            "summary_written": SESSION_SUMMARY.exists(),
        }


def detect_goodbye(message: str) -> bool:
    """
    Detect session-end signals in user message.
    Covers English, Indonesian, and casual告别 variants.
    """
    message = message.lower().strip()
    goodbye_signals = [
        "done", "bye", "that's all", "thanks", "thank you",
        "selesai", "makasih", "ok done", "goodbye", "see you",
        "sampai jumpa", "足", "完毕", "終わり",
    ]
    return any(message.endswith(s) or message == s for s in goodbye_signals)


def detect_task_type(message: str) -> str:
    """
    Fast keyword-based task classification for OpenCode routing.
    Returns: MEMORY | CODE | RESEARCH | MULTI_STEP | ARCHITECTURAL | UNKNOWN
    """
    msg = message.lower()
    memory_kw = ["remember", "save", "note for later", "do you remember", "what did we"]
    if any(k in msg for k in memory_kw):
        return "MEMORY"
    code_kw = ["fix", "implement", "add", "remove", "change", "update", "write code"]
    if any(k in msg for k in code_kw):
        return "CODE"
    research_kw = ["research", "find out", "look up", "search", "what is", "how does"]
    if any(k in msg for k in research_kw):
        return "RESEARCH"
    if _count_steps_estimate(msg) > 2:
        return "MULTI_STEP"
    arch_kw = ["refactor", "architecture", "design", "system", "restructure"]
    if any(k in msg for k in arch_kw):
        return "ARCHITECTURAL"
    return "UNKNOWN"


def _count_steps_estimate(message: str) -> int:
    """Rough estimate of step count from message content."""
    step_indicators = [
        " then ", " next ", " after that ", " step ",
        " firstly", " first", " second", " third",
        " phases", " stage",
    ]
    count = sum(message.lower().count(s) for s in step_indicators)
    return min(count, 10)


_session_metrics: SessionMetrics | None = None


def get_session_metrics() -> SessionMetrics:
    global _session_metrics
    if _session_metrics is None:
        _session_metrics = SessionMetrics()
    return _session_metrics
