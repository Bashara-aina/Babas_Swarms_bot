---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/self-knowledge/legion/003-git-history.md",
  "reason": "daily_fast_scan: score=0.150 < 0.3",
  "score": 0.15000000000000002,
  "quarantined_at": "2026-04-12T01:00:01.402183"
}
---

---
title: "Legion/SwarmBot Git History"
source_type: CODE_EXTRACTION
extracted_from: swarm-bot
date: 2026-04-11
tags: [legion, git, history, commits, development]
---

# SwarmBot Git History

## Recent Commits (2026)

### 2026-04-11
- `0fb8fca` CHORE: move confirmed dead files to graveyard
- `5fc27d2` CHORE: pre-dead-file-purge checkpoint 2026-04-11

### 2026-04-10
- `e9262e8` chore: sync all local changes excluding env files
- `e074f45` feat(legion): wire soul/debate/memory routing and remove dead code
- `e8a7b72` docs: add comprehensive CLAUDE.md implementation status
- `baa21ae` feat(P3-2): add smoke tests for main.py and core bot
- `6817086` feat(P1-3): remove MCP functionality from legion_extras
- `089ef0e` feat(P1-2): rename /sessions to /legion_sessions
- `d362fdf` feat(P1-1): add /vcsearch command to search voice transcripts
- `1c0678e` feat(P0-3): add ruflo process manager with health monitoring
- `39416f1` feat(P2-3,P2-4): register admin_handlers router
- `501e892` feat(P2-3,P2-4): add /budget and /soul commands in admin_handlers.py

### 2026-04-09
- `005d770` fix(P1-4,P1-5): add langchain-community>=0.3.0 and pin browser-use==0.1.40
- `54ce4da` feat(P0-1): register debate_handlers router in handlers/__init__.py
- `a1dbf6c` feat(P0-1): add handlers/debate_handlers.py — /debate and /opinion commands
- `11085de` Replace CLAUDE.md with Legion v10 master engineering prompt
- `96e3f6b` v9 Soul Transplant: Intent routing, debate engine, and proactive curiosity
- `e901e73` feat: Legion Soul Transplant — 8-phase upgrade (Phases 1-8 complete)

### 2026-04-08
- `c7e2e76` Enhance episodic memory extraction and conversation history handling
- `e45d711` fix(personality): eliminate duplicate persona injection and wire real conversation history
- `7b3d0b4` feat: Jarvis-style continuity — working memory, cognition, ranked skills
- `1a1eb59` ci: bump Actions to Node 24–compatible majors

### 2026-03 (Selected)
- `da34d63` feat(legion): tier-3 stack — task router, Jarvis, simulation, MCP, memory, tools
- `d3a05bd` Add codebase understanding, relationship memory, and character voice systems
- `66d0f42` fix: wire Legion's personality pipeline and add Jarvis-level capabilities
- `71fc04a` feat: Jarvis upgrade — soul, memory, proactive, disagreement, multi-agent router
- `10e6733` fix: correct mem0_search import in proactive_initiator
- `92cb9ab` feat: add get_quick_brief() to briefing.py for proactive initiator
- `ea03f38` fix: wire proactive_initiator into main.py on_startup — Legion now talks first
- `626aa43` feat: add proactive_initiator.py — Legion talks first (Jarvis-style check-ins)
- `ff8f7b4` Improve character enforcer with robust error handling
- `345a3f8` fix: wire SystemPromptBuilder correctly + emotion→temp + multi-turn history
- `6c52e50` 🧠 Tier 1 Soul Transplant: masterprompt, system_prompt_builder, composio_client, rumahlabuh_crew

## Key Architectural Decisions (from commit messages)

### Soul Engine (v9-v10)
- Intent routing with debate engine
- Proactive curiosity engine
- Jarvis-style continuity with working memory

### Router Refactoring
- Removed MCP functionality
- Added debate_handlers with 6 debate personas
- /sessions renamed to /legion_sessions

### Testing Infrastructure
- Added smoke tests for main.py
- asyncio.run fixes for Py3.11+

### Self-Upgrade Capability
- GitHub trending analysis
- Hot-reload and rollback
- Weekly trend scanning

---
*Extracted: 2026-04-11 by @worker*
