# Priority 9 Log: /capabilities and /self_report Commands

**Date**: 2026-04-13
**Task**: ADD /CAPABILITIES AND /SELF_REPORT COMMANDS
**Status**: ✅ COMPLETE

## What was done

### 1. Added handlers to `handlers/admin_handlers.py`

Two new command handlers added:
- `cmd_capabilities()` — handles `/capabilities`
- `cmd_self_report()` — handles `/self_report`

Both use the existing `_require_owner()` decorator for owner-only access.

### 2. Created supporting data modules

**`data/message_count.py`**
- `load_message_count(days=1)` — queries `data/conversation.db` for message count
- Fallback to legacy `messages` table if `conversation_history` doesn't exist
- Returns 0 on any error (non-fatal)

**`data/self_improvement_buffer.py`**
- `get_recent_learnings(n=10)` — async, queries `memory.db` for learning_logs table
- Fallback to kv_store with `%learning%` key pattern
- `log_learning(content)` — async, writes to learning_logs table (for future use)

### 3. Registered commands in `main.py`

Added to `set_my_commands`:
- `BotCommand(command="capabilities", description="Honest capability status")`
- `BotCommand(command="self_report", description="24h activity summary")`

### 4. Verification

```bash
python scripts/verify_wiring.py
# All 7 tests PASS
# Handler Wiring: PASS
# Core Imports: PASS
# LLM Client: PASS
# Tools: PASS
# Bridges: PASS
# Skills: PASS
# Agents: PASS
```

## Files Modified/Created

| File | Action |
|------|--------|
| `handlers/admin_handlers.py` | Modified — added 2 command handlers |
| `main.py` | Modified — added 2 BotCommands |
| `data/message_count.py` | Created |
| `data/self_improvement_buffer.py` | Created |
| `.wiki/decisions/ADR-018.md` | Created |
| `.wiki/logs/priority-9-commands.md` | Created (this file) |

## Behavior

**`/capabilities`**:
- Runs `CapabilityAudit().run_audit()` which checks benchmark file list
- Shows ✅ for present capabilities, ❌ for missing
- Shows coverage percentage

**`/self_report`**:
- Queries message count from conversation.db
- Queries recent learnings from memory.db
- Shows "(none yet)" if no learnings found

Both commands are owner-only (same auth as `/budget`, `/soul`).