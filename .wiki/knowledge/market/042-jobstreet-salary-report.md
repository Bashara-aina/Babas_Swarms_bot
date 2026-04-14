---
title: Jobstreet Salary Report
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
summary: JobStreet is the largest job platform in Indonesia with extensive salary
  data. Their Hiring, Compensation & Benefits Report 2024 provides authoritative market
  benchmarks that cekwajar.id can use to...
wikilinks: []
confidence: medium
source: research
---

# JobStreet Salary Report Indonesia 2024: Official Hiring & Compensation Data

## Why This Matters for cekwajar.id
JobStreet is the largest job platform in Indonesia with extensive salary data. Their Hiring, Compensation & Benefits Report 2024 provides authoritative market benchmarks that cekwajar.id can use to validate our salary ranges and position against Glints, LinkedIn, and Michael Page competitors.

## Core Knowledge

### JobStreet HCB Report 2024 Key Findings

**Hiring Growth**: 97% of companies recruited at least one employee in 2023
**Average Salary Increase 2023**: 7%
**Market Sentiment**: Positive hiring intent continuing into 2024

### Salary Ranges by Role (JobStreet Indonesia April 2026)

| Role | Monthly Range (IDR) |
|------|-------------------|
| Software Engineer | Rp 7,000,000 – 10,000,000 |
| Officer/Staff | Rp 4,150,000 – 6,500,000 |
| Account Manager | Rp 44M – 615M annually |
| Business Development | Rp 42M – 50M annually |
| Marketing | Rp 42M – 60M annually |

### Industry Coverage
- Banking & Financial Services
- Fast Moving Consumer Goods (FMCG)
- Technology & Digital
- Manufacturing
- Retail
- Healthcare

### JobStreet vs Indonesia Average
JobStreet data tends to skew toward formal sector jobs with salaries 20-40% above BPS national average due to platform user demographics.

## Edge Cases and Common Mistakes
- JobStreet salaries skew higher than reality (platform self-selection bias)
- Not distinguishing between " advertised salary" and "actual accepted salary"
- Ignoring regional variations within Indonesia

## cekwajar.id Implementation Notes
- **File to update**: `src/lib/jobstreet-integration.ts` or Supabase `jobstreet_data` table
- **Function to modify/create**: `getJobStreetRange(jobTitle, industry, city)`
- **Data source to query**: Supabase `salary_market_data` with source='jobstreet'
- **Update frequency**: Annual report, plus periodic job posting analysis
- **Legion action**: Can scrape JobStreet salary pages monthly for real-time data

## Monetization Angle
- Recruiter subscription tier with JobStreet-competitive analytics
- Salary range API for ATS integrations
- Talent acquisition consulting reports

## Sources and Cross-References
- Official URL: https://id.jobstreet.com/id/about/news/article/sea-hcb-report-2024
- Related: #040 Tech Salaries, #041 Mercer, #043 Glints Report, #044 LinkedIn
