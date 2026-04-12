---
title: composio-calendar-guide
domain: communications
impact_score: 7
last_updated: 2026-04-12
injects_into: system, agents, briefing
tokens_estimated: 380
---

# Composio Calendar Guide

## ONE-LINE SUMMARY
Google Calendar integration via Composio — reads ALL calendar events without user filtering, hardcoded to Asia/Tokyo timezone, used in daily briefings.

## CORE FUNCTIONS

### Read Events
```python
async def get_calendar_events(days_ahead: int = 7) -> list[dict[str, Any]]:
```
- Uses `Action.GOOGLECALENDAR_LIST_EVENTS` via Composio
- Returns next 7 days of events by default
- Falls back to generic `composio_action("GOOGLECALENDAR_LIST_EVENTS", ...)`
- Returns list of event dicts: `{summary, start{dateTime}, end{dateTime}, description, location}`

### Today's Schedule (for Briefing)
```python
async def calendar_get_today_schedule() -> str:
```
- Gets 8 upcoming events
- Filters to today's date only
- Returns formatted string: `[Today's calendar (JST):\n  09:00 — Meeting\n  14:00 — Review\n]`
- Returns empty string if no events (used in system prompt injection)

### Create Event
```python
async def create_calendar_event(title, start, end, description="") -> dict[str, Any]:
```
- Hardcoded to Asia/Tokyo timezone: `"timeZone": "Asia/Tokyo"`
- ISO 8601 format: `"2026-04-10T10:00:00+09:00"`
- Returns `{"error": "..."}` dict on failure

## TELEGRAM COMMAND

`/calendar` in `handlers/communications.py`:
```python
events = await get_calendar_events(days_ahead=7)
# Displays: "📅 Upcoming Events (next 7 days)"
# Format: "• Event Title — 2026-04-13T09:00"
# Limited to 8 events
```

## EVENT FILTERING — CRITICAL GAP

**No user/calendar filtering exists.**

All events from ALL calendars the Composio OAuth account has access to are returned. This means:
- Work calendar events appear
- Personal calendar events appear  
- Shared calendar events appear
- Other users' events on shared calendars appear

There is NO:
- `calendar_id` parameter to filter by specific calendar
- `owner` or `organizer` filter
- Bashara-specific calendar filter
- Exclusion rules for personal vs work

## TIMEZONE HANDLING

- All events created: hardcoded `Asia/Tokyo` timezone
- Events read: Composio returns ISO 8601 with timezone or UTC
- Display: Raw `dateTime` string shown, no timezone conversion in Telegram output

```python
# create_calendar_event hardcodes timezone
"start": {"dateTime": start, "timeZone": "Asia/Tokyo"},
"end": {"dateTime": end, "timeZone": "Asia/Tokyo"},
```

## BRIEFING INTEGRATION

`calendar_get_today_schedule()` is called for daily briefings:
```python
# Called in: tools/briefing.py or ProactiveScheduler
schedule = await calendar_get_today_schedule()
# Injected into system prompt as: "[Today's calendar (JST):\n  09:00 — Title\n]"
```

The briefing shows today's events only (not full week) to keep token count low.

## RATE LIMITS & API FAILURES

Composio handles rate limiting automatically:
- Token refresh: handled by Composio OAuth
- API rate limits: Composio SDK has built-in retry logic
- Network failures: Exception caught → `{"error": "..."}` returned → logged as warning

```python
# calendar_list_upcoming error handling
except Exception as e:
    logger.warning("calendar_list_upcoming failed: %s", e)
    return [{"error": str(e)}]
```

## LIMITATIONS

1. **No calendar filtering**: ALL calendars returned — privacy/confusion risk
2. **Hardcoded timezone**: Only `Asia/Tokyo` supported for event creation
3. **No update/delete**: Only read and create operations exist
4. **No recurring event support**: Single events only
5. **No attendee management**: Cannot add/remove attendees
6. **No meeting room/location search**: Location field accepted but not searched

## RECOMMENDED FIXES

1. **Add calendar_id parameter**: Allow filtering to specific calendar ID
2. **Add organizer filter**: Exclude other users' events on shared calendars
3. **Timezone configuration**: Make timezone configurable via env var
4. **Add update/delete operations**: Full CRUD for events
5. **Location search**: Query available meeting rooms/resources

## DEBATE RECORD
Advocate: 7 | Skeptic: 7 | Judge: WRITE 7
Advocate note: Calendar is used in daily briefings — foundation for meeting-aware behavior.
Skeptic note: No calendar filtering is a significant gap — events from ALL calendars appear.
Judge note: Gap is worth documenting — page scores 7 because it identifies actionable limitation.
