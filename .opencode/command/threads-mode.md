---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: [topic]
description: "Threads mode: analyze conversation threads, identify patterns, summarize discussions."
---

# /threads-mode — Conversation thread analysis

Analyze message threads and conversation patterns.

## Usage
```
/threads-mode
/threads-mode analyze this session
/threads-mode summarize open decisions
```

## What it does
1. Identifies conversation threads
2. Tracks topic evolution
3. Identifies unresolved questions
4. Summarizes key decisions

## Thread Analysis Output
```
## THREADS_IDENTIFIED
1. LLM fallback strategy — 12 messages — RESOLVED
2. Memory system design — 8 messages — IN_PROGRESS
3. Handler registration — 3 messages — RESOLVED

## KEY_DECISIONS
- Use groq + cerebras fallback chain
- mem0ai for episodic memory
- aiogram 3.x router pattern

## OPEN_QUESTIONS
- Multi-tenant support timeline?
- Redis vs SQLite for memory persistence?
```

## Swarm-Bot Session Tracking
- Session logs: `.wiki/logs/`
- Decision records: `.wiki/decisions/`
- Research notes: `.wiki/research/`

## Constraints
- Depends on available conversation history
- May not capture all nuance
- Best-effort pattern recognition
