-- ══════════════════════════════════════════════════════════════════════════════
-- cekwajar.id — 008_wajar_kabur_tables.sql
-- PPP and international salary tables
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS ppp_reference (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  country_code TEXT NOT NULL,
  country_name TEXT NOT NULL,
  currency_code TEXT NOT NULL,
  currency_symbol TEXT NOT NULL,
  flag_emoji TEXT NOT NULL,
  ppp_factor NUMERIC(10,4),
  ppp_year INTEGER,
  is_free_tier BOOLEAN DEFAULT false,
  display_order INTEGER,
  fetched_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(country_code)
);

CREATE TABLE IF NOT EXISTS col_cities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  country_code TEXT NOT NULL,
  city_name TEXT NOT NULL,
  meal_cheap_idr BIGINT,
  meal_restaurant_idr BIGINT,
  transport_monthly_idr BIGINT,
  rent_1br_center_idr BIGINT,
  rent_1br_outside_idr BIGINT,
  utilities_basic_idr BIGINT,
  data_source TEXT DEFAULT 'numbeo',
  fetched_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS abroad_salary_benchmarks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  country_code TEXT NOT NULL,
  job_title TEXT NOT NULL,
  currency_code TEXT NOT NULL,
  p25 BIGINT,
  p50 BIGINT NOT NULL,
  p75 BIGINT,
  sample_count INTEGER,
  data_source TEXT,
  updated_at TIMESTAMPTZ DEFAULT now()
);
