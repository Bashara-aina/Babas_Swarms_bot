-- ══════════════════════════════════════════════════════════════════════════════
-- cekwajar.id — 010_reference_data_tables.sql
-- PPh21 TER, BPJS rates, PTKP values
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS pph21_ter_rates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  category TEXT NOT NULL CHECK (category IN ('A', 'B', 'C')),
  min_salary BIGINT NOT NULL,
  max_salary BIGINT NOT NULL,
  monthly_rate_percent NUMERIC(5,2) NOT NULL,
  effective_from DATE NOT NULL DEFAULT '2024-01-01'
);

CREATE TABLE IF NOT EXISTS bpjs_rates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  component TEXT NOT NULL CHECK (component IN ('JHT', 'JP', 'JKK', 'JKM', 'KESEHATAN')),
  party TEXT NOT NULL CHECK (party IN ('employee', 'employer')),
  rate_percent NUMERIC(5,3) NOT NULL,
  salary_cap_idr BIGINT,
  notes TEXT,
  effective_from DATE NOT NULL DEFAULT '2015-01-01'
);

CREATE TABLE IF NOT EXISTS ptkp_values (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  status_code TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL,
  annual_value_idr BIGINT NOT NULL,
  effective_from DATE NOT NULL
);
