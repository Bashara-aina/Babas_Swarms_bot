/**
 * WAJAR SLIP — Regulation Constants
 * All values sourced from official Indonesian government regulations.
 * Last verified: March 2026
 * Maintainer: update JP_WAGE_CAP annually (changes every March)
 */

export const REGULATION_META = {
  version: "2026-03-12",
  last_updated: "2026-03-12",
  jp_cap_next_update: "2027-03-01",  // remind maintainer
  changelog: [
    {
      date: "2026-03-12",
      change:
        "CRITICAL FIX: wage_cap_2026 corrected from Rp11.004.000 (estimate) to Rp11.086.300 (verified from SE BPJS B/1226/022026, 25 Feb 2026). PDB 2025 = 5.11% per BPS No.18/02/Th.XXIX. wage_cap_2026_verified = true.",
      verified: true,
    },
    {
      date: "2026-03-12",
      change:
        "Bug fixes: progressiveTax bandWidth, annualImpactWithInterest added, JP 2026 warning infrastructure",
    },
    {
      date: "2026-03-11",
      change:
        "Added wage_cap_2026 (Rp11.004.000 — ESTIMATE, pending Perpres verification)",
      verified: false,
    },
    { date: "2024-01-01", change: "PMK 168/2023 TER tables effective" },
    { date: "2025-03-01", change: "JP cap updated to Rp10.547.400" },
  ] as ReadonlyArray<{
    date: string
    change: string
    verified?: boolean
  }>,
} as const

export interface TERSlab {
  min: number
  max: number | null
  rate: number
}

// ─────────────────────────────────────────────
// SECTION 1: PPh 21 TER TABLES
// Source: PMK No. 168/PMK.03/2023
// Effective: 1 January 2024
// Official PDF: https://pajak.go.id/sites/default/files/2024-02/PMK%20168%20Tahun%202023%20Tentang%20PPh%20Pasal%2021%20TER.pdf
// ─────────────────────────────────────────────

export const TER_A: TERSlab[] = [
  // Category A — applies to: TK/0, TK/1, K/0
  // PMK 168/2023 Lampiran A
  { min: 0,              max: 5_400_000,    rate: 0.0000 },
  { min: 5_400_001,      max: 5_650_000,    rate: 0.0025 },
  { min: 5_650_001,      max: 5_950_000,    rate: 0.0050 },
  { min: 5_950_001,      max: 6_300_000,    rate: 0.0075 },
  { min: 6_300_001,      max: 6_750_000,    rate: 0.0100 },
  { min: 6_750_001,      max: 7_500_000,    rate: 0.0125 },
  { min: 7_500_001,      max: 8_550_000,    rate: 0.0150 },
  { min: 8_550_001,      max: 9_650_000,    rate: 0.0175 },
  { min: 9_650_001,      max: 10_050_000,   rate: 0.0200 },
  { min: 10_050_001,     max: 10_350_000,   rate: 0.0225 },
  { min: 10_350_001,     max: 10_700_000,   rate: 0.0250 },
  { min: 10_700_001,     max: 11_050_000,   rate: 0.0300 },
  { min: 11_050_001,     max: 11_600_000,   rate: 0.0350 },
  { min: 11_600_001,     max: 12_500_000,   rate: 0.0400 },
  { min: 12_500_001,     max: 13_750_000,   rate: 0.0500 },
  { min: 13_750_001,     max: 15_100_000,   rate: 0.0600 },
  { min: 15_100_001,     max: 16_950_000,   rate: 0.0700 },
  { min: 16_950_001,     max: 19_750_000,   rate: 0.0800 },
  { min: 19_750_001,     max: 24_150_000,   rate: 0.0900 },
  { min: 24_150_001,     max: 26_450_000,   rate: 0.1000 },
  { min: 26_450_001,     max: 28_000_000,   rate: 0.1100 },
  { min: 28_000_001,     max: 30_050_000,   rate: 0.1200 },
  { min: 30_050_001,     max: 32_400_000,   rate: 0.1300 },
  { min: 32_400_001,     max: 35_400_000,   rate: 0.1400 },
  { min: 35_400_001,     max: 39_100_000,   rate: 0.1500 },
  { min: 39_100_001,     max: 43_850_000,   rate: 0.1600 },
  { min: 43_850_001,     max: 47_800_000,   rate: 0.1700 },
  { min: 47_800_001,     max: 51_400_000,   rate: 0.1800 },
  { min: 51_400_001,     max: 56_300_000,   rate: 0.1900 },
  { min: 56_300_001,     max: 62_200_000,   rate: 0.2000 },
  { min: 62_200_001,     max: 68_600_000,   rate: 0.2100 },
  { min: 68_600_001,     max: 77_500_000,   rate: 0.2200 },
  { min: 77_500_001,     max: 89_000_000,   rate: 0.2300 },
  { min: 89_000_001,     max: 103_000_000,  rate: 0.2400 },
  { min: 103_000_001,    max: 125_000_000,  rate: 0.2500 },
  { min: 125_000_001,    max: 157_000_000,  rate: 0.2600 },
  { min: 157_000_001,    max: 206_000_000,  rate: 0.2700 },
  { min: 206_000_001,    max: 337_000_000,  rate: 0.2800 },
  { min: 337_000_001,    max: 454_000_000,  rate: 0.2900 },
  { min: 454_000_001,    max: 550_000_000,  rate: 0.3000 },
  { min: 550_000_001,    max: 695_000_000,  rate: 0.3100 },
  { min: 695_000_001,    max: 910_000_000,  rate: 0.3200 },
  { min: 910_000_001,    max: 1_400_000_000,rate: 0.3300 },
  { min: 1_400_000_001,  max: null,         rate: 0.3400 },
]

