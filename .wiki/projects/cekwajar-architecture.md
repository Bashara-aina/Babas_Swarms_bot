---
## Business Overview
---
- **Type**: Indonesian wage/salary verification SaaS
- **Purpose**: Workers verify if their salary is fair — accounts for PPh 21 (income tax), BPJS (social insurance) deductions
- **Target users**: Indonesian workers checking wage fairness
- **Status**: Still in brainstorming phase with AI assistance
- **Vision**: One-man company powered by Legion/swarms as the entire backend team
- **Priority**: Future money generator — not yet active
---


## Domain Knowledge — Indonesian Labor Law

### PPh 21 Tax Brackets (2026)
| Taxable Income | Tax Rate |
|---|---|
| Up to IDR 60 million | 5% |
| IDR 60M – IDR 250M | 15% |
| IDR 250M – IDR 500M | 25% |
| IDR 500M – IDR 5 billion | 30% |
| Above IDR 5 billion | 35% |

### TER Method (Tarif Efektif Rata-rata)
- Simplified monthly withholding via fixed effective rate by income bracket
- Reduces calculation complexity, minimizes year-end corrections
- 2026 PPh 21 calculators now include TER mode

### BPJS 2026 Updates (March 2026)
- **BPJS JP (pension) ceiling**: IDR 11,086,300/month (up 5.11% from IDR 10,547,400)
- **BPJS Healthcare minimum**: IDR 286,494/month (5% of DKI Jakarta minimum wage)
- **DKI Jakarta 2026 minimum wage**: IDR 5,729,876/month

### Standard Worker Deductions
- BPJS JHT employee contribution: 2%
- BPJS JP employee contribution: 1%
- BPJS Healthcare employee contribution: 1%
- Approved pension contributions
- PTKP (non-taxable threshold based on dependents)

---

## Competitive Landscape
- recruitgo.com — Indonesian salary calculator
- cekindo.com/incorp — company formation + compliance
- Bashara's edge: must be more accurate, more explainable, or AI-powered explanation

---

## Tech Stack (planned)
- **Frontend**: Next.js (same as rumahlabuh.com)
- **Backend**: Supabase (leverage existing infrastructure)
- **AI**: Legion swarm as backend team

---

## What Needs to Be Built
1. PPh 21 calculator with TER method support
2. BPJS deduction calculator with 2026 ceiling
3. Net salary = Gross - PPh 21 - BPJS - PTKP
4. Explanation of each deduction step
5. AI-powered wage fairness comparison

---

## Related Wiki Files
- `.wiki/profiles/BASHARA-MASTER-PROFILE.md` — business context
- `.wiki/research/EXTERNAL-RESEARCH-FINDINGS.md` — Indonesian labor law details
