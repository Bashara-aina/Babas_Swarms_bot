---
name: using-superpowers
description: >-
  Meta-skill that establishes the Superpowers SDLC workflow. Always check
  skills before acting. Use when starting any new task or responding to any
  user request.
---

If you were dispatched as a subagent to execute a specific task, skip this skill.

If you think there is even a 1% chance a skill might apply to what you are doing, you MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

## Workflow Priority

1. **Process skills first** (brainstorming, systematic-debugging) — determine HOW to approach the task
2. **Implementation skills second** (writing-plans, executing-plans, tdd) — guide execution
3. **Review/finish skills last** (requesting-code-review, finishing-a-development-branch)

## Standard SDLC Flow

brainstorming → writing-plans → executing-plans (or subagent-driven-development) → tdd → requesting-code-review → finishing-a-development-branch

## Red Flags

These thoughts mean STOP — you're rationalizing:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I can check git/files quickly" | Files lack conversation context. Check for skills. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## Data Locations
- Specs: `.superpowers/specs/`
- Plans: `.superpowers/plans/`
- Observations: `.superpowers/homunculus/observations/`
