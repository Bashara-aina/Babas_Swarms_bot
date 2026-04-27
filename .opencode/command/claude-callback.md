---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <prompt>
description: "Invoke Claude (claude -1 --prompt) with a specific prompt. Returns full output."
---

# /claude-callback — Invoke Claude CLI

Run a prompt through the Claude CLI and return the full output.

## Usage
```
/claude-callback Explain the difference between async iterators and async generators in Python
/claude-callback Write a context manager for database connections
```

## Requirements
- `claude` CLI must be installed and authenticated
- `CLAUDE_API_KEY` env var or `claude auth` configured

## What it does
1. Runs `claude -1 --prompt "<prompt>"`
2. Streams and returns full output
3. May be verbose — use for deep dives

## Swarm-Bot Use Cases
- Complex Python logic questions
- Architectural decision help
- Code review deep dives
- Research synthesis

## Limitations
- Cannot access current file context automatically
- Cannot run code or tests
- Returns text only
