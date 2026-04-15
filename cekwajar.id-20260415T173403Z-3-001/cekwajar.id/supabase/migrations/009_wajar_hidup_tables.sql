-- ══════════════════════════════════════════════════════════════════════════════
-- cekwajar.id — 009_wajar_hidup_tables.sql
-- Cost of Living indices tables
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS col_indices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  city_code TEXT NOT NULL UNIQUE,
  city_name TEXT NOT NULL,
  province TEXT NOT NULL,
  col_index NUMERIC(5,1) NOT NULL,
  data_year INTEGER NOT NULL,
  data_quarter INTEGER NOT NULL,
  source TEXT DEFAULT 'bps_cpi',
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS col_categories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  category_code TEXT NOT NULL UNIQUE,
  label_id TEXT NOT NULL,
  hemat_weight NUMERIC(4,3) NOT NULL,
  standar_weight NUMERIC(4,3) NOT NULL,
  nyaman_weight NUMERIC(4,3) NOT NULL
);
