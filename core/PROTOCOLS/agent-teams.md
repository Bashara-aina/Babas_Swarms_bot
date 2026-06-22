# M3 Agent Teams Protocol

Every complex task runs through a 3-role adversarial team. This is how we get to correct — not just done.

## Role Definitions

| Role | Owner | Never Does |
|------|-------|------------|
| **PLANNER** | Goal, spec, success criteria | Writes code |
| **BUILDER** | Executes against locked SPEC | Invents architecture |
| **CRITIC** | Adversarial quality gate | Skips reviews |

## Adversarial Reasoning Protocol

```
Before Planner finalizes SPEC:
  → Critic reviews → attacks assumptions → Planner resolves → SPEC locked

Before Builder ships:
  → Critic reviews → finds issues → Builder fixes → Planner approves
```

**NEVER skip the Critic step** when doing architectural work or multi-file changes.

Role discipline: Planner locks goals → Builder implements → Critic reviews → Planner resolves. Roles MUST NOT drift.

## Usage

```python
from core.agent_teams import get_agent_team

team = get_agent_team()
session = await team.run("Add /budget command with spend tracking")

# session.spec — Planner's spec
# session.build_result — Builder's output
# session.critic_report — Critic's issue list (P0→P3)
# session.resolution — Planner's resolution of Critic's issues
```

## Self-Critique Checklist (run before any architectural decision)

1. **Reasoning quality**: Rate confidence 1–10. If <7, revise before presenting.
2. **Blind spots**: Explicitly name what you DON'T know.
3. **Future simulation**: Would this make sense in 3 months? With a new engineer? Under production load?
4. **Assumption audit**: What must be true for this to work? Any invalidated?

When confidence is low: "I'm 60% confident this handles X — here's why, and here are the conditions where it would break."