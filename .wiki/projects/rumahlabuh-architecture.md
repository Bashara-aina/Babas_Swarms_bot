# rumahlabuh.com — Architecture & Business Context
Generated: April 11, 2026
Source: swarm-bot codebase + BASHARA-MASTER-PROFILE

---

## Business Overview
- **Type**: Premium kos (boarding house) booking platform
- **Properties**:
  - Kost Labuh Biru, Pajang, Surakarta (23 rooms)
  - Kost Labuh Banyu, Pajang, Surakarta (9 rooms)
- **Total capacity**: 32 rooms
- **URL**: https://rumahlabuh.com
- **Current occupancy**: ~40% (down from ~80% in 2025)
- **Revenue**: 30–50 million IDR/month (varies)
- **Definition of "done"**: Stable 80–100% occupancy

---

## Tech Stack
- **Frontend**: Next.js + React
- **Backend/Database**: Supabase (PostgreSQL)
- **Payments**: Midtrans (Indonesian payment gateway)
- **WhatsApp notifications**: Fonnte WhatsApp API
- **Hosting**: Vercel
- **SEO**: JSON-LD schemas (LodgingBusiness, WebSite, Organization)

---

## Supabase Schema (tools/supabase_client.py)
The bot uses `tools/supabase_client.py` — an async REST client wrapping Supabase PostgREST API.

### Key Tables (introspect via `introspect_schema()`)
- **bookings** — booking records (id, user_id, property, check_in, check_out, status, total_price)
- **users/profiles** — tenant/guest information
- **payments** — Midtrans transaction records
- **rooms** — room inventory per property

### Available Operations (via SupabaseClient)
```python
# Query bookings
await db.query("bookings", select="id,status,total_price", eq={"status": "confirmed"})

# Check health
await db.health_check()  # → {ok, latency_ms}

# Introspect schema
await db.introspect_schema()  # → {table_name: [{column, type, nullable}]}

# Natural language query
await db.query_natural("show me bookings this week")
```

### Environment Variables Required
```
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=<anon_key>
SUPABASE_SERVICE_ROLE_KEY=<service_role_key>
```

---

## Database Agent Skill (skills/database_agent.py)
- Natural language → PostgREST SQL queries
- SELECT-only for safety (validated before execution)
- Returns HTML formatted tables for Telegram
- Falls back to schema introspection if skill file missing

---

## Booking Alert System (tools/rumahlabuh_crew.py)
- `check_booking_alerts()` — monitors new bookings last 30min, failed payments, overbooking detection
- Runs via proactive scheduler every 30 minutes
- Alerts via Telegram when anomalies detected

---

## Pain Points (2026)
1. Occupancy dropped from 80% → 40%
2. Low website visitor count
3. SEO not yet ranking in AI search recommendations (Perplexity, Gemini)

### SEO Recovery Status
- JSON-LD schemas implemented (LodgingBusiness, WebSite, Organization)
- Targeting AI model visibility
- Consider: Google Business Profile, Mamikos/Kos-Kosan/Infokos aggregators

---

## Legion's Role
- Monitor uptime (ping every 30 min via proactive scheduler)
- Supabase health check
- Daily booking summary
- SEO alerts if site performance degrades
- Alert immediately if rumahlabuh.com is down or slow

---

## Related Wiki Files
- `.wiki/profiles/BASHARA-MASTER-PROFILE.md` — business context
- `.wiki/research/EXTERNAL-RESEARCH-FINDINGS.md` — Surakarta market research
