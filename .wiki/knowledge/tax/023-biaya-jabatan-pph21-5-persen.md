---
title: Biaya Jabatan Pph21 5 Persen
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- tax
created: '2026-04-14'
updated: '2026-04-14'
summary: Biaya jabatan reduces taxable income before PPh 21 calculation. With Rp500,000/month
  cap, it saves employees ~Rp60,000–Rp225,000 in annual tax depending on bracket.
  Failing to deduct biaya jabatan ...
wikilinks: []
confidence: medium
source: research
---

# Biaya Jabatan PPh 21 - 5% dari Penghasilan Bruto Maksimal Rp500rb/bulan

## Why This Matters for cekwajar.id
Biaya jabatan reduces taxable income before PPh 21 calculation. With Rp500,000/month cap, it saves employees ~Rp60,000–Rp225,000 in annual tax depending on bracket. Failing to deduct biaya jabatan results in over-taxation and employee complaints.

## Core Knowledge

**Biaya jabatan** is a standard expense deduction for fixed employees (pegawai tetap), representing work-related costs that don't require receipts.

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

**Annual calculation:**
```
total_biaya_jabatan = min(5% × gross_annual, Rp 6,000,000)
```

**Relationship with Biaya Pensiun:**
- Biaya pensiun: 5% of gross, cap Rp 200,000/month (Rp 2,400,000/year)
- Both can be deducted simultaneously from gross income
- Total deduction cap: Rp 700,000/month combined

## Exact Formulas / Numbers (if applicable)

```typescript
// Biaya jabatan calculation
const BIAYA_JABATAN_MONTHLY_CAP = 500_000;
const BIAYA_JABATAN_ANNUAL_CAP = 6_000_000;
const BIAYA_JABATAN_RATE = 0.05;

function calculateBiayaJabatan(grossMonthly: number): number {
  const calculated = grossMonthly * BIAYA_JABATAN_RATE;
  return Math.min(calculated, BIAYA_JABATAN_MONTHLY_CAP);
}

function calculateBiayaJabatanAnnual(grossAnnual: number): number {
  const calculated = grossAnnual * BIAYA_JABATAN_RATE;
  return Math.min(calculated, BIAYA_JABATAN_ANNUAL_CAP);
}

// For employees with multiple employers
function calculateBiayaJabatanPerEmployer(
  grossPerEmployer: number,
  employerCount: number
): number {
  // Each employer calculates separately
  const calculated = grossPerEmployer * BIAYA_JABATAN_RATE;
  return Math.min(calculated, BIAYA_JABATAN_MONTHLY_CAP);
}

// Full net income calculation
function calculateNetIncome(
  grossMonthly: number,
  biayaPensiun: number = 0
): number {
  const biayaJabatan = calculateBiayaJabatan(grossMonthly);
  return grossMonthly - biayaJabatan - biayaPensiun;
}
```

## Edge Cases and Common Mistakes

1. **Misapplying to non-fixed employees**: Biaya jabatan only for pegawai tetap, not freelancers/daily workers
2. **Exceeding monthly cap**: If 5% calculation > Rp 500,000, use cap (not the excess)
3. **Annual over-cap**: Even if monthly deductions are under Rp 500,000, annual total capped at Rp 6M
4. **Double counting with pensiun**: Biaya pensiun is separate and should not be mixed up
5. **Employee with multiple jobs**: Each employer calculates biaya jabatan separately from their own payment

## cekwajar.id Implementation Notes

- **File to update**: `src/tax/biaya-jabatan.ts`
- **Function to modify/create**: `calculateBiayaJabatan()`, `calculateNetIncome()`
- **Data source to query**: `payroll.gross_monthly` (Supabase)
- **Update frequency**: Static unless PMK changes rates (rare)
- **Legion action**: Can auto-calculate during payroll; can flag when gross income approaches annual cap

## Monetization Angle

- Proper biaya jabatan deduction saves employees real money → trust in payroll system
- Automated calculation differentiates from manual Excel payroll
- Combined with BPJSTK/JHT deduction creates complete pre-tax calculation

## Sources and Cross-References

- Official URL: https://klikpajak.id/blog/biaya-jabatan-pph-21/
- PMK 168/2023 Pasal 10
- Related: 022-pph17-pasal-17-progresif (net income calculation)
- Related: 025-pph21-karyawan-tidak-tetap (different rules for non-fixed)
