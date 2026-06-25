-- ══════════════════════════════════════════════════════════════════════════════
-- cekwajar.id — 016_seed_col_indices.sql
-- Cost of Living indices and categories
-- ══════════════════════════════════════════════════════════════════════════════

-- COL indices (Jakarta = 100.0)
INSERT INTO col_indices (city_code, city_name, province, col_index, data_year, data_quarter) VALUES
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
  ('PLM', 'Palembang', 'Sumatera Selatan', 61.8, 2025, 4);

-- COL categories (weight breakdown for 3 living standards)
INSERT INTO col_categories (category_code, label_id, hemat_weight, standar_weight, nyaman_weight) VALUES
  ('HOUSING', 'Biaya Tempat Tinggal', 0.300, 0.280, 0.250),
  ('FOOD', 'Makanan & Makan Luar', 0.350, 0.280, 0.220),
  ('TRANSPORT', 'Transportasi', 0.120, 0.120, 0.100),
  ('UTILITIES', 'Listrik, Air, Gas', 0.060, 0.050, 0.040),
  ('HEALTHCARE', 'Kesehatan', 0.040, 0.040, 0.040),
  ('EDUCATION', 'Pendidikan', 0.030, 0.050, 0.060),
  ('ENTERTAINMENT', 'Hiburan & Rekreasi', 0.020, 0.060, 0.100),
  ('CLOTHING', 'Pakaian', 0.030, 0.040, 0.050),
  ('PERSONAL_CARE', 'Perawatan Diri', 0.030, 0.040, 0.060),
  ('SAVINGS', 'Tabungan & Darurat', 0.020, 0.040, 0.080);
