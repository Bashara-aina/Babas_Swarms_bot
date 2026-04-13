---
title: legion-bot
type: project
status: active
tags: [telegram, bot, ai, multi-agent]
created: 2026-04-13
updated: 2026-04-13
summary: Legion is Bashara's permanent AI coworker - a Telegram bot with multi-agent orchestration, memory, and autonomous task execution.
wikilinks: [[entities/opencode.md]], [[concepts/multi-agent-orchestration.md]], [[architecture/legion-module-map.md]]
confidence: high
source: implementation
---

# Legion Bot

## TL;DR
Legion is a Telegram AI bot with 76+ specialized agents across 9 departments, integrated with OpenCode for autonomous coding, and backed by ChromaDB for memory.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Interface | Telegram (aiogram 3.4+) |
| LLM Routing | LiteLLM + OpenRouter |
| Memory | ChromaDB + mem0 + SQLite |
| Code Agent | OpenCode CLI |
| Deployment | systemd service |

## Key Capabilities

- **Multi-agent swarm**: 87 agents for complex research
- **Memory**: Conversation, session transcripts, long-term facts
- **Skills**: 30+ skills (web search, code review, research)
- **Media**: Vision, voice, video analysis
- **Autonomy**: Full coding pipeline via OpenCode

## Directory Structure

```
main.py              # Bot entry point
core/                # Core modules
handlers/            # 45+ handler files
agents/              # 76+ agents
tools/               # External integrations
llm_client.py        # LLM routing
```

## Related Pages

- [[architecture/legion-module-map.md]] — Module architecture
- [[concepts/multi-agent-orchestration.md]] — Agent system
- [[entities/opencode.md]] — Code agent integration
