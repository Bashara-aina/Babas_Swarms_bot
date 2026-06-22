# Monitoring & Health Metrics — Recommendations

Generated: 2026-06-17

## Current State Assessment

### metrics_collector.py (239 lines)
- **Status**: NOT ACTIVE — `/tmp/hermes_metrics.db` does not exist, meaning no tool has ever called `handle_metrics()`.
- **Design**: Clean SQLite-backed decorator pattern. Tracks call_count, latency, p50/p95/p99, error_rate.
- **Issue**: Uses `/tmp/` (volatile, lost on reboot). Should use project-local data dir.
- **Issue**: Requires manual decorator adoption — no tools currently use `@track_metrics`.

### hermes_token_meter.py (30KB)
- **Status**: NOT RUNNING — MCP connection returns "Connection closed".
- **Design**: Thorough per-session tracking with MiniMax pricing, tiktoken integration.
- **Issue**: Needs service activation or import integration to function.

### Health Check (8 servers)
- **3 connected**: gitnexus (4.3s slow), ddg (1.5s), context7 (1.2s)
- **5 timeout**: tavily, firecrawl, github, chrome_devtools, playwright
- **Note**: 5 timeouts is expected — these are external services not available in this environment.
- **Action**: Remove or disable timeout-susceptible servers from active health monitoring.

### Circuit Breaker
- **Status**: Empty — no tools have failure counts tracked.
- **Action**: Populate with the 5 timeout-prone servers at minimum (threshold: 3 failures / 30s window).

### Security State Files
- **Status**: No fragmented `security_warnings_state_*.json` files found. Single consolidated `audit-status.json` (130 bytes) exists at `.claude-flow/security/`.
- **Note**: The 7-file fragmentation from previous sessions has been resolved or was cleaned up.
- **CVEs**: 0 fixed, 3 total, audit status PENDING as of 2026-06-17T07:42.

### statusline.cjs (930 lines)
- **Pros**: Well-optimized — single git execSync, no ps aux, strict 2s timeouts, shared settings cache.
- **Cons**: 930 lines is heavy for a status line. `getTestStats()` recursively scans `src/` and `v3/` directories on every render — could be slow on large source trees.
- **Risk**: 2s timeout on git execSync could cause visible lag in TTY rendering if repo is large.

## Recommendations

### 1. Activate metrics_collector polling
- **Interval**: 60s (sufficient for trend analysis, no need for sub-minute granularity)
- **Move DB**: Change `METRICS_DB` from `/tmp/hermes_metrics.db` to `.claude-flow/data/metrics.db`
- **Adoption**: Add `@track_metrics` decorator to 3 highest-volume handlers first (gitnexus, ddg, context7)
- **Export**: Schedule daily CSV export to `.claude-flow/metrics/daily/` for historical trending

### 2. Activate token_meter
- Start as warm service on session init (not lazy-loaded)
- Connect to the `hermes_token_meter` MCP tool — currently returning "Connection closed"
- Set budget: 128K tokens per session with hard limit warning at 100K

### 3. Circuit breaker configuration
- Track: tavily, firecrawl, github, chrome_devtools, playwright (5 timeout-prone)
- Threshold: 3 failures within 30s window → open circuit for 60s
- Auto-reset: half-open after 60s, close on next success

### 4. Statusline optimization
- Cache `getTestStats()` with 30s TTL (don't re-scan on every render)
- Or pre-compute test counts and write to a small cache file
- Consider lazy-loading the `getLearningStats()` SQLite header reads

### 5. Security audit
- Address 3 pending CVEs from audit-status.json
- Schedule weekly audit (default: every Sunday)
- Remove reference to "7 fragmented security state files" from team awareness — already consolidated
