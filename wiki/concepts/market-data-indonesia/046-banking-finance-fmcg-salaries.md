---
source_id: 046
title: "Industry Salary Comparisons 2024: Banking, Finance & FMCG Indonesia"
source_type: MARKET_DATA
authority: INDUSTRY
url: "https://www.michaelpage.co.id/salary-guide, https://dealls.com/pengembangan-karir/gaji-kerja-di-bank"
last_verified: "2026-04-11"
tags: [banking, finance, fmcg, salary, banking-salary, director-salary]
cekwajar_impact: HIGH
legion_can_act: YES
---

# Industry Salary Comparisons 2024: Banking, Finance & FMCG Indonesia

## Why This Matters for cekwajar.id
Understanding salary benchmarks by industry allows cekwajar.id to provide sector-specific "gaji wajar" recommendations. Banking, finance, and FMCG are among the highest-paying sectors and serve as reference points for professional salary expectations.

## Core Knowledge

### Banking Sector Salaries 2024

**Bank Salaries by Position**:

| Position | Monthly Salary |
|----------|---------------|
| Teller (Fresh Grad) | Rp 4,700,000 |
| Staff/Sales & Marketing | Rp 4,700,000 |
| Personal Financial Consultant | Rp 5,750,000 |
| Account Officer | Rp 7,300,000 |
| IT Business Analyst (Senior) | Rp 15-25 million |
| Senior Backend Developer (Retail Banking) | Rp 40 million |
| Marketing Manager | Rp 30 million |
| IT Business Analyst Senior | Rp 20-25 million |

**Bank Indonesia (Central Bank)**:
- Competitive with commercial banks
- Additional benefits (housing allowance, vehicle)
- prestigious employer

**Major Banks Salary Reference**:
- BCA: Rp 5-8M entry, Rp 15-25M mid, Rp 40M+ senior
- Bank Mandiri: Similar to BCA
- BNI: Slightly lower, Rp 4-7M entry
- BRI: Rp 4-6M entry level

### FMCG Sector Salaries 2024

**FMCG Industry**:
- Second-highest paying sector after banking
- Entry level: Rp 6-9M
- Mid level: Rp 12-20M
- Senior: Rp 25-45M

**Top FMCG Companies** ( Unilever, P&G, Wings, etc.)
- Marketing: 30-40% premium
- Sales: 20-30% premium
- Supply Chain: 10-20% premium

### Financial Services Sector

**Finance Companies**:
- Entry: Rp 5-7M
- Mid: Rp 10-18M
- Senior: Rp 20-35M

**Insurance**:
- Actuarial roles command 50-80% premium
- Underwriting: Rp 6-12M mid-level

## Edge Cases and Common Mistakes
- Banking salaries vary greatly between state-owned (BUMN) and private banks
- Not accounting for performance bonuses (can add 2-6 months salary)
- Ignoring non-salary benefits (BPJS, pension, health insurance)

## cekwajar.id Implementation Notes
- **File to update**: `src/lib/industry-benchmarks.ts` or Supabase `industry_salary_data` table
- **Function to modify/create**: `getIndustrySalaryRange(industry, position, level)`
- **Data source to query**: Supabase `finance_fmcg_salaries` table
- **Update frequency**: Annual (Michael Page Salary Guide release)
- **Legion action**: Can aggregate from multiple job portals and industry reports

## Monetization Angle
- Industry-specific salary tools for job seekers
- Recruitment platform integrations
- Career advisory services

## Sources and Cross-References
- Official Sources: JobStreet, Glassdoor, Michael Page Indonesia Salary Guide 2024
- Company career pages: BCA, Mandiri, BNI, BRI
- Related: #041 Mercer, #042 JobStreet, #051 Executive Remuneration
