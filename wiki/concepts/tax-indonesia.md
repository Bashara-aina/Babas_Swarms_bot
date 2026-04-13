---
title: Tax Indonesia PPh 21
type: concept
project: cekwajar
sources: [020-pph21-ter-pmk168-2023.md, 021-ptkp-2024-pmk101-2016.md, 022-pph17-pasal-17-progresif.md, 023-biaya-jabatan-pph21-5-persen.md, 024-pph21-bonus-thr-penghasilan-tidak-teratur.md, 025-pph21-karyawan-tidak-tetap-harian-lepas.md, 026-npwp-wajib-pajak-sanksi-tidak-punya.md, 027-natura-kenikmatan-pmk66-2023.md, 028-spt-tahunan-pph-orang-pribadi.md, 029-pph21-direksi-komisaris-tidak-tetap.md]
related: [[intent-routing]], [[vector-search]]
confidence: high
last_compiled: 2026-04-13
status: stub
tags: [pph21, pph17, pt kp, ter, biaya-jabatan, bonus, thr, natura, npwp, pajak, indonesia, bpjs, labor-law]
word_count: 3300
---

# Tax Indonesia PPh 21

## Overview

This document covers Indonesian income tax (PPh Pasal 21) calculations for employees, including TER (Tarif Efektif Rata-rata), progressive rates, deductions, and special cases for various employment types.

---

## 1. PPh 21 TER - Tarif Efektif Rata-Rata (PMK 168/2023)

### Why This Matters
PPh 21 TER is cekwajar's **#1 most-used tax calculation**. Every payroll run requires correct TER application to compute monthly tax deductions. Wrong TER = wrong salary = employee complaints + DJP penalties.

### Core Knowledge

Since January 2024, PPh 21 for employees uses **Tarif Efektif Rata-Rata (TER)** based on PP 58/2023 and PMK 168/2023.

**Key Principles:**
- TER simplifies monthly PPh 21 calculation by using pre-computed effective rates
- For Jan–Nov: multiply gross monthly income by applicable TER category
- In December (or final month): recalculate using progressive Pasal 17 rates, credit taxes already withheld

**Three TER Categories:**

| Kategori | PTKP Status | Annual PTKP |
|----------|-------------|-------------|
| A | TK/0 | Rp 54,000,000 |
| A | TK/1, K/0 | Rp 58,500,000 |
| B | TK/2, K/1 | Rp 63,000,000 |
| B | TK/3, K/2 | Rp 67,500,000 |
| C | K/3 | Rp 72,000,000 |

**TER Bulanan Tables (Kategori A - PTKP Rp 54M dan Rp 58,5M):**

| Gross Monthly (IDR) | TER % |
|----------------------|-------|
| 0 – 4,500,000 | 0% |
| 4,500,001 – 5,000,000 | 0.25% |
| 5,000,001 – 6,000,000 | 0.5% |
| 6,000,001 – 7,000,000 | 0.75% |
| 7,000,001 – 8,000,000 | 1.0% |
| 8,000,001 – 9,000,000 | 1.5% |
| 9,000,001 – 10,000,000 | 2.0% |
| 10,000,001 – 12,000,000 | 2.5% |
| 12,000,001 – 15,000,000 | 3.0% |
| 15,000,001 – 18,000,000 | 3.5% |
| 18,000,001 – 22,000,000 | 4.0% |
| 22,000,001 – 25,000,000 | 4.5% |
| 25,000,001 – 30,000,000 | 5.0% |
| 30,000,001 – 35,000,000 | 6.0% |
| 35,000,001 – 40,000,000 | 7.0% |
| 40,000,001 – 45,000,000 | 8.0% |
| 45,000,001 – 50,000,000 | 9.0% |
| > 50,000,000 | 10.0% |

**TER Harian:**
- Gross ≤ Rp 450,000/day → 0%
- Rp 450,001 – Rp 2,500,000/day → 0.5%
- > Rp 2,500,000/day → use Pasal 17 progressive on 50% of daily gross

---

## 2. PTKP 2024 - Penghasilan Tidak Kena Pajak (PMK 101/2016)

### Core Knowledge

PTKP (Penghasilan Tidak Kena Pajak) is regulated under **PMK 101/PMK.010/2016**. The values have NOT changed since 2016.

**PTKP Values Table:**

| Status | Kode | Annual PTKP |
|--------|------|-------------|
| Tidak Kawin, 0 tanggungan | TK/0 | Rp 54,000,000 |
| Tidak Kawin, 1 tanggungan | TK/1 | Rp 58,500,000 |
| Tidak Kawin, 2 tanggungan | TK/2 | Rp 63,000,000 |
| Tidak Kawin, 3 tanggungan | TK/3 | Rp 67,500,000 |
| Kawin, 0 tanggungan | K/0 | Rp 58,500,000 |
| Kawin, 1 tanggungan | K/1 | Rp 63,000,000 |
| Kawin, 2 tanggungan | K/2 | Rp 67,500,000 |
| Kawin, 3 tanggungan | K/3 | Rp 72,000,000 |
| Kawin + Income merged (0 tanggungan) | K/I/0 | Rp 112,500,000 |
| Kawin + Income merged (1 tanggungan) | K/I/1 | Rp 117,000,000 |
| Kawin + Income merged (2 tanggungan) | K/I/2 | Rp 121,500,000 |
| Kawin + Income merged (3 tanggungan) | K/I/3 | Rp 126,000,000 |

