---
# PLANNER — Cycles 11-20 Wiki Knowledge Expansion
> Session: 2026-04-12 (PART 2)
> Target: Fill .wiki/ with 100x-performance-impact knowledge pages
> Debate threshold: Judge score >= 7 to write
> Last updated: 2026-04-12

---

## OVERVIEW

Cycles 1-10 covered: Bashara context, LLM routing, memory architecture, intent routing, personality/soul, proactive intelligence, tools/skills, security/stability, context window, future architecture.

**Cycles 11-20** now target operational domains: browser/web, email/communications, voice/media, data/analytics, database, git/version control, deployment/CI/CD, API/integrations, error handling, and testing/quality.

**Orchestration:** Launch 10 workers (cycles 11-20 in parallel batches), each running:
1. Read all target files for their domain
2. Answer research questions
3. Draft candidate wiki pages
4. Run 3-agent debate (Advocate/Skeptic/Judge)
5. Write approved pages (score 7+) to .wiki/
6. Log decisions to .wiki/LOOP_LOG.md

---

## CYCLE 11: BROWSER & WEB AGENT
**Domain:** Playwright browser control, web scraping, Crawl4AI integration

### Target Files to Read
- `/home/newadmin/swarm-bot/tools/browser_agent.py`
- `/home/newadmin/swarm-bot/tools/video.py`
- `/home/newadmin/swarm-bot/handlers/media_tools.py` (search command, photo/video handling)
- `/home/newadmin/swarm-bot/tools/minimax_media.py` (if exists)

### Research Questions
1. How does `browse_task()` work vs `check_site_health()`? What triggers each?
2. What is the fallback chain: browser-use → Crawl4AI → Playwright raw scrape?
3. How does video URL understanding work? What domains are supported?
4. What are the timeout settings? Are there race conditions?
5. How does `/scrape` command work in system.py?
6. What happens when browser-use is not installed?

### Candidate Wiki Pages to Produce
| Page | Description | Impact if Written |
|------|-------------|-------------------|
| `.wiki/browser-agent-map.md` | browse_task, check_site_health, fallback chain, env vars | High — web automation reliability |
| `.wiki/video-processing.md` | yt-dlp extraction, transcript pipeline, supported domains | Medium — media intelligence |
| `.wiki/web-search-guide.md` | /search, /scrape, Crawl4AI vs Playwright tradeoffs | Medium — information retrieval |

### Security Issues / Critical Gaps
- Gap: No rate limiting on web scraping — could be abused
- Gap: browser-use uses LangChain + OpenAI-compatible LLM — cost exposure?
- Security: `check_site_health` accepts any URL — SSRF potential

---

## CYCLE 12: EMAIL & COMMUNICATIONS
**Domain:** Composio email/calendar integrations, email handler

### Target Files to Read
- `/home/newadmin/swarm-bot/handlers/communications.py`
- `/home/newadmin/swarm-bot/tools/composio_hub.py`
- `/home/newadmin/swarm-bot/tools/composio_client.py` (if exists)

### Research Questions
1. What is the Composio toolset initialization chain? (lazy, cached, error handling)
2. How do `get_unread_emails` and `send_email` work? What fallbacks exist?
3. What calendar operations are supported? Create event? Delete?
4. What happens when COMPOSIO_API_KEY is not set?
5. How is WhatsApp integration used? Is it active?
6. What is the error handling pattern? Does it leak stack traces?

### Candidate Wiki Pages to Produce
| Page | Description | Impact if Written |
|------|-------------|-------------------|
| `.wiki/composio-hub-guide.md` | All composio actions, fallback chain, status check | High — email/calendar reliability |
| `.wiki/email-calendar-commands.md` | /emails, /calendar commands and expected behavior | Medium — user-facing clarity |
| `.wiki/composio-fallback-design.md` | Lazy init pattern, error handling, 850+ connectors | Medium — operational understanding |

### Security Issues / Critical Gaps
- Gap: No email content filtering — sensitive data could be exposed
- Gap: Calendar events exposed to any allowed user — should filter by owner
- Security: COMPOSIO_API_KEY exposed in env — need to verify it's not logged

---

## CYCLE 13: VOICE & MEDIA PROCESSING
**Domain:** Voice transcription, text-to-speech, image generation, file processing

### Target Files to Read
- `/home/newadmin/swarm-bot/handlers/voice.py`
- `/home/newadmin/swarm-bot/handlers/media_tools.py`
- `/home/newadmin/swarm-bot/core/utils/multimodal_processor.py`

### Research Questions
1. What is the voice transcription priority chain? (faster-whisper GPU → CPU → openai-whisper → Groq)
2. How does TTS work? (kokoro-onnx → edge-tts fallback)
3. What image generation model is used? MiniMax image-01?
4. How does `/vcsearch` work? Is transcript storage implemented?
5. What document types are supported? (PDF, DOCX, TXT, max sizes)
6. How does video keyframe extraction work? (ffmpeg, 1 frame per 10s, max 8)

