# Settings Best Practice

Claude Code settings — `.claude/settings.json` configuration options.

## Top-Level Settings

| Setting | Type | Description |
|---------|------|-------------|
| `disableAllHooks` | boolean | Disable all hooks when `true` |
| `permissions` | object | Allow, deny, and ask rules for tool permissions |
| `spinnerVerbs` | object | Custom spinner text during tool execution |
| `spinnerTipsOverride` | object | Custom tips shown during spinner |
| `plansDirectory` | string | Directory for plan output (default: `./plans`) |
| `outputStyle` | string | Output style: `stream`, `print`, `explanatory` |
| `statusLine` | object | Custom status line configuration |
| `attribution` | object | Commit and PR attribution settings |
| `spinnerTipsEnabled` | boolean | Enable/disable spinner tips |
| `respectGitignore` | boolean | Ignore gitignored files in searches |
| `env` | object | Environment variables for hooks |
| `enableAllProjectMcpServers` | boolean | Enable all MCP servers in project |
| `hooks` | object | Global lifecycle hooks |
| `mcpServers` | object | Project MCP server configurations |

## Permissions

```json
{
  "permissions": {
    "allow": ["Edit(*)", "Write(*)", "Bash(npm *)", "WebFetch(domain:github.com)"],
    "deny": ["Bash(rm -rf *)", "Bash(mkfs *)"],
    "ask": ["Bash(*)"]
  }
}
```

## Hooks

All available hook events:

| Hook | Description |
|------|-------------|
| `PreToolUse` | Before a tool is called |
| `PostToolUse` | After a tool completes |
| `PostToolUseFailure` | After a tool fails |
| `UserPromptSubmit` | When user submits a prompt |
| `Notification` | When a notification occurs |
| `Stop` | When the session stops |
| `SubagentStart` | When a subagent starts |
| `SubagentStop` | When a subagent stops |
| `PreCompact` | Before context compaction |
| `PostCompact` | After context compaction |
| `SessionStart` | When session starts |
| `SessionEnd` | When session ends |
| `Setup` | During initial setup |
| `TeammateIdle` | When a teammate becomes idle |
| `TaskCreated` | When a task is created |
| `TaskCompleted` | When a task completes |
| `ConfigChange` | When configuration changes |
| `PermissionRequest` | When a permission is requested |

## Implementation

See [implementation/claude-settings-implementation.md](../implementation/claude-settings-implementation.md)

## Sources

- [Settings — Claude Code Docs](https://code.claude.com/docs/en/settings)
- [Permissions — Claude Code Docs](https://code.claude.com/docs/en/permissions)
- [Model Config — Claude Code Docs](https://code.claude.com/docs/en/model-config)