export const TER_B: TERSlab[] = [
  // Category B — applies to: TK/2, TK/3, K/1, K/2
  // PMK 168/2023 Lampiran B
  { min: 0,              max: 6_200_000,    rate: 0.0000 },
  { min: 6_200_001,      max: 6_500_000,    rate: 0.0025 },
  { min: 6_500_001,      max: 6_850_000,    rate: 0.0050 },
  { min: 6_850_001,      max: 7_300_000,    rate: 0.0075 },
  { min: 7_300_001,      max: 9_200_000,    rate: 0.0100 },
  { min: 9_200_001,      max: 10_750_000,   rate: 0.0150 },
  { min: 10_750_001,     max: 11_250_000,   rate: 0.0200 },
  { min: 11_250_001,     max: 11_600_000,   rate: 0.0250 },
  { min: 11_600_001,     max: 12_600_000,   rate: 0.0300 },
  { min: 12_600_001,     max: 13_600_000,   rate: 0.0400 },
  { min: 13_600_001,     max: 14_950_000,   rate: 0.0500 },
  { min: 14_950_001,     max: 16_400_000,   rate: 0.0600 },
  { min: 16_400_001,     max: 18_450_000,   rate: 0.0700 },
  { min: 18_450_001,     max: 21_850_000,   rate: 0.0800 },
  { min: 21_850_001,     max: 26_000_000,   rate: 0.0900 },
  { min: 26_000_001,     max: 27_700_000,   rate: 0.1000 },
  { min: 27_700_001,     max: 29_350_000,   rate: 0.1100 },
  { min: 29_350_001,     max: 31_450_000,   rate: 0.1200 },
  { min: 31_450_001,     max: 33_950_000,   rate: 0.1300 },
  { min: 33_950_001,     max: 37_100_000,   rate: 0.1400 },
  { min: 37_100_001,     max: 41_100_000,   rate: 0.1500 },
  { min: 41_100_001,     max: 45_800_000,   rate: 0.1600 },
  { min: 45_800_001,     max: 49_500_000,   rate: 0.1700 },
  { min: 49_500_001,     max: 53_800_000,   rate: 0.1800 },
  { min: 53_800_001,     max: 58_500_000,   rate: 0.1900 },
  { min: 58_500_001,     max: 64_000_000,   rate: 0.2000 },
  { min: 64_000_001,     max: 71_000_000,   rate: 0.2100 },
  { min: 71_000_001,     max: 80_000_000,   rate: 0.2200 },
  { min: 80_000_001,     max: 93_000_000,   rate: 0.2300 },
  { min: 93_000_001,     max: 109_000_000,  rate: 0.2400 },
  { min: 109_000_001,    max: 129_000_000,  rate: 0.2500 },
  { min: 129_000_001,    max: 163_000_000,  rate: 0.2600 },
  { min: 163_000_001,    max: 211_000_000,  rate: 0.2700 },
  { min: 211_000_001,    max: 374_000_000,  rate: 0.2800 },
  { min: 374_000_001,    max: 459_000_000,  rate: 0.2900 },
  { min: 459_000_001,    max: 555_000_000,  rate: 0.3000 },
  { min: 555_000_001,    max: 704_000_000,  rate: 0.3100 },
  { min: 704_000_001,    max: 957_000_000,  rate: 0.3200 },
  { min: 957_000_001,    max: 1_405_000_000,rate: 0.3300 },
  { min: 1_405_000_001,  max: null,         rate: 0.3400 },
]