### Candidate Wiki Pages to Produce
| Page | Description | Impact if Written |
|------|-------------|-------------------|
| `.wiki/voice-pipeline-guide.md` | Transcribe chain, TTS chain, voice mode toggle | High — voice UX reliability |
| `.wiki/multimodal-processing.md` | Vision, TTS, document extraction, priority chains | High — media understanding |
| `.wiki/media-commands-spec.md` | /imagine, /speak, /search, /mcp_status usage | Medium — user-facing clarity |

### Security Issues / Critical Gaps
- Gap: `/vcsearch` is placeholder — not implemented, could mislead users
- Gap: No file size validation on video uploads (media_tools.py has 100MB limit but not enforced in handler)
- Security: Temp file cleanup — verify `os.unlink` is always called in finally block

---

## CYCLE 14: DATA & ANALYTICS
**Domain:** Supabase queries, data analysis patterns, metrics

### Target Files to Read
- `/home/newadmin/swarm-bot/handlers/brain.py` (data aspects)
- `/home/newadmin/swarm-bot/tools/` (data-related tools)
- `/home/newadmin/swarm-bot/core/observability/` (metrics)

### Research Questions
1. What metrics are tracked by the observability system?
2. How is Supabase used? (if at all — check for supabase client)
3. What data analysis patterns exist in the codebase?
4. How are `/om_stats` and memory stats computed?
5. What dashboards or health checks exist?
6. Are there any data aggregation pipelines?

### Candidate Wiki Pages to Produce
| Page | Description | Impact if Written |
|------|-------------|-------------------|
| `.wiki/observability-guide.md` | Metrics tracked, health checks, logging | High — operational awareness |
| `.wiki/data-metrics-map.md` | What data is collected, where, how analyzed | Medium — analytics understanding |
| `.wiki/memory-stats-guide.md` | /om_stats, memory metrics, OpenMemory tracking | Medium — memory debugging |

### Security Issues / Critical Gaps
- Gap: No data retention policy documented — what gets stored, how long?
- Gap: Observability data might contain PII — need to verify
- Security: Check if supabase queries are parameterized (SQL injection risk)

---

## CYCLE 15: SUPABASE & DATABASE
**Domain:** Database schema, RLS policies, backend patterns

### Target Files to Read
- `/home/newadmin/swarm-bot/supabase/` (if exists)
- `/home/newadmin/swarm-bot/` for supabase client usage
- `/home/newadmin/swarm-bot/.wiki/architecture/block_02_database_schema.md`

### Research Questions
1. What Supabase tables exist? What is the schema?
2. Are RLS policies defined? Are they enforced?
3. How does the Supabase client authenticate?
4. What tables are being written to vs read from?
5. Is there a migration system?
6. What backup/recovery exists?

### Candidate Wiki Pages to Produce
| Page | Description | Impact if Written |
|------|-------------|-------------------|
| `.wiki/supabase-schema-guide.md` | Tables, RLS policies, auth patterns | High — data layer understanding |
| `.wiki/database-patterns.md` | Query patterns, migrations, backups | Medium — operational reliability |

### Security Issues / Critical Gaps
- Critical: RLS policies — verify they exist and are enabled
- Security: API keys for Supabase — are they in env, not hardcoded?
- Gap: No documented migration strategy

---

## CYCLE 16: GIT & VERSION CONTROL
**Domain:** GitHub integrations, PR handling, commit analysis

### Target Files to Read
- `/home/newadmin/swarm-bot/tools/composio_hub.py` (GitHub aspects)
- `/home/newadmin/swarm-bot/handlers/github_intel_handler.py`
- `/home/newadmin/swarm-bot/handlers/system.py` (git command)
- `/home/newadmin/swarm-bot/core/self_upgrade.py`

### Research Questions
1. How does `/github_intel` work? What GitHub API calls are made?
2. How does self-upgrade analyze GitHub trending repos?
3. What GitHub actions are triggered programmatically?
4. How does the `/git` command work in system.py?
5. What is the upgrade process? (git pull + restart pipeline)
6. Are there any GitHub webhook handlers?

### Candidate Wiki Pages to Produce
| Page | Description | Impact if Written |
|------|-------------|-------------------|
| `.wiki/github-intel-guide.md` | /github_intel, /eval_repo, upgrade_from | High — code quality intelligence |
| `.wiki/git-workflow-guide.md` | /git command, upgrade process, rollback | Medium — operational clarity |
| `.wiki/self-upgrade-pipeline.md` | Trending analysis, hot-reload, scan_weekly_trends | Medium — autonomous improvement |

