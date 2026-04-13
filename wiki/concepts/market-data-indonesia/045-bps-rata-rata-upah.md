---
source_id: 045
title: "BPS Statistics Indonesia 2024: Average Employee Wages & Salaries"
source_type: MARKET_DATA
authority: OFFICIAL_GOV
url: "https://www.bps.go.id/id/statistics-table/1/MjI0OSMx/rata-rata-upah-gaji-bersih-sebulan-buruh-karyawan-pegawai-menurut-kelompok-umur-dan-lapangan-pekerjaan-utama--2024.html"
last_verified: "2026-04-11"
tags: [bps, statistics, wages, national-average, sakernas, official-data]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# BPS Statistics Indonesia 2024: Average Employee Wages & Salaries

## Why This Matters for cekwajar.id
BPS (Badan Pusat Statistik) is Indonesia's official statistics agency. Their Sakernas survey data represents the ground truth for national average wages. cekwajar.id must anchor our "gaji wajar" calculations to BPS data to maintain credibility against competitors and provide legally defensible salary recommendations.

## Core Knowledge

### BPS Official Average Salary Data 2024

**February 2024**: Rp 3,04 million/month (average employee salary)
**August 2024**: Rp 3,27 million/month (up from previous year)
**August 2025**: Rp 3,33 million/month (latest available)

### By Sector (August 2024)
| Sector | Monthly Wage |
|--------|-------------|
| Informatics | Rp 5,23 million (highest) |
| Financial Services | Rp 4,5-5 million |
| Construction | Rp 3,8 million |
| Trade/Retail | Rp 2,9 million |
| Other Services | Rp 1,97 million (lowest) |

### By Province (2024)
| Province | Monthly Wage |
|----------|-------------|
| DKI Jakarta | Rp 8,824,817 |
| Jawa Barat | Rp 4,200,000 |
| Jawa Timur | Rp 3,800,000 |
| Jawa Tengah | Rp 3,200,000 |
| Banten | Rp 4,500,000 |
| Bali | Rp 4,100,000 |

### By Age Group
- 25-29: Rp 2.8M
- 30-34: Rp 3.2M
- 35-39: Rp 3.5M
- 40-44: Rp 3.8M
- 45-49: Rp 3.6M
- 50+: Rp 3.3M

### By Education Level
Higher education correlates with higher wages - university graduates earn 40-80% more than senior high school graduates.

## Exact Formulas / Numbers (if applicable)
```typescript
interface BPSWageData {
  period: string; // '2024-02' | '2024-08' | '2025-08'
  nationalAverage: number;
  bySector: Record<string, number>;
  byProvince: Record<string, number>;
}

const BPS_OFFICIAL_WAGES: BPSWageData = {
  '2024-08': {
    nationalAverage: 3270000,
    bySector: {
      informatics: 5230000,
      financial: 4700000,
      construction: 3800000,
      trade: 2900000,
      otherServices: 1970000,
    },
    byProvince: {
      'DKI Jakarta': 8824817,
      'Jawa Barat': 4200000,
      'Jawa Timur': 3800000,
      'Banten': 4500000,
      'Bali': 4100000,
    },
  },
};

function calculateRegionalAdjustment(baseSalary: number, province: string): number {
  const provinceIndex = {
    'DKI Jakarta': 1.0,
    'Jawa Barat': 0.75,
    'Jawa Timur': 0.68,
    'Banten': 0.80,
    'Bali': 0.73,
  };
  return baseSalary * (provinceIndex[province] || 0.65);
}
```

## Edge Cases and Common Mistakes
- BPS data includes informal workers which lowers the average
- Not distinguishing between gross and net salary
- Using February data when August data is more current
- Ignoring sectoral variations (tech vs agriculture wage gap)

## cekwajar.id Implementation Notes
- **File to update**: `src/lib/bps-integration.ts` or Supabase `bps_official_data` table
- **Function to modify/create**: `getBPSNationalAverage(year, month)` and `getBPSBySector(sector)`
- **Data source to query**: Supabase `national_wage_statistics` table
- **Update frequency**: Bi-annual (February and August Sakernas)
- **Legion action**: Can fetch BPS API data automatically twice yearly

## Monetization Angle
- Government/enterprise data API subscriptions
- Compliance-focused salary tools with BPS anchoring
- Labor market research reports

## Sources and Cross-References
- Official URL: https://www.bps.go.id (Sakernas 2024)
- BPS Statistics Table: Wages by sector, province, age, education
- Related: #046 Banking/Finance/FMCG, #053 Cost of Living, #054 Inflation
