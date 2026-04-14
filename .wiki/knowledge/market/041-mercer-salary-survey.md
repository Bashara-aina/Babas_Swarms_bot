---
title: Mercer Salary Survey
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- market
created: '2026-04-14'
updated: '2026-04-14'
summary: Mercer is the gold standard for enterprise salary benchmarking in Indonesia.
  Enterprise HR departments and MNCs use Mercer data - having this integrated into
  cekwajar.id adds authoritative credibil...
wikilinks: []
confidence: medium
source: research
---

# Mercer Salary Survey Indonesia 2024-2025: Enterprise Compensation Benchmark

## Why This Matters for cekwajar.id
Mercer is the gold standard for enterprise salary benchmarking in Indonesia. Enterprise HR departments and MNCs use Mercer data - having this integrated into cekwajar.id adds authoritative credibility and allows positioning against competitors like Robert Walters and Michael Page.

## Core Knowledge

### Key Mercer Survey Highlights for Indonesia 2024-2025

**Overall Salary Increase Prediction 2026**: 5.8% average (down from 2025)
**Asia-Pacific Average**: 5.2% for 2024

### Sector Variations (Projected 2026 Raises)
| Sector | Expected Raise |
|--------|---------------|
| Chemical | 6.0% |
| Financial Services | 5.5% |
| Technology | 5.8% |
| Consumer Goods | 5.2% |
| Healthcare | 5.5% |
| Manufacturing | 4.8% |

### Mercer-Specific Findings for Indonesia
- **Pay Disparity Across Cities**: Mercer Indonesia survey reveals significant pay gaps between Jakarta and other cities
- **Total Remuneration Approach**: Mercer recommends looking at total compensation (base + benefits + bonuses)
- **Data Coverage**: Mercer WIN® platform provides comprehensive industry coverage

### Subscription Tiers
- **Mercer WIN®**: Entry-level survey access
- **Full TRS (Total Remuneration Survey)**: Enterprise-level, position-specific benchmarking
- **Global Pay Summary**: 50 benchmark positions across 10 job families

## Edge Cases and Common Mistakes
- Treating base salary as total compensation (benefits, bonus structure matter)
- Using global Mercer data without Indonesia-specific adjustments
- Not accounting for industry-specific variations

## cekwajar.id Implementation Notes
- **File to update**: `src/lib/mercer-integration.ts` or Supabase `enterprise_benchmarks` table
- **Function to modify/create**: `getMercerBenchmark(jobFamily, level, sector)`
- **Data source to query**: Supabase `mercer_data` table (requires subscription/API)
- **Update frequency**: Annual (survey releases Q4 for following year)
- **Legion action**: Can integrate with Mercer API if available, otherwise manual quarterly updates

## Monetization Angle
- Enterprise tier subscriptions with Mercer-quality benchmarks
- Custom industry reports for consulting engagements
- HR consulting firm partnerships

## Sources and Cross-References
- Official URL: https://www.imercer.com
- Last regulation update: 2024 TRS data released Q4 2023
- Related: #040 Tech Salaries, #042 JobStreet Report, #044 LinkedIn Insights