**Tanggungan definition (max 3):**
- Must live with the taxpayer
- No independent income
- Supported by the taxpayer
- Includes legitimate children, adopted children, parents

---

## 3. PPh Pasal 17 - Tarif Progresif 5 Bracket

### Core Knowledge

**Pasal 17 UU PPh No. 36/2008** establishes progressive income tax rates for individual taxpayers.

**5 Bracket Progressive Tax Rates:**

| Lapisan | Penghasilan Kena Pajak (PKP) Tahunan | Tarif |
|---------|--------------------------------------|-------|
| I | Rp 0 – Rp 60,000,000 | 5% |
| II | Rp 60,000,001 – Rp 250,000,000 | 15% |
| III | Rp 250,000,001 – Rp 500,000,000 | 25% |
| IV | Rp 500,000,001 – Rp 5,000,000,000 | 30% |
| V | > Rp 5,000,000,000 | 35% |

**Important notes:**
- Rates are **progressive** (graduated) — only the income above each threshold is taxed at the higher rate
- Used for: December reconciliation, employees with >Rp 2.5M daily, bukan pegawai, mantan pegawai
- When combined with no NPWP: add 20% surcharge to each bracket rate

---

## 4. Biaya Jabatan PPh 21 - 5% dari Penghasilan Bruto

### Core Knowledge

**Biaya jabatan** is a standard expense deduction for fixed employees (pegawai tetap).

**Rules (PMK 168/2023):**
- **Rate**: 5% of gross monthly income
- **Monthly cap**: Rp 500,000
- **Annual cap**: Rp 6,000,000
- **Only for**: Fixed employees (pegawai tetap)
- **Not for**: Freelancers, daily workers, contract employees

**Formula:**
```
biaya_jabatan = min(5% × gross_monthly, Rp 500,000)
```

**Relationship with Biaya Pensiun:**
- Biaya pensiun: 5% of gross, cap Rp 200,000/month (Rp 2,400,000/year)
- Both can be deducted simultaneously from gross income
- Total deduction cap: Rp 700,000/month combined

---

## 5. Bonus dan THR - Penghasilan Tidak Teratur

### Core Knowledge

Since 2024 (PMK 168/2023), bonus and THR are **no longer taxed separately** — they must be combined with regular salary in the month received.

**Key rules:**
- Bonus/THR + regular salary in same month → combined gross income
- Apply TER based on combined income for that month
- December: use Pasal 17 progressive + credit all TER paid Jan–Nov

**Common bonus types:**
1. Bonus kinerja (performance bonus)
2. Bonus tahunan (annual bonus)
3. Bonus referral
4. THR (religious holiday allowance)
5. Tantiem (board bonuses)

---

## 6. PPh 21 Karyawan Tidak Tetap - Harian dan Lepas

### Core Knowledge

**Definitions (PMK 168/2023):**
- **Pegawai tidak tetap**: Paid only when working, based on days worked, units produced, or task completion
- Includes: daily workers, weekly workers, piece workers, task-based workers

**Two calculation methods:**

### 1. Daily Payment (TER Harian)
| Daily Gross Income | TER Rate |
|-------------------|----------|
| ≤ Rp 450,000 | 0% |
| Rp 450,001 – Rp 2,500,000 | 0.5% |
| > Rp 2,500,000 | Use Pasal 17 on 50% of daily gross |

### 2. Monthly Payment (for non-fixed employees paid monthly)
- Use **TER Bulanan** same as fixed employees

---

## 7. NPWP - Sanksi Tidak Punya NPWP

### Core Knowledge

**NPWP requirement (UU PPh Article 2):**
- Every taxpayer conducting taxable activities must have NPWP
- For PPh 21: Employee without NPWP → 20% surcharge on all tax rates

**Surcharge impact:**

| Bracket | Normal Rate | Without NPWP |
|---------|------------|--------------|
| 0 – 60M | 5% | 6% |
| 60M – 250M | 15% | 18% |
| 250M – 500M | 25% | 30% |
| 500M – 5B | 30% | 36% |
| > 5B | 35% | 42% |

**Current policy (2024+):**
- NIK can be used as tax identifier (bridged with population data)
- If NIK is valid and registered, the 20% surcharge may not apply

---

## 8. Natura dan Kenikmatan (PMK 66/2023)

### Core Knowledge

**PMK 66/2023 Key Points:**

**Taxable Natura (became taxable since July 1, 2023):**
- Meals/lunch allowances
- Transportation allowances
- Housing allowances
- Any non-cash benefits given regularly

