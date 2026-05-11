# Sub-agents Implementation

The weather agent is implemented in this repo as an example of the **Command → Agent → Skill** architecture pattern, demonstrating two distinct skill patterns.

## Weather Agent

**File**: [`.claude/agents/weather-agent.md`](../.claude/agents/weather-agent.md)

```yaml
---
name: weather-agent
description: Use this agent PROACTIVELY when you need to fetch weather data for Dubai, UAE. This agent fetches real-time temperature from Open-Meteo using its preloaded weather-fetcher skill.
allowedTools:
  - "Read"
  - "Skill"
model: sonnet
color: green
maxTurns: 5
permissionMode: acceptEdits
memory: project
skills:
  - weather-fetcher
---
```

The agent has one preloaded skill (`weather-fetcher`) that provides instructions for fetching from Open-Meteo. It returns the temperature value and unit to the calling command.

## Key Implementation Details

### Agent Skills vs Standalone Skills

The `weather-fetcher` skill is an **agent skill** — it is preloaded into the `weather-agent` at startup via the `skills:` frontmatter field. This means:

1. The skill's instructions are injected into the agent's context at startup
2. The skill is NOT shown in the `/` command menu (`user-invocable: false`)
3. The agent uses the skill via the Skill tool, not direct invocation

### Tool Allowlisting

The `weather-agent` has a restricted tool allowlist:
- `Read` — for reading files if needed
- `Skill` — for invoking skills

This is intentional — the agent should NOT call WebFetch, WebSearch, or any HTTP tools directly. If it needs weather data, it MUST use the `weather-fetcher` skill.

## How to Use

```
$ claude
> what is the weather in dubai?
```

## How to Implement

You can create an agent by asking Claude to create one for you — it will generate the markdown file with YAML frontmatter and body in `.claude/agents/<name>.md`

## Architecture

The weather agent is the **Agent** in the Command → Agent → Skill orchestration pattern:

| Component | Role | This Repo |
|-----------|------|-----------|
| **Command** | Entry point, user interaction | [`/weather-orchestrator`](../.claude/commands/weather-orchestrator.md) |
| **Agent** | Fetches data with preloaded skill | [`weather-agent`](../.claude/agents/weather-agent.md) with [`weather-fetcher`](../.claude/skills/weather-fetcher/SKILL.md) |
| **Skill** | Creates output independently | [`weather-svg-creator`](../.claude/skills/weather-svg-creator/SKILL.md) |