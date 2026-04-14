---
title: Adr 004 Dynamic Revalidation
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: Implement a **Dynamic Revalidation System** that makes every regulatory number
  (UMR, PTKP, BPJS rates, tax brackets) time-aware with explicit TTL (time-to-live).
  This ensures all verdict computatio...
wikilinks: []
confidence: medium
source: research
---
Implement a **Dynamic Revalidation System** that makes every regulatory number (UMR, PTKP, BPJS rates, tax brackets) time-aware with explicit TTL (time-to-live). This ensures all verdict computations use only current, non-expired data, and alerts Legion when data goes stale.

## Motivation

Currently, `taxRules` table has `effectiveFrom`/`effectiveUntil` columns but:
- No automated freshness enforcement at computation time
- No TTL warnings before expiry
- No audit trail of data freshness
- No alerts to maintainer when rates expire

**Problem**: If maintainer forgets to update rates after January 1 (UMR changes) or PTKP changes, verdicts compute with stale data → user harm.

**Solution**: TTL-gated verifications with proactive alerts to Legion.
---


## Technical Design

### 1. Database Stage (SQL Migrations)

```sql
-- 001_add_ttl_to_taxRules.sql
ALTER TABLE taxRules ADD COLUMN IF NOT EXISTS ttl_hours INTEGER;
ALTER TABLE taxRules ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMPTZ;

-- 002_create_umrRegistry.sql
CREATE TABLE umrRegistry (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  city_code TEXT NOT NULL,
  city_name TEXT NOT NULL,
  year INTEGER NOT NULL,
  umr_amount BIGINT NOT NULL,
  effective_from DATE NOT NULL,
  effective_until DATE,
  ttl_hours INTEGER DEFAULT 8760, -- 1 year default
  last_verified_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 003_create_bpjsRates.sql
CREATE TABLE bpjsRates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rate_type TEXT NOT NULL, -- 'JK' (Jaminan Kecelakaan), 'JHT', 'JPN', 'Kesehatan'
  effective_from DATE NOT NULL,
  effective_until DATE,
  rate_percentage NUMERIC(5,3) NOT NULL,
  cap_amount BIGINT,
  ttl_hours INTEGER DEFAULT 8760,
  last_verified_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 004_create_ptkpRates.sql
CREATE TABLE ptkpRates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status TEXT NOT NULL, -- 'K0', 'K1', 'K2', 'K3'
  dependents INTEGER NOT NULL,
  annual_amount BIGINT NOT NULL,
  effective_from DATE NOT NULL,
  effective_until DATE,
  ttl_hours INTEGER DEFAULT 8760,
  last_verified_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 005_create_dataFreshnessLog.sql
CREATE TABLE dataFreshnessLog (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  table_name TEXT NOT NULL,
  record_id UUID NOT NULL,
  freshness_status TEXT NOT NULL, -- 'FRESH', 'WARNING', 'EXPIRED', 'STALE'
  ttl_hours INTEGER NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  checked_at TIMESTAMPTZ DEFAULT NOW()
);

-- 006_create_staleDataAlerts.sql
CREATE TABLE staleDataAlerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  alert_hash TEXT NOT NULL UNIQUE, -- hash of table+record+day to dedupe
  table_name TEXT NOT NULL,
  record_id UUID NOT NULL,
  alert_type TEXT NOT NULL, -- 'EXPIRED', 'STALE', 'WARNING'
  message TEXT NOT NULL,
  sent_at TIMESTAMPTZ DEFAULT NOW(),
  resolved_at TIMESTAMPTZ
);

-- 007_create_v_data_freshness.sql
CREATE OR REPLACE VIEW v_data_freshness AS
SELECT 
  'taxRules' as table_name, id as record_id,
  CASE 
    WHEN effective_until < NOW() THEN 'EXPIRED'
    WHEN effective_until < NOW() + INTERVAL '30 days' THEN 'WARNING'
    ELSE 'FRESH'
  END as status,
  effective_until as expires_at,
  ttl_hours,
  last_verified_at
FROM taxRules
UNION ALL
SELECT 'umrRegistry' as table_name, id, 
  CASE WHEN effective_until < NOW() THEN 'EXPIRED' WHEN effective_until < NOW() + INTERVAL '30 days' THEN 'WARNING' ELSE 'FRESH' END,
  effective_until, ttl_hours, last_verified_at
FROM umrRegistry
UNION ALL
-- ... similar for bpjsRates, ptkpRates
```

### 2. Core Engine (`lib/revalidation/engine.ts`)

