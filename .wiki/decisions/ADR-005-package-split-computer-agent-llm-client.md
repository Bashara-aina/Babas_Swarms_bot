---
title: "ADR-005: Package Split for computer_agent and llm_client"
created: 2026-04-11
type: decision
tags: [ADR-005-package-split-computer-agent-llm-client]
---
# ADR-005: Package Split for computer_agent and llm_client

- **Date:** 2026-04-11
- **Status:** Accepted
- **Context:** `computer_agent.py` (2077 lines) and `llm_client.py` (1917 lines) had grown into unmaintainable monoliths requiring structural refactoring without disrupting existing import paths or function signatures
- **Decision:** Convert both files into packages with backwards-compatible re-exports
- **Consequences:**
  - `computer_agent/` package: 4 files (shell.py, display.py, tools.py, __init__.py) — 63 tools preserved, all APP_MAP entries preserved
  - `llm_client/` package: 2 files (__init__.py with full implementation, llm_client.py as shim) — zero functional change
  - All existing import paths continue to work: `import computer_agent`, `from computer_agent import take_screenshot`, `import llm_client`, `from llm_client import chat`
  - Test fix: `test_get_fallback_chain_coding` updated to expect `minimax/MiniMax-M2.7` as primary
  - Test fix: `max_turns` alias parameter added to `_compact_messages()` for backwards compatibility
