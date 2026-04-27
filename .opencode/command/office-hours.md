---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <topic>
description: "Office hours: ask questions about the codebase, architecture, or patterns. Freeform Q&A."
---

# /office-hours — Freeform Q&A about swarm-bot

Ask any question about swarm-bot architecture, patterns, or codebase.

## Usage
```
/office-hours how does the agent loop work
/office-hours why do we use mem0ai instead of raw vector DB
/office-hours explain the fallback chain design
```

## What it answers
- Architecture explanations
- Design pattern rationale
- Why certain choices were made
- How components interact
- Best practices in this codebase

## Swarm-Bot Architecture Context
- **Type**: Python Telegram bot (aiogram 3.x)
- **LLM**: litellm with groq/cerebras fallbacks
- **Memory**: mem0ai episodic + semantic (separate from OpenCode memory)
- **Deployment**: systemd on Ubuntu, not Docker
- **Owner**: Bashara

## Office Hours Output Format
```
## QUESTION
<user's question>

## ANSWER
<detailed explanation>

## RELATED
- [[wiki/architecture/...]]
- core/specific_file.py
```

## Limitations
- Based on current codebase state
- May not reflect future plans
- Best-effort explanations
