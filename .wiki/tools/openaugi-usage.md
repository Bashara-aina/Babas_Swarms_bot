---
title: Openaugi Usage
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- tools
created: '2026-04-14'
updated: '2026-04-14'
summary: 'Source: ~/swarm-bot/.wiki/tools/openaugi'
wikilinks: []
confidence: medium
source: research
---
# OpenAugi — Notes to Agent Tasks
Source: ~/swarm-bot/.wiki/tools/openaugi
Purpose: Extracts [[task]] items from Obsidian notes and dispatches as AI agent jobs

## How to Use
- Tag any note line with #agent-task
- Run: python ~/swarm-bot/.wiki/tools/openaugi/main.py --vault ~/swarm-bot/.wiki
- Tasks auto-dispatch to OpenCode agents

## Integration with SwarmBot
- Place task notes in ~/swarm-bot/.wiki/prompts/
- Use [[link]] syntax to connect related tasks
- Agent reads and executes automatically via MCP

## Architecture
- Converts Obsidian notes into actionable agent tasks
- Uses MCP (Model Context Protocol) for tool communication
- SQLite Vec for semantic search of task embeddings
