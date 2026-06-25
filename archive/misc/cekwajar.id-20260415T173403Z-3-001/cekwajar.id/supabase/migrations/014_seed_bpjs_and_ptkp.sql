-- ══════════════════════════════════════════════════════════════════════════════
-- cekwajar.id — 014_seed_bpjs_and_ptkp.sql
-- BPJS contribution rates and PTKP values
-- ══════════════════════════════════════════════════════════════════════════════

-- BPJS contribution rates
INSERT INTO bpjs_rates (component, party, rate_percent, salary_cap_idr, notes, effective_from) VALUES
  ('JHT', 'employee', 2.000, NULL, 'No salary cap for JHT', '2015-01-01'),
  ('JHT', 'employer', 3.700, NULL, 'No salary cap', '2015-01-01'),
  ('JP', 'employee', 1.000, 9559600, 'Cap = 7× UMP DKI Jan 2024', '2015-01-01'),
  ('JP', 'employer', 2.000, 9559600, 'Same cap as employee', '2015-01-01'),
  ('JKK', 'employer', 0.240, NULL, 'Kelompok I — office/low risk', '2015-01-01'),
  ('JKK', 'employer', 0.540, NULL, 'Kelompok II — general risk', '2015-01-01'),
  ('JKK', 'employer', 0.890, NULL, 'Kelompok III — medium risk', '2015-01-01'),
  ('JKK', 'employer', 1.270, NULL, 'Kelompok IV — manufacturing', '2015-01-01'),
  ('JKK', 'employer', 1.740, NULL, 'Kelompok V — mining/high risk', '2015-01-01'),
  ('JKM', 'employer', 0.300, NULL, 'No salary cap', '2015-01-01'),
  ('KESEHATAN', 'employee', 1.000, 12000000, 'Cap IDR 12,000,000', '2015-01-01'),
  ('KESEHATAN', 'employer', 4.000, 12000000, 'Same cap', '2015-01-01');

-- PTKP values (Tax-free threshold)
INSERT INTO ptkp_values (status_code, description, annual_value_idr, effective_from) VALUES
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
  ('K/I/3', 'Kawin, Istri Bekerja, 3 tanggungan', 126000000, '2016-01-01');