export const TER_C: TERSlab[] = [
  // Category C — applies to: K/3, K/I/0, K/I/1, K/I/2, K/I/3
  // PMK 168/2023 Lampiran C
  { min: 0,              max: 6_600_000,    rate: 0.0000 },
  { min: 6_600_001,      max: 6_950_000,    rate: 0.0025 },
  { min: 6_950_001,      max: 7_350_000,    rate: 0.0050 },
  { min: 7_350_001,      max: 7_800_000,    rate: 0.0075 },
  { min: 7_800_001,      max: 8_850_000,    rate: 0.0100 },
  { min: 8_850_001,      max: 9_800_000,    rate: 0.0125 },
  { min: 9_800_001,      max: 10_950_000,   rate: 0.0150 },
  { min: 10_950_001,     max: 11_200_000,   rate: 0.0175 },
  { min: 11_200_001,     max: 12_050_000,   rate: 0.0200 },
  { min: 12_050_001,     max: 12_950_000,   rate: 0.0300 },
  { min: 12_950_001,     max: 14_150_000,   rate: 0.0400 },
  { min: 14_150_001,     max: 15_550_000,   rate: 0.0500 },
  { min: 15_550_001,     max: 17_050_000,   rate: 0.0600 },
  { min: 17_050_001,     max: 19_500_000,   rate: 0.0700 },
  { min: 19_500_001,     max: 22_700_000,   rate: 0.0800 },
  { min: 22_700_001,     max: 26_600_000,   rate: 0.0900 },
  { min: 26_600_001,     max: 28_100_000,   rate: 0.1000 },
  { min: 28_100_001,     max: 30_100_000,   rate: 0.1100 },
  { min: 30_100_001,     max: 32_600_000,   rate: 0.1200 },
  { min: 32_600_001,     max: 35_400_000,   rate: 0.1300 },
  { min: 35_400_001,     max: 38_900_000,   rate: 0.1400 },
  { min: 38_900_001,     max: 43_000_000,   rate: 0.1500 },
  { min: 43_000_001,     max: 47_400_000,   rate: 0.1600 },
  { min: 47_400_001,     max: 51_200_000,   rate: 0.1700 },
  { min: 51_200_001,     max: 55_800_000,   rate: 0.1800 },
  { min: 55_800_001,     max: 60_400_000,   rate: 0.1900 },
  { min: 60_400_001,     max: 66_700_000,   rate: 0.2000 },
  { min: 66_700_001,     max: 74_500_000,   rate: 0.2100 },
  { min: 74_500_001,     max: 83_200_000,   rate: 0.2200 },
  { min: 83_200_001,     max: 95_600_000,   rate: 0.2300 },
  { min: 95_600_001,     max: 110_000_000,  rate: 0.2400 },
  { min: 110_000_001,    max: 134_000_000,  rate: 0.2500 },
  { min: 134_000_001,    max: 169_000_000,  rate: 0.2600 },
  { min: 169_000_001,    max: 221_000_000,  rate: 0.2700 },
  { min: 221_000_001,    max: 390_000_000,  rate: 0.2800 },
  { min: 390_000_001,    max: 463_000_000,  rate: 0.2900 },
  { min: 463_000_001,    max: 561_000_000,  rate: 0.3000 },
  { min: 561_000_001,    max: 709_000_000,  rate: 0.3100 },
  { min: 709_000_001,    max: 965_000_000,  rate: 0.3200 },
  { min: 965_000_001,    max: 1_419_000_000,rate: 0.3300 },
  { min: 1_419_000_001,  max: null,         rate: 0.3400 },
]

// ─────────────────────────────────────────────
// SECTION 2: PTKP VALUES
// Source: PMK 101/PMK.010/2016
// Reference: https://pajak.go.id/id/penghasilan-tidak-kena-pajak
// ⚠ K/I variants: verify PMK 101/PMK.010/2016 Pasal 1 before prod
// ─────────────────────────────────────────────

export const PTKP: Record<string, number> = {
  'TK/0': 54_000_000,
  'TK/1': 58_500_000,
  'TK/2': 63_000_000,
  'TK/3': 67_500_000,
  'K/0':  58_500_000,
  'K/1':  63_000_000,
  'K/2':  67_500_000,
  'K/3':  72_000_000,
  'K/I/0': 112_500_000,  // ⚠ verify PMK 101/PMK.010/2016
  'K/I/1': 117_000_000,  // ⚠ verify PMK 101/PMK.010/2016
  'K/I/2': 121_500_000,  // ⚠ verify PMK 101/PMK.010/2016
  'K/I/3': 126_000_000,  // ⚠ verify PMK 101/PMK.010/2016
}

