-- ══════════════════════════════════════════════════════════════════════════════
-- cekwajar.id — 006_wajar_gaji_tables.sql
-- Salary benchmarking tables
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS job_categories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title TEXT NOT NULL UNIQUE,
  title_normalized TEXT NOT NULL,
  industry TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS salary_submissions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_category_id UUID REFERENCES job_categories(id),
  job_title_raw TEXT NOT NULL,
  city TEXT NOT NULL,
  province TEXT NOT NULL,
  gross_salary BIGINT NOT NULL,
  experience_bucket TEXT NOT NULL CHECK (experience_bucket IN ('0-2', '3-5', '6-10', '10+')),
  industry TEXT,
  submission_fingerprint TEXT NOT NULL,
  is_validated BOOLEAN DEFAULT false,
  is_outlier BOOLEAN DEFAULT false,
  submission_date DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS salary_benchmarks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_category_id UUID REFERENCES job_categories(id),
  city TEXT,
  province TEXT NOT NULL,
  experience_bucket TEXT,
  data_source TEXT NOT NULL,
  sample_count INTEGER NOT NULL,
  p25 BIGINT,
  p50 BIGINT NOT NULL,
  p75 BIGINT,
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS umk_2026 (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  province TEXT NOT NULL,
  city TEXT NOT NULL,
  monthly_minimum_idr BIGINT NOT NULL,
  effective_date DATE NOT NULL,
  source_url TEXT,
  UNIQUE(city, effective_date)
);

-- Indexes
CREATE INDEX idx_salary_submissions_fingerprint ON salary_submissions(submission_fingerprint);
CREATE INDEX idx_salary_benchmarks_city_category ON salary_benchmarks(city, job_category_id);
CREATE INDEX idx_job_categories_trgm ON job_categories USING GIN(title gin_trgm_ops);
