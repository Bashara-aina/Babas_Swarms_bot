---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/smoke-results-bucket1.md",
  "reason": "daily_fast_scan: score=0.050 < 0.3",
  "score": 0.05,
  "quarantined_at": "2026-04-12T01:00:00.093034"
}
---

# Smoke Test Results — Bucket 1: Telegram Handler Routes

## Summary
| Metric | Value |
|--------|-------|
| **Bucket** | 1 |
| **Category** | Telegram Handler Routes |
| **Files Tested** | 37 (handlers/*.py) |
| **Result** | ✅ PASS |
| **Errors** | 0 |
| **ImportErrors** | 0 |
| **Crashes** | 0 |

## Test Method
```bash
python -c "from handlers import *; print('handlers: OK')"
```

## Details
- All 37 handler modules imported successfully
- No ImportError raised
- No crashes on import
- `handlers/__init__.py` exports all routers correctly

## Log File
`.wiki/logs/smoke-bucket1-handlers-20260411-000000.log`
