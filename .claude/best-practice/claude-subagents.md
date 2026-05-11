# Sub-agents Best Practice

Claude Code subagents — frontmatter fields and official built-in agent types.

## Frontmatter Fields (16)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique identifier using lowercase letters and hyphens |
| `description` | string | Yes | When to invoke. Use `"PROACTIVELY"` for auto-invocation by Claude |
| `tools` | string/list | No | Comma-separated allowlist of tools (e.g., `Read`, `Write`, `Edit`, `Bash`). Inherits all tools if omitted. Supports `Agent(agent_type)` syntax to restrict spawnable subagents |
| `disallowedTools` | string/list | No | Tools to deny, removed from inherited or specified list |
| `model` | string | No | Model to use: `sonnet`, `opus`, `haiku`, a full model ID, or `inherit` (default) |
| `permissionMode` | string | No | Permission mode: `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, or `plan` |
| `maxTurns` | integer | No | Maximum number of agentic turns before the subagent stops |
| `skills` | list | No | Skill names to preload into agent context at startup (full content injected) |
| `mcpServers` | list | No | MCP servers for this subagent — server name strings or inline `{name: config}` objects |
| `hooks` | object | No | Lifecycle hooks scoped to this subagent |
| `memory` | string | No | Persistent memory scope: `user`, `project`, or `local` |
| `background` | boolean | No | Set to `true` to always run as a background task (default: `false`) |
| `effort` | string | No | Effort level override when this subagent is active: `low`, `medium`, `high`, `xhigh`, `max` |
| `isolation` | string | No | Set to `"worktree"` to run in a temporary git worktree |
| `initialPrompt` | string | No | Auto-submitted as the first user turn when this agent runs as the main session agent |
| `color` | string | No | Display color for the subagent in the task list: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, or `cyan` |

## Official Agents (5)

| # | Agent | Model | Tools | Description |
|---|-------|-------|-------|-------------|
| 1 | `general-purpose` | inherit | All | Complex multi-step tasks — the default agent type |
| 2 | `Explore` | haiku | Read-only | Fast codebase search and exploration |
| 3 | `Plan` | inherit | Read-only | Pre-planning research in plan mode |
| 4 | `statusline-setup` | sonnet | Read, Edit | Configures the status line setting |
| 5 | `claude-code-guide` | haiku | Glob, Grep, Read, WebFetch, WebSearch | Answers questions about Claude Code features |

## Implementation

See [implementation/claude-subagents-implementation.md](../implementation/claude-subagents-implementation.md)

## Sources

- [Create custom subagents — Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [CLI reference — Claude Code Docs](https://code.claude.com/docs/en/cli-reference)