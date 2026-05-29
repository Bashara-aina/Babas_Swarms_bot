"""M2.7 Context Health Monitor — tracks Claude Code session context levels.

Prevents context pollution which causes M2.7 to become "noticeably dumber
after compaction" (r/openclaw community finding, April 2026).

CONTEXT HEALTH LEVELS:
  🟢 HEALTHY    (0–40%): normal operation
  🟡 CAUTION    (40–60%): trigger pre-compaction checkpoint, stop new concerns
  🔴 CRITICAL   (60–80%): finish current task, then /compact
  💀 OVERFLOW   (80%+):   mandatory /compact before ANY new work

Designed to be called from CLAUDE.md behavioral guidance.
Writes checkpoints to .claude/memory_bootstrap.md.

Reference: M2.7 Full Capability Activation — Context Management (Section C1-C2)
"""

from __future__ import annotations

import datetime
import json
from collections import deque
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

MEMORY_BOOTSTRAP = Path(__file__).parent.parent / ".claude" / "memory_bootstrap.md"


# ---------------------------------------------------------------------------
# Health levels
# ---------------------------------------------------------------------------


class HealthLevel(StrEnum):
    HEALTHY = "HEALTHY"
    CAUTION = "CAUTION"
    CRITICAL = "CRITICAL"
    OVERFLOW = "OVERFLOW"


# ---------------------------------------------------------------------------
# Checkpoint model
# ---------------------------------------------------------------------------


@dataclass
class Checkpoint:
    """A pre-compaction checkpoint record."""

    timestamp: str
    session_description: str
    task: str
    context_percent_estimate: float
    health_level: HealthLevel
    decisions: list[str]
    modified_files: list[str]
    blockers: list[str]
    next_steps: list[str]
    anti_patterns: list[str]


# ---------------------------------------------------------------------------
# Monitor
# ---------------------------------------------------------------------------