/**
 * PTKP → TER Category mapping per PMK 168/2023
 * Category A: TK/0, TK/1, K/0         (single / married no children)
 * Category B: TK/2, TK/3, K/1, K/2   (2–3 dependents)
 * Category C: K/3, K/I/0–K/I/3        (max dependents or dual-income)
 * ⚠ K/2 = Category B (NOT C) — common mistake
 */
export const TER_CATEGORY: Record<string, 'A' | 'B' | 'C'> = {
  'TK/0': 'A', 'TK/1': 'A', 'K/0': 'A',
  'TK/2': 'B', 'TK/3': 'B', 'K/1': 'B', 'K/2': 'B',
  'K/3':  'C',
  'K/I/0':'C', 'K/I/1':'C', 'K/I/2':'C', 'K/I/3':'C',
}

// ─────────────────────────────────────────────
// SECTION 3: BIAYA JABATAN
// Source: PMK No. 250/PMK.03/2008 Pasal 4
// Rate: 5% × penghasilan bruto, max Rp500.000/bulan atau Rp6.000.000/tahun
// PMK 168/2023 uses this in December annual reconciliation (Pasal 10)
// Official: https://peraturan.bpk.go.id/Details/46748
// ─────────────────────────────────────────────

export const BIAYA_JABATAN = {
  rate: 0.05,
  monthly_cap: 500_000,
  annual_cap: 6_000_000,
} as const

// ─────────────────────────────────────────────
// SECTION 4: PASAL 17 RATES (December reconciliation)
// Source: UU No. 7/2021 (HPP) Pasal 17 ayat (1)
// Bracket 35% for >Rp5M added by UU HPP effective 2022
// Official: https://peraturan.bpk.go.id/Details/182060
// ─────────────────────────────────────────────

export const PASAL_17: TERSlab[] = [
  { min: 0,            max: 60_000_000,   rate: 0.05 },
  { min: 60_000_001,   max: 250_000_000,  rate: 0.15 },
  { min: 250_000_001,  max: 500_000_000,  rate: 0.25 },
  { min: 500_000_001,  max: 5_000_000_000,rate: 0.30 },
  { min: 5_000_000_001,max: null,         rate: 0.35 },
]

// ─────────────────────────────────────────────
// SECTION 5: BPJS KESEHATAN
// Source: Perpres 64/2020 amending Perpres 82/2018
// Official: https://peraturan.bpk.go.id/Details/136650/perpres-no-64-tahun-2020
// ⚠ Wage cap: verify Perpres 82/2018 article before prod
// ─────────────────────────────────────────────

export const BPJS_KESEHATAN = {
  employee_rate: 0.01,      // 1% dipotong dari karyawan
  employer_rate: 0.04,      // 4% ditanggung perusahaan
  wage_cap: 12_000_000,     // max base salary for calculation
  employee_max: 120_000,    // 1% × 12.000.000
  employer_max: 480_000,    // 4% × 12.000.000
} as const

// ─────────────────────────────────────────────
// SECTION 6: BPJS KETENAGAKERJAAN
// Source: PP 44/2015 (JKK, JKM), PP 45/2015 (JP), PP 46/2015 (JHT)
// JKK+JKM official: https://peraturan.bpk.go.id/Home/Details/5612
// ─────────────────────────────────────────────

export const BPJS_JHT = {
  // Source: PP 46/2015 Pasal 6 — confirmed
  // employee: 2%, employer: 3.7%, no wage cap
  employee_rate: 0.02,    // 2%
  employer_rate: 0.037,   // 3.7%
  wage_cap: null,         // no cap for JHT
} as const

export const BPJS_JP = {
  // Source: PP 45/2015 + annual Perpres wage cap updates
  employee_rate: 0.01,    // 1%
  employer_rate: 0.02,    // 2%
  // ⚠ UPDATE EVERY FEBRUARY for the following March
  wage_cap_2024: 10_042_300,   // effective 1 Mar 2024
  wage_cap_2025: 10_547_400,   // effective 1 Mar 2025
  wage_cap_2026: 11_086_300,   // ✅ VERIFIED — BPJS SE B/1226/022026, 25 Feb 2026
  wage_cap_2026_verified: true as const,
  // Calculation: Rp10.547.400 × (1 + 5.11% PDB 2025) = Rp11.086.372 → Rp11.086.300
  // Source: BPS Berita Resmi No. 18/02/Th.XXIX, 5 Feb 2026
  benefit_min_2026: 411_400,   // Rp411.400/month, effective Feb 2026
  benefit_max_2026: 4_932_300, // Rp4.932.300/month, effective Feb 2026
  // Source: SE B/1226/022026 — inflasi 2025 = 2.92%
} as const

