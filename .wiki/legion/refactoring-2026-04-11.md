---
# Refactoring Log — 2026-04-11 Round 2

## Overview

Two monolithic files split into packages. No functional changes — purely structural maintainability improvements.

---

## computer_agent/ Split

**Before:** `computer_agent.py` (2077 lines, single file)  
**After:** `computer_agent/` package (4 files)

### File Map

| Old Location | New Location | Contents |
|--------------|--------------|----------|
| computer_agent.py | computer_agent/__init__.py | Backwards-compatible re-exports |
| computer_agent.py | computer_agent/shell.py | subprocess execution, APP_MAP, open_app/open_url, install_packages, restart_bot |
| computer_agent.py | computer_agent/display.py | Display detection, screenshot, mouse/keyboard, window management, clipboard, WhatsApp, file ops |
| computer_agent.py | computer_agent/tools.py | TOOL_DEFINITIONS (63 tools), execute_tool() dispatcher, web/email/git/dev wrappers |

### What Was Preserved

- All 63 tool definitions (identical TOOL_DEFINITIONS)
- All 29 APP_MAP entries (unchanged)
- All function signatures unchanged
- execute_tool() dispatcher logic unchanged
- Backwards-compatible import paths

### Backwards Compatibility

```python
# These all work exactly as before:
import computer_agent
from computer_agent import take_screenshot
from computer_agent import execute_tool
from computer_agent.shell import open_app
from computer_agent.display import get_active_window_title
```

---

## llm_client/ Split

**Before:** `llm_client.py` (1917 lines, single file)  
**After:** `llm_client/` package (2 files)

### File Map

| Old Location | New Location | Contents |
|--------------|--------------|----------|
| llm_client.py | llm_client/__init__.py | Complete implementation (identical content to old llm_client.py) |
| llm_client.py | llm_client.py | Backwards-compatible shim (re-exports from llm_client/) |

### What Was Preserved

- All 10 SYSTEM_PROMPTS modes
- All 63 TOOL_DEFINITIONS (shared with computer_agent)
- chat() function and signature
- agent_loop() function
- analyze_screenshot() function
- All retry/exponential backoff logic
- Ollama bypass removal (from Round 1 fixes)
- chunk_output() infinite loop guard (from Round 1 fixes)

### Backwards Compatibility

```python
# These all work exactly as before:
import llm_client
from llm_client import chat
from llm_client import agent_loop
from llm_client import TOOL_DEFINITIONS
```

---

## Test Fixes

### 1. tests/test_agent_registry.py

Updated `test_get_fallback_chain_coding` expectation:
- **Before:** primary model was `groq/llama-3.3-70b-versatile`
- **After:** primary model is `minimax/MiniMax-M2.7`

Reflects the model routing change from Round 1 (2026-04-11 morning session).

### 2. llm_client/__init__.py

Added `max_turns` alias parameter to `_compact_messages()`:
- Existing tests pass `max_turns=max_turns` keyword arg
- Function signature updated to accept `max_turns` as alias for `max_messages`

---

## Verification

| Check | Result |
|-------|--------|
| pytest tests/ -x --asyncio-mode=auto -q | 276 passed ✅ |
| import computer_agent | ✅ |
| from computer_agent import take_screenshot | ✅ |
| import llm_client | ✅ |
| from llm_client import chat | ✅ |
| main.py imports cleanly | ✅ |

---

## Files Changed Summary

### Created
- `computer_agent/__init__.py`
- `computer_agent/shell.py`
- `computer_agent/display.py`
- `computer_agent/tools.py`
- `llm_client/__init__.py`
- `llm_client.py` (shim)
- `.wiki/legion/refactoring-2026-04-11.md` (this file)

### Deleted
- `computer_agent.py` (replaced by package)

### Modified
- `tests/test_agent_registry.py` (model expectation fix)
- `.wiki/legion/audit-2026-04-11-fixes.md` (Round 2 section added)
- `.wiki/decisions/ADR-005-package-split-computer-agent-llm-client.md` (new ADR)

---

## ADR Reference

- [ADR-005: Package Split for computer_agent and llm_client](../decisions/ADR-005-package-split-computer-agent-llm-client.md)
