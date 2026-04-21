---
name: legiona-global-memory
description: Cross-session persistent memory for Legiona agent — survives across all Claude Code sessions
type: reference
---

# Legiona Global Memory
Persists across ALL sessions. Updated by `evolve()` after each agent run.

## Project Facts
Architecture-level facts about swarm-bot (populated by evolve() after each agent run). Key systems: aiogram 3.4+ async Telegram bot, litellm 1.57+ LLM routing, 76+ specialized agents across 9 departments, 45+ handler routers, GitNexus code intelligence indexed.

## Architecture Decisions

- **MMX-CLI native tools** (`lib/legiona/tools/mmx_tools.py`): mmx-cli wraps 7 MiniMax modalities (text, vision, speech, music, search, video, image-gen). Tool loop uses `subprocess.run` with `NO_COLOR=1 NON_INTERACTIVE=1` for deterministic output. API key set via `mmx config set api_key=<key>` — not env vars. Registered as 3 tools in registry.py: `mmx_vision`, `mmx_search`, `mmx_speech` (8 tools total). Temperature always 1.0 + reasoning_split=True for M2.7.

## Known Gotchas
Bugs, edge cases, and workaround rules (populated by evolve() — tracked in .wiki/decisions/ and .wiki/logs/).

## Self-Evolved Rules
Rules synced from memory/rules.md by evolve() after each agent run. Includes anti-loop protocols, confidence gates, and surface-specific overrides. See .wiki/EVOLVED_RULES.md for full reference.