```typescript
// TTL_CONFIG per data type
const TTL_CONFIG = {
  umrRegistry: { ttlHours: 8760, warningHours: 720 }, // 1 year, 30-day warning
  ptkpRates: { ttlHours: 8760, warningHours: 720 },
  bpjsRates: { ttlHours: 8760, warningHours: 720 },
  taxRules: { ttlHours: 4380, warningHours: 720 }, // 6 months
};

export async function checkFreshness(table: string, recordId: string): Promise<FreshnessResult>
export async function buildUserMessage(freshness: FreshnessResult): Promise<string>
export async function buildLegionAlert(alerts: FreshnessAlert[]): Promise<string>
export async function getFreshnessRecord(table: string, recordId: string): Promise<FreshnessRecord | null>
```

### 3. Verdict Wrapper (`lib/revalidation/verdict-wrapper.ts`)

```typescript
export async function withFreshnessGate<T>(
  verdictFn: () => Promise<T>,
  context: { table: string; recordId: string; userId: string }
): Promise<{ result: T; freshness: FreshnessResult }>
```

Wraps ALL verdict computations. If data is expired → blocks computation, returns error with freshness info.

### 4. Legion Alert Sender (`lib/legion/alerts.ts`)

```typescript
export async function sendTelegramAlert(message: string, level: 'INFO' | 'WARNING' | 'CRITICAL'): Promise<void>
export async function sendDataFreshnessReport(report: DataFreshnessReport): Promise<void>
```

### 5. Supabase Cron (`supabase/functions/scheduled-freshness-check/`)

Daily edge function at `00:00 UTC` that:
1. Checks all registered tables for stale/expired data
2. Logs to `dataFreshnessLog`
3. Sends deduplicated alerts via `staleDataAlerts`
4. Triggers Telegram message to Legion

### 6. Telegram Commands (Python - Babas_Swarms_bot)

| Command | Purpose |
|---------|---------|
| `/freshness` | Show current data freshness dashboard |
| `/updaterate <type> <value>` | Admin update rate with verification |
| `/ratecheck <type>` | Check specific rate TTL status |

---

## Subtask Breakdown

| # | Subtask | File Path | Type | Priority |
|---|---------|-----------|------|----------|
| 1 | Clone cekwajar repo | `/home/newadmin/slip_cekwajar_id` | Bash | BLOCKING |
| 2 | SQL: Add TTL columns to taxRules | `supabase/migrations/001_add_ttl_to_taxRules.sql` | SQL | P0 |
| 3 | SQL: Create umrRegistry | `supabase/migrations/002_create_umrRegistry.sql` | SQL | P0 |
| 4 | SQL: Create bpjsRates | `supabase/migrations/003_create_bpjsRates.sql` | SQL | P0 |
| 5 | SQL: Create ptkpRates | `supabase/migrations/004_create_ptkpRates.sql` | SQL | P0 |
| 6 | SQL: Create dataFreshnessLog | `supabase/migrations/005_create_dataFreshnessLog.sql` | SQL | P0 |
| 7 | SQL: Create staleDataAlerts | `supabase/migrations/006_create_staleDataAlerts.sql` | SQL | P0 |
| 8 | SQL: Create v_data_freshness view | `supabase/migrations/007_create_v_data_freshness.sql` | SQL | P0 |
| 9 | Core Engine | `lib/revalidation/engine.ts` | TypeScript | P0 |
| 10 | Verdict Wrapper | `lib/revalidation/verdict-wrapper.ts` | TypeScript | P0 |
| 11 | Legion Alert Sender | `lib/legion/alerts.ts` | TypeScript | P1 |
| 12 | Supabase Cron Function | `supabase/functions/scheduled-freshness-check/index.ts` | TypeScript | P1 |
| 13 | Telegram /freshness command | `handlers/freshness.py` | Python | P2 |
| 14 | Telegram /updaterate command | `handlers/updaterate.py` | Python | P2 |
| 15 | Telegram /ratecheck command | `handlers/ratecheck.py` | Python | P2 |
| 16 | Wiki Doctrine | `.wiki/02-cekwajar-tech/REVALIDATION-DOCTRINE.md` | Markdown | P1 |
| 17 | Master Context Update | Append to `.wiki/00-meta/LEGION-MASTER-CONTEXT.md` | Markdown | P2 |

---

## Consequences

### Positive
- All verdict computations are TTL-gated → no stale data leaks
- Legion gets proactive alerts before rates expire
- Audit trail for compliance
- Maintainer accountability via /freshness dashboard

### Risks
- **Breaking change**: All verdict functions must be wrapped
- **Migration complexity**: Existing data needs `ttl_hours` backfill
- **Cron reliability**: Supabase Pro plan required for scheduled functions

### Mitigation
- V1: Soft warnings only, no blocking
- V2: Full enforcement with user-visible freshness badge

---

## References

- Existing: `.wiki/02-cekwajar-tech/ARCHITECTURE.md` (taxRules versioning)
- Related: `.wiki/03-regulatory/` (BPJS, PTKP legal basis)
- Legion: `.wiki/00-meta/LEGION-MASTER-CONTEXT.md`
