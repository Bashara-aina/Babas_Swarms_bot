---
title: Contract 03 Opencode Pipeline
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: Modify `run_opencode_task()` in `core/opencode_bridge.py` to directly call
  `opencode_write_session_summary()` after subprocess completion, instead of relying
  on hook-based approach in `builtin_hook...
wikilinks: []
confidence: medium
source: research
---
## CONTRACT #3: Replace hook-based opencode session writes with direct callback

WHAT:
  Modify `run_opencode_task()` in `core/opencode_bridge.py` to directly call `opencode_write_session_summary()` after subprocess completion, instead of relying on hook-based approach in `builtin_hooks.py`.

FILES:
  READ:  /home/newadmin/swarm-bot/core/opencode_bridge.py
  READ:  /home/newadmin/swarm-bot/core/builtin_hooks.py
  WRITE: /home/newadmin/swarm-bot/core/opencode_bridge.py
  WRITE: /home/newadmin/swarm-bot/core/builtin_hooks.py

DONE_WHEN:
  - `run_opencode_task()` directly calls `opencode_write_session_summary()` after subprocess completes
  - `opencode_session_start_hook` and `opencode_session_end_hook` are removed from `builtin_hooks.py` registration
  - The `opencode_write_session_summary` function remains available in `wiki_bridge.py` for direct calls
  - Session summary includes: session_id, task_description, outcome, files_modified

PROOF_FORMAT:
  CODE: `grep -n "opencode_write_session_summary\|opencode_session_start_hook\|opencode_session_end_hook" /home/newadmin/swarm-bot/core/opencode_bridge.py /home/newadmin/swarm-bot/core/builtin_hooks.py`
  Expected: `opencode_bridge.py` should contain call to `opencode_write_session_summary`, and `builtin_hooks.py` should NOT contain `opencode_session_start_hook` or `opencode_session_end_hook` registrations

BLOCKER_IF:
  - `opencode_write_session_summary` function is removed from `wiki_bridge.py` (it must remain available)
  - The modification breaks the subprocess execution in `run_opencode_task()`

DEPENDS_ON: none
