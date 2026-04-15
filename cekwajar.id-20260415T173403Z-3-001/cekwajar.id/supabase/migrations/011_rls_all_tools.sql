-- ══════════════════════════════════════════════════════════════════════════════
-- cekwajar.id — 011_rls_all_tools.sql
-- RLS for all tool tables
-- ══════════════════════════════════════════════════════════════════════════════

-- payslip_audits
ALTER TABLE payslip_audits ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_select_own_payslip" ON payslip_audits FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "users_insert_own_payslip" ON payslip_audits FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "anon_insert_payslip" ON payslip_audits FOR INSERT WITH CHECK (user_id IS NULL AND session_id IS NOT NULL);
CREATE POLICY "anon_select_recent_payslip" ON payslip_audits FOR SELECT USING (user_id IS NULL AND session_id IS NOT NULL AND created_at > now() - INTERVAL '2 hours');

-- salary_submissions
ALTER TABLE salary_submissions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anyone_insert_salary" ON salary_submissions FOR INSERT WITH CHECK (true);

-- salary_benchmarks
ALTER TABLE salary_benchmarks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_salary_benchmarks" ON salary_benchmarks FOR SELECT USING (true);

-- job_categories
ALTER TABLE job_categories ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_job_categories" ON job_categories FOR SELECT USING (true);

-- umk_2026
ALTER TABLE umk_2026 ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_umk" ON umk_2026 FOR SELECT USING (true);

-- property_benchmarks
ALTER TABLE property_benchmarks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_property_benchmarks" ON property_benchmarks FOR SELECT USING (true);

-- property_submissions
ALTER TABLE property_submissions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_insert_property_submissions" ON property_submissions FOR INSERT WITH CHECK (true);

-- ppp_reference
ALTER TABLE ppp_reference ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_ppp" ON ppp_reference FOR SELECT USING (true);

-- col_cities
ALTER TABLE col_cities ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_col_cities" ON col_cities FOR SELECT USING (true);

-- abroad_salary_benchmarks
ALTER TABLE abroad_salary_benchmarks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_abroad_salary" ON abroad_salary_benchmarks FOR SELECT USING (true);

-- col_indices
ALTER TABLE col_indices ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_col_indices" ON col_indices FOR SELECT USING (true);

-- col_categories
ALTER TABLE col_categories ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_col_categories" ON col_categories FOR SELECT USING (true);

-- pph21_ter_rates
ALTER TABLE pph21_ter_rates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_ter_rates" ON pph21_ter_rates FOR SELECT USING (true);

-- bpjs_rates
ALTER TABLE bpjs_rates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_bpjs_rates" ON bpjs_rates FOR SELECT USING (true);

-- ptkp_values
ALTER TABLE ptkp_values ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_ptkp" ON ptkp_values FOR SELECT USING (true);

-- ocr_quota_counter — service role only (no public policies)
ALTER TABLE ocr_quota_counter ENABLE ROW LEVEL SECURITY;
