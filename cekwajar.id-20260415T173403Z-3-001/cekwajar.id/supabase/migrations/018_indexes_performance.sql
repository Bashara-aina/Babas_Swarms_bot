-- ══════════════════════════════════════════════════════════════════════════════
-- cekwajar.id — 018_indexes_performance.sql
-- Additional performance indexes
-- ══════════════════════════════════════════════════════════════════════════════

CREATE INDEX idx_payslip_audits_user_created ON payslip_audits(user_id, created_at DESC);
CREATE UNIQUE INDEX idx_transactions_midtrans_order ON transactions(midtrans_order_id);
CREATE INDEX idx_salary_submissions_city_job ON salary_submissions(city, job_category_id, experience_bucket);
CREATE INDEX idx_property_benchmarks_city_type ON property_benchmarks(city, district, property_type, is_outlier);
CREATE INDEX idx_ppp_reference_country ON ppp_reference(country_code);
CREATE INDEX idx_umk_2026_city ON umk_2026(city);
CREATE INDEX idx_col_indices_city_code ON col_indices(city_code);
