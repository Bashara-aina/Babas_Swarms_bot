# Stage 2 — Database Schema, Migrations & Seed Data
**cekwajar.id Vibe Coding Playbook**  
**Estimated time:** 2–3 hours  
**Prerequisites:** Stage 1 complete. Supabase project exists. `supabase link` done.  
**Goal:** All 19 SQL migrations applied, reference data seeded, RLS active on all tables.

---

## What You're Building in This Stage

- 19 numbered SQL migrations in `supabase/migrations/`
- All tables created with correct indexes
- RLS enabled and policies set for every table
- pg_cron jobs registered
- Reference data seeded: TER rates, BPJS rates, PTKP values, UMK 2026 (top 50 cities), COL indices (20 cities)
- TypeScript database types generated from schema
- Supabase client query helpers

---

## New Dependencies This Stage

```bash
# Generate TypeScript types from Supabase schema
pnpm add -D supabase

# Zod for runtime validation
pnpm add zod

# (already installed in Stage 1, but verify)
pnpm add @supabase/supabase-js @supabase/ssr
```

---

## ═══════════════════════════════════════════════
## MASTER PROMPT — SEND THIS TO CLAUDE CODE
## (Stage 2 — Database Full Setup)
## ═══════════════════════════════════════════════

```
===START===
We are building cekwajar.id — Indonesian consumer data intelligence platform.
Stage 1 scaffold is complete (Next.js 15, Supabase configured, all stubs).

YOUR TASK FOR STAGE 2:
Create ALL SQL migrations, seed data, RLS policies, and TypeScript database types.
Every migration goes in supabase/migrations/ as numbered .sql files.

════════════════════════════════════════════════════
MIGRATION FILES TO CREATE:
════════════════════════════════════════════════════

--- supabase/migrations/001_init_extensions.sql ---
Enable these PostgreSQL extensions:
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
  CREATE EXTENSION IF NOT EXISTS "pg_cron";
  CREATE EXTENSION IF NOT EXISTS "pg_trgm";
  CREATE EXTENSION IF NOT EXISTS "pg_net";      -- for HTTP calls from pg_cron
  
--- supabase/migrations/002_user_tables.sql ---
Create user_profiles table:
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE
  email TEXT NOT NULL
  full_name TEXT
  subscription_tier TEXT NOT NULL DEFAULT 'free' CHECK (IN 'free','basic','pro')
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()

Create trigger to auto-update updated_at.
Create trigger handle_new_user() SECURITY DEFINER that inserts into user_profiles 
when new row in auth.users. Function reads NEW.email and NEW.raw_user_meta_data->>'full_name'.

--- supabase/migrations/003_subscription_tables.sql ---
Create subscriptions table:
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE
  plan_type TEXT NOT NULL CHECK (IN 'basic','pro')
  status TEXT NOT NULL DEFAULT 'active' CHECK (IN 'active','expired','cancelled')
  starts_at TIMESTAMPTZ NOT NULL DEFAULT now()
  ends_at TIMESTAMPTZ NOT NULL
  last_payment_order_id TEXT
  created_at TIMESTAMPTZ DEFAULT now()
  UNIQUE(user_id)   ← one subscription per user at a time

Create transactions table:
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  user_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL
  midtrans_order_id TEXT NOT NULL UNIQUE
  plan_type TEXT NOT NULL
  billing_period TEXT NOT NULL CHECK (IN 'monthly','annual')
  gross_amount BIGINT NOT NULL
  status TEXT NOT NULL DEFAULT 'pending'
  fraud_status TEXT
  midtrans_payload JSONB
  is_webhook_processed BOOLEAN NOT NULL DEFAULT false
  webhook_received_at TIMESTAMPTZ
  created_at TIMESTAMPTZ DEFAULT now()

--- supabase/migrations/004_rls_phase1.sql ---
Enable RLS on user_profiles and subscriptions.
Create policies as specified:

user_profiles:
  "users_select_own" FOR SELECT USING (auth.uid() = id)
  "users_update_own" FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id)
  
subscriptions:
  "users_select_own_subscription" FOR SELECT USING (auth.uid() = user_id)
  
transactions:
  Enable RLS.
  "users_select_own_transactions" FOR SELECT USING (auth.uid() = user_id)

--- supabase/migrations/005_wajar_slip_tables.sql ---
Create payslip_audits table (full schema):
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  user_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL
  session_id TEXT
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
  delete_at TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '30 days')
  
  -- inputs
  gross_salary BIGINT NOT NULL
  ptkp_status TEXT NOT NULL
  city TEXT NOT NULL
  month_number INTEGER NOT NULL CHECK (BETWEEN 1 AND 12)
  year INTEGER NOT NULL DEFAULT EXTRACT(YEAR FROM now())::integer
  has_npwp BOOLEAN NOT NULL DEFAULT true
  
  -- reported deductions
  reported_pph21 BIGINT NOT NULL DEFAULT 0
  reported_jht_employee BIGINT NOT NULL DEFAULT 0
  reported_jp_employee BIGINT NOT NULL DEFAULT 0
  reported_jkk BIGINT NOT NULL DEFAULT 0
  reported_jkm BIGINT NOT NULL DEFAULT 0
  reported_kesehatan_employee BIGINT NOT NULL DEFAULT 0
  reported_take_home BIGINT NOT NULL DEFAULT 0
  
  -- OCR metadata
  ocr_source TEXT CHECK (IN 'google_vision','tesseract','manual')
  ocr_confidence NUMERIC(4,3)
  payslip_file_path TEXT
  
  -- calculated results
  calculated_pph21 BIGINT
  calculated_jht BIGINT
  calculated_jp BIGINT
  calculated_kesehatan BIGINT
  city_umk BIGINT
  
  -- violations
  violations JSONB NOT NULL DEFAULT '[]'
  verdict TEXT CHECK (IN 'SESUAI','ADA_PELANGGARAN')
  
  -- access control
  is_paid_result BOOLEAN NOT NULL DEFAULT false
  subscription_tier_at_time TEXT NOT NULL DEFAULT 'free'

Indexes:
  idx_payslip_audits_user_id ON (user_id) WHERE user_id IS NOT NULL
  idx_payslip_audits_delete_at ON (delete_at)
  idx_payslip_audits_session_id ON (session_id) WHERE session_id IS NOT NULL

Create ocr_quota_counter table:
  month_key TEXT PRIMARY KEY  -- 'YYYY-MM'
  count INTEGER DEFAULT 0
  updated_at TIMESTAMPTZ DEFAULT now()

Create increment_ocr_counter() RETURNS INTEGER function:
  Increments count for current month_key (YYYY-MM), returns new count.
  Uses INSERT ... ON CONFLICT DO UPDATE.

--- supabase/migrations/006_wajar_gaji_tables.sql ---
Create job_categories table:
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  title TEXT NOT NULL UNIQUE
  title_normalized TEXT NOT NULL   -- LOWER(TRIM(title))
  industry TEXT
  is_active BOOLEAN DEFAULT true
  created_at TIMESTAMPTZ DEFAULT now()

Create salary_submissions table:
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  job_category_id UUID REFERENCES job_categories(id)
  job_title_raw TEXT NOT NULL     -- as entered by user
  city TEXT NOT NULL
  province TEXT NOT NULL
  gross_salary BIGINT NOT NULL
  experience_bucket TEXT NOT NULL CHECK (IN '0-2','3-5','6-10','10+')
  industry TEXT
  submission_fingerprint TEXT NOT NULL   -- SHA256 hash for dedup
  is_validated BOOLEAN DEFAULT false
  is_outlier BOOLEAN DEFAULT false
  submission_date DATE NOT NULL DEFAULT CURRENT_DATE
  created_at TIMESTAMPTZ DEFAULT now()

Create salary_benchmarks table (aggregated, updated by Python agent):
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  job_category_id UUID REFERENCES job_categories(id)
  city TEXT
  province TEXT NOT NULL
  experience_bucket TEXT
  data_source TEXT NOT NULL   -- 'crowdsource', 'bps_sakernas', 'scraped', 'blended'
  sample_count INTEGER NOT NULL
  p25 BIGINT
  p50 BIGINT NOT NULL
  p75 BIGINT
  updated_at TIMESTAMPTZ DEFAULT now()

Create umk_2026 table:
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  province TEXT NOT NULL
  city TEXT NOT NULL
  monthly_minimum_idr BIGINT NOT NULL
  effective_date DATE NOT NULL
  source_url TEXT
  UNIQUE(city, effective_date)

Indexes:
  idx_salary_submissions_fingerprint ON salary_submissions(submission_fingerprint)
  idx_salary_benchmarks_city_category ON salary_benchmarks(city, job_category_id)
  CREATE INDEX idx_job_categories_trgm ON job_categories USING GIN(title gin_trgm_ops)

--- supabase/migrations/007_wajar_tanah_tables.sql ---
Create property_benchmarks table:
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  province TEXT NOT NULL
  city TEXT NOT NULL
  district TEXT NOT NULL      -- kecamatan
  property_type TEXT NOT NULL CHECK (IN 'RUMAH','TANAH','APARTEMEN','RUKO')
  price_per_sqm BIGINT NOT NULL
  land_area_sqm INTEGER
  source TEXT NOT NULL CHECK (IN '99co','rumah123','olx','user_submission')
  listing_url TEXT
  is_outlier BOOLEAN DEFAULT false
  scraped_at TIMESTAMPTZ DEFAULT now()
  created_at TIMESTAMPTZ DEFAULT now()

Create property_submissions table (user crowdsource):
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  province TEXT NOT NULL
  city TEXT NOT NULL
  district TEXT NOT NULL
  property_type TEXT NOT NULL
  total_price BIGINT NOT NULL
  land_area_sqm INTEGER NOT NULL
  price_per_sqm BIGINT NOT NULL GENERATED ALWAYS AS (total_price / NULLIF(land_area_sqm, 0)) STORED
  submission_fingerprint TEXT
  created_at TIMESTAMPTZ DEFAULT now()

Indexes:
  idx_property_benchmarks_location ON property_benchmarks(province, city, district, property_type)
  idx_property_benchmarks_outlier ON property_benchmarks(is_outlier)

--- supabase/migrations/008_wajar_kabur_tables.sql ---
Create ppp_reference table:
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  country_code TEXT NOT NULL        -- ISO 2-letter
  country_name TEXT NOT NULL
  currency_code TEXT NOT NULL       -- 3-letter
  currency_symbol TEXT NOT NULL
  flag_emoji TEXT NOT NULL
  ppp_factor NUMERIC(10,4)          -- local currency per international dollar
  ppp_year INTEGER
  is_free_tier BOOLEAN DEFAULT false   -- true for top 5 countries
  display_order INTEGER
  fetched_at TIMESTAMPTZ DEFAULT now()
  UNIQUE(country_code)

Create col_cities table:
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  country_code TEXT NOT NULL
  city_name TEXT NOT NULL
  meal_cheap_idr BIGINT
  meal_restaurant_idr BIGINT
  transport_monthly_idr BIGINT
  rent_1br_center_idr BIGINT
  rent_1br_outside_idr BIGINT
  utilities_basic_idr BIGINT
  data_source TEXT DEFAULT 'numbeo'
  fetched_at TIMESTAMPTZ DEFAULT now()

Create abroad_salary_benchmarks table:
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  country_code TEXT NOT NULL
  job_title TEXT NOT NULL
  currency_code TEXT NOT NULL
  p25 BIGINT
  p50 BIGINT NOT NULL
  p75 BIGINT
  sample_count INTEGER
  data_source TEXT
  updated_at TIMESTAMPTZ DEFAULT now()

--- supabase/migrations/009_wajar_hidup_tables.sql ---
Create col_indices table:
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  city_code TEXT NOT NULL UNIQUE     -- 'JKT', 'BDG', etc.
  city_name TEXT NOT NULL
  province TEXT NOT NULL
  col_index NUMERIC(5,1) NOT NULL    -- Jakarta = 100.0
  data_year INTEGER NOT NULL
  data_quarter INTEGER NOT NULL
  source TEXT DEFAULT 'bps_cpi'
  updated_at TIMESTAMPTZ DEFAULT now()

Create col_categories table:
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  category_code TEXT NOT NULL UNIQUE
  label_id TEXT NOT NULL        -- Bahasa Indonesia label
  hemat_weight NUMERIC(4,3) NOT NULL
  standar_weight NUMERIC(4,3) NOT NULL
  nyaman_weight NUMERIC(4,3) NOT NULL

--- supabase/migrations/010_reference_data_tables.sql ---
Create pph21_ter_rates table:
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  category TEXT NOT NULL CHECK (IN 'A','B','C')
  min_salary BIGINT NOT NULL
  max_salary BIGINT NOT NULL
  monthly_rate_percent NUMERIC(5,2) NOT NULL
  effective_from DATE NOT NULL DEFAULT '2024-01-01'

Create bpjs_rates table:
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  component TEXT NOT NULL CHECK (IN 'JHT','JP','JKK','JKM','KESEHATAN')
  party TEXT NOT NULL CHECK (IN 'employee','employer')
  rate_percent NUMERIC(5,3) NOT NULL
  salary_cap_idr BIGINT
  notes TEXT
  effective_from DATE NOT NULL DEFAULT '2015-01-01'

Create ptkp_values table:
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  status_code TEXT NOT NULL UNIQUE
  description TEXT NOT NULL
  annual_value_idr BIGINT NOT NULL
  effective_from DATE NOT NULL

--- supabase/migrations/011_rls_all_tools.sql ---
Enable RLS and create policies for ALL tool tables.

payslip_audits:
  Enable RLS.
  "users_select_own" FOR SELECT USING (auth.uid() = user_id)
  "users_insert_own" FOR INSERT WITH CHECK (auth.uid() = user_id)
  "anon_insert" FOR INSERT WITH CHECK (user_id IS NULL AND session_id IS NOT NULL)
  "anon_select_recent" FOR SELECT USING (user_id IS NULL AND session_id IS NOT NULL AND created_at > now() - INTERVAL '2 hours')

salary_submissions:
  Enable RLS.
  "anyone_insert" FOR INSERT WITH CHECK (true)

salary_benchmarks: Enable RLS. "public_read" FOR SELECT USING (true)
job_categories: Enable RLS. "public_read" FOR SELECT USING (true)
umk_2026: Enable RLS. "public_read" FOR SELECT USING (true)
property_benchmarks: Enable RLS. "public_read" FOR SELECT USING (true)
property_submissions: Enable RLS. "public_insert" FOR INSERT WITH CHECK (true)
ppp_reference: Enable RLS. "public_read" FOR SELECT USING (true)
col_cities: Enable RLS. "public_read" FOR SELECT USING (true)
abroad_salary_benchmarks: Enable RLS. "public_read" FOR SELECT USING (true)
col_indices: Enable RLS. "public_read" FOR SELECT USING (true)
col_categories: Enable RLS. "public_read" FOR SELECT USING (true)
pph21_ter_rates: Enable RLS. "public_read" FOR SELECT USING (true)
bpjs_rates: Enable RLS. "public_read" FOR SELECT USING (true)
ptkp_values: Enable RLS. "public_read" FOR SELECT USING (true)
ocr_quota_counter: Enable RLS. Service role only.

--- supabase/migrations/012_pgcron_jobs.sql ---
Register these cron jobs using cron.schedule():

1. 'purge-payslip-records' — '5 17 * * *':
   UPDATE payslip_audits SET payslip_file_path = NULL WHERE delete_at < now() AND payslip_file_path IS NOT NULL;
   
2. 'purge-anon-audits' — '10 17 * * *':
   DELETE FROM payslip_audits WHERE user_id IS NULL AND created_at < now() - INTERVAL '7 days';
   
3. 'subscription-expiry-check' — '0 18 * * *':
   UPDATE user_profiles up SET subscription_tier = 'free', updated_at = now()
   FROM subscriptions s WHERE s.user_id = up.id AND s.status = 'active' AND s.ends_at < now() - INTERVAL '1 day' AND up.subscription_tier != 'free';
   UPDATE subscriptions SET status = 'expired' WHERE status = 'active' AND ends_at < now() - INTERVAL '1 day';

4. 'cleanup-anon-sessions' — '0 16 * * *':
   DELETE FROM payslip_audits WHERE user_id IS NULL AND created_at < now() - INTERVAL '7 days';

--- supabase/migrations/013_seed_ter_rates.sql ---
INSERT all TER A, TER B, TER C rate brackets from PMK 168/2023.
This is a lot of data. Create the full table for all three categories.

TER A (TK/0, TK/1) key brackets:
(0, 5400000, 0.00), (5400001, 5650000, 0.25), (5650001, 5950000, 0.50),
(5950001, 6300000, 0.75), (6300001, 6750000, 1.00), (6750001, 7500000, 1.25),
(7500001, 8550000, 1.50), (8550001, 9650000, 1.75), (9650001, 10050000, 2.00),
(10050001, 10350000, 2.25), (10350001, 10700000, 2.50), (10700001, 11050000, 3.00),
(11050001, 11600000, 3.50), (11600001, 12500000, 4.00), (12500001, 13750000, 5.00),
(13750001, 15100000, 6.00), (15100001, 16950000, 7.00), (16950001, 19750000, 8.00),
(19750001, 24150000, 9.00), (24150001, 26450000, 10.00), (26450001, 28000000, 11.00),
(28000001, 30050000, 12.00), (30050001, 32400000, 13.00), (32400001, 35400000, 14.00),
(35400001, 39100000, 15.00), (39100001, 43850000, 16.00), (43850001, 47800000, 17.00),
(47800001, 51400000, 18.00), (51400001, 56300000, 19.00), (56300001, 62200000, 20.00),
(62200001, 77700000, 21.00), (77700001, 103600000, 22.00), (103600001, 134000000, 23.00),
(134000001, 167500000, 24.00), (167500001, 999999999, 25.00)

TER B (K/0, K/1, TK/2, TK/3) — shifted thresholds, slightly lower rates:
Start from 0 with first bracket 0.00 up to 6200000, then:
(6200001, 6500000, 0.25), (6500001, 6850000, 0.50), ... continue pattern to 25.00% max

TER C (K/2, K/3) — further shifted, lowest rates:
First zero bracket up to 6600000, then increment similarly.

Use INSERT INTO pph21_ter_rates (category, min_salary, max_salary, monthly_rate_percent) VALUES ...

--- supabase/migrations/014_seed_bpjs_and_ptkp.sql ---
INSERT bpjs_rates:
  ('JHT', 'employee', 2.000, NULL, 'No salary cap for JHT'),
  ('JHT', 'employer', 3.700, NULL, 'No salary cap'),
  ('JP', 'employee', 1.000, 9559600, 'Cap = 7× UMP DKI Jan 2024'),
  ('JP', 'employer', 2.000, 9559600, 'Same cap as employee'),
  ('JKK', 'employer', 0.240, NULL, 'Kelompok I — office/low risk'),
  ('JKK', 'employer', 0.540, NULL, 'Kelompok II — general risk'),
  ('JKK', 'employer', 0.890, NULL, 'Kelompok III — medium risk'),
  ('JKK', 'employer', 1.270, NULL, 'Kelompok IV — manufacturing'),
  ('JKK', 'employer', 1.740, NULL, 'Kelompok V — mining/high risk'),
  ('JKM', 'employer', 0.300, NULL, 'No salary cap'),
  ('KESEHATAN', 'employee', 1.000, 12000000, 'Cap IDR 12,000,000'),
  ('KESEHATAN', 'employer', 4.000, 12000000, 'Same cap')

INSERT ptkp_values:
  ('TK/0', 'Tidak Kawin, 0 tanggungan', 54000000, '2016-01-01'),
  ('TK/1', 'Tidak Kawin, 1 tanggungan', 58500000, '2016-01-01'),
  ('TK/2', 'Tidak Kawin, 2 tanggungan', 63000000, '2016-01-01'),
  ('TK/3', 'Tidak Kawin, 3 tanggungan', 67500000, '2016-01-01'),
  ('K/0', 'Kawin, 0 tanggungan', 58500000, '2016-01-01'),
  ('K/1', 'Kawin, 1 tanggungan', 63000000, '2016-01-01'),
  ('K/2', 'Kawin, 2 tanggungan', 67500000, '2016-01-01'),
  ('K/3', 'Kawin, 3 tanggungan', 72000000, '2016-01-01'),
  ('K/I/0', 'Kawin, Istri Bekerja, 0 tanggungan', 112500000, '2016-01-01'),
  ('K/I/1', 'Kawin, Istri Bekerja, 1 tanggungan', 117000000, '2016-01-01'),
  ('K/I/2', 'Kawin, Istri Bekerja, 2 tanggungan', 121500000, '2016-01-01'),
  ('K/I/3', 'Kawin, Istri Bekerja, 3 tanggungan', 126000000, '2016-01-01')

--- supabase/migrations/015_seed_umk_2026.sql ---
INSERT top 50 Indonesian cities with 2026 UMK values.
Research / use these real 2026 values (use best available data, mark source):

Key cities (use 2025 values + ~7% increment as estimate for 2026 if 2026 not yet official):
('DKI Jakarta', 'Jakarta', 5396761, '2026-01-01'),
('Jawa Barat', 'Kota Bekasi', 5331680, '2026-01-01'),
('Jawa Barat', 'Kota Depok', 4878612, '2026-01-01'),
('Jawa Barat', 'Kota Bogor', 4812637, '2026-01-01'),
('Jawa Barat', 'Kota Bandung', 4482914, '2026-01-01'),
('Banten', 'Kota Tangerang', 4906862, '2026-01-01'),
('Banten', 'Kota Tangerang Selatan', 4756500, '2026-01-01'),
('Jawa Timur', 'Kota Surabaya', 4635295, '2026-01-01'),
('Jawa Timur', 'Kota Malang', 3513275, '2026-01-01'),
('Jawa Tengah', 'Kota Semarang', 3454827, '2026-01-01'),
('DIY', 'Kota Yogyakarta', 2494495, '2026-01-01'),
('Bali', 'Kota Denpasar', 3096000, '2026-01-01'),
('Sumatera Utara', 'Kota Medan', 3778685, '2026-01-01'),
('Kepulauan Riau', 'Kota Batam', 4726700, '2026-01-01'),
('Riau', 'Kota Pekanbaru', 3452737, '2026-01-01'),
-- add 35 more major cities

--- supabase/migrations/016_seed_col_indices.sql ---
INSERT col_indices for 20 cities (Jakarta = 100.0):
('JKT', 'Jakarta', 'DKI Jakarta', 100.0, 2025, 4),
('BKS', 'Bekasi', 'Jawa Barat', 85.2, 2025, 4),
('TGR', 'Tangerang', 'Banten', 87.1, 2025, 4),
('DPK', 'Depok', 'Jawa Barat', 84.3, 2025, 4),
('BOG', 'Bogor', 'Jawa Barat', 73.6, 2025, 4),
('BDG', 'Bandung', 'Jawa Barat', 72.3, 2025, 4),
('SBY', 'Surabaya', 'Jawa Timur', 78.5, 2025, 4),
('MDN', 'Medan', 'Sumatera Utara', 65.4, 2025, 4),
('SMG', 'Semarang', 'Jawa Tengah', 70.1, 2025, 4),
('YGY', 'Yogyakarta', 'DIY', 66.2, 2025, 4),
('MLG', 'Malang', 'Jawa Timur', 64.8, 2025, 4),
('SOL', 'Solo', 'Jawa Tengah', 62.4, 2025, 4),
('MKS', 'Makassar', 'Sulawesi Selatan', 68.2, 2025, 4),
('BTM', 'Batam', 'Kepulauan Riau', 79.6, 2025, 4),
('DPS', 'Denpasar', 'Bali', 83.4, 2025, 4),
('BPN', 'Balikpapan', 'Kalimantan Timur', 76.3, 2025, 4),
('PKB', 'Pekanbaru', 'Riau', 67.3, 2025, 4),
('PNK', 'Pontianak', 'Kalimantan Barat', 63.7, 2025, 4),
('MND', 'Manado', 'Sulawesi Utara', 71.2, 2025, 4),
('PLM', 'Palembang', 'Sumatera Selatan', 61.8, 2025, 4)

INSERT col_categories:
('HOUSING', 'Biaya Tempat Tinggal', 0.300, 0.280, 0.250),
('FOOD', 'Makanan & Makan Luar', 0.350, 0.280, 0.220),
('TRANSPORT', 'Transportasi', 0.120, 0.120, 0.100),
('UTILITIES', 'Listrik, Air, Gas', 0.060, 0.050, 0.040),
('HEALTHCARE', 'Kesehatan', 0.040, 0.040, 0.040),
('EDUCATION', 'Pendidikan', 0.030, 0.050, 0.060),
('ENTERTAINMENT', 'Hiburan & Rekreasi', 0.020, 0.060, 0.100),
('CLOTHING', 'Pakaian', 0.030, 0.040, 0.050),
('PERSONAL_CARE', 'Perawatan Diri', 0.030, 0.040, 0.060),
('SAVINGS', 'Tabungan & Darurat', 0.020, 0.040, 0.080)

--- supabase/migrations/017_seed_ppp_countries.sql ---
INSERT 15 countries into ppp_reference:
('SG', 'Singapore', 'SGD', '$', '🇸🇬', 0.88, 2023, true, 1),
('MY', 'Malaysia', 'MYR', 'RM', '🇲🇾', 1.54, 2023, true, 2),
('AU', 'Australia', 'AUD', 'A$', '🇦🇺', 1.52, 2023, true, 3),
('US', 'United States', 'USD', '$', '🇺🇸', 1.00, 2023, true, 4),
('GB', 'United Kingdom', 'GBP', '£', '🇬🇧', 0.71, 2023, true, 5),
('JP', 'Japan', 'JPY', '¥', '🇯🇵', 100.5, 2023, false, 6),
('KR', 'South Korea', 'KRW', '₩', '🇰🇷', 880.2, 2023, false, 7),
('AE', 'United Arab Emirates', 'AED', 'د.إ', '🇦🇪', 2.35, 2023, false, 8),
('NL', 'Netherlands', 'EUR', '€', '🇳🇱', 0.85, 2023, false, 9),
('DE', 'Germany', 'EUR', '€', '🇩🇪', 0.85, 2023, false, 10),
('CA', 'Canada', 'CAD', 'C$', '🇨🇦', 1.35, 2023, false, 11),
('NZ', 'New Zealand', 'NZD', 'NZ$', '🇳🇿', 1.67, 2023, false, 12),
('HK', 'Hong Kong', 'HKD', 'HK$', '🇭🇰', 6.09, 2023, false, 13),
('ZA', 'South Africa', 'ZAR', 'R', '🇿🇦', 8.55, 2023, false, 14),
('TH', 'Thailand', 'THB', '฿', '🇹🇭', 14.89, 2023, false, 15)

--- supabase/migrations/018_indexes_performance.sql ---
CREATE INDEX idx_payslip_audits_user_created ON payslip_audits(user_id, created_at DESC);
CREATE UNIQUE INDEX idx_transactions_midtrans_order ON transactions(midtrans_order_id);
CREATE INDEX idx_salary_submissions_city_job ON salary_submissions(city, job_category_id, experience_bucket);
CREATE INDEX idx_property_benchmarks_city_type ON property_benchmarks(city, district, property_type, is_outlier);
CREATE INDEX idx_ppp_reference_country ON ppp_reference(country_code);
CREATE INDEX idx_umk_2026_city ON umk_2026(city);
CREATE INDEX idx_col_indices_city_code ON col_indices(city_code);

--- supabase/migrations/019_consent_tables.sql ---
Create user_consents table:
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE
  policy_version TEXT NOT NULL
  privacy_policy_accepted BOOLEAN NOT NULL DEFAULT false
  terms_accepted BOOLEAN NOT NULL DEFAULT false
  marketing_accepted BOOLEAN NOT NULL DEFAULT false
  accepted_at TIMESTAMPTZ NOT NULL DEFAULT now()
  ip_hash TEXT    -- one-way hash of IP for audit trail

Enable RLS:
  "users_select_own" FOR SELECT USING (auth.uid() = user_id)
  "users_insert_own" FOR INSERT WITH CHECK (auth.uid() = user_id)

════════════════════════════════════════════════════
TYPESCRIPT DATABASE TYPES:
════════════════════════════════════════════════════

After all migrations are created, generate TypeScript types:
Run: supabase gen types typescript --linked > src/types/database.types.ts

Then create src/lib/db/queries.ts with these helper functions:

// Get user subscription tier (always from DB, never from client)
export async function getUserTier(userId: string, supabase: SupabaseClient): Promise<SubscriptionTier> {
  const { data } = await supabase
    .from('user_profiles')
    .select('subscription_tier')
    .eq('id', userId)
    .single()
  return (data?.subscription_tier as SubscriptionTier) ?? 'free'
}

// Get UMK for city
export async function getUMKForCity(city: string, supabase: SupabaseClient): Promise<number | null> {
  const { data } = await supabase
    .from('umk_2026')
    .select('monthly_minimum_idr')
    .ilike('city', city)
    .single()
  return data?.monthly_minimum_idr ?? null
}

// Get TER rate for salary + category
export async function getTERRate(grossSalary: number, category: 'A'|'B'|'C', supabase: SupabaseClient): Promise<number> {
  const { data } = await supabase
    .from('pph21_ter_rates')
    .select('monthly_rate_percent')
    .eq('category', category)
    .lte('min_salary', grossSalary)
    .gte('max_salary', grossSalary)
    .single()
  return data?.monthly_rate_percent ?? 0
}

// Get all BPJS rates
export async function getBPJSRates(supabase: SupabaseClient) {
  const { data } = await supabase
    .from('bpjs_rates')
    .select('*')
  return data ?? []
}

// Get PTKP annual value
export async function getPTKPValue(statusCode: string, supabase: SupabaseClient): Promise<number> {
  const { data } = await supabase
    .from('ptkp_values')
    .select('annual_value_idr')
    .eq('status_code', statusCode)
    .single()
  return data?.annual_value_idr ?? 54000000
}

// Increment OCR quota counter, return new count
export async function incrementOCRCounter(supabase: SupabaseClient): Promise<number> {
  const { data } = await supabase.rpc('increment_ocr_counter')
  return data ?? 999
}

════════════════════════════════════════════════════
APPLY MIGRATIONS:
════════════════════════════════════════════════════

After creating all migration files, run:
  supabase db push --linked

Then verify in Supabase Studio (studio.supabase.com or local):
  SELECT COUNT(*) FROM pph21_ter_rates;     -- should be ~105 rows
  SELECT COUNT(*) FROM bpjs_rates;           -- should be 12 rows
  SELECT COUNT(*) FROM ptkp_values;          -- should be 12 rows
  SELECT COUNT(*) FROM umk_2026;             -- should be 50+ rows
  SELECT COUNT(*) FROM col_indices;          -- should be 20 rows
  SELECT COUNT(*) FROM ppp_reference;        -- should be 15 rows
  SELECT * FROM cron.job;                    -- should show 4 cron jobs

Run the health check endpoint:
  curl localhost:3000/api/health
  -- Should now show all tables accessible

ALSO generate TypeScript types:
  supabase gen types typescript --linked > src/types/database.types.ts

Fix any type errors this creates in existing files.
===END===
```

---

## Verification Checklist for Stage 2

```bash
# Check migration count
ls supabase/migrations/ | wc -l
# Expected: 19

# Check DB via Supabase CLI
supabase db diff --linked
# Expected: no pending changes

# Check types generated
ls src/types/database.types.ts
# Expected: file exists, no TS errors

# Check all tables have RLS
psql $SUPABASE_DB_URL -c "
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;"
# Every row should show rowsecurity = true

# Check TER data
psql $SUPABASE_DB_URL -c "SELECT COUNT(*) FROM pph21_ter_rates;"
# Expected: ~105

# Check cron jobs
psql $SUPABASE_DB_URL -c "SELECT jobname FROM cron.job;"
# Expected: 4 jobs listed

# TypeScript still clean
pnpm tsc --noEmit
```

**Next:** Stage 3 — Authentication + User Dashboard
