---
title: Smoke Results Bucket2
type: concept
status: legacy
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Date**: 2026-04-11 20:35:57'
wikilinks: []
confidence: medium
source: research
---
# Smoke Test Results — Bucket 2: Agent System

**Date**: 2026-04-11 20:35:57
**Files Tested**: `agents/__init__.py`, `core/agent_registry.py`

## Test Results

| Test | Result |
|------|--------|
| `from agents import AGENT_MODELS, FALLBACK_CHAIN` | PASS — No ImportError |
| `from core.agent_registry import LEGACY_FALLBACK_CHAIN` | PASS — No ImportError |
| Agent model count | 22 models (target: >70) |
| Fallback chain count | 22 fallbacks |
| Legacy chain count | 23 agents |

## Verdict

**FAIL** — Agent counts below threshold.

- `AGENT_MODELS`: 22 (expected > 70)
- `LEGACY_FALLBACK_CHAIN`: 23 (expected > 70)

## Log File

`smoke-bucket2-agents-20260411-203557.log`