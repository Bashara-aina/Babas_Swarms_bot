---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/architecture/cekwajar-tech-stack.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-11T01:00:00.392422"
}
---

---
title: cekwajar-tech-stack
type: architecture
status: active
tags: [cekwajar, tech-stack, database, nextjs]
created: 2026-04-13
updated: 2026-04-13
summary: cekwajar.id uses Next.js App Router, Supabase PostgreSQL, and Vercel deployment.
wikilinks:
  - [[projects/cekwajar-id]]
  - [[entities/supabase]]
confidence: high
source: implementation
---

# Cekwajar Tech Stack

## TL;DR
Next.js App Router frontend with Supabase PostgreSQL backend, deployed on Vercel.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Next.js App   │────▶│    Supabase     │
│   (Vercel)      │     │   (PostgreSQL)  │
└─────────────────┘     └─────────────────┘
        │
        ▼
┌─────────────────┐
│    Midtrans     │
│   (Payments)    │
└─────────────────┘
```

## Database Schema

### users
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| email | text | unique |
| created_at | timestamp | |

### salary_reports
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| user_id | uuid | FK → users |
| position | text | Job title |
| salary | integer | Monthly IDR |
| company | text | Company name |
| created_at | timestamp | |

### market_data
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| position | text | Indexed |
| salary_min | integer | |
| salary_max | integer | |
| salary_avg | integer | |
| source | text | |
| collected_at | timestamp | |

## API Routes

- `/api/submit-salary` — Submit salary data
- `/api/market-data` — Query market rates
- `/api/report` — Generate PDF report

## API Routes

### /api/submit-salary
Accepts anonymous salary submissions with validation:
- Request body: `{ industry, role, experience_years, monthly_salary, location }`
- Server-side validation: all fields required, salary > 0
- RLS: submitted anonymously, no user_id tracking
- Returns: `{ success: true, submission_id: uuid }`

### /api/market-data
Returns aggregated salary benchmarks:
- Query params: `?industry=&role=&region=`
- Reads from `market_bands` table
- Returns: `{ p25, p50, p75, sample_size, source }`

### /api/report
Generates PDF salary report for user:
- Requires: Supabase Auth session
- Calls: Puppeteer/headless Chrome for PDF generation
- Returns: Signed URL to PDF (expires: 24h)

## Deployment

| Environment | Platform | URL |
|------------|----------|-----|
| Production | Vercel | cekwajar.vercel.app |
| Staging | Vercel Preview | preview cekwajar |
| Database | Supabase | cekwajar-db.supabase.co |

## Environment Variables

```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...  # server-only
MIDTRANS_SERVER_KEY=xxx
MIDTRANS_CLIENT_KEY=xxx
```

## See Also

- [[projects/cekwajar-id]] — Project overview
- [[entities/supabase]] — Database provider
- [[concepts/labor-law-indonesia]] — Indonesian labor regulations affecting salary data
- [[concepts/market-data-indonesia]] — Salary benchmark data sources
