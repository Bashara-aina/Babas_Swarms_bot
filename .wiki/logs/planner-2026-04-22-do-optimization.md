---
title: Planner 2026 04 22 Do Optimization
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Plan: /do Optimization — Smart Task Decomposition + Intent Routing + Cognitive Injection

**Date:** 2026-04-22
**Type:** FEATURE (optimization + enhancement)
**Context gathered:** Read AGENTS.md, .wiki/INDEX.md, recent git commits, explored handlers/computer.py, tools/computer_use_agent.py, core/intent_classifier.py, handlers/shared.py, llm_client/__init__.py, core/system_prompt_builder.py, core/soul_engine.py

### Key Findings

1. **Keyword detection is explicit and fragile** — `handlers/computer.py` lines 56-75 show brute-force `exec_keywords = ["run", "execute", "plot", "train", "test"]` + `"code", "python", "script", "bash"` detection for code routing
2. **`_run_agent_loop` calls `agent_loop` NOT `computer_use_loop`** — `agent_loop` (llm_client/__init__.py:890) → `_agent_loop_inner` (line 654) which lacks structured vision-action-verify cycles
3. **Cognitive layers exist but bypassed** — `soul_engine`, `system_prompt_builder`, `memory_manager`, `gsa_voice` all imported in llm_client/__init__.py but only `SYSTEM_PROMPTS.get(agent_key)` is used, not `SystemPromptBuilder`
4. **`computer_use_loop` already exists** with proper vision-reasoning-act-verify in `tools/computer_use_agent.py`, but `/do` doesn't use it
5. **Self-healing is shallow** — `_execute_tool_with_self_heal` only does argument sanitization, not multi-strategy recovery

### Risk Assessment
- Breaking `cmd_do`: HIGH — this is a primary user-facing command
- Changing intent routing: MEDIUM — could mis-route edge cases
- Adding planning layer: MEDIUM — complexity could introduce latency
- Cognitive injection: LOW — uses existing infrastructure

### Approach
1. **Contract 1** (Intent + Decomposition): Replace keyword detection with intent_classifier, add task decomposition using existing `core/intent_classifier.py` infrastructure
2. **Contract 2** (Cognitive Injection): Use `SystemPromptBuilder` to build full cognitive context for `agent_loop`, inject soul + GSA voice + memory
3. **Contract 3** (Planning Layer): Add planning phase to `/do` using computer_use_loop's structured approach; route complex tasks through planning before execution
4. **Contract 4** (Self-Healing): Extend `_execute_tool_with_self_heal` with multi-strategy recovery (retry, alternative approach, fallback)