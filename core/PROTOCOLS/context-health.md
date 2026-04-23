# Context Health Monitor

Tracks how full the conversation context is. Prevents the "noticeably dumber after compaction" problem.

## Health Levels

| Level | Range | Action |
|-------|-------|--------|
| 🟢 HEALTHY | 0–40% | Normal operation |
| 🟡 CAUTION | 40–60% | Trigger pre-compaction checkpoint, stop expanding scope |
| 🔴 CRITICAL | 60–80% | Finish current task, then /compact |
| 💀 OVERFLOW | 80%+ | Mandatory /compact before ANY new work |

## Usage

```python
from core.context_health import get_context_monitor

monitor = get_context_monitor("/home/newadmin/swarm-bot")
health = monitor.assess(context_chars=85000)  # or monitor.assess() for auto
print(monitor.format_health_report(health))
# Example: "Context Health: 🟢 HEALTHY | Last checkpoint: 2026-04-16T14:30 | Action: Normal operation."
```

## Mandatory Actions

- **HEALTHY**: Normal operation. Nothing needed.
- **CAUTION**: Run pre-compaction checkpoint before adding new concerns.
- **CRITICAL**: Finish current task. Do not start new features. Run checkpoint then /compact.
- **OVERFLOW**: Do nothing new. Run /compact before ANY action.

## Pre-Compaction Checkpoint Ritual

**WHEN**: CAUTION level (40%) first time, then CRITICAL (60%) mandatory.

```python
from core.checkpoint_runner import run_pre_compaction_checkpoint

await run_pre_compaction_checkpoint(
    task="Adding /budget command",
    decisions=["Using aiosqlite for sync-free DB", "BudgetManager as singleton"],
    modified_files=["handlers/admin.py", "swarms_bot/routing/budget_manager.py"],
    blockers=["Need Bashara to confirm display format"],
    next_steps=["Add /budget handler", "Wire BudgetManager into llm_client"],
    anti_patterns=["Didn't pre-check aiosqlite install"],
    context_percent=0.45,
)
```

**Writes to:**
- `.claude/.checkpoint_index.json` — machine-readable, last 20 checkpoints
- `.claude/memory_bootstrap.md` — human-readable, each session annotated

## Post-Compaction Recovery Order

1. Read `.claude/memory_bootstrap.md`
2. Read `DECISIONS.md`
3. Read `FAILURES.md`
4. `git log --oneline -10`
5. `git status`
6. Reinstantiate Agent Team roles from session tag