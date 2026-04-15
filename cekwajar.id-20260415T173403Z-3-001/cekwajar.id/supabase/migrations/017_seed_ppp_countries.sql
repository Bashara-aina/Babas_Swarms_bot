-- ══════════════════════════════════════════════════════════════════════════════
-- cekwajar.id — 017_seed_ppp_countries.sql
-- PPP reference data for 15 countries
-- ══════════════════════════════════════════════════════════════════════════════

INSERT INTO ppp_reference (country_code, country_name, currency_code, currency_symbol, flag_emoji, ppp_factor, ppp_year, is_free_tier, display_order) VALUES
  ('SG', 'Singapore', 'SGD', '$', '🇸🇬', 0.88, 2023, true, 1),
  ('MY', 'Malaysia', 'MYR', 'RM', '🇲🇾', 1.54, 2023, true, 2),
  ('AU', 'Australia', 'AUD', 'A$', '🇦🇺', 1.52, 2023, true, 3),
  ('US', 'United States', 'USD', '$', '🇺🇸', 1.00, 2023, true, 4),
  ('GB', 'United Kingdom', 'GBP', '£', '🇬🇧', 0.71, 2023, true, 5),
  ('JP', 'Japan', 'JPY', '¥', '🇯🇵', 100.5, 2023, false, 6),
  ('KR', 'South Korea', 'KRW', '₩', '🇰🇷', 880.2, 2023, false, 7),
  ('AE', 'United Arab Emirates', 'AED', 'د.إ', '🇦🇪', 2.35, 2023, false, 8),
  ('NL', 'Netherlands', 'EUR', '€', '🇳🇱', 0.85, 2023, false, 9),
  ('DE', 'Germany', 'EUR', '€', '🇩🇪', 0.85, 2023, false, 10),
  ('CA', 'Canada', 'CAD', 'C$', '🇨🇦', 1.35, 2023, false, 11),
  ('NZ', 'New Zealand', 'NZD', 'NZ$', '🇳🇿', 1.67, 2023, false, 12),
  ('HK', 'Hong Kong', 'HKD', 'HK$', '🇭🇰', 6.09, 2023, false, 13),
  ('ZA', 'South Africa', 'ZAR', 'R', '🇿🇦', 8.55, 2023, false, 14),
  ('TH', 'Thailand', 'THB', '฿', '🇹🇭', 14.89, 2023, false, 15);
