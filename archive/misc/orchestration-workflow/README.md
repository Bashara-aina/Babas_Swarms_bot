# Orchestration Workflow

> **Architecture Pattern**: Command → Agent → Skill

This directory contains the implementation of the **Command → Agent → Skill** orchestration pattern, demonstrating how OpenCode commands can delegate to sub-agents which use preloaded skills, and then call standalone skills for output generation.

## Overview

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│     Command     │ ──▶  │      Agent       │ ──▶  │      Skill      │
│ (weather-       │      │ (weather-agent)  │      │ (weather-svg-   │
│  orchestrator)  │      │                  │      │  creator)        │
└─────────────────┘      └──────────────────┘      └─────────────────┘
        │                        │                         │
   Entry point,          Fetches data using           Creates visual
   user interaction      preloaded skill             output
```

## Components

| Component | Role | File |
|-----------|------|------|
| **Command** | Entry point, user interaction | [`.claude/commands/weather-orchestrator.md`](../.claude/commands/weather-orchestrator.md) |
| **Agent** | Fetches data with preloaded skill (agent skill) | [`.claude/agents/weather-agent.md`](../.claude/agents/weather-agent.md) with [`weather-fetcher`](../.claude/skills/weather-fetcher/SKILL.md) |
| **Skill** | Creates output independently (skill) | [`.claude/skills/weather-svg-creator/SKILL.md`](../.claude/skills/weather-svg-creator/SKILL.md) |

## Two Skill Patterns

| Pattern | Invocation | Example | Key Difference |
|---------|-----------|---------|----------------|
| **Agent Skill** | Preloaded via `skills:` field | `weather-fetcher` | Injected into agent context at startup, `user-invocable: false` |
| **Skill** | Invoked directly via Skill tool | `weather-svg-creator` | Called directly by command or agent |

## Workflow Example

### Weather Orchestrator

1. **Command** asks user for temperature unit preference (Celsius or Fahrenheit)
2. **Command** invokes `weather-agent` via the Agent tool
3. **Agent** uses its preloaded `weather-fetcher` skill to fetch temperature
4. **Agent** returns temperature to command
5. **Command** invokes `weather-svg-creator` skill to create visual output

## Best Practice Documentation

See:
- [Best Practice: Sub-agents](../best-practice/claude-subagents.md)
- [Best Practice: Commands](../best-practice/claude-commands.md)
- [Best Practice: Skills](../best-practice/claude-skills.md)
- [Implementation: Sub-agents](../implementation/claude-subagents-implementation.md)
- [Implementation: Commands](../implementation/claude-commands-implementation.md)
- [Implementation: Skills](../implementation/claude-skills-implementation.md)