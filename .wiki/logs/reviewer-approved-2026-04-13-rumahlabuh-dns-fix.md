## Approved: rumahlabuh.com DNS-resilient HTTP client (bug fix)
Date: 2026-04-13
Task: Fix rumahlabuh.com connectivity by replacing bare aiohttp.ClientSession with DNS-resilient session using Cloudflare (1.1.1.1) + Google (8.8.8.8) DNS fallback
Files: tools/rumahlabuh_http.py (new), tools/rumahlabuh_crew.py, core/proactive_engine.py, handlers/business_handler.py
Reviewed by: @reviewer
Outcome: APPROVED ✅ on loop 1

### Verification evidence
- `python -m py_compile` → exit 0 for all 4 files
- All imports resolve cleanly
- Runtime test: `get_resilient_session().get('https://rumahlabuh.com')` → HTTP 200 OK
- No secrets, no .env modifications, no files outside scope
- `check_website_uptime()` returns `{'ok': True, 'status': 200, 'latency_ms': ...}` as required

### Note
scheduler.py transitively uses the fixed `rumahlabuh_crew.check_website_uptime()` — confirmed clean via transitive verification.