### Security Issues / Critical Gaps
- Security: GitHub API keys — verify not hardcoded, proper scopes
- Gap: No commit message linting or PR quality checks
- Gap: Self-upgrade could pull malicious code — is there any verification?

---

## CYCLE 17: DEPLOYMENT & CI/CD
**Domain:** Systemd service, GitHub workflows, deployment patterns

### Target Files to Read
- `/home/newadmin/swarm-bot/main.py` (startup, health checks)
- `/home/newadmin/swarm-bot/.github/workflows/ci.yml`
- `/home/newadmin/swarm-bot/.github/workflows/release.yml`
- `/home/newadmin/swarm-bot/.github/workflows/typecheck.yml`
- `/home/newadmin/swarm-bot/` for systemd service files

### Research Questions
1. What systemd service configuration exists?
2. How does the CI/CD pipeline work? (CI → release → typecheck)
3. What is the startup sequence in main.py?
4. What health checks run at startup? (FEATURE_FLAGS, verify_api_keys)
5. What are the rollback procedures?
6. How is the bot deployed to production?

### Candidate Wiki Pages to Produce
| Page | Description | Impact if Written |
|------|-------------|-------------------|
| `.wiki/deployment-guide.md` | Startup sequence, systemd, health checks, rollback | High — operational reliability |
| `.wiki/cicd-pipeline-guide.md` | GitHub workflows, CI gates, release process | Medium — development workflow |
| `.wiki/systemd-service-spec.md` | Service config, restart policy, logging | Medium — production stability |

### Security Issues / Critical Gaps
- Security: Production deployment credentials — verify secure storage
- Gap: No canary deployment strategy
- Gap: No rollback automation beyond git stash

---

## CYCLE 18: API & INTEGRATIONS
**Domain:** External API patterns, n8n bridge, third-party integrations

### Target Files to Read
- `/home/newadmin/swarm-bot/tools/n8n_bridge.py`
- `/home/newadmin/swarm-bot/handlers/` (API handlers)
- `/home/newadmin/swarm-bot/tools/composio_hub.py` (generic API patterns)
- `/home/newadmin/swarm-bot/tools/` (other integrations)

### Research Questions
1. How does n8n_bridge work? What workflows are triggered?
2. What external API integrations exist?
3. How are API keys managed? (os.getenv pattern verification)
4. What is the retry/circuit breaker pattern for external APIs?
5. Are there webhook handlers for external services?
6. What is the rate limiting strategy for external APIs?

### Candidate Wiki Pages to Produce
| Page | Description | Impact if Written |
|------|-------------|-------------------|
| `.wiki/n8n-bridge-guide.md` | Workflow triggers, n8n integration patterns | High — automation reliability |
| `.wiki/api-integration-patterns.md` | External API calls, retry logic, error handling | High — integration stability |
| `.wiki/rate-limit-strategy.md` | Per-service rate limits, circuit breakers | Medium — external API resilience |

### Security Issues / Critical Gaps
- Critical: n8n_bridge modifies crontab unsandboxed (per ADR-005)
- Security: API keys for external services — verify secure storage
- Gap: No API contract testing

---

## CYCLE 19: ERROR HANDLING & DEBUGGING
**Domain:** Error patterns, recovery strategies, logging

### Target Files to Read
- `/home/newadmin/swarm-bot/core/` (error handling patterns)
- `/home/newadmin/swarm-bot/handlers/shared.py`
- `/home/newadmin/swarm-bot/llm_client.py` (error handling in LLM calls)

### Research Questions
1. What is the exception hierarchy? Are there custom exception types?
2. How are errors logged? (format, levels, destinations)
3. What is the retry strategy for transient failures?
4. How does circuit breaker work? (where is it used?)
5. What happens when an error is not caught? (bare except?)
6. How are async exceptions handled differently from sync?
7. What is the panic recovery procedure?

### Candidate Wiki Pages to Produce
| Page | Description | Impact if Written |
|------|-------------|-------------------|
| `.wiki/error-handling-guide.md` | Exception hierarchy, logging patterns, retry logic | High — debugging speed |
| `.wiki/circuit-breaker-pattern.md` | When trip/retry/reset happen, health state | High — resilience |
| `.wiki/debugging-playbook.md` | Common errors, log locations, recovery steps | High — incident response |

### Security Issues / Critical Gaps
- Gap: `bare except` in main.py — need to verify what's caught
- Gap: Circuit breaker health state is in-memory only — lost on restart (per ADR-005)
- Security: Error messages could leak sensitive info to users

---

## CYCLE 20: TESTING & QUALITY
**Domain:** Test patterns, pytest configuration, quality gates

### Target Files to Read
- `/home/newadmin/swarm-bot/tests/` (test files)
- `/home/newadmin/swarm-bot/pytest.ini` or `pyproject.toml`
- `/home/newadmin/swarm-bot/.github/workflows/ci.yml` (CI test gates)

