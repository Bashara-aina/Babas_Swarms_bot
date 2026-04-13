---
title: Supabase
type: entity
status: active
tags: [database, backend, postgres, realtime]
created: 2026-04-13
updated: 2026-04-13
summary: Supabase is the primary database for rumahlabuh.com and cekwajar.id, providing PostgreSQL, Row Level Security (RLS), auth, and realtime subscriptions for both projects.
wikilinks:
  - [[rumahlabuh-com]]
  - [[cekwajar-id]]
confidence: high
source: implementation
project: general
---

# Supabase

## TL;DR
Supabase is an open-source Firebase alternative used as the primary database for both rumahlabuh.com (property listings) and cekwajar.id (salary survey data). It provides PostgreSQL with Row Level Security, authentication, and realtime subscriptions. Both projects connect via `SUPABASE_URL` and `SUPABASE_KEY` environment variables.

## Projects Using Supabase

### rumahlabuh.com — Property Rental Platform
- `rumahlabuh_db`: Property listings, amenities, photos
- User authentication (email + password)
- Booking inquiry submissions
- RLS policies: only owners can edit their own listings

### cekwajar.id — Salary Fairness Platform
- `cekwajar_db`: Salary survey responses, company data, wage benchmarks
- Anonymous data submission with privacy controls
- Survey aggregation queries
- PPH 21 tax calculations (Indonesian payroll)

## Features Used

| Feature | Implementation |
|---------|----------------|
| PostgreSQL | Primary relational database |
| Auth | Email/password via Supabase Auth |
| Realtime | Live dashboard updates (optional) |
| Row Level Security | Per-table access policies |
| Storage | Property photo uploads |

## Connection
```python
from supabase import create_client, create_client
client = create_client(SUPABASE_URL, SUPABASE_KEY)
# All queries go through the official supabase-py client
```

## Environment Variables
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1...  # anon/public key
```
Never log SUPABASE_KEY values.

## See Also
[[rumahlabuh-com]] — Property platform using Supabase
[[cekwajar-id]] — Salary platform using Supabase for survey data
