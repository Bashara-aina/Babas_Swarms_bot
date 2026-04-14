---
title: Pph21 Karyawan Tidak Tetap Harian Lepas
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
summary: Daily workers (tenaga kerja lepas) and freelancers follow **different TER
  rules** than fixed employees. Wrong application of daily TER rates leads to over/under-taxation
  and compliance issues with ...
wikilinks: []
confidence: medium
source: research
---

# PPh 21 Karyawan Tidak Tetap - Harian dan Lepas

## Why This Matters for cekwajar.id
Daily workers (tenaga kerja lepas) and freelancers follow **different TER rules** than fixed employees. Wrong application of daily TER rates leads to over/under-taxation and compliance issues with DJP.

## Core Knowledge

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

**Important:** If cumulative daily income exceeds Rp 2,500,000/day, switch to Pasal 17 progressive calculation.

### 2. Monthly Payment (for non-fixed employees paid monthly)
- Use **TER Bulanan** same as fixed employees
- Based on PTKP status of the worker

**Example calculation (daily worker):**
Ali works 15 days × Rp 450,000 = Rp 6,750,000 total
- Day 1–14: Each day ≤ Rp 450,000 → 0% tax
- Day 15: Daily gross exceeds threshold → apply progressive on 50%

## Exact Formulas / Numbers (if applicable)

```typescript
// TER Harian calculation
const TER_HARIAN_THRESHOLD_1 = 450_000;
const TER_HARIAN_THRESHOLD_2 = 2_500_000;
const TER_HARIAN_RATE = 0.005;

function calculateTERHarian(dailyGross: number): number {
  if (dailyGross <= TER_HARIAN_THRESHOLD_1) {
    return 0;
  } else if (dailyGross <= TER_HARIAN_THRESHOLD_2) {
    return dailyGross * TER_HARIAN_RATE;
  } else {
    // Use Pasal 17 on 50% of daily gross
    const dpp = dailyGross * 0.5;
    return calculateProgressiveTax(dpp) / 12; // Convert annual to daily
  }
}

// Cumulative calculation for multiple days
function calculateCumulativeDailyTax(
  dailyRates: number[],
  workDays: number
): { totalGross: number; totalTax: number; avgDailyTax: number } {
  let totalGross = 0;
  let totalTax = 0;
  
  for (let i = 0; i < workDays; i++) {
    const dailyGross = dailyRates[i];
    totalGross += dailyGross;
    totalTax += calculateTERHarian(dailyGross);
  }
  
  return {
    totalGross,
    totalTax: Math.round(totalTax),
    avgDailyTax: totalTax / workDays
  };
}

// Monthly payment calculation for non-fixed
function calculateMonthlyNonFixed(
  monthlyGross: number,
  ptkpCode: string
): number {
  const ptkp = getPTKP(ptkpCode);
  const category = getTERCategory(ptkp);
  const terRate = lookupTER(monthlyGross, category);
  return Math.round(monthlyGross * terRate);
}
```

## Edge Cases and Common Mistakes

1. **Not tracking cumulative income**: Daily thresholds reset but cumulative matters for annual reconciliation
2. **Confusing daily vs monthly payment workers**: Monthly paid workers use TER Bulanan, not TER Harian
3. **Missing NPWP surcharge**: Non-fixed workers without NPWP get 20% higher rates
4. **Piece workers (upah satuan)**: Calculate average daily rate for TER Harian application
5. **Year-end calculation**: If annual income exceeds PTKP, may need to file SPT Tahunan

## cekwajar.id Implementation Notes

- **File to update**: `src/tax/non-fixed-employee-calculator.ts`
- **Function to modify/create**: `calculateTERHarian()`, `calculateCumulativeDailyTax()`
- **Data source to query**: `daily_workers.daily_rate`, `daily_workers.work_days` (Supabase)
- **Update frequency**: Per payroll run (daily/weekly workers)
- **Legion action**: Can auto-calculate based on timecards; can flag anomalous daily rates

## Monetization Angle

- Gig economy/freelancer workforce is growing → demand for accurate daily tax calculation
- Multiple daily-rate workers creates compliance complexity → premium payroll feature
- Integration with attendance/time-tracking systems for automated daily tax

## Sources and Cross-References

- Official URL: https://ortax.org/penghitungan-pph-21-atas-upah-tenaga-kerja-lepas
- PMK 168/2023 Pasal 16
- Related: 020-pph21-ter-pmk168-2023 (TER tables)
- Related: 022-pph17-pasal-17-progresif (Pasal 17 for >Rp 2.5M daily)
