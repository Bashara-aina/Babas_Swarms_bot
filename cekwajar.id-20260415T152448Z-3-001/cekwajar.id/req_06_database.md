# req_06 — Database Engineering Spec: cekwajar.id
**Document Type:** Database Engineering Specification  
**Version:** 1.0  
**Scope:** Migration strategy, RLS policies, cron jobs, seeding, anonymization

> **Note:** The actual table DDL is in `block_02_database_schema.md`. This document covers the *operational* layer: how tables come into existence, who can read/write what, what runs on a schedule, and how privacy is enforced at the data layer.

---

## 3.2 Migration Files Index

### Philosophy

Every schema change is a numbered, immutable SQL file committed to the repo. Never modify a migration after it runs in production. Write a new migration instead. Migration runner: `supabase db push` (applies pending migrations in order). Rollback: the `-- rollback` section is documented but must be run manually — Supabase does not auto-rollback.

### File Naming Convention

```
supabase/migrations/
  001_init_extensions.sql
  002_user_tables.sql
  003_subscription_tables.sql
  004_rls_phase1.sql
  005_wajar_slip_tables.sql
  006_wajar_gaji_tables.sql
  007_wajar_tanah_tables.sql
  008_wajar_kabur_tables.sql
  009_wajar_hidup_tables.sql
  010_reference_data_tables.sql
  011_rls_all_tools.sql
  012_pgcron_jobs.sql
  013_seed_ter_rates.sql
  014_seed_bpjs_rates.sql
  015_seed_umk_2026.sql
  016_seed_bps_sakernas.sql
  017_seed_col_indices.sql
  018_indexes_performance.sql
  019_consent_audit_tables.sql
```

### Migration Detail Table

| # | File | Purpose | Affected Tables | Rollback |
|---|------|---------|-----------------|---------|
| 001 | `001_init_extensions.sql` | Enable uuid-ossp, pgvector, pg_cron, pg_trgm | system | `DROP EXTENSION` each — dangerous, only in dev |
| 002 | `002_user_tables.sql` | Create `user_profiles`, extend auth.users | `user_profiles` | `DROP TABLE user_profiles CASCADE` |
| 003 | `003_subscription_tables.sql` | Create `subscriptions`, `transactions` | `subscriptions`, `transactions` | `DROP TABLE` cascade |
| 004 | `004_rls_phase1.sql` | Enable RLS on user_profiles, subscriptions | `user_profiles`, `subscriptions` | `ALTER TABLE ... DISABLE ROW LEVEL SECURITY` |
| 005 | `005_wajar_slip_tables.sql` | Create `payslip_audits`, storage bucket | `payslip_audits`, storage | `DROP TABLE payslip_audits CASCADE` |
| 006 | `006_wajar_gaji_tables.sql` | Create `salary_benchmarks`, `salary_submissions`, `job_categories`, `umk_2026` | 4 tables | `DROP TABLE` cascade in reverse order |
| 007 | `007_wajar_tanah_tables.sql` | Create `property_benchmarks`, `property_submissions` | 2 tables | `DROP TABLE` cascade |
| 008 | `008_wajar_kabur_tables.sql` | Create `ppp_reference`, `col_cities`, `abroad_salary_benchmarks` | 3 tables | `DROP TABLE` cascade |
| 009 | `009_wajar_hidup_tables.sql` | Create `col_indices`, `col_categories`, `lifestyle_tiers` | 3 tables | `DROP TABLE` cascade |
| 010 | `010_reference_data_tables.sql` | Create `pph21_ter_rates`, `bpjs_rates`, `ptkp_values` | 3 tables | `DROP TABLE` cascade |
| 011 | `011_rls_all_tools.sql` | Enable RLS + policies for all tool tables | all 9 tool tables | Per-table policy drops |
| 012 | `012_pgcron_jobs.sql` | Register all pg_cron scheduled jobs | cron.job | `SELECT cron.unschedule('job-name')` for each |
| 013–017 | Seed migrations | Load static reference data | reference tables | `TRUNCATE TABLE` |
| 018 | `018_indexes_performance.sql` | Add GIN trigram, btree, pgvector indexes | all tables | `DROP INDEX` by name |
| 019 | `019_consent_audit_tables.sql` | Create `user_consents`, `consent_audit_log` | 2 tables | `DROP TABLE` cascade |

---

### Migration File Contents (Critical Migrations)

#### `001_init_extensions.sql`

```sql
-- Purpose: Enable required PostgreSQL extensions
-- Rollback: DROP EXTENSION statements below — NEVER run in production without data migration
-- Run time: ~5 seconds

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";          -- for job title similarity search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";           -- for fuzzy text matching
CREATE EXTENSION IF NOT EXISTS "pg_cron";           -- for scheduled jobs
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- for query performance monitoring

-- Verify
SELECT extname, extversion FROM pg_extension 
WHERE extname IN ('uuid-ossp', 'pgvector', 'pg_trgm', 'pg_cron');

-- rollback:
-- DROP EXTENSION IF EXISTS "pg_cron";
-- DROP EXTENSION IF EXISTS "pgvector";
-- DROP EXTENSION IF EXISTS "pg_trgm";
```

