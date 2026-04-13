---
title: "Review: Legacy Agent Count Mismatch"
type: review
tags: [001-legacy-agent-count-mismatch]
---
# Review: Legacy Agent Count Mismatch
**File:** `config/departments.yaml` line 713-715  
**Severity:** ⚠️ Warning  
**Status:** Non-blocking

## Finding
The `legacy` department header comment says "22 agents":

```yaml
# ── Legacy agents (mirrors agents.py AGENT_MODELS, used for backwards compat) ──
legacy:
  default_agent: general
  description: "Legacy 22-agent registry — mirrors agents.py AGENT_MODELS for backwards compat"
```

However, counting the actual agents defined under `legacy.agents` yields **23 agents**:

vision, coding, debug, math, architect, analyst, computer, general, researcher, marketer, devops, pm, humanizer, reviewer, think, owl, ag2_researcher, ag2_critic, ag2_synthesizer, code_exec, predictor, claude_orchestrator, debate

## Impact
- Documentation is misleading (comment says 22 but there are 23)
- If any downstream code relies on the "22" count for validation, it will fail

## Recommendation
Update the description to say `"Legacy 23-agent registry — mirrors agents.py AGENT_MODELS for backwards compat"` (or investigate if one agent should not be included).
