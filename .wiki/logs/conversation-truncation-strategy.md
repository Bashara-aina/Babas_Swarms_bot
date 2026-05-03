---
title: Conversation Truncation Strategy
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

# Conversation Truncation Strategy — Review & Recommendations

> Status: PARTIALLY IMPLEMENTED — gaps remain for semantic context compaction

## What's Already Implemented

### 1. `_compact_messages()` — LLM API layer (llm_client/__init__.py:687)
Soft-truncation before sending to the model API itself.
Preserves last 6 turns, compresses older ones to one summary message.
Does NOT require a running LLM — uses heuristic stripping (tool names, first 150–200 chars).

**Limitation**: Only fires at the litellm API call boundary. The conversation context
injected into the system prompt via `get_conversation_summary_prompt()` is separate.

---

## What's Missing (Gaps)

### Gap A — `get_conversation_summary_prompt()` (conversation_interface.py:214)
```python
def get_conversation_summary_prompt(user_id: str) -> str:
    history = get_conversation_history(user_id, last_n=6)
    ...
```
- Hard-codes `last_n=6` — no token-count awareness
- No LLM-powered summarization of older turns
- When `last_n=6` is exceeded, earlier turns are silently discarded (not summarized)

**Fix location**: `core/conversation_interface.py:214` in `get_conversation_summary_prompt()`

**Strategy**:
```python
# Add after line 216 — if history exceeds ~3000 tokens, call LLM to summarize older turns
def get_conversation_summary_prompt(user_id: str, max_context_tokens: int = 4000) -> str:
    history = get_conversation_history(user_id, last_n=6)
    # Estimate total tokens
    total_chars = sum(len(str(h["content"])) for h in history)
    est_tokens = total_chars // 4  # rough 4 chars/token

    if est_tokens > max_context_tokens and len(history) > 4:
        # Summarize middle turns with an LLM call, keep recent 3 + summary
        ...
```

---

### Gap B — `add_to_thread()` (conversation_interface.py:230)
```python
if len(ACTIVE_THREADS[thread_id]) > 10:
    ACTIVE_THREADS[thread_id] = ACTIVE_THREADS[thread_id][-10:]
```
- Hard 10-turn sliding window — no token-count awareness
- `result[:500]` truncates at 500 chars — fine for logging, but thread context
  passed to agents is only last 3 turns via `get_thread_context(last_n=3)` (line 245)

**Fix location**: `core/conversation_interface.py:230`

**Strategy**: Same pattern as Gap A — measure cumulative thread size in chars,
invoke `_compact_messages()` or LLM summarization when threshold exceeded.

---

### Gap C — `CONVERSATION_HISTORY` in-memory store (conversation_interface.py:32)
```python
MAX_HISTORY_TURNS = 20
MAX_HISTORY_CHARS = 8000
```
- Cap exists in constants but is not actively enforced during `add_to_conversation()`
- `get_conversation_history()` does enforce `last_n=MAX_HISTORY_TURNS` (line ~114)
- No LLM summarization when approaching the cap

**Fix location**: `core/conversation_interface.py:113` (get_conversation_history)

**Strategy**: Add a "summarize and collapse" mode when turn count > 15:
summarize oldest 10 turns into 1 composite message, keeping newest 10.

---

## Recommended Implementation (Priority Order)

### Priority 1 — Summarize middle turns in `get_conversation_summary_prompt()`

File: `core/conversation_interface.py`, function `get_conversation_summary_prompt()` (line 214)

Trigger: When `history` has > 4 turns (i.e., more than the last 4 are "older")
Action: Call a lightweight LLM (e.g., `minimax/MiniMax-Text-01`) to summarize the
oldest N-4 turns into a single paragraph, then inject as `[Earlier conversation: ...]`
before the last 4 turns.

```python
# Pseudocode — actual implementation needs async LLM call
if len(history) > 4:
    older = history[:-4]
    summary = await _llm_summarize_turns(older)  # separate LLM call
    context_block = f"[Earlier conversation summarized: {summary}]\n"
    context_block += "\n".join(f"{turn['role']}: {turn['content'][:300]}" for turn in history[-4:])
else:
    context_block = ...  # existing logic
```

### Priority 2 — Thread context smarter windowing

File: `core/conversation_interface.py`, `get_thread_context()` (line 245)

Change `last_n=3` to be token-budget aware. If thread history exceeds ~2000 chars,
summarize instead of brute-force truncation.

### Priority 3 — Enforce `MAX_HISTORY_CHARS` actively

File: `core/conversation_interface.py`, `add_to_conversation()` (line ~110)

After appending a new turn, check total chars and collapse+summarize if over 8000.

---

## Rollout Note

The existing `_compact_messages()` at `llm_client/__init__.py:687` is the
last-resort safety net. The above changes move the truncation point earlier
and preserve more semantic information via summarization rather than raw drop.