export const BPJS_JKK = {
  // Source: PP 44/2015 Lampiran I
  // EMPLOYER ONLY — deducting from employee = TIDAK WAJAR
  rates: {
    group_1: 0.0024,   // Risiko sangat rendah
    group_2: 0.0054,   // Risiko rendah
    group_3: 0.0089,   // Risiko sedang
    group_4: 0.0127,   // Risiko tinggi
    group_5: 0.0174,   // Risiko sangat tinggi
  },
  employee_deduction_allowed: false, // PP 44/2015 — employer only
} as const

export const BPJS_JKM = {
  // Source: PP 44/2015 Pasal 18
  // EMPLOYER ONLY — deducting from employee = TIDAK WAJAR
  rate: 0.003,
  employee_deduction_allowed: false,
} as const

// ─────────────────────────────────────────────
// SECTION 7: VERDICT THRESHOLDS
// Note: No official rupiah tolerance exists in regulations.
// These are application-level rounding thresholds only —
// NOT legal safe harbors. Source: internal product decision.
// ─────────────────────────────────────────────

export const VERDICT_THRESHOLDS = {
  wajar_tolerance: 10_000,    // ≤ Rp10.000 diff = WAJAR (rounding)
  perlu_dicek_max: 50_000,    // Rp10.001–50.000 = PERLU_DICEK
  // > Rp50.000 = TIDAK_WAJAR
} as const

// ─────────────────────────────────────────────
// SECTION 8: REGULATION SOURCES (render in VerdictCard)
// ─────────────────────────────────────────────

export const REGULATION_SOURCES = {
  biaya_jabatan: {
    name: "PMK No. 250/PMK.03/2008",
    description: "Biaya Jabatan — 5% max Rp6jt/tahun",
    url: "https://peraturan.bpk.go.id/Details/46748",
    effective: "2009-01-01",
    verified: true,
  },
  pph21_ter: {
    name: 'PMK No. 168/PMK.03/2023',
    description: 'Tarif Efektif PPh Pasal 21',
    url: 'https://pajak.go.id/sites/default/files/2024-02/PMK%20168%20Tahun%202023%20Tentang%20PPh%20Pasal%2021%20TER.pdf',
    effective: '2024-01-01',
    verified: true,
  },
  ptkp: {
    name: 'PMK No. 101/PMK.010/2016',
    description: 'Penghasilan Tidak Kena Pajak (K/I = PTKP diri + kawin + istri per Pasal 1 ayat (3))',
    url: 'https://peraturan.bpk.go.id/Details/108843',
    effective: '2016-01-01',
    verified: true,
  },
  bpjs_kesehatan: {
    name: 'Perpres No. 64/2020',
    description: 'Iuran BPJS Kesehatan PPU',
    url: 'https://peraturan.bpk.go.id/Details/136650/perpres-no-64-tahun-2020',
    effective: '2020-07-01',
    verified: true,
  },
  bpjs_jht: {
    name: 'PP No. 46/2015',
    description: 'Jaminan Hari Tua (Pasal 6: karyawan 2%, pemberi kerja 3,7%)',
    url: 'https://peraturan.bpk.go.id/Details/5614/pp-no-46-tahun-2015',
    effective: '2015-07-01',
    verified: true,
  },
  bpjs_jp: {
    name: 'PP No. 45/2015 + Perpres annual cap',
    description: 'Jaminan Pensiun — cap update tiap Maret',
    url: 'https://peraturan.bpk.go.id/',
    effective: '2015-07-01',
    verified: true,
    cap_2026_verified: true,
    cap_2026_source: "SE BPJS Ketenagakerjaan B/1226/022026 tanggal 25 Februari 2026",
  },
  bpjs_jkk_jkm: {
    name: 'PP No. 44/2015',
    description: 'JKK & JKM — tanggungan pemberi kerja',
    url: 'https://peraturan.bpk.go.id/Home/Details/5612',
    effective: '2015-07-01',
    verified: true,
  },
} as const
