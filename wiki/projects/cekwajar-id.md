---
title: cekwajar-id
type: project
status: active
tags: [indonesia, salary, fairness, web-app]
created: 2026-04-13
updated: 2026-04-13
summary: cekwajar.id is an Indonesian wage fairness platform helping users compare salaries and understand compensation fairness.
wikilinks: [[entities/supabase.md], [architecture/cekwajar-tech-stack.md], [concepts/freemium-gate.md]]
confidence: high
source: implementation
---

# cekwajar.id

## TL;DR
cekwajar.id is a Next.js + Supabase web application helping Indonesian workers understand wage fairness through salary comparisons and market data.

## Goals

- Help workers understand if their salary is fair
- Provide market data for salary negotiation
- Aggregate Indonesian salary information

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js (App Router) |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth |
| Styling | Custom CSS |
| Deployment | Vercel |

## Database Schema

See [[architecture/cekwajar-tech-stack.md]]

## Features

- Salary comparison dashboard
- Market rate lookup
- User salary submissions
- PDF report generation

## Related Pages

- [[architecture/cekwajar-tech-stack.md]] — Technical details
- [[entities/supabase.md]] — Database
- [[concepts/freemium-gate.md]] — Monetization
