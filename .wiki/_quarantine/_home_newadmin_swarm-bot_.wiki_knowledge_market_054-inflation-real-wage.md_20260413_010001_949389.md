---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/market/054-inflation-real-wage.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.949418"
}
---

---
source_id: 054
title: "Indonesia Inflation 2024-2025: Real Wage & Purchasing Power Analysis"
source_type: RESEARCH
authority: OFFICIAL_GOV
url: "https://www.bi.go.id/id/statistik/indikator/data-inflasi.aspx, https://www.kemenkeu.go.id/opini/inflasi-dan-deflasi-memahami-dinamika-harga-dan-kebijakan-ekonomi-indonesia-2025"
last_verified: "2026-04-11"
tags: [inflation, real-wage, purchasing-power, bi-rate, umr, cost-of-living]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# Indonesia Inflation 2024-2025: Real Wage & Purchasing Power Analysis

## Why This Matters for cekwajar.id
Inflation directly erodes purchasing power - a Rp 5M salary last year is worth less today. Understanding real wage growth vs inflation is fundamental to cekwajar.id's "gaji wajar" calculations and helps users understand if their raises are actually improving their standard of living.

## Core Knowledge

### Indonesia Inflation Data 2024-2025

**Official Bank Indonesia Data**:

| Month | 2024 | 2025 |
|-------|------|------|
| January | 2.9% | 2.3% |
| February | 3.0% | 2.2% |
| March | 3.1% | 2.1% |
| April | 3.0% | 2.0% |
| May | 2.8% | 2.1% |
| June | 2.5% | 2.3% |
| July | 2.1% | 2.4% |
| August | 2.1% | 2.6% |
| September | 1.9% | 2.65% |
| October | 1.7% | 2.86% |
| November | 1.6% | 2.72% |
| December | 1.7% | 2.92% |

**2024 Full Year**: 1.7% (lowest in years)
**2025 Full Year**: ~2.5% (normalized)
**2026 Projection**: 2.8-3.0%

### Real Wage Growth Analysis

| Year | Nominal Increase | Inflation | Real Wage Growth |
|------|-----------------|-----------|-----------------|
| 2023 | 7.0% | 3.5% | 3.4% |
| 2024 | 6.2% | 1.7% | 4.4% |
| 2025 | 6.0% | 2.5% | 3.4% |
| 2026 (Proj) | 5.8% | 2.8% | 2.9% |

**August 2025 Warning Sign**:
- Wage increase only 1.94% YoY
- Below inflation = negative real wage growth
- Consumer spending under pressure

### Purchasing Power Impact

**With 3% Inflation, Purchasing Power Erosion**:
| Salary | Year 1 | Year 2 | Year 3 | Year 5 |
|--------|--------|--------|--------|--------|
| Rp 5M | Rp 5M | Rp 4.85M | Rp 4.71M | Rp 4.43M |
| Rp 10M | Rp 10M | Rp 9.71M | Rp 9.42M | Rp 8.86M |

### Components of Inflation (2024)
- **Food**: 3.2% (largest driver)
- **Housing**: 1.8%
- **Transport**: 2.1%
- **Healthcare**: 2.8%
- **Education**: 2.5%

## Exact Formulas / Numbers (if applicable)
```typescript
interface InflationParams {
  nominalSalary: number;
  nominalIncrease: number;
  inflationRate: number;
  years: number;
}

function calculateRealSalary(params: InflationParams): number {
  const { nominalSalary, nominalIncrease, inflationRate, years } = params;
  const nominalGrowth = Math.pow(1 + nominalIncrease, years);
  const inflationErosion = Math.pow(1 + inflationRate, years);
  return (nominalSalary * nominalGrowth) / inflationErosion;
}

function calculateRealWageGrowth(nominalIncrease: number, inflation: number): number {
  return ((1 + nominalIncrease) / (1 + inflation) - 1) * 100;
}

function calculatePurchasingPowerLoss(salary: number, months: number, inflation: number): number {
  const monthlyInflation = Math.pow(1 + inflation, 1/12) - 1;
  let purchasingPower = salary;
  for (let i = 0; i < months; i++) {
    purchasingPower = purchasingPower / (1 + monthlyInflation);
  }
  return salary - purchasingPower;
}
```

## Edge Cases and Common Mistakes
- Confusing CPI inflation with personal inflation (different spending patterns)
- Not accounting for price differences between cities
- Ignoring that inflation affects different demographics differently
- Using nominal instead of real wage growth

## cekwajar.id Implementation Notes
- **File to update**: `src/lib/inflation-analysis.ts` or Supabase `inflation_data` table
- **Function to modify/create**: `getRealWageGrowth()` and `calculatePurchasingPower()`
- **Data source to query**: Supabase `bi_inflation_data` table
- **Update frequency**: Monthly (BI releases)
- **Legion action**: Can fetch BI API monthly and recalculate real wage indices

## Monetization Angle
- Real wage growth tracking tools
- Inflation-protected salary calculators
- Financial planning tools for workers

## Sources and Cross-References
- Official Sources: Bank Indonesia (bi.go.id), Ministry of Finance
- Related: #045 BPS Wages, #050 Salary Projections, #053 Cost of Living
