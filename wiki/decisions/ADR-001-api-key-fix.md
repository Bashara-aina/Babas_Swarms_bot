# ADR-001: API Key & Fallback Chain Fix

**Date**: 2026-04-11
**Status**: Proposed
**Deciders**: @planner

## Context

User reported two errors:
1. `"No API key for 'gemini'"` 
2. `"All models exhausted for 'scheduler'"`
3. User asked: "Bisa lihat layar sekarang apa ngga" (Can we see the screen now?)

### Root Cause Analysis

#### 1. GEMINI_API_KEY Disabled
In `.env` (line 19):
```
# GEMINI_API_KEY=disabled — using MiniMax M2.7 only
```

However, `FALLBACK_CHAIN` in `agents/__init__.py` lists `gemini/gemini-2.0-flash-exp:free` as a fallback for **15+ agent types** (coding, debug, math, architect, analyst, general, researcher, marketer, devops, pm, humanizer, owl, ag2_researcher, ag2_critic, ag2_synthesizer, code_exec, predictor, claude_orchestrator, reviewer).

When MiniMax fails or rate-limits, the system tries to use Gemini as a fallback but has no API key → `"No API key for 'gemini'"`

#### 2. Missing "scheduler" Agent Model
The `core/intent_classifier.py` (line 14, 184) recognizes `scheduler` as a valid agent key for scheduling-related tasks (reminders, calendar, cron).

However, `AGENT_MODELS` and `FALLBACK_CHAIN` in `agents/__init__.py` have **no entry for `scheduler`**.

When a scheduling task is classified as `scheduler` intent, the system cannot find a model → `"All models exhausted for 'scheduler'"`

#### 3. Screen Viewing ("Bisa lihat layar?")
The user's question triggers `vision` intent via `TASK_KEYWORDS` (screenshot, layar, lihat, etc.).

**Current vision chain** (`agents/__init__.py` FALLBACK_CHAIN "vision"):
```
1. ollama_chat/gemma4:e4b  (local - requires running Ollama)
2. groq/meta-llama/llama-4-scout-17b-16e-instruct  (cloud - requires GROQ_API_KEY)
3. gemini/gemini-2.0-flash  (cloud - requires GEMINI_API_KEY - DISABLED)
```

The GROQ_API_KEY is also disabled in `.env` (line 16: `# GROQ_API_KEY=disabled`).

**If Ollama is not running**, all three vision fallbacks fail.

## Decision

### Fix 1: Add Scheduler Agent Model
Add `scheduler` to `AGENT_MODELS` and `FALLBACK_CHAIN` in `agents/__init__.py`.

### Fix 2: Enable GEMINI_API_KEY
Uncomment and populate `GEMINI_API_KEY` in `.env`, OR remove gemini from fallback chains and use only models with valid API keys.

### Fix 3: Fix Vision/Screen Chain
Ensure Ollama is running with `gemma4:e4b` OR enable a working cloud vision fallback (Groq with valid key, or Gemini with valid key).

## Consequences

- Enabling GEMINI_API_KEY provides free tier Gemini 2.0 Flash as a robust fallback
- Scheduler tasks will work without model exhaustion errors
- Screen viewing will work if Ollama is running or cloud vision keys are available

## Alternatives Considered

1. **Remove Gemini from all fallback chains**: Would require all fallback requests to route through Groq only. Rejected because Groq is also disabled and we need multiple fallback options.

2. **Use OpenRouter for Gemini**: OpenRouter provides free Gemini access via `openrouter/google/gemini-flash-1.5`. Would require `OPENROUTER_API_KEY` to be set instead.

## Test Plan

After fixes:
1. `pytest tests/ -x --asyncio-mode=auto -q` passes
2. `/screen` command returns a screenshot
3. Scheduling keywords ("jadwalkan", "ingatkan") route to a working agent
4. `/keys` shows GEMINI_API_KEY as valid (if enabled)

---

**FINAL APPROVED by @reviewer**