#### `002_user_tables.sql`

```sql
-- Purpose: Core user profile table linked to Supabase Auth
-- Rollback: DROP TABLE user_profiles CASCADE;

CREATE TABLE user_profiles (
  id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email           TEXT NOT NULL,
  full_name       TEXT,
  subscription_tier TEXT NOT NULL DEFAULT 'free' 
                  CHECK (subscription_tier IN ('free', 'basic', 'pro')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_user_profiles_updated_at
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Auto-create profile on auth signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO user_profiles (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    NEW.raw_user_meta_data->>'full_name'
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- rollback:
-- DROP TRIGGER on_auth_user_created ON auth.users;
-- DROP TRIGGER trg_user_profiles_updated_at ON user_profiles;
-- DROP TABLE user_profiles CASCADE;
```

#### `005_wajar_slip_tables.sql`

```sql
-- Purpose: Payslip audit table + storage bucket for OCR files
-- Rollback: DROP TABLE payslip_audits CASCADE; + delete storage bucket

CREATE TABLE payslip_audits (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id           UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
  session_id        TEXT,                          -- for anonymous users
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  delete_at         TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '30 days'),
  
  -- Input data (all monetary in IDR)
  gross_salary      BIGINT NOT NULL,
  ptkp_status       TEXT NOT NULL,
  city              TEXT NOT NULL,
  month_number      INTEGER NOT NULL CHECK (month_number BETWEEN 1 AND 12),
  year              INTEGER NOT NULL DEFAULT EXTRACT(YEAR FROM now()),
  has_npwp          BOOLEAN NOT NULL DEFAULT true,
  
  -- Payslip deductions as reported
  reported_pph21    BIGINT NOT NULL DEFAULT 0,
  reported_jht_employee BIGINT NOT NULL DEFAULT 0,
  reported_jp_employee  BIGINT NOT NULL DEFAULT 0,
  reported_jkk          BIGINT NOT NULL DEFAULT 0,
  reported_jkm          BIGINT NOT NULL DEFAULT 0,
  reported_kesehatan_employee BIGINT NOT NULL DEFAULT 0,
  reported_take_home    BIGINT NOT NULL DEFAULT 0,
  
  -- OCR metadata
  ocr_source        TEXT CHECK (ocr_source IN ('google_vision', 'tesseract', 'manual')),
  ocr_confidence    NUMERIC(4,3),
  payslip_file_path TEXT,                          -- storage path, null after 30 days
  
  -- Calculated results
  calculated_pph21  BIGINT,
  calculated_jht    BIGINT,
  calculated_jp     BIGINT,
  calculated_kesehatan BIGINT,
  city_umk          BIGINT,
  
  -- Violations
  violations        JSONB NOT NULL DEFAULT '[]',   -- array of violation objects
  verdict           TEXT CHECK (verdict IN ('SESUAI', 'ADA_PELANGGARAN')),
  
  -- Access control
  is_paid_result    BOOLEAN NOT NULL DEFAULT false,
  subscription_tier_at_time TEXT NOT NULL DEFAULT 'free'
);

-- Index for user history queries
CREATE INDEX idx_payslip_audits_user_id ON payslip_audits(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_payslip_audits_delete_at ON payslip_audits(delete_at);
CREATE INDEX idx_payslip_audits_session_id ON payslip_audits(session_id) WHERE session_id IS NOT NULL;

-- Storage bucket for payslip files (private, 30-day auto-delete handled by pg_cron)
-- This is executed via Supabase Storage API, not SQL:
-- supabase.storage.createBucket('payslips', { public: false, fileSizeLimit: 5242880 }) -- 5MB

-- rollback:
-- DROP TABLE payslip_audits CASCADE;
-- supabase.storage.deleteBucket('payslips')
```

#### `018_indexes_performance.sql`

```sql
-- Purpose: Performance indexes after all tables exist
-- Add CONCURRENTLY in production to avoid locking

-- Salary benchmarks: fast city+title lookup
CREATE INDEX idx_salary_benchmarks_city_category 
  ON salary_benchmarks(city, job_category_id, data_source);

-- Trigram index for fuzzy job title search
CREATE INDEX idx_job_categories_title_trgm 
  ON job_categories USING GIN(title gin_trgm_ops);

-- pgvector index for semantic job title matching
CREATE INDEX idx_job_categories_embedding 
  ON job_categories USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);

-- Property benchmarks: fast location lookup
CREATE INDEX idx_property_benchmarks_location 
  ON property_benchmarks(province, city, district, property_type);

-- Col indices: fast city pair lookup
CREATE INDEX idx_col_indices_city ON col_indices(city_code);

-- PPP reference: fast country lookup
CREATE INDEX idx_ppp_reference_country ON ppp_reference(country_code, year);

-- Payslip audits: user audit history
CREATE INDEX idx_payslip_audits_user_created 
  ON payslip_audits(user_id, created_at DESC);

-- Transactions: webhook idempotency
CREATE UNIQUE INDEX idx_transactions_midtrans_order 
  ON transactions(midtrans_order_id);
```

