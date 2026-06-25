-- ══════════════════════════════════════════════════════════════════════════════
-- cekwajar.id — 005_wajar_slip_tables.sql
-- Payslip audit and OCR tables
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS payslip_audits (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
  session_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  delete_at TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '30 days'),

  -- inputs
  gross_salary BIGINT NOT NULL,
  ptkp_status TEXT NOT NULL,
  city TEXT NOT NULL,
  month_number INTEGER NOT NULL CHECK (month_number BETWEEN 1 AND 12),
  year INTEGER NOT NULL DEFAULT EXTRACT(YEAR FROM now())::integer,
  has_npwp BOOLEAN NOT NULL DEFAULT true,

  -- reported deductions
  reported_pph21 BIGINT NOT NULL DEFAULT 0,
  reported_jht_employee BIGINT NOT NULL DEFAULT 0,
  reported_jp_employee BIGINT NOT NULL DEFAULT 0,
  reported_jkk BIGINT NOT NULL DEFAULT 0,
  reported_jkm BIGINT NOT NULL DEFAULT 0,
  reported_kesehatan_employee BIGINT NOT NULL DEFAULT 0,
  reported_take_home BIGINT NOT NULL DEFAULT 0,

  -- OCR metadata
  ocr_source TEXT CHECK (ocr_source IN ('google_vision', 'tesseract', 'manual')),
  ocr_confidence NUMERIC(4,3),
  payslip_file_path TEXT,

  -- calculated results
  calculated_pph21 BIGINT,
  calculated_jht BIGINT,
  calculated_jp BIGINT,
  calculated_kesehatan BIGINT,
  city_umk BIGINT,

  -- violations
  violations JSONB NOT NULL DEFAULT '[]',
  verdict TEXT CHECK (verdict IN ('SESUAI', 'ADA_PELANGGARAN')),

  -- access control
  is_paid_result BOOLEAN NOT NULL DEFAULT false,
  subscription_tier_at_time TEXT NOT NULL DEFAULT 'free'
);

CREATE INDEX idx_payslip_audits_user_id ON payslip_audits(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_payslip_audits_delete_at ON payslip_audits(delete_at);
CREATE INDEX idx_payslip_audits_session_id ON payslip_audits(session_id) WHERE session_id IS NOT NULL;

-- OCR quota counter
CREATE TABLE IF NOT EXISTS ocr_quota_counter (
  month_key TEXT PRIMARY KEY,
  count INTEGER DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Increment OCR counter function
CREATE OR REPLACE FUNCTION increment_ocr_counter()
RETURNS INTEGER AS $$
DECLARE
  new_count INTEGER;
  current_month TEXT;
BEGIN
  current_month := to_char(now(), 'YYYY-MM');
  INSERT INTO ocr_quota_counter (month_key, count, updated_at)
  VALUES (current_month, 1, now())
  ON CONFLICT (month_key)
  DO UPDATE SET count = ocr_quota_counter.count + 1, updated_at = now()
  RETURNING count INTO new_count;
  RETURN new_count;
END;
$$ LANGUAGE plpgsql;