class ContextHealthMonitor:
    """Tracks Claude Code session context health.

    Usage:
        monitor = ContextHealthMonitor("/path/to/project")

        # After each significant action:
        health = monitor.assess()
        if monitor.should_checkpoint():
            monitor.run_checkpoint(...)

        # After compaction:
        checkpoint = monitor.load_latest_checkpoint()
    """

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.bootstrap_file = self.project_root / ".claude" / "memory_bootstrap.md"
        self.checkpoint_file = self.project_root / ".claude" / ".context_checkpoints.json"

        self._checkpoints: deque[Checkpoint] = deque(maxlen=100)
        self._last_checkpoint_at: str | None = None
        self._load_checkpoints()

    # ---------------------------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------------------------

    def _load_checkpoints(self) -> None:
        """Load checkpoint history from JSON file."""
        if self.checkpoint_file.exists():
            try:
                data = json.loads(self.checkpoint_file.read_text())
                self._checkpoints = deque(
                    Checkpoint(**c) for c in data.get("checkpoints", [])
                )
                self._last_checkpoint_at = data.get("last_checkpoint_at")
            except Exception:
                self._checkpoints = deque()

    def _save_checkpoints(self) -> None:
        """Persist checkpoint history to JSON."""
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "checkpoints": [
                {
                    "timestamp": c.timestamp,
                    "session_description": c.session_description,
                    "task": c.task,
                    "context_percent_estimate": c.context_percent_estimate,
                    "health_level": c.health_level.value,
                    "decisions": c.decisions,
                    "modified_files": c.modified_files,
                    "blockers": c.blockers,
                    "next_steps": c.next_steps,
                    "anti_patterns": c.anti_patterns,
                }
                for c in list(self._checkpoints)[-20:]  # keep last 20
            ],
            "last_checkpoint_at": self._last_checkpoint_at,
        }
        self.checkpoint_file.write_text(json.dumps(data, indent=2))

    # ---------------------------------------------------------------------------
    # Assessment
    # ---------------------------------------------------------------------------

    def assess(self, context_chars: int = 0, total_chars: int = 200_000) -> HealthLevel:
        """Assess current context health level.

        Args:
            context_chars: Estimated current context character count
            total_chars: Estimated total capacity (default 200k)

        Returns:
            HealthLevel enum value

        Note: For Claude Code / OpenCode, context percentage is approximate.
        For more accurate assessment, count actual messages in conversation.
        """
        if context_chars <= 0:
            return HealthLevel.HEALTHY

        ratio = context_chars / total_chars

        if ratio < 0.40:
            return HealthLevel.HEALTHY
        elif ratio < 0.60:
            return HealthLevel.CAUTION
        elif ratio < 0.80:
            return HealthLevel.CRITICAL
        else:
            return HealthLevel.OVERFLOW

    def should_checkpoint(self, current_health: HealthLevel | None = None) -> bool:
        """Return True if a pre-compaction checkpoint should run.

        Triggers when:
        - Health hits CAUTION (40%) for the first time
        - Health hits CRITICAL (60%) for the first time
        - 30 minutes have passed since last checkpoint (preventative)
        """
        if current_health is None:
            current_health = self.assess()

        # Never checkpoint in HEALTHY
        if current_health == HealthLevel.HEALTHY:
            return False

        # Always checkpoint if new CAUTION or worse and last checkpoint was HEALTHY
        if self._last_checkpoint_at is None:
            return current_health != HealthLevel.HEALTHY

        # Check time-based trigger (30 min = 1800 seconds)
        last = datetime.datetime.fromisoformat(self._last_checkpoint_at)
        elapsed = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))) - last
        if elapsed.total_seconds() > 1800:
            return True

        # Trigger at health transitions
        return current_health in (HealthLevel.CAUTION, HealthLevel.CRITICAL, HealthLevel.OVERFLOW)

    def get_health_emoji(self, level: HealthLevel) -> str:
        """Return emoji for health level."""
        return {
            HealthLevel.HEALTHY: "🟢",
            HealthLevel.CAUTION: "🟡",
            HealthLevel.CRITICAL: "🔴",
            HealthLevel.OVERFLOW: "💀",
        }.get(level, "⚪")

    # ---------------------------------------------------------------------------
    # Checkpoint operations
    # ---------------------------------------------------------------------------

    def run_checkpoint(
        self,
        task: str,
        session_description: str,
        decisions: list[str],
        modified_files: list[str],
        blockers: list[str],
        next_steps: list[str],
        anti_patterns: list[str],
        context_percent_estimate: float = 0.0,
    ) -> Checkpoint:
        """Run pre-compaction checkpoint — append to memory_bootstrap.md.

        This is the main entry point for CLAUDE.md Section 0d checkpoint ritual.
        """
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
        timestamp = now.isoformat()
        health = self.assess()

        checkpoint = Checkpoint(
            timestamp=timestamp,
            session_description=session_description,
            task=task,
            context_percent_estimate=context_percent_estimate,
            health_level=health,
            decisions=decisions,
            modified_files=modified_files,
            blockers=blockers,
            next_steps=next_steps,
            anti_patterns=anti_patterns,
        )

        self._checkpoints.append(checkpoint)
        self._last_checkpoint_at = timestamp
        self._save_checkpoints()

        # Also append to memory_bootstrap.md for human readability
        self._append_to_bootstrap_md(checkpoint)

        return checkpoint

    def _append_to_bootstrap_md(self, checkpoint: Checkpoint) -> None:
        """Append checkpoint to the human-readable memory_bootstrap.md."""
        if not self.bootstrap_file.exists():
            # Write template header if file doesn't exist
            self.bootstrap_file.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "",
            f"## {checkpoint.timestamp[:16]} — {checkpoint.session_description}",
            "",
            "### Current Goal",
            checkpoint.task,
            "",
            "### Decisions Made This Session",
        ]
        lines.extend(f"- {d}" for d in checkpoint.decisions)
        lines.extend(["", "### Current State", ""])

        emoji = self.get_health_emoji(checkpoint.health_level)
        lines.append(f"🟢 Working: [fill in] {emoji} {checkpoint.health_level.value}")
        lines.append(f"📁 Modified: {', '.join(checkpoint.modified_files) or 'none'}")
        lines.extend(["", "### Open Risks / Blockers", ""])
        lines.extend(f"- {b}" for b in checkpoint.blockers)
        lines.extend(["", "### Next Planned Steps", ""])
        for i, step in enumerate(checkpoint.next_steps, 1):
            lines.append(f"{i}. {step}")
        lines.extend(["", "### Anti-Patterns Discovered", ""])
        lines.extend(f"- {a}" for a in checkpoint.anti_patterns)
        lines.append("---")

        try:
            with open(self.bootstrap_file, "a", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except Exception:
            pass  # Non-critical — checkpoint JSON is authoritative

    def load_latest_checkpoint(self) -> Checkpoint | None:
        """Load most recent checkpoint (for post-compaction recovery)."""
        return self._checkpoints[-1] if self._checkpoints else None

    def load_checkpoint_history(self, limit: int = 5) -> list[Checkpoint]:
        """Load last N checkpoints."""
        return list(self._checkpoints)[-limit:]

    def format_health_report(self, current_health: HealthLevel | None = None) -> str:
        """Format a human-readable health status report."""
        if current_health is None:
            current_health = self.assess()

        emoji = self.get_health_emoji(current_health)
        last_ck = self.load_latest_checkpoint()
        last_time = last_ck.timestamp[:16] if last_ck else "never"

        actions = {
            HealthLevel.HEALTHY: "Normal operation.",
            HealthLevel.CAUTION: "⚠️ Trigger pre-compaction checkpoint. Stop adding new concerns.",
            HealthLevel.CRITICAL: "🔴 Finish current task, then /compact. Do not start new features.",
            HealthLevel.OVERFLOW: "💀 Mandatory /compact before ANY new work.",
        }

        lines = [
            f"Context Health: {emoji} {current_health.value}",
            f"Last checkpoint: {last_time}",
            f"Action: {actions.get(current_health, 'Unknown')}",
        ]
        return " | ".join(lines)


# ---------------------------------------------------------------------------
# Convenience singleton
# ---------------------------------------------------------------------------

_monitor: ContextHealthMonitor | None = None


def get_context_monitor(project_root: str | None = None) -> ContextHealthMonitor:
    """Return global ContextHealthMonitor singleton."""
    global _monitor
    if _monitor is None:
        if project_root is None:
            project_root = str(Path(__file__).parent.parent)
        _monitor = ContextHealthMonitor(project_root)
    return _monitor
