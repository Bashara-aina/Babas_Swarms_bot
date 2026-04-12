---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/issues/002-missing-task-keywords.md",
  "reason": "daily_fast_scan: score=0.050 < 0.3",
  "score": 0.05,
  "quarantined_at": "2026-04-12T01:00:00.651548"
}
---

# Review: Missing TASK_KEYWORDS for 11 Legacy Agents
**File:** `core/agent_registry.py` lines 436-660  
**Severity:** ⚠️ Warning  
**Status:** Non-blocking but functional gap

## Finding
`LEGACY_TASK_KEYWORDS` has entries for only **12** of the **23** legacy agents:

**Has TASK_KEYWORDS (12):** analyst, architect, coding, computer, debug, devops, marketer, math, pm, researcher, reviewer, vision

**Missing TASK_KEYWORDS (11):** ag2_critic, ag2_researcher, ag2_synthesizer, claude_orchestrator, code_exec, debate, general, humanizer, owl, predictor, think

## Impact
- When `detect_agent()` is called with a task matching one of these 11 agents, keyword-based detection will never match them
- These agents can still be invoked **directly by name** via `get_model("ag2_researcher")` or `get_fallback_chain("ag2_researcher")`
- The fallback chain works fine since `LEGACY_FALLBACK_CHAIN` has all 23 agents
- For `detect_agent()` specifically: if a task scores 0 on all 12 agents with keywords, it falls back to `DEFAULT_AGENT = "general"`

## Recommendation
Either:
1. Add TASK_KEYWORDS entries for the 11 missing agents (best for accuracy), OR
2. Acknowledge this limitation and rely on direct agent name resolution for these agents

Note: The `detect_agent()` function has regex-based high-confidence overrides for `math`, `debug`, `architect`, and `general` (jokes/capital cities) that work independently of `LEGACY_TASK_KEYWORDS`.
