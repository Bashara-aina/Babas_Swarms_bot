---
source_id: 050
title: "Indonesia Salary Growth Projection 2025-2026: Wage Increase Forecasts"
source_type: RESEARCH
authority: INDUSTRY
url: "https://www.suara.com/bisnis/2025/12/23/155254/kenaikan-gaji-pekerja-ri-bakal-melambat-58-persen-tahun-2026"
last_verified: "2026-04-11"
tags: [salary-growth, wage-increase, projection, ump, inflation, merit-increase]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# Indonesia Salary Growth Projection 2025-2026: Wage Increase Forecasts

## Why This Matters for cekwajar.id
Accurate salary growth projections are essential for cekwajar.id to provide forward-looking "gaji wajar" recommendations. Understanding whether wages are growing faster or slower than inflation helps workers and employers plan compensation adjustments.

## Core Knowledge

### Mercer Survey: Salary Increase Projections

**2026 Projected Average Increase**: 5.8%
- Down from 2025 actual increases
- Still above 2024 inflation (~1.7%)

**Historical Context**:
| Year | Average Increase | Inflation |
|------|-----------------|-----------|
| 2023 | 7.0% | 3.5% |
| 2024 | 6.2% | 1.7% |
| 2025 | 6.0% | 2.5% |
| 2026 (Proj) | 5.8% | 2.8% |

### 2026 Sector Breakdown

| Sector | Projected Raise | Sentiment |
|--------|-----------------|-----------|
| Chemical | 6.0% | Most optimistic |
| Financial Services | 5.5% | Stable |
| Technology | 5.8% | Competitive |
| Consumer Goods | 5.2% | Moderate |
| Healthcare | 5.5% | Growing |
| Manufacturing | 4.8% | Conservative |

### Factors Affecting Individual Increases
1. **Individual Performance**: 0-20% variance
2. **Company Performance**: Reflects in bonus pools
3. **Salary Range Spreads**: Compression issues
4. **Market Competitiveness**: Retention adjustments

### UMR/UMP Updates 2026
- **Minimum wage 2026**: Rp 5.73 million (national average)
- Range by province: Rp 2.5M - Rp 5.73M
- Jakarta 2026: ~Rp 5.4 million

## Exact Formulas / Numbers (if applicable)
```typescript
interface SalaryProjection {
  year: number;
  baseIncrease: number;
  sectorAdjustment: Record<string, number>;
  inflation: number;
}

const PROJECTION_2026: SalaryProjection = {
  year: 2026,
  baseIncrease: 0.058, // 5.8%
  inflation: 0.028, // 2.8% projected
  sectorAdjustment: {
    chemical: 0.06,
    technology: 0.058,
    financialServices: 0.055,
    consumerGoods: 0.052,
    healthcare: 0.055,
    manufacturing: 0.048,
  },
};

function calculateRealSalaryGrowth(nominalIncrease: number, inflation: number): number {
  return ((1 + nominalIncrease) / (1 + inflation)) - 1;
}

function projectNextYearSalary(currentSalary: number, sector: string): number {
  return currentSalary * (1 + PROJECTION_2026.sectorAdjustment[sector]);
}
```

## Edge Cases and Common Mistakes
- Using nominal increases without adjusting for inflation
- Ignoring sector-specific variations
- Assuming uniform increases across all levels
- Not accounting for salary compression issues

## cekwajar.id Implementation Notes
- **File to update**: `src/lib/salary-projections.ts` or Supabase `salary_growth_data` table
- **Function to modify/create**: `getSalaryProjection(currentSalary, sector, year)` and `getRealGrowthRate()`
- **Data source to query**: Supabase `wage_projections` table
- **Update frequency**: Annual (Mercer survey release in Q4)
- **Legion action**: Can automatically update projections from Mercer data releases

## Monetization Angle
- Subscription-based salary projection tools
- Corporate compensation planning software
- Individual career growth calculators

## Sources and Cross-References
- Official Source: Mercer Total Remuneration Survey, Detik Finance
- Related: #041 Mercer Survey, #045 BPS Data, #054 Inflation Data
