---
title: Linkedin Salary Insights
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
summary: LinkedIn Salary Insights provides professional-grade salary data with high
  reliability due to LinkedIn's massive professional user base. This data helps validate
  cekwajar.id benchmarks and position...
wikilinks: []
confidence: medium
source: research
---

# LinkedIn Salary Insights Indonesia 2024-2025: Professional Salary Data

## Why This Matters for cekwajar.id
LinkedIn Salary Insights provides professional-grade salary data with high reliability due to LinkedIn's massive professional user base. This data helps validate cekwajar.id benchmarks and positions the platform against Michael Page, Robert Walters, and other executive search firms.

## Core Knowledge

### LinkedIn Salary Insights Indonesia 2026 Key Trends

**Talent Insider Indonesia Salary Guide 2026**:
- Key shifts in Indonesia's talent market
- Both employers and job seekers affected
- Salary transparency increasing

**Salary Expectations Rising**:
- Most candidates now expect higher salaries
- Selective hiring decisions
- 2026 data shows continued salary pressure

### Salary Ranges by Professional Level

| Level | Annual Range (IDR) | Notes |
|-------|-------------------|-------|
| Entry Professional | Rp 48M – 80M | Fresh grad to 2 years |
| Mid Professional | Rp 80M – 150M | 3-5 years experience |
| Senior Professional | Rp 150M – 300M | 5-10 years |
| Executive | Rp 300M – 1B+ | Director and above |

### Industry Premiums (LinkedIn Data)
- **Technology**: 30-50% above professional average
- **Financial Services**: 20-40% above average
- **Consulting**: 25-45% above average
- **Healthcare**: 10-25% above average

### Regional Variations
- **Jakarta**: Base (index 100)
- **Surabaya**: 85-95
- **Bandung**: 80-90
- **Medan**: 75-85
- **Other Tier 1**: 80-90

## Edge Cases and Common Mistakes
- LinkedIn data skews toward formal, corporate professionals (underrepresents informal/gig economy)
- Not accounting for industry-specific bonuses and equity compensation
- Confusing "expected salary" with "accepted salary"

## cekwajar.id Implementation Notes
- **File to update**: `src/lib/linkedin-integration.ts` or Supabase `linkedin_data` table
- **Function to modify/create**: `getLinkedInSalaryRange(industry, level, city)`
- **Data source to query**: Supabase `professional_salary_data` with source='linkedin'
- **Update frequency**: Quarterly updates from LinkedIn Talent Index reports
- **Legion action**: Can aggregate from LinkedIn Salary Insights pages and reports

## Monetization Angle
- Professional tier subscriptions with executive-level salary data
- Corporate recruitment tools with LinkedIn-competitive analytics
- Industry benchmark reports for enterprise clients

## Sources and Cross-References
- Official URL: LinkedIn Talent Insider Indonesia Salary Guide 2026
- Robert Walters Indonesia Salary Survey (cross-reference)
- Related: #041 Mercer Survey, #042 JobStreet, #043 Glints
