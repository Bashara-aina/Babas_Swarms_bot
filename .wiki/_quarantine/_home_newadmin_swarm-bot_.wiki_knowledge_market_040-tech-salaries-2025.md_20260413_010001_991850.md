---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/market/040-tech-salaries-2025.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.991876"
}
---

---
source_id: 040
title: "Tech Salaries Indonesia 2024-2025: Junior, Mid, Senior Benchmark"
source_type: MARKET_DATA
authority: INDUSTRY
url: "https://www.levels.fyi, https://www.glassdoor.com, https://id.jobstreet.com"
last_verified: "2026-04-11"
tags: [tech-salaries, software-engineer, jakarta, benchmark, salary-data, hrtech]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# Tech Salaries Indonesia 2024-2025: Junior, Mid, Senior Benchmark

## Why This Matters for cekwajar.id
cekwajar.id provides salary benchmarking services - understanding exact tech salary ranges by city, experience, and role is essential for accurate "gaji layak" calculations and competitive positioning against JobStreet, Glints, and Michael Page data sources.

## Core Knowledge

### Software Engineer Salary Ranges by Level (Jakarta)

| Level | Monthly (IDR) | Annual (IDR) |
|-------|---------------|--------------|
| Junior (0-2 yrs) | Rp 5,000,000 – 10,000,000 | Rp 60M – 120M |
| Mid (3-5 yrs) | Rp 12,000,000 – 25,000,000 | Rp 144M – 300M |
| Senior (5+ yrs) | Rp 20,000,000 – 35,000,000 | Rp 240M – 420M |
| Lead/Principal | Rp 35,000,000 – 60,000,000+ | Rp 420M – 720M+ |

### By Source Data Points

**levels.fyi (Jakarta Senior)**: IDR 237M – 459M annually
**SalaryExpert (Jakarta)**: Rp 563M average, Rp 399M entry, Rp 650M senior
**Jobstreet Indonesia**: Rp 7M – 10M monthly range for software engineers
**Glassdoor Jakarta Junior**: ~Rp 106M annually (~$8.8M/month)
**Glassdoor Jakarta Senior**: ~Rp 310M annually (~$25.8M/month)

### Regional Variations
- **Jakarta**: Premium 20-40% above national average
- **Bandung**: 10-20% below Jakarta for tech
- **Surabaya**: 5-15% below Jakarta
- **Remote/International**: Can command USD salaries (IDR 150M-350M for mid-level)

### Tech vs Non-Tech Premium
Tech roles command 40-100% premium over non-tech equivalents in Indonesia.

## Exact Formulas / Numbers (if applicable)
```typescript
// Salary to Gaji Layak Index calculation
interface TechSalaryBenchmark {
  level: 'junior' | 'mid' | 'senior' | 'lead';
  city: 'jakarta' | 'surabaya' | 'bandung' | 'medan' | 'remote';
  currency: 'idr' | 'usd';
  monthlyGross: number;
  annualGross: number;
}

const TECH_SALARY_MATRIX: Record<string, TechSalaryBenchmark> = {
  'jakarta_junior': { level: 'junior', city: 'jakarta', currency: 'idr', monthlyGross: 7500000, annualGross: 90000000 },
  'jakarta_mid': { level: 'mid', city: 'jakarta', currency: 'idr', monthlyGross: 18000000, annualGross: 216000000 },
  'jakarta_senior': { level: 'senior', city: 'jakarta', currency: 'idr', monthlyGross: 27500000, annualGross: 330000000 },
  'surabaya_junior': { level: 'junior', city: 'surabaya', currency: 'idr', monthlyGross: 6000000, annualGross: 72000000 },
  'bandung_junior': { level: 'junior', city: 'bandung', currency: 'idr', monthlyGross: 5500000, annualGross: 66000000 },
};

function calculateGajiLayakIndex(actualSalary: number, expectedSalary: number): number {
  return Math.round((actualSalary / expectedSalary) * 100);
}
```

## Edge Cases and Common Mistakes
- Converting USD to IDR incorrectly (use midpoint rates, not selling rates)
- Including allowances as base salary
- Not accounting for Jakarta premium when benchmarking nationally
- Using global benchmarks without Indonesia-specific adjustments (cost of living differs)

## cekwajar.id Implementation Notes
- **File to update**: `src/lib/salary-benchmark.ts` or Supabase `salary_benchmarks` table
- **Function to modify/create**: `getTechSalaryRange(city, level, year)` 
- **Data source to query**: Supabase `tech_salaries` table with city/level/year breakdown
- **Update frequency**: Quarterly (Q1, Q2, Q3, Q4 data refresh)
- **Legion action**: Can autonomously scrape/aggregate from JobStreet, Glints, levels.fyi periodically

## Monetization Angle
- Premium B2B dashboard with real-time tech salary benchmarks
- Salary comparison API for HR tech integrations
- Candidate positioning reports for recruiters

## Sources and Cross-References
- Official Source: levels.fyi, Glassdoor, JobStreet Indonesia (April 2026)
- Mercer Indonesia Compensation Survey (paid, enterprise)
- Related: #041 Mercer Survey, #042 JobStreet Report
