---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/legion/audit-2026-04-11-fixes.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-11T18:14:42.186907"
}
---

# Audit 2026-04-11: Critical Fixes Applied

**Date:** 2026-04-11  
**Scope:** Babas_Swarms_bot (Legion Bot)  
**Tests:** All 276 tests passing

---

## Fixes Applied

| # | File | Line(s) | Description | Severity |
|---|------|---------|-------------|----------|
| 1 | `handlers/__init__.py` | ~66 | Removed duplicate `admin_handlers.router` entry shadowing first registration — fixed `/budget` and `/soul` routing | critical |
| 2 | `main.py` | new | Added `on_shutdown` handler via `dp.shutdown.register()` — cancels all asyncio tasks on SIGTERM/SIGINT for graceful shutdown | critical |
| 3 | `main.py` | after `load_dotenv()` | Added fail-fast env validation — `TELEGRAM_BOT_TOKEN` and `ALLOWED_USER_ID` raise `RuntimeError` if missing | critical |
| 4 | `llm_client.py` | Ollama bypass removal | Removed Ollama blocking for local `ollama_chat/` model fallbacks — all agents now can use local Ollama | warning |
| 5 | `llm_client.py` | MiniMax retry | Replaced fixed 30s retry with exponential backoff + jitter: ~30s → ~60s → ~120s delays | warning |
| 6 | `llm_client.py` | `chunk_output()` | Added `if remaining_space <= 0: break` guard to prevent infinite loop when `max_length == remaining_space` | critical |
| 7 | `core/agent_registry.py` | `LEGACY_FALLBACK_CHAIN` | Updated all 22 legacy agents: primary=`minimax/MiniMax-M2.7`, fallback1=`ollama_chat/llama3.3:70b`, fallback2=`ollama_chat/gemma4:e4b` | warning |

---

## Model Routing Change

- **Before:** `minimax/MiniMax-M2.7` only (no fallbacks)
- **After:** `minimax/MiniMax-M2.7` → `ollama_chat/llama3.3:70b` → `ollama_chat/gemma4:e4b`
- Local models only activated when MiniMax fails/unavailable

---

## Round 2: File Split Refactoring (2026-04-11)

Two monolithic files refactored into packages. Zero functional changes — purely structural.

### Split 1: `computer_agent/` (2077 lines → 4-file package)

| File | Contents |
|------|----------|
| `computer_agent/__init__.py` | Backwards-compatible re-exports (import computer_agent as before) |
| `computer_agent/shell.py` | Subprocess execution, APP_MAP (29 entries), open_app/open_url, install_packages, restart_bot |
| `computer_agent/display.py` | Display detection, screenshot, mouse/keyboard, window management, clipboard, WhatsApp, file ops |
| `computer_agent/tools.py` | TOOL_DEFINITIONS (63 tools), execute_tool() dispatcher, web/email/git/dev wrappers |

- All 63 tools preserved with identical signatures
- All 29 APP_MAP entries preserved
- Backwards-compatible: `import computer_agent`, `from computer_agent import take_screenshot` both work

### Split 2: `llm_client/` (1917 lines → 2-file package)

| File | Contents |
|------|----------|
| `llm_client/__init__.py` | Complete implementation (identical to old llm_client.py) |
| `llm_client.py` | Backwards-compatible shim (re-exports from llm_client/ package) |

- No functional changes — purely for maintainability
- All 10 SYSTEM_PROMPTS modes, 63 TOOL_DEFINITIONS, chat(), agent_loop(), analyze_screenshot() unchanged

### Test Fixes Applied

| # | File | Fix |
|---|------|-----|
| 1 | `tests/test_agent_registry.py` | Updated `test_get_fallback_chain_coding` to expect `minimax/MiniMax-M2.7` as primary (was `groq/llama-3.3-70b-versatile`) |
| 2 | `llm_client/__init__.py` | Added `max_turns` alias parameter to `_compact_messages()` for backwards compat with existing tests |

### Verification

- **276 tests passing**
- All import paths verified:
  - `import computer_agent` ✅
  - `from computer_agent import take_screenshot` ✅
  - `import llm_client` ✅
  - `from llm_client import chat` ✅
  - `main.py` imports cleanly ✅

---

## Already Correct (No Changes Needed)

- Soul at prompt position 0 ✅
- Disagreement protocol injected in `chat()` ✅
- `/debate` handler uses correct `chat(task=..., agent_key="debate")` ✅
- `run_shell()` stderr only on non-zero exit ✅
- `SYSTEM_PROMPTS` wired into `prompt_sections` ✅
- Orphan `_tool_label` entries removed ✅
- `handlers/streaming.py` is utility module (not router) — correctly excluded ✅
