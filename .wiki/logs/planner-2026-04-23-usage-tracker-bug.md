---
title: Planner 2026 04 23 Usage Tracker Bug
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Plan: Fix test_daily_report_with_usage bug
Date: 2026-04-23
Type: BUG_FIX
Context gathered:
- `minimax/MiniMax-Text-01` is in DAILY_LIMITS but NOT in PRICING dict
- `daily_report()` iterates only models in PRICING.keys() → skips MiniMax-Text-01 → returns "No API usage recorded today."
- Test assertion `"glm-4" in report` looks incorrect (model is "MiniMax-Text-01", not "glm-4")
Risk assessment: Low — fix is isolated, test coverage exists
Approach:
1. Add "minimax/MiniMax-Text-01": {"input": 0.0, "output": 0.0} to PRICING
2. Fix test assertion to check for correct model name
3. Run full test suite to verify

## Execution Order
Serial (must run in sequence): 1a → 1b
Final gate (must run last): pytest pass

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Fix causes regressions | Low | High | Run full test suite after change |
| Test assertion "glm-4" is wrong | High | Medium | Fix assertion to match actual model name |