**Exempt Natura (not taxable if ≤ Rp 2,000,000/month):**
- Work equipment: laptops, tools, safety gear
- Work facilities: company cars for work use, mobile phones for work
- Uniforms/work clothing
- Medical facilities for work-related injuries

---

## 9. SPT Tahunan PPh Orang Pribadi

### Core Knowledge

**SPT Tahunan OP (Orang Pribadi) deadlines:**
- **Original deadline**: March 31 of following year
- **Extended deadline for 2025**: April 30, 2026 (per DJP extension)

**Who must file:**
- Employees with annual income > PTKP (Rp 54M for TK/0)
- All employees who had tax deducted by employer
- Anyone with other taxable income

**Filing methods:**
1. **Coretax DJP** (new system) - primary platform
2. **e-Filing DJP** (legacy) - still available
3. **Manual** - only for specific cases

**Form types:**
- **1721-A1**: For employees with one employer (most common)
- **1721-A2**: For employees with multiple employers
- **1770**: For self-employed/freelancers

---

## 10. PPh 21 Direksi Komisaris Tidak Tetap

### Core Knowledge

**Two types of board member taxation:**

### 1. Board Member Who is Also Fixed Employee
- Receives regular salary → use **TER Bulanan** like normal employee
- Taxed together with their employee income

### 2. Board Member Who is NOT an Employee (non-fixed)
- Receives irregular/occasional payments → use **Pasal 17 progressive directly**
- DPP (dasar pengenaan pajak) = 50% of gross income per payment
- No cumulative calculation across payments throughout year

**Key difference:**

| Type | TER Applicable | Calculation Method |
|------|---------------|-------------------|
| Fixed employee + board | Yes (Jan–Nov) | TER × monthly gross |
| Non-fixed board only | No (always Pasal 17) | 50% × DPP × progressive rate |

---

## 11. Implementation Notes for cekwajar.id

### Key Functions

```typescript
// TER calculation
const TER_TABLE_A = [
  { minGross: 0, maxGross: 4_500_000, terRate: 0.00 },
  { minGross: 4_500_001, maxGross: 5_000_000, terRate: 0.0025 },
  // ... full table
];

function getTERCategory(ptkpAnnual: number): 'A' | 'B' | 'C' {
  if (ptkpAnnual <= 58_500_000) return 'A';
  if (ptkpAnnual <= 67_500_000) return 'B';
  return 'C';
}

function lookupTER(grossMonthly: number, category: 'A' | 'B' | 'C'): number {
  const table = category === 'A' ? TER_TABLE_A : TER_TABLE_B;
  for (const tier of table) {
    if (grossMonthly >= tier.minGross && grossMonthly <= tier.maxGross) {
      return tier.terRate;
    }
  }
  return 0.10;
}

// Biaya jabatan
const BIAYA_JABATAN_MONTHLY_CAP = 500_000;
function calculateBiayaJabatan(grossMonthly: number): number {
  return Math.min(grossMonthly * 0.05, BIAYA_JABATAN_MONTHLY_CAP);
}

// Progressive tax calculation
function calculateProgressiveTax(pkp: number, hasNPWP: boolean = true): number {
  const NPWP_SURCHARGE = 1.20;
  let tax = 0;
  
  if (pkp <= 60_000_000) {
    tax = pkp * 0.05;
  } else if (pkp <= 250_000_000) {
    tax = 60_000_000 * 0.05 + (pkp - 60_000_000) * 0.15;
  } else if (pkp <= 500_000_000) {
    tax = 60_000_000 * 0.05 + 190_000_000 * 0.15 + (pkp - 250_000_000) * 0.25;
  } else if (pkp <= 5_000_000_000) {
    tax = 60_000_000 * 0.05 + 190_000_000 * 0.15 + 250_000_000 * 0.25 + (pkp - 500_000_000) * 0.30;
  } else {
    tax = 60_000_000 * 0.05 + 190_000_000 * 0.15 + 250_000_000 * 0.25 + 4_500_000_000 * 0.30 + (pkp - 5_000_000_000) * 0.35;
  }
  
  return hasNPWP ? tax : tax * NPWP_SURCHARGE;
}
```

### Update Frequency

- PTKP values: Static (rarely changed)
- TER tables: Static unless PP 58/2023 amended
- Biaya jabatan caps: Static
- Natura rules: When PMK 66/2023 changes

---

## Sources and References

- PMK 168/2023: https://jdih.kemenkeu.go.id/PMK168/2023
- PMK 101/2016 (PTKP): https://jdih.kemenkeu.go.id/dok/101-pmk-010-2016
- PMK 66/2023 (Natura): https://jdih.kemenkeu.go.id/api/download/dce5daf1-d4e5-4bd1-bc4e-2c086ae33c04/2023pmkeuangan066.pdf
- UU PPh No. 36/2008 Pasal 17
- PP 58/2023 (base law): https://pp58tahun2023.com
- DJP Coretax: https://coretax.djp.go.id