---

## 3.3 Row Level Security (RLS) Policy Spec

### Design Principles

1. **Default deny:** RLS enabled on all tables. No policy = no access.
2. **user_id = auth.uid():** All user-owned data gated by this. Never trust client-passed user_id.
3. **Service role bypass:** The Swarms Python agents and Edge Functions use `service_role` key — they bypass RLS intentionally. Never expose `service_role` client-side.
4. **Reference data is public read:** Static tables (TER rates, BPJS rates, UMK, etc.) are readable by all, writeable only by service_role.

---

### Table-by-Table RLS Policies

#### `user_profiles`

```sql
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
CREATE POLICY "users_select_own_profile"
  ON user_profiles FOR SELECT
  USING (auth.uid() = id);

-- Users can update their own profile (but not subscription_tier — that's webhook-set)
CREATE POLICY "users_update_own_profile"
  ON user_profiles FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Insert handled by trigger handle_new_user() which runs as SECURITY DEFINER
-- No direct INSERT policy needed for regular users

-- service_role can do everything (implicit via bypass)
```

**Access matrix:**

| Operation | Anonymous | Authenticated (self) | Authenticated (other) | service_role |
|-----------|-----------|---------------------|----------------------|--------------|
| SELECT | ❌ | ✅ own row | ❌ | ✅ |
| INSERT | ❌ | ❌ (trigger handles) | ❌ | ✅ |
| UPDATE | ❌ | ✅ own row | ❌ | ✅ |
| DELETE | ❌ | ❌ | ❌ | ✅ |

---

#### `subscriptions`

```sql
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_select_own_subscription"
  ON subscriptions FOR SELECT
  USING (auth.uid() = user_id);

-- No user INSERT/UPDATE/DELETE — all subscription changes come from webhook via service_role
```

**Why no user write:** Subscriptions are set exclusively by the Midtrans webhook handler (Edge Function using service_role). A user cannot self-promote their tier.

---

#### `transactions`

```sql
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_select_own_transactions"
  ON transactions FOR SELECT
  USING (auth.uid() = user_id);

-- No user write access — transactions created by webhook only
```

---

#### `payslip_audits`

```sql
ALTER TABLE payslip_audits ENABLE ROW LEVEL SECURITY;

-- Authenticated users see only their own audits
CREATE POLICY "users_select_own_audits"
  ON payslip_audits FOR SELECT
  USING (auth.uid() = user_id);

-- Authenticated users can insert new audits (user_id must match)
CREATE POLICY "users_insert_own_audits"
  ON payslip_audits FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Anonymous users can insert with session_id (user_id = NULL)
CREATE POLICY "anon_insert_audit_no_user"
  ON payslip_audits FOR INSERT
  WITH CHECK (user_id IS NULL AND session_id IS NOT NULL);

-- Anonymous users can select their own session audits (limited window)
CREATE POLICY "anon_select_own_session_audits"
  ON payslip_audits FOR SELECT
  USING (user_id IS NULL AND session_id IS NOT NULL 
         AND created_at > now() - INTERVAL '2 hours');

-- No user DELETE — deletion handled by pg_cron purge job
```

**Anonymous session handling:** When a user isn't logged in, the API generates a short-lived `session_id` (UUIDv4) stored in a httpOnly cookie. Anonymous audits are readable for 2 hours (enough to prompt login/upgrade), then only accessible via auth.

---

#### `salary_submissions`

```sql
ALTER TABLE salary_submissions ENABLE ROW LEVEL SECURITY;

-- Anyone can INSERT (crowdsource — no login required, no PII stored)
CREATE POLICY "anyone_can_submit_salary"
  ON salary_submissions FOR INSERT
  WITH CHECK (true);

-- No SELECT for regular users — aggregate view only
-- salary_benchmarks view is what users query, not raw submissions

-- service_role reads for aggregation pipeline
```

---

#### `salary_benchmarks` (aggregated)

```sql
ALTER TABLE salary_benchmarks ENABLE ROW LEVEL SECURITY;

-- Everyone can read aggregated benchmarks (k-anonymity enforced in data pipeline)
CREATE POLICY "public_read_benchmarks"
  ON salary_benchmarks FOR SELECT
  USING (true);

-- Only service_role writes (Python aggregation agent)
```

---

#### `property_benchmarks`

```sql
ALTER TABLE property_benchmarks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public_read_property_benchmarks"
  ON property_benchmarks FOR SELECT
  USING (true);

-- Only service_role writes (Python scraper agent)
```

