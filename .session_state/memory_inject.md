---
name: memory_inject
description: Session context bootstrap — auto-injected at session start from prior session.
session: session-20260611-opencode-go-proxy
mode: bootstrap
hidden: true
---

# MEMORY INJECT — SESSION BOOTSTRAP
_Generated: 2026-06-11_

## CURRENT ARCHITECTURE

**Proxy:** oc-cc-proxy v0.1.3 on `http://127.0.0.1:4001`
**Backend:** OpenCode Go API (opencode.ai/zen/go/v1)
**Auth:** `OPENCODE_GO_API_KEY` in .env → proxy handles real auth; Claude Code uses dummy key

## ROLE PRESETS (Claude-style tiering)
| Role | Model | Use |
|------|-------|-----|
| Haiku | deepseek-v4-flash | Volume tasks (~80% traffic) |
| Sonnet | deepseek-v4-pro | Daily workhorse |
| Opus | minimax-m3 | Complex orchestration |
| Fable | kimi-k2.6 | Hardest reasoning only |

## MEMORY LAYERS (6-layer system)
1. **L1 Checkpoints** — `.claude-flow/data/checkpoints/` (session snapshots)
2. **L2 ChromaDB** — `data/legion_chroma/` (vector embeddings)
3. **L3 Langmem** — `.claude/` (language memory)
4. **L4 Observations** — `data/observations.db` (behavioral patterns)
5. **L5 GraphRAG** — `.claude-flow/data/auto-memory-store.json` (161 semantic entries)
6. **L6 Mem0 Cloud** — Supabase pgvector (persistent cross-session)

## COMPACTION
- Triggers at 800K tokens (80% of 1M context)
- Reserved: 65K tokens for summary + working room
- Session state persisted to `.session_state/remembered_context.md`

---
_This file is regenerated at every SessionStart._
