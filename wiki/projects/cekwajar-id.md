---
title: cekwajar-id
type: project
status: active
tags: [indonesia, salary, fairness, web-app, nextjs, supabase]
created: 2026-04-13
updated: 2026-04-13
summary: cekwajar.id is an Indonesian wage fairness platform built with Next.js and Supabase that helps workers compare their salaries against market rates and understand compensation fairness using aggregated salary data and UU PDP compliance.
wikilinks:
  - [[supabase]]
  - [[cekwajar-tech-stack]]
  - [[freemium-gate]]
  - [[rumahlabuh-com]]
confidence: high
source: implementation
---

# cekwajar.id

## TL;DR
cekwajar.id (meaning "is it fair?" in Indonesian) is a Next.js + Supabase web application that empowers Indonesian workers to evaluate their salary fairness by comparing against aggregated market data. The platform collects salary submissions, provides anonymized benchmarking, and generates PDF reports for negotiation support — all compliant with Indonesian data protection laws (UU PDP).

## Project Overview

**Domain**: cekwajar.id  
**Target Users**: Indonesian workers seeking salary transparency and fair compensation  
**Core Value Proposition**: "Is my salary fair?" — providing data-driven answers  
**Tech Stack**: Next.js (App Router) + Supabase (PostgreSQL) + Vercel deployment

## Problem Statement

Indonesian workers face significant salary opacity:
- Limited publicly available salary data for most industries
- Cultural barriers to discussing compensation openly
- No standardized benchmarking tools for Indonesian market
- Difficulty articulating salary requests during negotiations

## Core Features

### 1. Salary Comparison Dashboard
Users input their role, industry, location, and experience level. The system returns:
- Position salary distribution (25th, 50th, 75th percentile)
- Comparison to user's submitted salary
- Visual representation of fairness score

### 2. Market Rate Aggregation
- Anonymous salary submissions from verified users
- Industry-specific salary bands
- Regional adjustments (Jakarta vs. other cities)
- Experience level normalization

### 3. Salary Submission System
- User-contributed salary data (anonymized)
- Verification process to ensure data quality
- GDPR-equivalent UU PDP compliance for Indonesian data protection

### 4. PDF Report Generation
- Exportable fairness reports for:
  - Performance reviews
  - Salary negotiation meetings
  - Annual appraisal support

## Tech Stack Details

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js (App Router) | SSR, API routes, React components |
| Database | Supabase PostgreSQL | Primary data store |
| Auth | Supabase Auth | User authentication |
| Storage | Supabase Storage | Report file storage |
| Analytics | Supabase Analytics | Usage tracking |
| Deployment | Vercel | Edge hosting |
| Styling | Custom CSS | Design system |

## Database Schema

Key tables in Supabase:

```sql
-- Salary submissions (anonymized)
salary_submissions (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users,
  industry TEXT,
  role TEXT,
  experience_years INTEGER,
  monthly_salary BIGINT,
  location TEXT,
  submitted_at TIMESTAMPTZ
)

-- Aggregated market data
market_bands (
  id UUID PRIMARY KEY,
  industry TEXT,
  role TEXT,
  p25_salary BIGINT,
  p50_salary BIGINT,
  p75_salary BIGINT,
  sample_size INTEGER,
  region TEXT
)

-- User profiles
user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users,
  display_name TEXT,
  created_at TIMESTAMPTZ,
  is_verified BOOLEAN DEFAULT false
)
```

## UU PDP Compliance

cekwajar.id follows Indonesian Personal Data Protection (UU PDP) requirements:

| Requirement | Implementation |
|-------------|----------------|
| Consent | Explicit opt-in for data collection |
| Purpose limitation | Data used only for salary benchmarking |
| Data minimization | Only essential fields collected |
| User rights | Delete/export functionality via Supabase RLS |
| Retention | Anonymization after 2 years |

## Integration with Legion

From `wiki/raw/docs/legion-master.md`, cekwajar.id is one of Bashara's active projects. Legion can:
- Check cekwajar status via `/cekwajar_status` skill
- Query Supabase for latest inquiry data
- Monitor platform health

## Related Pages

- [[cekwajar-tech-stack]] — Technical architecture
- [[supabase]] — Database provider
- [[freemium-gate]] — Monetization strategy
- [[rumahlabuh-com]] — Sister project (rental platform)