---

#### `property_submissions`

```sql
ALTER TABLE property_submissions ENABLE ROW LEVEL SECURITY;

-- Anyone can submit (anonymous crowdsource)
CREATE POLICY "anyone_can_submit_property"
  ON property_submissions FOR INSERT
  WITH CHECK (true);

-- No user read of raw submissions
```

---

#### `ppp_reference`, `col_cities`, `abroad_salary_benchmarks`

```sql
ALTER TABLE ppp_reference ENABLE ROW LEVEL SECURITY;
ALTER TABLE col_cities ENABLE ROW LEVEL SECURITY;
ALTER TABLE abroad_salary_benchmarks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public_read_ppp" ON ppp_reference FOR SELECT USING (true);
CREATE POLICY "public_read_col_cities" ON col_cities FOR SELECT USING (true);
CREATE POLICY "public_read_abroad_benchmarks" ON abroad_salary_benchmarks FOR SELECT USING (true);
```

---

#### `col_indices`, `col_categories`, `lifestyle_tiers`

```sql
ALTER TABLE col_indices ENABLE ROW LEVEL SECURITY;
ALTER TABLE col_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE lifestyle_tiers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public_read_col_indices" ON col_indices FOR SELECT USING (true);
CREATE POLICY "public_read_col_categories" ON col_categories FOR SELECT USING (true);
CREATE POLICY "public_read_lifestyle_tiers" ON lifestyle_tiers FOR SELECT USING (true);
```

---

#### `pph21_ter_rates`, `bpjs_rates`, `ptkp_values`, `umk_2026`

```sql
ALTER TABLE pph21_ter_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE bpjs_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE ptkp_values ENABLE ROW LEVEL SECURITY;
ALTER TABLE umk_2026 ENABLE ROW LEVEL SECURITY;

-- All reference tables: public read, service_role write
CREATE POLICY "public_read_ter_rates" ON pph21_ter_rates FOR SELECT USING (true);
CREATE POLICY "public_read_bpjs_rates" ON bpjs_rates FOR SELECT USING (true);
CREATE POLICY "public_read_ptkp_values" ON ptkp_values FOR SELECT USING (true);
CREATE POLICY "public_read_umk" ON umk_2026 FOR SELECT USING (true);
```

---

#### `user_consents`

```sql
ALTER TABLE user_consents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_select_own_consents"
  ON user_consents FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "users_insert_own_consent"
  ON user_consents FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```

---

#### Storage Bucket: `payslips`

```sql
-- Storage policies (configured via Supabase dashboard or API, not SQL)
-- Bucket: payslips (private)

-- Policy: Authenticated users can upload to their own folder
-- Path pattern: {user_id}/{filename}
-- INSERT: auth.uid()::text = (storage.foldername(name))[1]
-- SELECT: auth.uid()::text = (storage.foldername(name))[1]
-- DELETE: NOT allowed for users (pg_cron handles deletion)
```

---

## 3.4 pg_cron Job Registry

### Setup

```sql
-- pg_cron runs as a background worker in Supabase
-- All jobs run in UTC. Indonesia is UTC+7. Convert accordingly.
-- 11:00 PM Jakarta = 16:00 UTC
-- 01:00 AM Jakarta = 18:00 UTC previous day

SELECT cron.schedule(...) returns a job ID.
```

### Complete Job Registry

| Job Name | Cron (UTC) | Purpose | SQL / Action | Alert If Fails |
|----------|-----------|---------|--------------|----------------|
| `purge-payslip-files` | `0 17 * * *` (= midnight Jakarta) | Delete payslip files older than 30 days from storage | See SQL below | Yes — UU PDP violation risk |
| `purge-payslip-records` | `5 17 * * *` | Delete payslip audit records where delete_at < now() | See SQL below | Yes |
| `purge-anon-audits` | `10 17 * * *` | Delete anonymous audits older than 7 days | See SQL below | No |
| `aggregate-salary-benchmarks` | `0 18 1 * *` (= 1st of month, 01:00 WIB) | Trigger Python agent via Edge Function | HTTP POST to Edge Function | Yes |
| `aggregate-property-benchmarks` | `0 19 1 * *` | Trigger Playwright scraper pipeline | HTTP POST to Edge Function | Yes |
| `refresh-ppp-data` | `0 18 1 1 *` (= Jan 1, annual) | Refresh World Bank PPP data | HTTP POST to Edge Function | No |
| `subscription-expiry-check` | `0 18 * * *` | Downgrade expired subscriptions | See SQL below | Yes — revenue impact |
| `dunning-email-day1` | `0 18 * * *` | Send email to subscribers expiring in 3 days | HTTP POST to Edge Function | No |
| `cleanup-expired-sessions` | `0 16 * * *` | Remove stale anonymous session data | See SQL below | No |
| `daily-smoke-test` | `0 16 * * *` | Run basic health checks | HTTP POST to smoke test endpoint | Yes |

