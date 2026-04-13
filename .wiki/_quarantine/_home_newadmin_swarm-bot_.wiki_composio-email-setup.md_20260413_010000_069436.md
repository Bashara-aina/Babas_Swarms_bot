---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/composio-email-setup.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.069459"
}
---

---
title: composio-email-setup
domain: communications
impact_score: 8
last_updated: 2026-04-12
injects_into: system, agents
tokens_estimated: 420
---

# Composio Email Setup

## ONE-LINE SUMMARY
850+ Composio tool connectors wired via tools/composio_hub.py and tools/composio_client.py — email via Gmail OAuth, graceful degradation when COMPOSIO_API_KEY is missing.

## CONNECTED TOOLS

### Gmail
- **Read**: `gmail_list_unread()`, `gmail_search()` — via `Action.GMAIL_LIST_THREADS`
- **Send**: `gmail_send()` — via `Action.GMAIL_SEND_EMAIL`
- **Query filter**: `is:unread` default for inbox, custom query support
- **Auth**: OAuth via Composio (run `composio add gmail` once on server)

### Google Calendar
- **Read**: `calendar_list_upcoming()`, `calendar_get_today_schedule()` — via `Action.GOOGLECALENDAR_LIST_EVENTS`
- **Create**: `calendar_create_event()` — via `Action.GOOGLECALENDAR_CREATE_EVENT`
- **Auth**: OAuth via Composio (run `composio add google-calendar` once)

### WhatsApp Business
- **Read**: `get_whatsapp_messages()` — via `WHATSAPP_GET_MESSAGES`
- **Send**: `send_whapp_message()` — via `WHATSAPP_SEND_MESSAGE`
- **Note**: Requires WhatsApp Business API configured in Composio

### GitHub (augments existing github_intel.py)
- **Create issue**: `github_create_issue()` — via `Action.GITHUB_CREATE_AN_ISSUE`
- **Note**: Existing github_intel.py handles most GitHub ops; Composio is fallback

## PERMISSIONS MODEL

Composio handles OAuth token management automatically:
1. User runs `composio login` on server
2. User runs `composio add gmail google-calendar github` — OAuth consent flows
3. Composio manages token refresh automatically
4. Legion calls tools via `os.getenv("COMPOSIO_API_KEY")` — no tokens stored in code

Required env vars:
```
COMPOSIO_API_KEY=   # From https://app.composio.dev
```

## GRACEFUL DEGRADATION

When `COMPOSIO_API_KEY` is not set:
```python
# composio_hub.py _get_composio_toolset()
api_key = os.getenv("COMPOSIO_API_KEY", "")
if not api_key:
    logger.info("[ComposioHub] COMPOSIO_API_KEY not set — Composio features disabled")
    return None
```

All functions return error dicts instead of raising:
```python
# gmail_list_unread()
return [{"error": "Composio not configured. Set COMPOSIO_API_KEY..."}]
# send_email()
return await composio_action("GMAIL_SEND_EMAIL", {...})  # returns {"error": "..."}
```

`composio_hub_status()` returns human-readable status for `/keys` command:
- `❌ Composio: not configured (COMPOSIO_API_KEY missing)`
- `❌ Composio: init failed (check logs)`
- `✅ Composio: ready (850+ tool connectors)`

## ERROR HANDLING STRATEGY

All Composio calls use 3-layer fallback:
1. **Primary**: `tools.composio_client` specialized functions (more reliable)
2. **Fallback**: Generic `composio_action("ACTION_NAME", params)` 
3. **Graceful error**: Returns `{"error": "..."}` dict — never raises

```python
async def get_unread_emails(max_results: int = 10) -> list[dict[str, Any]]:
    try:
        from tools.composio_client import gmail_list_unread
        emails = await gmail_list_unread(max_results=max_results)
        if emails and not (len(emails) == 1 and "error" in emails[0]):
            return emails
    except Exception:
        pass
    # Generic Composio fallback
    result = await composio_action("GMAIL_FETCH_EMAILS", {"max_results": max_results, "query": "is:unread"})
    return result.get("emails", result.get("messages", [result] if "error" not in result else []))
```

## TELEGRAM INTEGRATION

`handlers/communications.py` exposes two slash commands:
- `/emails` or `/inbox` — shows unread emails
- `/calendar` — shows upcoming 7-day events

Output format: HTML with `html.escape()` on all content:
```python
sender = html.escape(str(e.get("from", e.get("sender", "Unknown")))[:60])
subject = html.escape(str(e.get("subject", "No subject")))[:80]
lines.append(f"<b>From:</b> {sender}\n<b>Subject:</b> {subject}\n<i>{snippet}</i>\n")
```

## SETUP COMMANDS

```bash
# Install Composio
pip install composio-core composio-langchain

# Authenticate (run once on server)
composio login

# Connect apps
composio add gmail google-calendar github

# Set API key in .env
COMPOSIO_API_KEY=your_key_here
```

## LIMITATIONS

1. **No content filtering**: `html.escape()` prevents HTML injection but no anti-phishing/URL scanning
2. **No email deletion/marking read**: Only list and send
3. **Calendar shows ALL events**: No per-user filtering — every authenticated calendar event appears
4. **WhatsApp requires Business API**: Regular WhatsApp not supported
5. **No draft management**: Only send, no draft operations

## DEBATE RECORD
Advocate: 8 | Skeptic: 7 | Judge: WRITE 8
Advocate note: Core email/calendar infrastructure — 8 because it's foundational for productivity workflows.
Skeptic note: WhatsApp Business is rarely used; could reduce scope.
Judge note: Email+Calendar is mission-critical for Bashara's productivity — write.
