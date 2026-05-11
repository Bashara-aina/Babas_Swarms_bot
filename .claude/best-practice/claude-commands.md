# Commands Best Practice

Claude Code commands — frontmatter fields and official built-in slash commands.

## Frontmatter Fields (15)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Display name and `/slash-command` identifier. Defaults to the directory name |
| `description` | string | Recommended | What the command does. Shown in autocomplete |
| `when_to_use` | string | No | Additional context for when to invoke |
| `argument-hint` | string | No | Hint shown during autocomplete (e.g., `[issue-number]`) |
| `arguments` | string/list | No | Named positional arguments for `$name` substitution |
| `disable-model-invocation` | boolean | No | Set `true` to prevent automatic invocation |
| `user-invocable` | boolean | No | Set `false` to hide from the `/` menu |
| `paths` | string/list | No | Glob patterns that limit when this skill is activated |
| `allowed-tools` | string | No | Tools allowed without permission prompts when this command is active |
| `model` | string | No | Model to use when this command runs |
| `effort` | string | No | Override the model effort level when invoked |
| `context` | string | No | Set to `fork` to run in an isolated subagent context |
| `agent` | string | No | Subagent type when `context: fork` is set |
| `shell` | string | No | Shell for shell blocks — `bash` (default) or `powershell` |
| `hooks` | object | No | Lifecycle hooks scoped to this command |

## Official Commands (75+)

Claude Code includes 75+ built-in slash commands including:

| Category | Commands |
|----------|----------|
| Auth | `/login`, `/logout`, `/upgrade` |
| Config | `/config`, `/theme`, `/color`, `/focus`, `/permissions` |
| Context | `/context`, `/cost`, `/extra-usage`, `/insights` |
| Development | `/bug`, `/test`, `/review`, `/explain` |
| Git | `/commit`, `/pr`, `/branch`, `/checkout` |
| Search | `/search`, `/grep`, `/web` |

## Implementation

See [implementation/claude-commands-implementation.md](../implementation/claude-commands-implementation.md)

## Sources

- [Commands — Claude Code Docs](https://code.claude.com/docs/en/slash-commands)
- [CLI reference — Claude Code Docs](https://code.claude.com/docs/en/cli-reference)