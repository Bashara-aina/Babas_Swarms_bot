---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/product/059-karir-kompas-indonesia.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.747923"
}
---

---
source_id: 059
title: "Kompas Karir.com Indonesian Salary Survey Landscape"
source_type: MARKET_DATA
authority: INDUSTRY
url: "https://dataindonesia.id/internet/detail/data-jumlah-pengguna-linkedin-di-indonesia-hingga-april-2024"
last_verified: "2026-04-11"
tags: [kompas, karir-com, salary-survey, indonesia, lowongan-kerja, bps, sakeras, median-gaji]
cekwajar_impact: HIGH
legion_can_act: YES
---

# Indonesian Salary Survey Landscape (Kompas, Karir.com)

## Why This Matters for cekwajar.id
Indonesian salary data is fragmented across Jobstreet, Karir.com, and government sources like BPS Sakernas. The average formal worker earns Rp 3.09 million/month (2025 BPS data). cekwajar.id can aggregate these sources for better market coverage.

## Core Knowledge

### Key Indonesian Data Sources

| Source | Coverage | Methodology |
|--------|----------|-------------|
| **BPS Sakernas** | National labor force survey | Government door-to-door, annual |
| **Jobstreet by SEEK** | Formal sector jobs | Employer-posted salaries, job listings |
| **Karir.com** | Mid-level professionals | Salary benchmarking tool with Kelly Services data |
| **LinkedIn** | 28.36 million Indonesian users (April 2024) | Professional network data |

### Market Context
- **Average formal worker salary**: Rp 3,090,000/month (BPS Sakernas 2025)
- **Median vs Mean**: Indonesia has high income inequality, median is lower than mean
- **Jakarta premium**: Jakarta salaries 40-60% above national average
- **Formal vs informal**: 60%+ of workforce in informal sector (no recorded salary)

### Salary Benchmarking Tools
- **Kelly Services Indonesia**: Annual salary guide published
- **Robert Walters Indonesia**: Quarterly salary surveys
- **HRDBacot**: Informal community-driven salary data (LinkedIn posts)

### Digital Adoption
- LinkedIn: 28.36 million Indonesian users (0.35% MoM growth)
- Median LinkedIn user: Millennial (25-34), urban, professional
- Premium adoption: ~39% of LinkedIn users globally pay for premium

## Exact Formulas / Numbers (if applicable)

```typescript
// Indonesian salary normalization by region
interface RegionalAdjustment {
  jakarta: 1.0,
  surabaya: 0.85,
  bandung: 0.80,
  semarang: 0.72,
  other_major_cities: 0.65,
  tier2_cities: 0.55,
  rural: 0.45
}

// Calculate market rate for a role
function calculateIndonesiaMarketRate(
  baseRole: string,
  experienceYears: number,
  location: keyof RegionalAdjustment,
  industry: string
): SalaryRange {
  const baseSalary = getBaseSalaryFromSurvey(baseRole, industry);
  const regionalMultiplier = RegionalAdjustment[location];
  const experienceMultiplier = 1 + (experienceYears * 0.05); // 5% per year
  
  const adjusted = baseSalary * regionalMultiplier * experienceMultiplier;
  
  return {
    min: adjusted * 0.85,
    median: adjusted,
    max: adjusted * 1.2
  };
}

// Convert annual to monthly
function annualToMonthly(annualSalary: number): number {
  return annualSalary / 12;
}

// PPH 21 (income tax) calculation for Indonesia
function calculatePPH21(annualBruto: number): number {
  const net = annualBruto - (annualBruto * 0.05); // 5% penghasilan neto
  // Progressive tax brackets...
}
```

## Edge Cases and Common Mistakes
- **Survey sample bias**: Most surveys cover formal sector, missing informal workers
- **Currency confusion**: Some sources report in annual vs monthly figures
- **Benefit exclusion**: Many surveys only show base salary, excluding allowances, THR, bonuses
- **Title inconsistency**: "Manager" can mean very different things in SME vs MNC

## cekwajar.id Implementation Notes
- **File to update**: `swarms_bot/services/indonesia_salary_aggregator.py` (new file)
- **Function to modify/create**: `fetch_bps_data()`, `aggregate_jobstreet_salaries()`, `calculateRegionalAdjustment()`
- **Data source to query**: BPS Sakernas API, Jobstreet scraper (if allowed)
- **Update frequency**: Annual for BPS, quarterly for private surveys
- **Legion action**: Can build automated data pipeline; needs Bashara for API integrations

## Monetization Angle
1. **Premium salary reports**: Rp50-200k per detailed industry report
2. **Employer benchmarking**: SaaS subscription for HR departments
3. **Job board affiliate**: Commission on redirected applications
4. **Resume writing services**: Rp100-300k per professional resume

## Sources and Cross-References
- BPS Sakernas 2025: Average Rp 3.09 juta/bulan
- LinkedIn Indonesia: 28.36 million users (Napoleon Cat data)
- Karir.com salary tool: http://www.karir.com/salary
- Robert Walters Indonesia Salary Survey 2026