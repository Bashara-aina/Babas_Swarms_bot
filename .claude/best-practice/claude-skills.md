# Skills Best Practice

Claude Code skills — frontmatter fields and official bundled skills.

## Frontmatter Fields (15)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Display name and `/slash-command` identifier. Defaults to directory name |
| `description` | string | Recommended | What the skill does. Shown in autocomplete |
| `when_to_use` | string | No | Additional context for when to invoke |
| `argument-hint` | string | No | Hint shown during autocomplete |
| `arguments` | string/list | No | Named positional arguments for `$name` substitution |
| `disable-model-invocation` | boolean | No | Set `true` to prevent automatic invocation |
| `user-invocable` | boolean | No | Set `false` to hide from `/` menu — for agent preloading |
| `allowed-tools` | string | No | Tools allowed without permission prompts |
| `model` | string | No | Model to use when this skill runs |
| `effort` | string | No | Override the model effort level |
| `context` | string | No | Set to `fork` to run in an isolated subagent context |
| `agent` | string | No | Subagent type when `context: fork` is set |
| `hooks` | object | No | Lifecycle hooks scoped to this skill |
| `paths` | string/list | No | Glob patterns that limit when this skill auto-activates |
| `shell` | string | No | Shell for shell blocks — `bash` (default) or `powershell` |

## Two Skill Patterns

| Pattern | Invocation | Example | Key Difference |
|---------|-----------|---------|----------------|
| **Skill** | `Skill(skill: "name")` | `weather-svg-creator` | Invoked directly via Skill tool |
| **Agent Skill** | Preloaded via `skills:` field | `weather-fetcher` | Injected into agent context at startup, `user-invocable: false` |

## Official Bundled Skills (6)

| # | Skill | Description |
|---|-------|-------------|
| 1 | `simplify` | Review changed code for reuse, quality, and efficiency |
| 2 | `batch` | Run commands across multiple files in bulk |
| 3 | `debug` | Debug failing commands or code issues |
| 4 | `loop` | Run a prompt on a recurring interval (up to 3 days) |
| 5 | `claude-api` | Build apps with the Claude API or Anthropic SDK |
| 6 | `fewer-permission-prompts` | Scan transcripts for common read-only calls |

## Implementation

See [implementation/claude-skills-implementation.md](../implementation/claude-skills-implementation.md)

## Sources

- [Skills — Claude Code Docs](https://code.claude.com/docs/en/skills)
- [Official Skills Repository](https://github.com/anthropics/skills/tree/main/skills)