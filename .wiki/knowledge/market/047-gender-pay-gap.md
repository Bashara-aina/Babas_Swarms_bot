---
source_id: 047
title: "Gender Pay Gap Indonesia 2023-2024: Wage Inequality Research"
source_type: RESEARCH
authority: ACADEMIC
url: "https://databoks.katadata.co.id/en/tags/gender-wage-gap, https://scholarhub.ui.ac.id/jekk/vol1/iss1/4/"
last_verified: "2026-04-11"
tags: [gender-pay-gap, wage-inequality, equal-pay, pph21, labor-law]
cekwajar_impact: HIGH
legion_can_act: YES
---

# Gender Pay Gap Indonesia 2023-2024: Wage Inequality Research

## Why This Matters for cekwajar.id
Gender pay gap analysis is crucial for cekwajar.id to provide equitable salary recommendations. Understanding the gap helps position the platform as a fairness-focused solution and addresses regulatory trends toward pay transparency and equal pay requirements.

## Core Knowledge

### Global Context
- **Global Average**: Women receive ~37% lower wages than men for equivalent work (World Economic Forum 2022)
- **Indonesia**: Gap persists across all age groups, sectors, and education levels

### Indonesia Gender Pay Gap Statistics 2024

**By Age Group** (End of 2025):
- Gap exists in ALL age groups
- Widest gap in 35-45 age bracket (childbearing years impact)
- Gap narrows but doesn't disappear post-retirement age

**By Sector**:
- Formal sector: 15-25% gap
- Informal sector: 10-20% gap
- Tech sector: 20-35% gap (higher due to seniority disparities)

**By Position Level**:
| Level | Male Avg | Female Avg | Gap |
|-------|----------|------------|-----|
| Entry | Rp 5.2M | Rp 4.8M | 8% |
| Mid | Rp 12M | Rp 10.2M | 15% |
| Senior | Rp 25M | Rp 19.5M | 22% |
| Executive | Rp 55M | Rp 38M | 31% |

### Contributing Factors (Research-Based)
1. **Occupational Segregation**: Women concentrated in lower-paying sectors
2. **Motherhood Penalty**: Career breaks for childbearing
3. **Seniority Gap**: Women underrepresented in senior positions
4. **Negotiation Differences**: Research shows women negotiate salaries less aggressively
5. **Unpaid Care Work**: Disproportionate domestic responsibilities

### Regulatory Trends
- Many Indonesian companies don't regularly check gender pay gaps
- Government pushing for pay transparency
- Compliance requirements increasing

## Exact Formulas / Numbers (if applicable)
```typescript
interface GenderPayGap {
  sector: string;
  level: 'entry' | 'mid' | 'senior' | 'executive';
  maleSalary: number;
  femaleSalary: number;
  gapPercentage: number;
}

function calculateGenderPayGap(maleSalary: number, femaleSalary: number): number {
  return ((maleSalary - femaleSalary) / maleSalary) * 100;
}

function calculateEqualPayTarget(femaleSalary: number, targetGap: number): number {
  // For closing gap to target %
  return femaleSalary / (1 - targetGap / 100);
}
```

## Edge Cases and Common Mistakes
- Confusing raw gap with adjusted gap (same job, same experience)
- Not accounting for part-time work (more women work part-time)
- Ignoring non-wage benefits differences
- Using global statistics for Indonesia-specific analysis

## cekwajar.id Implementation Notes
- **File to update**: `src/lib/gender-equity.ts` or Supabase `gender_pay_gap_data` table
- **Function to modify/create**: `getGenderPayGap(sector, level)` and `calculateEqualPayRecommendation()`
- **Data source to query**: Supabase `labor_equity_statistics` table
- **Update frequency**: Annual (based on research publications)
- **Legion action**: Can compile research data and provide equity recommendations

## Monetization Angle
- DE&I reporting tools for enterprise HR
- Pay equity audit services
- Compliance and certification offerings

## Sources and Cross-References
- Sources: Katadata Databoks, UI Scholar Hub, International Journal
- Related: #040 Tech Salaries, #045 BPS Official Data, #052 Salary Negotiation
