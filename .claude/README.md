# Claude Code Best Practice

> From vibe coding to agentic engineering — practice makes Claude perfect.

This directory contains the Claude Code best practices implementation including:

- **Commands** (`.claude/commands/`) — Entry point slash commands
- **Agents** (`.claude/agents/`) — Specialized subagents with preloaded skills
- **Skills** (`.claude/skills/`) — Reusable skill modules
- **Hooks** (`.claude/hooks/`) — Lifecycle hook scripts
- **Best Practice** (`.claude/best-practice/`) — Documentation of frontmatter fields and patterns
- **Implementation** (`.claude/implementation/`) — Working examples of the patterns

## Architecture: Command → Agent → Skill

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

## Quick Reference

### Command (Entry Point)
- File: `.claude/commands/<name>.md`
- Frontmatter: `description`, `model`, `allowed-tools`
- Invokes: Agent tool or Skill tool

### Agent (Specialized Worker)
- File: `.claude/agents/<name>.md`
- Frontmatter: `name`, `description`, `allowedTools`, `model`, `skills`, `memory`
- Can have preloaded skills via `skills:` field
- Invoked via: Agent tool

### Skill (Reusable Module)
- File: `.claude/skills/<name>/SKILL.md`
- Frontmatter: `name`, `description`, `user-invocable`, `allowed-tools`
- Two patterns:
  - **Standalone Skill**: Invoked via Skill tool
  - **Agent Skill**: Preloaded into agent via `skills:` field

## Key Concepts

### Execution Contract
Commands and agents use execution contracts to enforce strict workflow:

```
## Execution Contract (non-negotiable)

You MUST complete this command by delegating to the `weather-agent` subagent.
You are forbidden from:
- Fetching weather data yourself
- Skipping Step 1
- Calling `weather-svg-creator` before the agent returns a temperature
```

### Fail-Closed Guardrails
```
**Fail-closed guardrail**: If the agent does not return a numeric temperature
and unit, DO NOT proceed to Step 3. Report the failure to the user and stop.
```

### Tool Allowlisting
Agents can have restricted tool allowlists to enforce proper delegation:

```yaml
allowedTools:
  - "Read"
  - "Skill"
```

This ensures the agent uses skills for capabilities instead of calling tools directly.

## Examples

See the `orchestration-workflow/` directory for a complete working example:
- `/weather-orchestrator` command
- `weather-agent` with `weather-fetcher` skill
- `weather-svg-creator` skill

## Resources

- [Claude Code Documentation](https://code.claude.com/docs)
- [Official Skills Repository](https://github.com/anthropics/skills/tree/main/skills)
- [Claude Code Best Practice (external)](https://github.com/shanraisshan/claude-code-best-practice)