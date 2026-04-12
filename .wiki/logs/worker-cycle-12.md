# Worker Cycle 12: EMAIL & COMMUNICATIONS
Date: 2026-04-12
Executed by: @worker
Session: LEGION WIKI LOOP 2026-04-12

## TARGET FILES
- handlers/communications.py (84 lines)
- tools/composio_hub.py (209 lines)
- tools/composio_client.py (303 lines)
- .env.example (COMPOSIO_API_KEY at line 159)

## DOMAIN
Composio email/calendar integrations, email handler, WhatsApp bridge

## SOURCE ANALYSIS

### Research Questions & Answers

**1. What Composio tools are connected?**
- Gmail: read (GMAIL_LIST_THREADS), send (GMAIL_SEND_EMAIL), search
- Google Calendar: list events (GOOGLECALENDAR_LIST_EVENTS), create event (GOOGLECALENDAR_CREATE_EVENT)
- WhatsApp Business: get messages, send messages
- GitHub: create issue (augments existing github_intel.py)
- Slack, Notion, Web search via Composio

**2. How is email content filtered for security?**
- html.escape() on all display fields (from, subject, snippet)
- NO URL scanning in body
- NO sender verification against contacts
- NO content policy/anti-phishing patterns
- Attachments not displayed

**3. What happens if COMPOSIO_API_KEY is missing?**
- _get_composio_toolset() returns None
- All functions return {"error": "Composio not configured..."} dict
- composio_hub_status() returns "❌ Composio: not configured"
- Features disabled gracefully — no crashes

**4. How are calendar events filtered?**
- NO user/calendar_id filtering
- ALL events from ALL calendars returned
- No organizer filter
- No personal vs work separation
- This is a privacy/confusion gap

**5. What is the error handling strategy?**
- 3-layer fallback: composio_client → composio_action → error dict
- Exceptions caught and logged
- Returns error dicts, never raises
- asyncio.to_thread() for blocking calls

**6. How does output get formatted for Telegram?**
- HTML: <b>, <i>, <code> tags
- html.escape() on all user content
- send_chunked() for long output
- Truncation at 60/80/120 chars for from/subject/snippet
- Parse mode: HTML

**7. What permissions are requested?**
- Gmail: OAuth read+send (composio add gmail)
- Calendar: OAuth read+write (composio add google-calendar)
- Composio manages token refresh automatically
- No explicit scope configuration in code

**8. What happens on rate limits or API failures?**
- Composio SDK handles rate limit retry
- Network failures: exception → error dict
- Logged as warnings
- No user-facing retry UI

## PAGES CREATED

### 1. composio-email-setup.md (impact: 8)
- Connected tools list
- Permissions model
- Graceful degradation
- Error handling strategy
- Setup commands
- Limitations

### 2. composio-calendar-guide.md (impact: 7)
- Core functions (read, create, today's schedule)
- Event filtering gap (NO user/calendar filtering)
- Timezone handling (hardcoded Asia/Tokyo)
- Briefing integration
- Rate limits & API failures
- Limitations and recommended fixes

### 3. email-security-patterns.md (impact: 8)
- HTML escape pattern (what is protected)
- What is NOT protected (URL scanning, sender verification, content analysis)
- Send email security (no content filtering)
- WhatsApp security (same pattern)
- Composio OAuth security
- Recommended additions (URL scanner, contact verification, content policy)
- Risk matrix

## DEBATE RESULTS

| Page | Advocate | Skeptic | Judge | Score | Status |
|------|----------|---------|-------|-------|--------|
| composio-email-setup.md | 8 | 7 | 8 | 8 | ✅ WRITE |
| composio-calendar-guide.md | 7 | 7 | 7 | 7 | ✅ WRITE |
| email-security-patterns.md | 8 | 7 | 8 | 8 | ✅ WRITE |

All 3 pages approved (score >= 7).

## FILES COPIED TO .WIKI/
- composio-email-setup.md
- composio-calendar-guide.md
- email-security-patterns.md

## KEY INSIGHTS

1. **Critical calendar gap**: ALL events from ALL calendars returned — no user filtering
2. **Email security is minimal**: html.escape() prevents injection but no anti-phishing
3. **WhatsApp requires Business API**: Not可用 for regular WhatsApp
4. **Hardcoded timezone**: Calendar create only works with Asia/Tokyo
5. **Graceful degradation**: Missing API key disables features without crashes

## RECOMMENDED FIXES (Priority Order)

1. **HIGH**: Add calendar_id parameter to filter which calendar to read
2. **HIGH**: Add URL scanning in email display
3. **MEDIUM**: Add timezone config env var for calendar create
4. **MEDIUM**: Add email content policy (wire fraud, password reset patterns)
5. **LOW**: Add update/delete calendar operations

## TIME SPENT
- Source analysis: ~3 minutes
- Page creation: ~2 minutes
- Review & copy: ~1 minute
- Total: ~6 minutes

---

*Cycle 12 complete — 3 pages written, 0 rejected*
