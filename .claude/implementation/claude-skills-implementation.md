# Skills Implementation

Two skills are implemented in this repo as part of the **Command → Agent → Skill** architecture pattern, demonstrating two distinct skill invocation patterns.

## Weather SVG Creator (Skill)

**File**: [`.claude/skills/weather-svg-creator/SKILL.md`](../.claude/skills/weather-svg-creator/SKILL.md)

```yaml
---
name: weather-svg-creator
description: Creates an SVG weather card showing the current temperature for Dubai.
  Writes the SVG to orchestration-workflow/weather.svg and updates orchestration-workflow/output.md.
---
```

This is a **skill** — invoked directly by the command via the Skill tool. It receives the temperature data from the conversation context and creates the SVG weather card and output summary.

## Weather Fetcher (Agent Skill)

**File**: [`.claude/skills/weather-fetcher/SKILL.md`](../.claude/skills/weather-fetcher/SKILL.md)

```yaml
---
name: weather-fetcher
description: Instructions for fetching current weather temperature data for Dubai, UAE from Open-Meteo API
user-invocable: false
allowed-tools:
  - "WebFetch(*)"
---
```

This is an **agent skill** — preloaded into the `weather-agent` at startup via the `skills:` frontmatter field. It is NOT invoked directly; instead, it serves as domain knowledge injected into the agent's context. Note `user-invocable: false` which hides it from the `/` command menu.

## Two Skill Patterns

| Pattern | Invocation | Example | Key Difference |
|---------|-----------|---------|----------------|
| **Skill** | `Skill(skill: "name")` | `weather-svg-creator` | Invoked directly via Skill tool |
| **Agent Skill** | Preloaded via `skills:` field | `weather-fetcher` | Injected into agent context at startup |

## How to Use

**Skill** — invoke directly via slash command:

```bash
$ claude
> /weather-svg-creator
```

## How to Implement

Ask Claude to create one for you — it will generate the markdown file with YAML frontmatter and body in `.claude/skills/<skill-name>/SKILL.md`

## Architecture

| Component | Role | This Repo |
|-----------|------|-----------|
| **Command** | Entry point, user interaction | [`/weather-orchestrator`](../.claude/commands/weather-orchestrator.md) |
| **Agent** | Fetches data with preloaded skill | [`weather-agent`](../.claude/agents/weather-agent.md) with [`weather-fetcher`](../.claude/skills/weather-fetcher/SKILL.md) |
| **Skill** | Creates output independently | [`weather-svg-creator`](../.claude/skills/weather-svg-creator/SKILL.md) |