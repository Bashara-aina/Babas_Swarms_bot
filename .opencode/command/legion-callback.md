---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <prompt>
description: "Invoke LegionBot with a prompt. Returns full output. Use for Legion-specific tasks."
---

# /legion-callback — Invoke LegionBot

Run a prompt through the LegionBot agent system.

## Usage
```
/legion-callback Analyze the current agent dispatch performance
/legion-callback Review memory usage patterns this week
```

## Requirements
- LegionBot must be running and accessible
- May require authentication

## What it does
1. Sends prompt to LegionBot
2. Returns full response
3. May be slower than local commands

## Differences from /claude-callback
| | /claude-callback | /legion-callback |
|--|-----------------|-----------------|
| Engine | Claude CLI | LegionBot agent |
| Context | Limited | Full session context |
| Speed | Fast | Slower |

## Swarm-Bot Use Cases
- Legion-specific agent orchestration questions
- Session memory analysis
- Multi-agent coordination issues