### Research Questions
1. What test framework is used? (pytest-asyncio confirmed)
2. What are the test categories? (unit, integration, smoke tests)
3. How are async tests handled?
4. What is the test discovery pattern?
5. How does CI gate work? (what fails CI?)
6. Are there any test fixtures? How are they shared?
7. What is the code coverage situation?
8. Are there any mutation testing or fuzzing?

### Candidate Wiki Pages to Produce
| Page | Description | Impact if Written |
|------|-------------|-------------------|
| `.wiki/testing-guide.md` | Test framework, async patterns, fixtures | High — test reliability |
| `.wiki/ci-quality-gates.md` | What CI checks, what fails build, coverage | Medium — code quality |
| `.wiki/test-patterns.md` | Common patterns, mocking, assertions | Medium — developer productivity |

### Security Issues / Critical Gaps
- Gap: No security-specific test suite (SQL injection, XSS, etc.)
- Gap: Test coverage unknown — no coverage reporting in CI
- Security: Test fixtures might use real credentials — need to verify

---

## WORKER LAUNCH SUMMARY

| Worker | Cycle | Domain | Files to Read | Pages to Produce |
|--------|-------|--------|---------------|------------------|
| Worker-11 | 11 | Browser & Web | 3 files | 3 pages |
| Worker-12 | 12 | Email & Comms | 3 files | 3 pages |
| Worker-13 | 13 | Voice & Media | 3 files | 3 pages |
| Worker-14 | 14 | Data & Analytics | 3 files | 3 pages |
| Worker-15 | 15 | Supabase & DB | 3 files | 2 pages |
| Worker-16 | 16 | Git & VC | 4 files | 3 pages |
| Worker-17 | 17 | Deployment & CI/CD | 4 files | 3 pages |
| Worker-18 | 18 | API & Integrations | 4 files | 3 pages |
| Worker-19 | 19 | Error Handling | 3 files | 3 pages |
| Worker-20 | 20 | Testing & Quality | 3 files | 3 pages |

**Total candidate pages:** 29
**Expected approved (debate threshold 7+):** ~20-25 pages

---

## DEBATE PROTOCOL REMINDER

For each candidate page, run:
1. **ADVOCATE**: Argues FOR — capability improvement, speed/awareness gain, what Legion does wrong without it
2. **SKEPTIC**: Argues AGAINST — already covered, token bloat, implementation-specific, speculative
3. **JUDGE**: Scores 1-10, verdict WRITE/REJECT

**Scoring rubric:**
- 9-10: Critical Legion failure mode fixed OR major new capability unlocked
- 7-8: Meaningfully improves existing capability Bashara uses daily
- 5-6: Nice to have, borderline token cost
- 3-4: Already covered elsewhere, minimal new value
- 1-2: Speculative, outdated, or harmful

**Only scores 7+ get written to .wiki/**

---

## WIKI PAGE FORMAT (mandatory)

Every page must follow this exact structure:
```markdown
---
title: [page title]
domain: [which subagent wrote this]
impact_score: [judge's score 1-10]
last_updated: 2026-04-12
injects_into: [which task types benefit]
tokens_estimated: [rough token count]
---

# [TITLE]

## ONE-LINE SUMMARY
[Single sentence. What does Legion do better because of this page?]

## FACTS
[Bullet list of concrete facts. Max 15 bullets.]

## LEGION BEHAVIOR RULES
[Numbered list of rules. Max 10 rules.]

## EXAMPLES
[2-3 concrete examples of Bashara message vs ideal Legion response]

## ANTI-PATTERNS
[2-3 failure modes without this page]

## DEBATE RECORD
Advocate: [score] | Skeptic: [score] | Judge: [verdict] [score]
Judge note: [1 sentence]
```

Page size limit: 600 tokens per page.

---

## LOGGING REQUIREMENTS

After each cycle, update `.wiki/LOOP_LOG.md` with:
- Cycle number and domain
- Pages written (with impact score)
- Pages rejected (with reason)
- Key findings (3 bullet points)
- Time taken

---

## CROSS-CYCLE SECURITY FLAGS TO TRACK

These issues were already identified in Cycles 1-10 and should be validated NOT repeated:
1. 4 subprocess.run() calls modify crontab unsandboxed (project_manager.py, n8n_bridge.py, cron_setup.py)
2. Telegram webhook has no verification secret
3. 4 separate ALLOWED_USER_ID sources of truth
4. 2 duplicate daily briefings (7:30AM + 8AM)
5. Circuit breaker health state in-memory only

Workers in Cycles 11-20 should NOT re-document these — they should FOCUS on their specific domains.

---

*Plan created: 2026-04-12 by @planner*
*Output: .wiki/logs/planner-cycles-11-20.md*