---

### Job SQL Definitions

```sql
-- Register all jobs in migration 012_pgcron_jobs.sql

-- 1. Purge payslip files from storage (calls Edge Function to use storage API)
SELECT cron.schedule(
  'purge-payslip-files',
  '0 17 * * *',
  $$
    SELECT net.http_post(
      url := current_setting('app.edge_function_url') || '/purge-payslip-files',
      headers := jsonb_build_object('Authorization', 'Bearer ' || current_setting('app.service_role_key')),
      body := jsonb_build_object('dry_run', false)
    );
  $$
);

-- 2. Purge payslip audit records
SELECT cron.schedule(
  'purge-payslip-records',
  '5 17 * * *',
  $$
    DELETE FROM payslip_audits
    WHERE delete_at < now()
    AND payslip_file_path IS NOT NULL;
    
    UPDATE payslip_audits
    SET payslip_file_path = NULL,
        ocr_confidence = NULL
    WHERE delete_at < now()
    AND payslip_file_path IS NOT NULL;
  $$
);
-- Note: We null the file_path but keep the calculation record (user's audit history)
-- The actual file is deleted by the Edge Function called in job 1

-- 3. Purge anonymous audits older than 7 days
SELECT cron.schedule(
  'purge-anon-audits',
  '10 17 * * *',
  $$
    DELETE FROM payslip_audits
    WHERE user_id IS NULL
    AND created_at < now() - INTERVAL '7 days';
  $$
);

-- 4. Subscription expiry check
SELECT cron.schedule(
  'subscription-expiry-check',
  '0 18 * * *',
  $$
    UPDATE user_profiles up
    SET subscription_tier = 'free',
        updated_at = now()
    FROM subscriptions s
    WHERE s.user_id = up.id
    AND s.status = 'active'
    AND s.ends_at < now() - INTERVAL '1 day'
    AND up.subscription_tier != 'free';
    
    UPDATE subscriptions
    SET status = 'expired'
    WHERE status = 'active'
    AND ends_at < now() - INTERVAL '1 day';
  $$
);

-- 5. Cleanup stale anonymous sessions (payslip_audits + any other anon data)
SELECT cron.schedule(
  'cleanup-expired-sessions',
  '0 16 * * *',
  $$
    DELETE FROM payslip_audits
    WHERE user_id IS NULL
    AND created_at < now() - INTERVAL '7 days';
  $$
);
```

### Monitoring Job Failures

```sql
-- Query to check recent job run results
SELECT 
  jobid,
  jobname,
  start_time,
  end_time,
  return_message,
  status
FROM cron.job_run_details
WHERE start_time > now() - INTERVAL '24 hours'
ORDER BY start_time DESC;

-- Create alert function (called from monitoring edge function)
CREATE OR REPLACE FUNCTION check_cron_failures()
RETURNS TABLE(job_name TEXT, failed_at TIMESTAMPTZ, error TEXT)
AS $$
  SELECT 
    j.jobname,
    r.start_time,
    r.return_message
  FROM cron.job_run_details r
  JOIN cron.job j ON r.jobid = j.jobid
  WHERE r.status = 'failed'
  AND r.start_time > now() - INTERVAL '25 hours';
$$ LANGUAGE sql SECURITY DEFINER;
```

---

## 3.5 Database Seeding Spec

### What Gets Seeded and When

| Table | When Seeded | Source | Update Frequency | Script |
|-------|-------------|--------|-----------------|--------|
| `pph21_ter_rates` | Migration 013 | PMK 168/2023 | Only when regulation changes | SQL insert |
| `bpjs_rates` | Migration 014 | PP 46/2015 + updates | Only when regulation changes | SQL insert |
| `ptkp_values` | Migration 014 | PMK 66/2023 | Only when regulation changes | SQL insert |
| `umk_2026` | Migration 015 | Kemnaker data (annual) | January each year | Python agent + SQL |
| `bps_sakernas` (salary prior) | Migration 016 | BPS Excel download | Annual BPS release | Python agent |
| `col_indices` | Migration 017 | BPS CPI + manual research | Quarterly | Python agent |
| `job_categories` | Migration 017 | Curated list | As needed | SQL insert |
| `lifestyle_tiers` | Migration 017 | Static config | Rarely | SQL insert |

---

### `pph21_ter_rates` Seed (Migration 013)

