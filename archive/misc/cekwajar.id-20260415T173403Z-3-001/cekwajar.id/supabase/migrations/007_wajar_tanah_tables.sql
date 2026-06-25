-- ══════════════════════════════════════════════════════════════════════════════
-- cekwajar.id — 007_wajar_tanah_tables.sql
-- Property benchmarking tables
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS property_benchmarks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  province TEXT NOT NULL,
  city TEXT NOT NULL,
  district TEXT NOT NULL,
  property_type TEXT NOT NULL CHECK (property_type IN ('RUMAH', 'TANAH', 'APARTEMEN', 'RUKO')),
  price_per_sqm BIGINT NOT NULL,
  land_area_sqm INTEGER,
  source TEXT NOT NULL CHECK (source IN ('99co', 'rumah123', 'olx', 'user_submission')),
  listing_url TEXT,
  is_outlier BOOLEAN DEFAULT false,
  scraped_at TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS property_submissions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  province TEXT NOT NULL,
  city TEXT NOT NULL,
  district TEXT NOT NULL,
  property_type TEXT NOT NULL,
  total_price BIGINT NOT NULL,
  land_area_sqm INTEGER NOT NULL,
  price_per_sqm BIGINT GENERATED ALWAYS AS (total_price / NULLIF(land_area_sqm, 0)) STORED,
  submission_fingerprint TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX idx_property_benchmarks_location ON property_benchmarks(province, city, district, property_type);
CREATE INDEX idx_property_benchmarks_outlier ON property_benchmarks(is_outlier);
