# M2.7 Full Capability Activation — Bootstrap Reference
**File:** `core/CLAUDE_M2_BOOTSTRAP.md`
**Purpose:** Standalone M2.7 reference — the infrastructure modules and behavioral
           protocols that live alongside CLAUDE.md. When CLAUDE.md is too crowded,
           move M2.7-specific discipline here and import from CLAUDE.md Section 0a.
**Maintainer:** Bashara + Legion

---

## Infrastructure Modules

| Module | File | What it does |
|--------|------|------|
| Agent Teams | `core/agent_teams.py` | 3-role adversarial reasoning (Planner/Builder/Critic) |
| Skill Harness | `core/skills/harness.py` | TIER 1-4 dynamic skill loading |
| Context Health | `core/context_health.py` | HEALTHY→CAUTION→CRITICAL→OVERFLOW tracking |
| Checkpoint Runner | `core/checkpoint_runner.py` | Pre-compaction save to memory_bootstrap.md |
| Drift Detector | `core/drift_detector.py` | Error accumulation prevention (RED flags) |
| Self-Evolution | `core/self_evolution.py` | FAILURES.md → EVAL_SET.md feedback pipeline |

---

## Bootstrap Files

| File | Purpose |
|------|---------|
| `FAILURES.md` | Seed for M2.7 evaluation set — all failure trajectories |
| `DECISIONS.md` | Architecture Decision Record log |
| `EVAL_SET.md` | Regression tests derived from 5+ FAILURES.md entries |
| `.claude/memory_bootstrap.md` | Pre-compaction checkpoint template |

---

## Quick Reference — When to Call What

```
Context hits 40% (CAUTION):
  from core.checkpoint_runner import run_pre_compaction_checkpoint
  await run_pre_compaction_checkpoint(...)

Context hits 60% (CRITICAL):
  → finish current task
  → python -c "from core.context_health import get_context_monitor; ..."
  → /compact

After any failure:
  from core.self_evolution import get_self_evolution_engine
  await engine.record_failure(task="...", approach="...", ...)

Before starting a plan (Critic adversarial challenges):
  challenges = engine.get_adversarial_challenges("Add /budget command")

Every 5 tool calls (drift check):
  from core.drift_detector import DriftDetector
  detector = DriftDetector()
  detector.set_goal("Add /budget command")
  detector.add_state("Modified handlers/admin.py...")
  detector.increment_tool_calls()
  report = detector.check_drift()
  if detector.should_abort():
      detector.raise_abort()

Skill loading at task start:
  from core.skills.harness import load_skills_for_task, format_skill_declaration
  skills = load_skills_for_task("feature", "cekwajar")
  declaration = format_skill_declaration("feature", "cekwajar")
```

---

## TIER Skill Loading Reference

```
TIER 1 — Always loaded (base skills):
  typescript-strict, next-js-app-router

TIER 2 — By feature type:
  feature:        supabase-realtime, stripe-integration, recharts-dataviz
  bugfix:         debugging-best-practices
  refactor:       refactoring-patterns
  security:       security-audit
  frontend:       shadcn-patterns, ui-ux-pro-max
  backend:        supabase-rls, postgres-best-practices

TIER 3 — By domain:
  cekwajar:       indonesian-market, property-valuation, salary-benchmark
  legion-swarm:    ai-agent-patterns, telegram-bot, litellm-routing
  ml:             ml-integration, numpy-performance

TIER 4 — By quality gate (wildcard always loaded):
  conventional-commits
  security-audit, a11y-compliance, performance-budget
```

---

## Health Level Actions

| Level | Context | Action |
|-------|---------|--------|
| 🟢 HEALTHY | 0–40% | Normal operation |
| 🟡 CAUTION | 40–60% | Run pre-compaction checkpoint. Stop expanding scope |
| 🔴 CRITICAL | 60–80% | Finish task. Run checkpoint. /compact |
| 💀 OVERFLOW | 80%+ | Mandatory /compact before ANY work |

---

## Drift RED FLAGS (stop and realign)

- Work no longer connects to original task
- "Temporary fix" has become the permanent approach
- Scope has silently expanded beyond original request
- An assumption made early has been invalidated
- Solution is more complex than the problem requires