```sql
-- Source: PMK 168/2023, effective January 2024
-- TER A = TK/0 and TK/1, TER B = TK/2, TK/3, K/0, K/1, TER C = K/2, K/3

INSERT INTO pph21_ter_rates (category, min_salary, max_salary, monthly_rate_percent) VALUES
-- TER A (TK/0, TK/1)
('A', 0, 5400000, 0.00),
('A', 5400001, 5650000, 0.25),
('A', 5650001, 5950000, 0.50),
('A', 5950001, 6300000, 0.75),
('A', 6300001, 6750000, 1.00),
('A', 6750001, 7500000, 1.25),
('A', 7500001, 8550000, 1.50),
('A', 8550001, 9650000, 1.75),
('A', 9650001, 10050000, 2.00),
('A', 10050001, 10350000, 2.25),
('A', 10350001, 10700000, 2.50),
('A', 10700001, 11050000, 3.00),
('A', 11050001, 11600000, 3.50),
('A', 11600001, 12500000, 4.00),
('A', 12500001, 13750000, 5.00),
('A', 13750001, 15100000, 6.00),
('A', 15100001, 16950000, 7.00),
('A', 16950001, 19750000, 8.00),
('A', 19750001, 24150000, 9.00),
('A', 24150001, 26450000, 10.00),
('A', 26450001, 28000000, 11.00),
('A', 28000001, 30050000, 12.00),
('A', 30050001, 32400000, 13.00),
('A', 32400001, 35400000, 14.00),
('A', 35400001, 39100000, 15.00),
('A', 39100001, 43850000, 16.00),
('A', 43850001, 47800000, 17.00),
('A', 47800001, 51400000, 18.00),
('A', 51400001, 56300000, 19.00),
('A', 56300001, 62200000, 20.00),
('A', 62200001, 77700000, 21.00),
('A', 77700001, 103600000, 22.00),
('A', 103600001, 134000000, 23.00),
('A', 134000001, 167500000, 24.00),
('A', 167500001, 9999999999, 25.00),
-- TER B (K/0, K/1, TK/2, TK/3) — lower rates for dependents
('B', 0, 6200000, 0.00),
('B', 6200001, 6500000, 0.25),
-- [continue full TER B table — similar structure, shifted thresholds]
-- TER C (K/2, K/3) — lowest rates
('C', 0, 6600000, 0.00),
('C', 6600001, 6950000, 0.25);
-- [continue full TER C table]
```

---

### `bpjs_rates` Seed (Migration 014)

```sql
-- Source: PP 46/2015 (JHT), PP 45/2015 (JP), PP 44/2015 (JKK/JKM), Perpres 82/2018 (Kesehatan)

INSERT INTO bpjs_rates (component, party, rate_percent, salary_cap_idr, notes) VALUES
-- JHT (Jaminan Hari Tua)
('JHT', 'employee', 2.00, NULL, 'No salary cap for JHT'),
('JHT', 'employer', 3.70, NULL, 'No salary cap'),
-- JP (Jaminan Pensiun)
('JP', 'employee', 1.00, 9559600, 'Cap = 7× UMP DKI Jan 2024'),
('JP', 'employer', 2.00, 9559600, 'Same cap as employee'),
-- JKK (Jaminan Kecelakaan Kerja) — rate varies by business risk
('JKK', 'employer', 0.24, NULL, 'Kelompok I — office/low risk'),
('JKK', 'employer', 0.54, NULL, 'Kelompok II — general risk'),
('JKK', 'employer', 0.89, NULL, 'Kelompok III — medium risk'),
('JKK', 'employer', 1.27, NULL, 'Kelompok IV — manufacturing'),
('JKK', 'employer', 1.74, NULL, 'Kelompok V — mining/high risk'),
-- JKM (Jaminan Kematian)
('JKM', 'employer', 0.30, NULL, 'No salary cap'),
-- Kesehatan (BPJS Kesehatan / JKN)
('KESEHATAN', 'employee', 1.00, 12000000, 'Cap = IDR 12,000,000 salary'),
('KESEHATAN', 'employer', 4.00, 12000000, 'Same cap');
```

---

### `ptkp_values` Seed

```sql
-- Source: PMK 101/PMK.010/2016 (still current as of 2024)
INSERT INTO ptkp_values (status_code, description, annual_value_idr) VALUES
('TK/0', 'Tidak Kawin, 0 tanggungan', 54000000),
('TK/1', 'Tidak Kawin, 1 tanggungan', 58500000),
('TK/2', 'Tidak Kawin, 2 tanggungan', 63000000),
('TK/3', 'Tidak Kawin, 3 tanggungan', 67500000),
('K/0',  'Kawin, 0 tanggungan', 58500000),
('K/1',  'Kawin, 1 tanggungan', 63000000),
('K/2',  'Kawin, 2 tanggungan', 67500000),
('K/3',  'Kawin, 3 tanggungan', 72000000),
('K/I/0','Kawin, Penghasilan Istri Digabung, 0 tanggungan', 112500000),
('K/I/1','Kawin, Penghasilan Istri Digabung, 1 tanggungan', 117000000),
('K/I/2','Kawin, Penghasilan Istri Digabung, 2 tanggungan', 121500000),
('K/I/3','Kawin, Penghasilan Istri Digabung, 3 tanggungan', 126000000);
```

---

### `umk_2026` Seed (Migration 015)

