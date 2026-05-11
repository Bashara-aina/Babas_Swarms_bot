# Settings Implementation

This file documents the settings configuration for the Claude Code best practice implementation.

## Global Settings

**File**: [`.claude/settings.json`](../.claude/settings.json)

```json
{
  "disableAllHooks": false,
  "permissions": {
    "allow": ["Edit(*)", "Write(*)", "Bash(npm *)"],
    "deny": [],
    "ask": ["Bash(rm *)"]
  },
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...]
  }
}
```

## Key Settings Explained

### Permissions

The permissions object controls what tools can be used without prompting:

- **allow**: Tools that can run without prompting
- **deny**: Tools that are blocked
- **ask**: Tools that require user confirmation

### Hooks

Hooks are defined in settings and run at specific lifecycle events:

```json
"hooks": {
  "PreToolUse": [{
    "hooks": [{
      "type": "command",
      "command": "python3 ${CLAUDE_PROJECT_DIR}/.claude/hooks/scripts/hooks.py",
      "timeout": 5000,
      "async": true
    }]
  }]
}
```

### Spinner Verbs

Custom text shown during tool execution:

```json
"spinnerVerbs": {
  "mode": "replace",
  "verbs": ["Admiring code", "Learning patterns", "Studying implementation"]
}
```

### Status Line

Custom status line configuration:

```json
"statusLine": {
  "type": "command",
  "command": "echo 'Custom status'",
  "padding": 0
}
```

## Implementation Notes

The hooks script at `.claude/hooks/scripts/hooks.py` is a reference implementation that:
1. Logs hook events for debugging
2. Can be extended for project-specific automation
3. Runs asynchronously to avoid blocking

## Best Practice

See [../best-practice/claude-settings.md](../best-practice/claude-settings.md)