---
title: supabase
type: entity
status: active
tags: [database, backend, postgres, realtime]
created: 2026-04-13
updated: 2026-04-13
summary: Supabase is the primary database for rumahlabuh.com and cekwajar.id, providing PostgreSQL, auth, and realtime subscriptions.
wikilinks: [[rumahlabuh-com]], [[cekwajar-id]]
confidence: high
source: implementation
---

# Supabase

## TL;DR
Supabase is an open-source Firebase alternative providing PostgreSQL database, authentication, and realtime subscriptions used by rumahlabuh and cekwajar.

## Projects Using Supabase

### rumahlabuh.com
- Property listings storage
- User authentication
- Booking inquiries

### cekwajar.id
- Salary data storage
- User accounts
- Survey responses

## Features Used

| Feature | Usage |
|---------|-------|
| PostgreSQL | Primary database |
| Auth | User authentication |
| Realtime | Live updates |
| Row Level Security | Data isolation |

## Connection

```python
from supabase import create_client
client = create_client(SUPABASE_URL, SUPABASE_KEY)
```

## Related Pages

- [[rumahlabuh-com]] — Property platform
- [[cekwajar-id]] — Salary tool
