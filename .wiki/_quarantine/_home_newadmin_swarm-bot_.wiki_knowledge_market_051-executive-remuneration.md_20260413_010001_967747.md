---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/market/051-executive-remuneration.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.967770"
}
---

---
source_id: 051
title: "Executive Remuneration Indonesia 2024: BUMN & Private Company Director Salaries"
source_type: MARKET_DATA
authority: INDUSTRY
url: "https://tuwaga.id/artikel/gaji-direksi-bumn/, https://www.cnnindonesia.com/edukasi/20250904110239-561-1270039/berapa-gaji-komisaris-dan-direktur-bumn-ini-kisarannya"
last_verified: "2026-04-11"
tags: [executive-salary, direktur, komisaris, BUMN, board-remuneration, tantiem]
cekwajar_impact: MEDIUM
legion_can_act: YES
---

# Executive Remuneration Indonesia 2024: BUMN & Private Company Director Salaries

## Why This Matters for cekwajar.id
Understanding executive compensation provides the upper ceiling for salary benchmarks. For cekwajar.id's "gaji wajar" system, knowing director-level pay helps establish salary bands and demonstrates the full compensation spectrum from entry to executive level.

## Core Knowledge

### BUMN (State-Owned Enterprise) Director Salaries 2024-2025

**Director Utama (CEO) Salaries by Company**:

| BUMN | Monthly | Annual (incl. bonus) |
|------|---------|---------------------|
| Pertamina | Rp 3.2M – 4.6B | Rp 38-55B |
| PLN | ~Rp 277M base | + Rp 19.1B tantiem |
| PGN | Rp 2.5B | Rp 30B total |
| BRI | Highest banking | Rp 40-108B total remuneration |
| Bank Mandiri | High | Similar to BRI |
| Adhi Karya | Rp 210M | Rp 2.5B annual |
| Semen Baturaja | Rp 263M | Rp 3.2B annual |

**Annual Remuneration Range (Total Package)**:
- **Director Utama**: Rp 40-108 billion per year
- **Director (non-CEO)**: 80-95% of CEO salary
- **Komisaris (Commissioner)**: 60-80% of Director salary

### Private Company Executive Compensation

**Multinational Corporations (MNC)**:
- CEO: Rp 150-500M monthly base
- Director: Rp 75-250M monthly
- VP: Rp 40-100M monthly

**Large Private Indonesian Groups**:
- CEO: Rp 80-300M monthly
- Director: Rp 40-150M monthly
- Senior VP: Rp 25-75M monthly

### Executive Compensation Components
1. **Base Salary**: Monthly fixed component
2. **Tantiem (Bonus)**: Performance-based annual bonus
3. **Benefits**: Housing, vehicle, health insurance
4. **Stock Options**: For MNCs and public companies
5. **Pension**: Separate retirement arrangements

## Edge Cases and Common Mistakes
- Focusing only on base salary ignoring tantiem
- Not accounting for benefit packages
- Using CEO pay for all executive comparisons
- Ignoring industry size differences

## cekwajar.id Implementation Notes
- **File to update**: `src/lib/executive-benchmarks.ts` or Supabase `executive_salary_data` table
- **Function to modify/create**: `getExecutiveSalaryRange(company, position)` and `calculateTotalRemuneration()`
- **Data source to query**: Supabase `board_remuneration` table
- **Update frequency**: Annual (company reports released Q1)
- **Legion action**: Can compile from financial reports and industry databases

## Monetization Angle
- Executive coaching with salary benchmarking
- Board compensation advisory
- Startup equity/compensation planning

## Sources and Cross-References
- Sources: CNN Indonesia, Tuwaga, Instagram (company reports)
- Related: #040 Tech Salaries, #046 Banking/FMCG, #050 Salary Projections