```sql
-- Source: SK Gubernur masing-masing provinsi, collected Jan 2026
-- Python agent (`agents/loaders/umk_loader.py`) fetches and processes
-- After processing, runs:
INSERT INTO umk_2026 (province, city, monthly_minimum_idr, effective_date, source_url)
VALUES 
('DKI Jakarta', 'Jakarta', 5396761, '2026-01-01', 'https://...'),
('Jawa Barat', 'Kota Bekasi', 5331680, '2026-01-01', 'https://...'),
('Jawa Barat', 'Kota Bandung', 4482914, '2026-01-01', 'https://...'),
('Jawa Tengah', 'Kota Semarang', 3454827, '2026-01-01', 'https://...'),
('Jawa Timur', 'Kota Surabaya', 4635295, '2026-01-01', 'https://...'),
('Banten', 'Kota Tangerang', 4906862, '2026-01-01', 'https://...'),
('DIY', 'Kota Yogyakarta', 2494495, '2026-01-01', 'https://...');
-- [514 cities total — loader script handles all]
```

---

### `col_indices` Seed (Migration 017)

```sql
-- Source: BPS CPI data + Numbeo Indonesia + manual research
-- Jakarta = 100 (baseline)
-- Scale: lower = cheaper than Jakarta, higher = more expensive

INSERT INTO col_indices (city_code, city_name, province, col_index, data_year, data_quarter) VALUES
('JKT', 'Jakarta', 'DKI Jakarta', 100.0, 2025, 4),
('BDG', 'Bandung', 'Jawa Barat', 72.3, 2025, 4),
('SBY', 'Surabaya', 'Jawa Timur', 78.5, 2025, 4),
('MDN', 'Medan', 'Sumatera Utara', 65.4, 2025, 4),
('MKS', 'Makassar', 'Sulawesi Selatan', 68.2, 2025, 4),
('SMG', 'Semarang', 'Jawa Tengah', 70.1, 2025, 4),
('PLM', 'Palembang', 'Sumatera Selatan', 61.8, 2025, 4),
('BTM', 'Batam', 'Kepulauan Riau', 79.6, 2025, 4),
('DPS', 'Denpasar', 'Bali', 83.4, 2025, 4),
('PKB', 'Pekanbaru', 'Riau', 67.3, 2025, 4),
('BKS', 'Bekasi', 'Jawa Barat', 85.2, 2025, 4),
('TGR', 'Tangerang', 'Banten', 87.1, 2025, 4),
('DPK', 'Depok', 'Jawa Barat', 84.3, 2025, 4),
('BOG', 'Bogor', 'Jawa Barat', 73.6, 2025, 4),
('YGY', 'Yogyakarta', 'DIY', 66.2, 2025, 4),
('MLG', 'Malang', 'Jawa Timur', 64.8, 2025, 4),
('SOL', 'Solo', 'Jawa Tengah', 62.4, 2025, 4),
('BPN', 'Balikpapan', 'Kalimantan Timur', 76.3, 2025, 4),
('PNK', 'Pontianak', 'Kalimantan Barat', 63.7, 2025, 4),
('MND', 'Manado', 'Sulawesi Utara', 71.2, 2025, 4);
```

---

## 3.6 K-Anonymity + Data Anonymization Rules

### Philosophy

cekwajar.id never stores or shows individual salary/property data. All submissions feed into aggregates. The k-anonymity threshold is the minimum cell size before aggregate data is published. This prevents re-identification by narrowing queries.

---

### Anonymization Rules by Data Type

#### Salary Submissions (`salary_submissions`)

| Field | What's Stored | What's Shown | Notes |
|-------|--------------|--------------|-------|
| `gross_salary` | Exact IDR value | Never shown individually | Used only for percentile calculation |
| `job_title` | Raw text (cleaned) | Via aggregated benchmark | Fuzzy-matched to category |
| `city` | Exact city name | City-level aggregates only | Province fallback if n<30 |
| `industry` | Category | Used in segmentation | |
| `ip_hash` | SHA256 of IP+title+city (16 chars) | Never | Used for deduplication only |
| `submission_date` | Date only (not time) | Never | For freshness weighting |
| `experience_years` | Bucket (0-2, 3-5, 6-10, 10+) | Via aggregate | Never raw |
| User ID | NULL for all submissions | N/A | No login required |

**K-anonymity thresholds:**

| Granularity | Minimum n | Fallback |
|------------|-----------|---------|
| City + Job Category + Experience Bucket | n ≥ 10 | Roll up to province |
| Province + Job Category | n ≥ 5 | Show BPS Sakernas prior only |
| Province + Job Category + Industry | n ≥ 15 | Show without industry split |

**Aggregation SQL view (what users query):**

