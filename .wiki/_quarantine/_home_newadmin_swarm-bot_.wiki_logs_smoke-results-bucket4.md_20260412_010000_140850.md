---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/smoke-results-bucket4.md",
  "reason": "daily_fast_scan: score=0.050 < 0.3",
  "score": 0.05,
  "quarantined_at": "2026-04-12T01:00:00.140885"
}
---

# Smoke Results - Bucket 4: Enterprise Layer

## Date: 2026-04-11 20:35:48

## Result: FAIL

## Errors Found:
1. **Import Path Error**: `swarms_bot.chief_of_staff` does not exist
   - Actual path: `swarms_bot.orchestrator.chief_of_staff`
   
2. **Import Path Error**: `swarms_bot.dag_executor` does not exist
   - Actual path: `swarms_bot.orchestrator.dag_executor`

## Summary:
The modules exist and are importable, but the test specification used incorrect import paths. The `ChiefOfStaff` and `DAGExecutor` modules are located in the `swarms_bot/orchestrator/` subdirectory, not directly in `swarms_bot/`.

## Files Tested:
- `swarms_bot/__init__.py` ✓
- `swarms_bot/orchestrator/chief_of_staff.py` ✓ (via correct path)
- `swarms_bot/orchestrator/dag_executor.py` ✓ (via correct path)

## Recommendation:
Update test specification to use correct import paths:
- `from swarms_bot.orchestrator.chief_of_staff import ChiefOfStaff`
- `from swarms_bot.orchestrator.dag_executor import DAGExecutor`