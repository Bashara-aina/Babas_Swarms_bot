# Commands Implementation

The weather orchestrator command is implemented in this repo as the entry point of the **Command → Agent → Skill** architecture pattern.

## Weather Orchestrator

**File**: [`.claude/commands/weather-orchestrator.md`](../.claude/commands/weather-orchestrator.md)

```yaml
---
description: Fetch weather data for Dubai and create an SVG weather card
model: haiku
---
```

The command orchestrates the entire workflow:
1. Asks the user for their temperature unit preference (Celsius or Fahrenheit)
2. Invokes the `weather-agent` via the Agent tool
3. Invokes the `weather-svg-creator` skill via the Skill tool

## How to Use

```bash
$ claude
> /weather-orchestrator
```

## How to Implement

Ask Claude to create one for you — it will generate the markdown file with YAML frontmatter and body in `.claude/commands/<name>.md`

## Execution Contract Pattern

The weather orchestrator uses an **Execution Contract** pattern:

```
## Execution Contract (non-negotiable)

You MUST complete this command by delegating to the `weather-agent` subagent.
You are forbidden from:
- Fetching weather data yourself via Bash, WebFetch, or any other tool
- Skipping Step 1 (the user's unit preference is required input to the agent)
- Calling `weather-svg-creator` before the agent returns a temperature

If you cannot invoke the Agent tool, stop and report the error to the user.
Do not improvise.
```

This pattern ensures:
1. Claude follows the intended workflow strictly
2. Each step is completed before proceeding to the next
3. Failures are reported, not hidden

## Architecture

The weather orchestrator is the **Command** in the Command → Agent → Skill orchestration pattern:

| Component | Role | This Repo |
|-----------|------|-----------|
| **Command** | Entry point, user interaction | [`/weather-orchestrator`](../.claude/commands/weather-orchestrator.md) |
| **Agent** | Fetches data with preloaded skill | [`weather-agent`](../.claude/agents/weather-agent.md) with [`weather-fetcher`](../.claude/skills/weather-fetcher/SKILL.md) |
| **Skill** | Creates output independently | [`weather-svg-creator`](../.claude/skills/weather-svg-creator/SKILL.md) |