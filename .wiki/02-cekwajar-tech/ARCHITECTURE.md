---
title: Architecture
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- cekwajar-tech
created: '2026-04-14'
updated: '2026-04-14'
summary: 'title: "cekwajar.id — Technical Architecture"'
wikilinks: []
confidence: medium
source: research
---
***
title: "cekwajar.id — Technical Architecture"
stack: Next.js 15 · TypeScript · Supabase · Vercel · Tailwind CSS
***

# cekwajar.id Technical Architecture

## Stack Overview

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 15 (App Router) + TypeScript | UI + SSR |
| Styling | Tailwind CSS | Design system |
| Backend | Supabase Edge Functions | Server-side logic |
| Database | PostgreSQL (Supabase) + pgvector | Data + semantic search |
| Auth | Supabase Auth | User management |
| Payments | Midtrans | IDR subscription + one-time |
| Hosting | Vercel | Frontend deployment |
| CDN | Vercel Edge | Static assets |
| AI | OpenRouter / MiniMax M2.7 | Legion backbone |

## Freemium Gating Architecture

All gating is enforced **server-side in Supabase Edge Functions**.
Free-tier users receive same API structure; locked fields return `null`
with `gated: true` flag. This prevents client-side bypass.

```typescript
// Edge Function pattern: generate-verdict/index.ts
// 1. Verify user auth token (Supabase JWT)
// 2. Check monthly verdict quota (verdictsUsedThisMonth < verdictsQuota)
// 3. Compute verdict via PostgreSQL RPC function
// 4. Log to verdictLogs (anonymized)
// 5. Return response with field-level gating applied
```

### Monthly Quota Enforcement
```sql
-- Atomic quota check + increment
IF userData.verdictsUsedThisMonth >= userData.verdictsQuota THEN
  RETURN 429 Too Many Requests
END IF;

UPDATE users 
SET verdictsUsedThisMonth = verdictsUsedThisMonth + 1
WHERE id = userId;
```

## Database Schema

| Table | Purpose | Access |
|-------|---------|--------|
| `users` | Auth, subscription, quota tracking | Private (RLS) |
| `rawSalarySubmissions` | Unvalidated user salary data | Private (own only) |
| `rawLandSubmissions` | Unvalidated land transaction data | Private (own only) |
| `crowdsourceQueue` | AI validation pipeline queue | Internal |
| `benchmarkSalary` | Public salary percentiles (k-anon ≥ 10) | **Public read** |
| `benchmarkLandPrices` | Public land price percentiles | **Public read** |
| `benchmarkCostOfLiving` | Public CoL indices | **Public read** |
| `benchmarkAbroadData` | International country data | **Public read** |
| `taxRules` | Versioned tax/BPJS rates | **Public read** |
| `verdictLogs` | Audit trail (anonymized) | Private (RLS) |
| `jobCategories` | Kemnaker taxonomy + pgvector embeddings | **Public read** |
| `cityRegistry` | All Indonesian admin regions | **Public read** |

## k-Anonymity Enforcement
```sql
-- benchmarkSalary only publishes cells where n ≥ 10
CHECK (sampleCount >= 10)
-- Raw submissions → crowdsourceQueue → validated → aggregate Edge Function → benchmark
```

## pgvector Job Matching
```sql
SELECT id, title, 1 - (embedding <=> query_embedding) AS similarity
FROM jobCategories ORDER BY similarity DESC LIMIT 5;
```
Similarity thresholds: ≥ 0.9 (exact), 0.7–0.9 (similar), < 0.5 (different)

## Privacy Architecture

1. Raw data NEVER touches published benchmarks (server-side only)
2. k-anonymity minimum: 10 validated submissions per benchmark cell
3. RLS at Postgres level — users cannot query others' data
4. No raw IP storage — hashed before storing
5. GDPR/UU PDP 27/2022 aligned — consent recorded, right to deletion
6. Encrypted at rest via Supabase Vault

## Tax Rate Versioning (Audit Trails)
All rates stored with `effectiveFrom` + `effectiveUntil` in `taxRules`.
Every verdict snapshot stores the rate set used at calculation time.

```json
{
  "payslipId": "SLIP-2026-04-EMP001",
  "ratesSnapshot": {
    "PTKP_K1": 63000000,
    "UMK_Jakarta": 4900000,
    "BPJS_JP_cap": 9559600,
    "BPJS_Kesehatan_cap": 12000000,
    "progressiveBrackets": [[60000000, 0.05], [250000000, 0.15]]
  }
}
```

## Shareable Verdict Cards (1080×1920px PNG)
```json
{
  "verdictCard": {
    "background": "linear-gradient(to bottom, #4F46E5, #7C3AED)",
    "colors": {
      "Di Atas Pasar": "#10B981",
      "Wajar": "#F59E0B",
      "Di Bawah Pasar": "#EF4444",
      "Bawah UMR": "#991B1B"
    }
  }
}