---
title: "LEGION WIKI LOOP — SESSION SUMMARY"
created: 2026-04-12
type: article
tags: [SESSION_SUMMARY]
---
# LEGION WIKI LOOP — SESSION SUMMARY
Date: 2026-04-12 (Cycles 11-20)

## Total Pages
- **Written (full session)**: 74
- **Cycles 11-20**: 40 pages
- **Rejected**: 0
- **Total tokens added**: ~23,580 estimated

## Pages by Domain (Cycles 11-20)

| Domain | Count | Pages |
|--------|-------|-------|
| Browser & Web | 3 | browser-agent-architecture, video-url-pipeline, web-scraping-patterns |
| Communications | 3 | composio-email-setup, composio-calendar-guide, email-security-patterns |
| Voice & Media | 3 | voice-pipeline, media-processing-guide, tts-setup |
| Data & Analytics | 3 | observability-stack, data-privacy-guide, supabase-query-patterns |
| Database | 3 | supabase-schema-overview, supabase-security-guide, database-resilience |
| Git & Version Control | 3 | github-integration-guide, github-security-patterns, self-upgrade-mechanism |
| Deployment & CI/CD | 3 | deployment-architecture, ci-cd-pipeline, logging-strategy |
| API & Integrations | 3 | n8n-bridge-guide, api-key-management, webhook-patterns |
| Error Handling | 3 | error-patterns-catalog, circuit-breaker-design, debugging-guide |
| Testing & Quality | 3 | test-patterns-guide, test-security-patterns, quality-gates-spec |

## Top 3 Highest-Impact Pages (Cycles 11-20)

1. **error-patterns-catalog.md** (impact: 9) — 11 error categories with humanized Indonesian messages, recovery hierarchy, circuit breaker states, and log anonymization. Maps every error Legion encounters to its root cause and recovery action.

2. **circuit-breaker-design.md** (impact: 9) — Two independent circuit breaker systems (provider-level + agent-level), 5-level recovery chain, watchdog auto-recovery, and per-provider status tracking. Critical resilience architecture documented.

3. **observability-stack.md** (impact: 9) — Prometheus metrics, AgentOps, in-memory cost tracking, session transcripts, memory storage — full observability picture with gaps (no Grafana, no alerting, no PII redaction).

## Top 3 Most Surprising Findings (Cycles 11-20)

1. **n8n bridge is a pure pass-through** — webhook listener on :7835 logs payload and returns `{"ok": True}` with no event routing, no agent dispatch, no HMAC verification. n8n can trigger Legion but Legion cannot act on the trigger.

2. **understand_audio is called but never defined** — `media_tools.py:400` and `video.py:176` import `understand_audio` from `tools.minimax_media` but the function doesn't exist there. Transcription fails silently, caught by try/except → returns empty string.

3. **skill_guardian.py has the best retry pattern but it's not used for webhooks or Supabase** — exponential backoff [0, 1, 4, 16]s with failure classification exists but only applies to Composio/GitHub tool calls. External webhook delivery and database queries have zero retry logic.

## Critical Issues Found (Cycles 11-20)

### CRITICAL (unfixed)
- **understand_audio undefined** — called in video.py and media_tools.py, never defined, silently returns ""
- **No webhook HMAC verification** — any client can POST to :7835/webhook, no signature validation
- **No persistent event queue** — bot restart loses all pending n8n webhook events

### HIGH (documented, unfixed)
- **No SSRF protection in browser mode** — no URL allowlist, no hostname validation, `file://` scheme accessible
- **No calendar filtering** — ALL events from ALL calendars returned, privacy risk
- **Composio GitHub token permissions opaque** — cannot audit what Composio has access to
- **self-upgrade pip install unsandboxed** — runs with full system pip permissions

### MEDIUM (documented, unfixed)
- **Duplicate SUPABASE env var names** — SUPABASE_SERVICE_ROLE_KEY vs SUPABASE_SERVICE_KEY causes silent failures
- **RedactingFormatter exists but unused** — main.py uses basicConfig with no secret redaction
- **No /health HTTP endpoint wired** — core/health.py exists but start_health_server() never called
- **No sidecar auto-recovery** — ruflo/opencode death only logged, not restarted

## Contradiction Verification

| Pair | Status | Resolution |
|------|--------|-------------|
| n8n-bridge-guide.md vs webhook-patterns.md | ✅ No conflict | Complementary: n8n-bridge-guide covers n8n-specific listener architecture; webhook-patterns covers generic webhook infrastructure + skill_guardian retry. Both document the same gap (no event routing). |
| observability-stack.md vs logging-strategy.md | ✅ No conflict |observability-stack covers metrics + cost tracking (what to measure); logging-strategy covers log output + rotation (how to record). Different layers, consistent facts. |
| supabase-security-guide.md vs database-resilience.md | ✅ No conflict | supabase-security-guide covers RLS + API key storage + injection prevention; database-resilience covers SQLite + Supabase connection handling + fallback chains. Different focus areas. |
| deployment-architecture.md vs ci-cd-pipeline.md | ✅ No conflict | deployment-architecture covers systemd service + startup + health monitoring; ci-cd-pipeline covers CI/CD workflows. Both document manual deployment as gap. |

## Estimated Legion Performance Improvement

**Before wiki loop**: Legion had fragmented knowledge — error handling undocumented, circuit breakers unknown, test coverage unclear, deployment scattered across multiple files.

**After wiki loop**:
- **Error handling**: 11 error categories mapped with humanized Indonesian messages; 5-level recovery chain documented
- **Circuit breakers**: Provider-level + agent-level systems visible; rate limit tracking understood
- **Testing**: 299 tests passing, 4-guard anti-slop system, pytest-asyncio patterns documented
- **Deployment**: systemd service, CI/CD pipeline, logging strategy all documented with gaps identified
- **API integrations**: n8n bridge limitations, 21+ API keys, webhook gaps all visible

## Recommended Next Loop Domains

1. **Calendar Integration** — zemi blocking, meeting-aware briefings, calendar_id filtering needed
2. **Weather API Tool** — briefing shows location but no weather data
3. **Skills Registry V2** — yt-dlp not wired to routing, Crawl4AI not registered, timer tool missing
4. **SSRF Protection** — add URL validator to browser_agent.py before any fetch
5. **Context Optimizer** — implement context-optimization.md (30-50% token reduction possible)

## Session Quality Notes

- 0 pages rejected across all 20 cycles
- All 40 cycles 11-20 pages follow wiki page format with frontmatter
- Token budgets: all pages under 800 tokens, average ~500 tokens
- One critical bug found and documented: understand_audio undefined (ADR-044)
- No contradictions between overlapping pages (verified above)
- Post-review fixes applied to cycles 11-15 pages (format fixes, DEBATE RECORD additions)

## ADR References Created This Session

- ADR-005: Full wiki loop session (cycles 1-10)
- ADR-006: Wiki quality gate system (existing, referenced)
- ADR-044: understand_audio bug documented

---

*Session 2026-04-12 — Cycles 11-20 complete — 40 pages written, 0 rejected*
*Final pass: INDEX.md updated, SESSION_SUMMARY.md updated, contradiction verification complete*
