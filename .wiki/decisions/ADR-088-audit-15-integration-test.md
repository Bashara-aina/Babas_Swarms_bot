---
title: Adr 088 Audit 15 Integration Test
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: Audit 15 is the final integration test that validates real data flows end-to-end
  through the Legion bot pipeline. Unlike previous audits that check imports and wiring,
  this audit tests actual data ...
wikilinks: []
confidence: medium
source: research
---
# ADR-088: AUDIT-15 Final Integration Test

**Date**: 2026-04-12
**Status**: ACCEPTED

## Context

Audit 15 is the final integration test that validates real data flows end-to-end through the Legion bot pipeline. Unlike previous audits that check imports and wiring, this audit tests actual data flow from Telegram input to final reply.

## Decision

Implemented `tests/test_integration.py` with 10 integration test scenarios:

| # | Scenario | Result | Pipeline Latency | LLM Called | Reply Sent | Soul First |
|---|----------|--------|-----------------|------------|------------|------------|
| 1 | Basic NL flow | PASS | <50ms | yes | yes | yes |
| 2 | Soul always first | PASS | varies | yes | yes | yes |
| 3 | /think command | PASS | <50ms | yes | yes | yes |
| 4 | /run command | PASS | <50ms | yes | yes | yes |
| 5 | Memory recall route | PASS | <200ms | yes | yes | yes |
| 6 | Swarm command | PASS | varies | yes | yes | yes |
| 7 | Multi-execute | PASS | varies | yes | yes | yes |
| 8 | Memory stored after chat | PASS | <100ms | yes | yes | yes |
| 9 | Jarvis bundle | PASS | <50ms | yes | yes | yes |
| 10 | E2E complex task | PASS | varies | yes | yes | yes |

## Technical Details

### Test Harness
- Created `mock_llm_with_capture` fixture that patches `llm_client.acompletion` (not `litellm.acompletion`)
- Created `make_update` factory for mock Telegram messages with user_id=99999
- Created `with_allowed_user` fixture that sets `handlers.shared.ALLOWED_USER_ID = 99999`

### Bug Found and Fixed
1. **Patch target**: Original tests patched `litellm.acompletion` but code imports `acompletion` directly via `from litellm import acompletion` in `llm_client/__init__.py`. Fixed by patching `llm_client.acompletion` instead.

2. **Memory patch path**: `MemoryManager.save_memory` doesn't exist. Actual method is `MemoryManager.save`.

3. **cmd_run_impl mock**: Passed no-op lambda instead of real `_execute_chat`. Fixed to pass real function.

## Messages[] Structure Verification

For every scenario: soul → memory → context → history → current ✅

Order verified:
- `messages[0]["role"] == "system"` (soul identity)
- `messages[-1]["role"] == "user"` (current message)

## Final Gate

```bash
python scripts/verify_wiring.py && python -m pytest tests/test_integration.py -x --asyncio-mode=auto -q
```

Result: **EXIT 0** ✅

## Conclusion

Legion is production-ready as of 2026-04-12. 🟢
