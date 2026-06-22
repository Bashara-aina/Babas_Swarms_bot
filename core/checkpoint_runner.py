"""M3 Pre-Compaction Checkpoint Runner.

Exposes the pre-compaction checkpoint ritual as an importable async module.
Used by CLAUDE.md Section 0d — run this at 60% context before /compact.

Writes structured markdown to .claude/memory_bootstrap.md.

Reference: M3 Full Capability Activation — Pre-Compaction Checkpoint (Section C2)
"""

from __future__ import annotations

import datetime
import json
from dataclasses import dataclass
from pathlib import Path

MEMORY_BOOTSTRAP = Path.home() / ".claude" / "memory_bootstrap.md"
CHECKPOINT_INDEX = Path(__file__).parent.parent / ".claude" / ".checkpoint_index.json"


# ---------------------------------------------------------------------------
# Checkpoint data model
# ---------------------------------------------------------------------------


@dataclass
class Checkpoint:
    """A single pre-compaction checkpoint record."""

    timestamp: str
    session_tag: str
    current_goal: str
    decisions: list[str]
    modified_files: list[str]
    blockers: list[str]
    next_steps: list[str]
    anti_patterns: list[str]
    context_percent: float = 0.0




# ---------------------------------------------------------------------------
# Pre-compaction checkpoint runner
# ---------------------------------------------------------------------------


async def run_pre_compaction_checkpoint(
    task: str,
    decisions: list[str],
    modified_files: list[str],
    blockers: list[str],
    next_steps: list[str],
    anti_patterns: list[str],
    session_tag: str | None = None,
    context_percent: float = 0.0,
) -> Checkpoint:
    """Run pre-compaction checkpoint — the M3 mandatory ritual before /compact.

    Call this when context hits CAUTION (40%) or CRITICAL (60%).
    Writes to both .claude/memory_bootstrap.md (human-readable) and
    .claude/.checkpoint_index.json (machine-readable).

    Args:
        task: Current goal / what is being worked on
        decisions: Architectural decisions made this session
        modified_files: Files touched, with brief change summaries
        blockers: Open risks / blockers / dependencies
        next_steps: Ordered list of what comes next
        anti_patterns: What failed this session — never repeat
        session_tag: Optional short label (e.g., "m2.7-activation")
        context_percent: Estimated context fill percentage

    Returns:
        Checkpoint dataclass (also saved to disk)

    Example call site (from CLAUDE.md):
        from core.checkpoint_runner import run_pre_compaction_checkpoint
        await run_pre_compaction_checkpoint(
            task="M3 full capability activation",
            decisions=["Added AgentTeams orchestrator", "Skill harness TIER system"],
            modified_files=["core/agent_teams.py", "core/skills/harness.py"],
            blockers=["Awaiting Bashara review of CLAUDE.md changes"],
            next_steps=["Verify all modules", "Run smoke tests"],
            anti_patterns=["Didn't pre-check skill availability before promising"],
            context_percent=0.45,
        )
    """
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    timestamp = now.isoformat()

    checkpoint = Checkpoint(
        timestamp=timestamp,
        session_tag=session_tag or "default",
        current_goal=task,
        decisions=decisions,
        modified_files=modified_files,
        blockers=blockers,
        next_steps=next_steps,
        anti_patterns=anti_patterns,
        context_percent=context_percent,
    )

    # Write to machine-readable index (append to list, keep last 20)
    _write_checkpoint_index(checkpoint)

    # Write to human-readable bootstrap
    _append_to_memory_bootstrap(checkpoint)

    return checkpoint


def _write_checkpoint_index(checkpoint: Checkpoint) -> None:
    """Append checkpoint to .checkpoint_index.json (machine-readable)."""
    CHECKPOINT_INDEX.parent.mkdir(parents=True, exist_ok=True)

    existing: list[dict] = []
    if CHECKPOINT_INDEX.exists():
        try:
            existing = json.loads(CHECKPOINT_INDEX.read_text())
        except Exception:
            existing = []

    # Serialize checkpoint (dataclass → dict)
    entry = {
        "timestamp": checkpoint.timestamp,
        "session_tag": checkpoint.session_tag,
        "current_goal": checkpoint.current_goal,
        "decisions": checkpoint.decisions,
        "modified_files": checkpoint.modified_files,
        "blockers": checkpoint.blockers,
        "next_steps": checkpoint.next_steps,
        "anti_patterns": checkpoint.anti_patterns,
        "context_percent": checkpoint.context_percent,
    }

    existing.append(entry)

    # Keep last 20
    existing = existing[-20:]

    CHECKPOINT_INDEX.write_text(json.dumps(existing, indent=2))


def _append_to_memory_bootstrap(checkpoint: Checkpoint) -> None:
    """Append checkpoint to memory_bootstrap.md (human-readable)."""
    MEMORY_BOOTSTRAP.parent.mkdir(parents=True, exist_ok=True)

    # Ensure file exists with header
    if not MEMORY_BOOTSTRAP.exists():
        MEMORY_BOOTSTRAP.write_text(
            "# M3 Memory Bootstrap\n"
            "# Pre-compaction checkpoints — survives context compaction\n\n"
            "## Template\n"
            "Copy and fill for each session. Reload after /compact.\n\n---\n\n"
        )

    lines = [
        f"## {checkpoint.timestamp[:16]} — {checkpoint.session_tag}",
        "",
        "### Current Goal",
        checkpoint.current_goal,
        "",
        "### Decisions Made This Session",
    ]
    lines.extend(f"- {d}" for d in checkpoint.decisions)
    lines.extend(["", "### Modified Files", ""])
    lines.extend(f"- {f}" for f in checkpoint.modified_files)
    lines.extend(["", "### Open Risks / Blockers", ""])
    lines.extend(f"- {b}" for b in checkpoint.blockers)
    lines.extend(["", "### Next Planned Steps", ""])
    for i, step in enumerate(checkpoint.next_steps, 1):
        lines.append(f"{i}. {step}")
    lines.extend(["", "### Anti-Patterns Discovered", ""])
    lines.extend(f"- {a}" for a in checkpoint.anti_patterns)
    lines.append(f"Context: ~{int(checkpoint.context_percent * 100)}% fill")
    lines.append("---")
    lines.append("")

    with open(MEMORY_BOOTSTRAP, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Post-compaction recovery
# ---------------------------------------------------------------------------


def load_latest_checkpoint() -> Checkpoint | None:
    """Load most recent checkpoint for post-compaction recovery."""
    if not CHECKPOINT_INDEX.exists():
        return None

    try:
        existing = json.loads(CHECKPOINT_INDEX.read_text())
        if not existing:
            return None
        last = existing[-1]
        return Checkpoint(**last)
    except Exception:
        return None


def load_checkpoint_history(limit: int = 5) -> list[Checkpoint]:
    """Load last N checkpoints."""
    if not CHECKPOINT_INDEX.exists():
        return []

    try:
        existing = json.loads(CHECKPOINT_INDEX.read_text())
        checkpoints = [Checkpoint(**e) for e in existing[-limit:]]
        return checkpoints
    except Exception:
        return []


def format_checkpoint_summary(checkpoint: Checkpoint) -> str:
    """Format a one-line summary of a checkpoint for display."""
    return (
        f"[{checkpoint.timestamp[:10]}] {checkpoint.session_tag}: "
        f"{checkpoint.current_goal[:60]}"
        + ("..." if len(checkpoint.current_goal) > 60 else "")
        + f" | {len(checkpoint.modified_files)} files | "
        + f"{len(checkpoint.next_steps)} next steps"
    )
