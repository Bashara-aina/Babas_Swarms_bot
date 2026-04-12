---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/market/043-glints-salary-insights.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:01.683007"
}
---

---
source_id: 043
title: "Glints Salary Insights Indonesia 2024: Tech vs Non-Tech Report"
source_type: MARKET_DATA
authority: INDUSTRY
url: "https://employers.glints.id/hiring-guide/indonesia, https://ebook.glints.com/tren-hr-dan-survei-gaji-2024/"
last_verified: "2026-04-11"
tags: [glints, salary-insights, tech, non-tech, startup, hiring-guide]
cekwajar_impact: HIGH
legion_can_act: YES
---

# Glints Salary Insights Indonesia 2024: Tech vs Non-Tech Report

## Why This Matters for cekwajar.id
Glints is the dominant platform for tech talent and startup jobs in Indonesia. Their salary data is critical for understanding the tech talent market, startup compensation trends, and for positioning cekwajar.id as the go-to source for tech salary benchmarking in the archipelago.

## Core Knowledge

### Glints Hiring Guide Indonesia Key Data

**Median Salary Comparison**: Indonesia has the lowest median salary compared to rest of Southeast Asia
**Tech Talent Advantage**: Hiring skilled tech talent is more economical in Indonesia vs regional peers

### Glints 2024 HR & Salary Survey Highlights

**Labor Market 2023-2024**:
- Unemployment rate dropped to 5.45% (2023)
- Tech sector driving demand
- Startup ecosystem maturing

**Learning & Development Trends 2024**:
- Companies investing more in L&D programs
- Cross-industry salary insights
- Case studies from prominent Indonesian companies

### Southeast Asia Startup Talent Trends 2024 (Glints)
- **Data Points**: 10,000+ startup tech and non-tech talent data points
- **Coverage**: 100+ startup insights including AI-centric roles
- **Regional Context**: Indonesia vs Singapore, Malaysia, Vietnam, Philippines

### Salary Differentials: Tech vs Non-Tech
| Category | Indonesia Median | Singapore Median |
|----------|-----------------|------------------|
| Tech Roles | Rp 8-15M/month | $4,000-8,000/month |
| Non-Tech Roles | Rp 4-8M/month | $2,500-5,000/month |

## Exact Formulas / Numbers (if applicable)
```typescript
interface GlintsSalaryBenchmark {
  roleType: 'tech' | 'non-tech';
  experienceLevel: 'entry' | 'mid' | 'senior';
  cityTier: 1 | 2 | 3;
  monthlySalary: number;
}

const GLINTS_BENCHMARK: GlintsSalaryBenchmark[] = [
  { roleType: 'tech', experienceLevel: 'entry', cityTier: 1, monthlySalary: 8000000 },
  { roleType: 'tech', experienceLevel: 'mid', cityTier: 1, monthlySalary: 15000000 },
  { roleType: 'tech', experienceLevel: 'senior', cityTier: 1, monthlySalary: 28000000 },
  { roleType: 'non-tech', experienceLevel: 'entry', cityTier: 1, monthlySalary: 5000000 },
  { roleType: 'non-tech', experienceLevel: 'mid', cityTier: 1, monthlySalary: 9000000 },
  { roleType: 'non-tech', experienceLevel: 'senior', cityTier: 1, monthlySalary: 15000000 },
];

function calculateSEACompetitiveness(indonesianSalary: number, roleType: string): number {
  const regionalMultiplier = roleType === 'tech' ? 0.3 : 0.25;
  return indonesianSalary * regionalMultiplier;
}
```

## Edge Cases and Common Mistakes
- Assuming all tech roles pay equally (product vs engineering vs data science variations)
- Not accounting for startup vs corporate compensation differences (equity vs cash)
- Using Jakarta benchmarks for tier-2/3 cities

## cekwajar.id Implementation Notes
- **File to update**: `src/lib/glints-integration.ts` or Supabase `glints_data` table
- **Function to modify/create**: `getGlintsTechRange(roleType, level, city)`
- **Data source to query**: Supabase `tech_salary_benchmarks` with source='glints'
- **Update frequency**: Annual ebook release, continuous job posting updates
- **Legion action**: Can scrape Glints employer resources and aggregate salary data

## Monetization Angle
- Startup-focused salary tools with Glints-competitive features
- Tech talent salary API for recruitment platforms
- Regional salary comparison (Indonesia vs SEA)

## Sources and Cross-References
- Official URL: https://employers.glints.id/hiring-guide/indonesia
- Glints 2024 HR & Salary Survey: https://ebook.glints.com/tren-hr-dan-survei-gaji-2024/
- Related: #040 Tech Salaries, #042 JobStreet Report, #044 LinkedIn Insights
