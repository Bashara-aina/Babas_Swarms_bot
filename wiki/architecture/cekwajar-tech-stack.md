---
title: cekwajar-tech-stack
type: architecture
status: active
tags: [cekwajar, tech-stack, database, nextjs]
created: 2026-04-13
updated: 2026-04-13
summary: cekwajar.id uses Next.js App Router, Supabase PostgreSQL, and Vercel deployment.
wikilinks: [[projects/cekwajar-id.md], [entities/supabase.md]]
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

## Related Pages

- [[projects/cekwajar-id.md]] — Project overview
- [[entities/supabase.md]] — Database