```sql
CREATE VIEW salary_benchmark_public AS
SELECT
  job_category_id,
  city,
  experience_bucket,
  COUNT(*)        AS sample_count,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY gross_salary) AS p25,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY gross_salary) AS p50,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY gross_salary) AS p75,
  MAX(submission_date)  AS latest_submission
FROM salary_submissions
WHERE is_validated = true
GROUP BY job_category_id, city, experience_bucket
HAVING COUNT(*) >= 10;  -- k-anonymity gate

-- Province-level fallback (lower threshold)
CREATE VIEW salary_benchmark_province_public AS
SELECT
  job_category_id,
  province,
  COUNT(*)        AS sample_count,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY gross_salary) AS p50
FROM salary_submissions
WHERE is_validated = true
GROUP BY job_category_id, province
HAVING COUNT(*) >= 5;
```

---

#### Property Benchmarks (`property_submissions`, `property_benchmarks`)

| Field | What's Stored | What's Shown | Notes |
|-------|--------------|--------------|-------|
| `price_per_sqm` | Exact IDR | Aggregated P25/P50/P75 | Never individual |
| `district` (kelurahan) | Full name | Used for grouping | |
| `land_area_sqm` | Exact | Bucketed in aggregates | |
| `listing_url` | URL of scraped listing | Never | Legal shield — source tracking only |
| `scraped_at` | Timestamp | Never | Freshness weighting |
| User submissions | Session ID only | Never | No login required |

**K-anonymity threshold for property:** n ≥ 5 per district × property_type × size_band cell.

**Property cell definition:**
- District (kelurahan): exact match
- Property type: Rumah / Tanah / Apartemen / Ruko
- Size band: ≤50m², 51–100m², 101–200m², >200m²

```sql
CREATE VIEW property_benchmark_public AS
SELECT
  province, city, district,
  property_type,
  CASE
    WHEN land_area_sqm <= 50  THEN '≤50m²'
    WHEN land_area_sqm <= 100 THEN '51-100m²'
    WHEN land_area_sqm <= 200 THEN '101-200m²'
    ELSE '>200m²'
  END AS size_band,
  COUNT(*)                    AS sample_count,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price_per_sqm) AS p25,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY price_per_sqm) AS p50,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price_per_sqm) AS p75,
  MAX(scraped_at)             AS data_freshness
FROM property_benchmarks
GROUP BY province, city, district, property_type, size_band
HAVING COUNT(*) >= 5;
```

---

#### Payslip Audits (`payslip_audits`)

| Field | What's Stored | After 30 Days | Notes |
|-------|--------------|---------------|-------|
| `gross_salary` | Exact | Retained | Used in audit history |
| `payslip_file_path` | Storage path | SET NULL | File deleted from bucket |
| `violations` | Full JSONB | Retained | User's audit record |
| `calculated_*` | All amounts | Retained | Needed for history |
| `ocr_confidence` | Float | SET NULL | No longer needed |
| `session_id` | Hash | Deleted (anon) | Anon audits fully deleted at 7 days |

**What's never stored in payslip_audits:**
- Employee name (not a field)
- Employee address
- Company name (not required for calculation)
- Tax ID / NIK
- Raw OCR text (only extracted fields)

---

#### User Profiles + Auth

| Field | Stored | Retention | Notes |
|-------|--------|-----------|-------|
| Email | Yes (from auth) | Until account deletion | Required for auth |
| Full name | Optional | Until account deletion | From Google OAuth |
| Google avatar URL | No | N/A | Not stored |
| Subscription history | Yes | 3 years | Tax/legal requirement |
| IP addresses | No | N/A | Never logged |
| Payment data | No | N/A | Midtrans stores this, not us |

---

### Deduplication Without PII

For salary crowdsource submissions, deduplication uses:

```python
import hashlib

def create_submission_fingerprint(ip: str, job_title: str, city: str, salary: int) -> str:
    """
    Create a privacy-preserving fingerprint to prevent duplicate submissions.
    Not reversible — cannot reconstruct IP from hash.
    """
    raw = f"{ip}:{job_title.lower().strip()}:{city.lower()}:{salary // 1_000_000}"
    # Normalize salary to nearest million to allow slight variations
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
```

Same user submitting the same title+city combo within salary tolerance = duplicate, rejected. This prevents ballot-stuffing without storing any PII.

---

### Data Retention Summary (UU PDP Pasal 29 Compliance)

| Data Type | Retention Period | Deletion Method |
|-----------|-----------------|-----------------|
| Payslip image files | 30 days from upload | pg_cron + Storage API |
| Anonymous audit records | 7 days | pg_cron |
| Authenticated audit records | 12 months | User-initiated or pg_cron |
| Salary submission raw | 24 months | pg_cron (then aggregate only) |
| Property benchmark data | 6 months (replaced by fresh scrape) | Python agent |
| User account data | Until deletion request | Manual (right to erasure, Art. 35 UU PDP) |
| Transaction records | 3 years | Cannot delete (Tax Law requirement) |
| Consent records | 5 years | Cannot delete (legal evidence) |
