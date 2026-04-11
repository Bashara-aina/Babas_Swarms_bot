---
title: "rumahlabuh API Structure - PARTIAL"
source_type: CODE_EXTRACTION
extracted_from: rumahlabuh
date: 2026-04-11
tags: [rumahlabuh, api, booking, flow, PARTIAL]
---

# rumahlabuh API Structure and Booking Flow

## Status: PARTIAL EXTRACTION

### Evidence from SwarmBot Code
rumahlabuh integration is found in:
- `tools/rumahlabuh_crew.py` — CrewAI integration for rumahlabuh tasks
- `handlers/business_handler.py` — `/bookings` command

### Functions Found

From `tools/rumahlabuh_crew.py`:
```python
async def _query_supabase(query_description: str) -> str:
async def check_website_uptime(url: str = "https://rumahlabuh.com") -> dict[str, Any]:
async def draft_guest_reply(guest_message: str, guest_name: str = "Guest") -> str:
async def check_booking_alerts() -> list[str]:
async def get_business_summary() -> str:
def build_rumahlabuh_crew() -> Any | None:
def get_rumahlabuh_crew() -> Any | None:
async def run_crew_task(task_description: str) -> str:
```

### Business Handler Commands
From `handlers/business_handler.py`:
- `/db` — Database operations
- `/site_health` — Health check
- `/bookings` — Booking management
- `/db_schema` — Database schema

### Note
The full rumahlabuh API documentation and booking flow design are not explicitly
documented in the wiki. Only partial integration points through Supabase queries
and CrewAI tasks are visible in the SwarmBot codebase.

---
*Extracted: 2026-04-11 by @worker*
