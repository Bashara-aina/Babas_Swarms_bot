---
title: Spt Tahunan Pph Orang Pribadi
type: concept
status: legacy
tags:
- /
- home
- newadmin
- swarm-bot
- tax
created: '2026-04-14'
updated: '2026-04-14'
summary: Every employee who earns above PTKP must file SPT Tahunan (annual tax return).
  cekwajar should remind employees of deadlines and provide accurate annual income
  data (Form 1721-A1) for filing. Misse...
wikilinks: []
confidence: medium
source: research
---

# SPT Tahunan PPh Orang Pribadi - Cara Lapor dan Deadline 2025

## Why This Matters for cekwajar.id
Every employee who earns above PTKP must file SPT Tahunan (annual tax return). cekwajar should remind employees of deadlines and provide accurate annual income data (Form 1721-A1) for filing. Missed deadlines result in penalties.

## Core Knowledge

**SPT Tahunan OP (Orang Pribadi) deadlines:**
- **Original deadline**: March 31 of following year
- **Extended deadline for 2025**: April 30, 2026 (per DJP extension)
- No penalties if filed by extended deadline

**Who must file:**
- Employees with annual income > PTKP (Rp 54M for TK/0)
- All employees who had tax deducted by employer
- Anyone with other taxable income

**Filing methods:**
1. **Coretax DJP** (new system) - primary platform
2. **e-Filing DJP** (legacy) - still available
3. **Manual** - only for specific cases

**Form types:**
- **1721-A1**: For employees with one employer (most common)
- **1721-A2**: For employees with multiple employers
- **1770**: For self-employed/freelancers

**Required documents:**
- Form 1721-A1 from employer
- NPWP
- NIK/KTP
- Income evidence from other sources (if any)

## Process Flow

```
1. Employer generates Form 1721-A1 (Jan-Feb)
2. Employee receives and reviews data
3. Employee logs into Coretax/e-Filing
4. Employee fills SPT Tahunan with pre-filled data
5. Employee submits and receives proof of receipt
6. If tax owed → pay via e-Billing
7. If overpaid → claim refund
```

## Edge Cases and Common Mistakes

1. **Not filing despite income below PTKP**: Even zero-tax filers should file to maintain good standing
2. **Wrong pre-filled data**: Must verify all employer data before submission
3. **Forgetting to include other income**: Freelance, rental, business income must be reported
4. **Deadline confusion**: Original deadline was March 31, extended to April 30 for 2025
5. **Not keeping proof of filing**: Save confirmation receipt for 5 years

## cekwajar.id Implementation Notes

- **File to update**: Not directly applicable - employee self-files
- **Function to provide**: Generate Form 1721-A1 data for employees
- **Data source to query**: `employees.annual_income_summary` (Supabase)
- **Update frequency**: Annual (January-February for form generation)
- **Legion action**: Can send reminders before deadline; can generate annual income report; CANNOT file on behalf of employee

## Monetization Angle

- Annual tax filing reminder service → engagement touchpoint
- Form 1721-A1 generation is a value-add for payroll subscribers
- Integration with e-Filing API for smoother employee experience (future)

## Sources and Cross-References

- Official URL: https://pajak.go.id/panduan-layanan-pajak/pelaporan-2025
- DJP Coretax: https://coretax.djp.go.id
- Related: 021-ptkp-2024-pmk101-2016 (PTKP values)
