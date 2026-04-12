---
title: data-privacy-guide
domain: data-analytics
impact_score: 8
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 440
---

# Data Privacy Guide

## ONE-LINE SUMMARY
User data flows: Telegram ID as pseudonymous identifier, conversation transcripts in SQLite, memories in SQLite, no encryption at rest, budget tracking in-memory only.

## FACTS

### User Identity
- **Primary identifier**: Telegram user ID (integer) — pseudonymous, not directly identifying
- **Username**: `msg.from_user.username` optionally captured in `main.py:95` — not stored in transcripts
- **Allowed user enforcement**: `is_allowed()` checks `msg.from_user.id == ALLOWED_USER_ID` (single user bot)
- **No email, phone, or real name stored** in any SQLite database

### Data Stored

**`data/session_transcripts.db`** (core/session/transcript.py):
- `thread_id` TEXT — conversation thread identifier
- `user_id` TEXT NOT NULL — Telegram user ID string
- `role` TEXT NOT NULL — 'user' or 'assistant'
- `content` TEXT NOT NULL — message content, truncated to 8000 chars
- `model_used` TEXT — which LLM model handled it
- `timestamp` REAL — Unix timestamp

**`~/.legion_memory.db`** (tools/memory.py):
- `text` TEXT — user memories (manually saved via /remember)
- `tags` TEXT — comma-separated tags
- `source` TEXT — 'manual', 'conversation', etc.
- `tfidf` TEXT — JSON TF-IDF vector for search
- created/accessed timestamps
- NOT encrypted at rest (SQLite)

**BudgetManager in-memory** (swarms_bot/routing/budget_manager.py):
- List of CostEntry: timestamp, agent, model, cost_usd, tokens_in, tokens_out, task_type
- Max 10000 entries, FIFO trim
- Lost on restart — no persistence

**Observability stats** (core/observability/__init__.py):
- `_PROVIDER_STATS`: {calls, tokens, latency_ms, errors} per provider
- No user ID attached

### PII Exposure Points

| Location | PII Risk | Current State |
|----------|----------|---------------|
| Structured JSON logs | User message content logged verbatim | CONFIRMED |
| session_transcripts.db | Full conversation content | CONFIRMED |
| memory.py SQLite | User memories (manual saves) | CONFIRMED |
| Telegram API calls | Bot token in env | SAFE (env only) |
| Supabase client | Service role key in env | SAFE (env only) |
| BudgetManager | No PII stored | SAFE |
| Observability metrics | No PII stored | SAFE |

### Third-Party Data Flows

**Mem0** (tools/mem0_client.py):
- Sends `user_id` and `content` to Mem0 API
- user_id is Telegram ID string — could be pseudonymous but linkable across sessions
- Content is user message text

**OpenViking** (tools/viking_context.py):
- Sends `user_id` and conversation content to OpenViking
- Same privacy concern as Mem0

**AgentOps** (core/observability/__init__.py):
- Optional — only active if `AGENTOPS_API_KEY` set
- Records: agent name, provider, latency_ms, tokens, success
- No message content — only metadata

**Supabase** (tools/supabase_client.py):
- Used for external business data (rumahlabuh.com)
- Bot uses service role key — bypasses RLS
- No user Telegram data stored in Supabase

## LEGION BEHAVIOR RULES
1. Telegram user ID is the only user identifier used — pseudonymous by design
2. No encryption at rest for SQLite files — physical access = readable
3. Budget tracking is ephemeral — lost on restart
4. Third-party memory services (Mem0, OpenViking) receive user content — privacy implications for multi-user deployments
5. PII in structured logs — user message text appears in swarm-bot.log

## EXAMPLES
Privacy audit query — find all PII logged:
```bash
grep -r "from_user" data/session_transcripts.db  # no direct PII
grep "msg.from_user" handlers/  # telemetry only
```

## ANTI-PATTERNS
1. Telegram username not currently stored but `msg.from_user.username` IS captured in main.py — potential drift
2. Memory export to Obsidian exports ALL memories as .md files — includes potentially sensitive content
3. No data retention policy — session_transcripts.db grows indefinitely
4. Memory auto-extraction runs on every message > 200 chars — more data sent to OpenViking/Mem0 than necessary

## PRIVACY GAPS
1. **No data retention/deletion policy** — session_transcripts.db never auto-purges
2. **No PII scrubbing in logs** — structured logger emits user message text verbatim
3. **No encryption at rest** — SQLite files readable by anyone with filesystem access
4. **Third-party memory services** — no DPA in place for Mem0/OpenViking
5. **No consent mechanism** — user cannot view/delete their data

## DEBATE RECORD
Advocate: 8 | Skeptic: 6 | Judge: WRITE 8
Judge note: Single-user bot reduces risk, but PII in logs and no encryption at rest are confirmed gaps.
