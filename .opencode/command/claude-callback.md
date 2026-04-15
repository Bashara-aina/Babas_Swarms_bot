---
name: claude-callback
description: Spawn Claude Code as sub-agent from OpenCode
type: command
tags: [callback, claude, bridge]
created: 2026-04-16
---

# Claude Callback Command

After task completion, if `@claude` directive was found:

1. Parse the directive via `extract_claude_directive(result_text)`
2. Call `spawn_claude_from_opencode(result_text, depth=N)`
3. Write Claude Code result to `.wiki/claude-code/sessions/`
4. Return combined result to the parent pipeline
