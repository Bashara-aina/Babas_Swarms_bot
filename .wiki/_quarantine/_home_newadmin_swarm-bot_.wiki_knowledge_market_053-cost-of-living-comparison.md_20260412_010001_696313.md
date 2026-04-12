---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/market/053-cost-of-living-comparison.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:01.696353"
}
---

---
source_id: 053
title: "Cost of Living Comparison 2024: Jakarta, Surabaya, Bandung, Yogyakarta, Bali"
source_type: MARKET_DATA
authority: INDUSTRY
url: "https://livingcost.org/cost/bandung/surabaya, https://www.traveloka.com/id-id/explore/destination/kota-dengan-biaya-hidup-termurah-di-indonesia-acc/268895"
last_verified: "2026-04-11"
tags: [cost-of-living, jakarta, surabaya, bandung, bali, yogya, comparison, col]
cekwajar_impact: HIGH
legion_can_act: YES
---

# Cost of Living Comparison 2024: Jakarta, Surabaya, Bandung, Yogyakarta, Bali

## Why This Matters for cekwajar.id
Cost of living is crucial for "gaji wajar" calculations - the same salary means different things in different cities. This data allows cekwajar.id to provide city-adjusted salary recommendations and helps workers understand real purchasing power.

## Core Knowledge

### Major City Cost Comparison (Monthly Expenses)

| City | Kost | Food | Transport | Total | Index |
|------|------|------|-----------|-------|-------|
| Jakarta | Rp 2-5M | Rp 1.5-3M | Rp 0.5-1.5M | Rp 4-9.5M | 100 |
| Surabaya | Rp 1-2M | Rp 1-1.8M | Rp 0.3-0.8M | Rp 2.3-4.6M | 70 |
| Bandung | Rp 0.9-1.5M | Rp 1-1.4M | Rp 0.3-0.6M | Rp 2.2-3.5M | 65 |
| Yogyakarta | Rp 0.6-1.2M | Rp 0.8-1.2M | Rp 0.2-0.4M | Rp 1.6-2.8M | 50 |
| Bali (Denpasar) | Rp 1-2M | Rp 1.2-2M | Rp 0.3-0.7M | Rp 2.5-4.7M | 75 |
| Medan | Rp 0.7-1.5M | Rp 0.8-1.3M | Rp 0.2-0.5M | Rp 1.7-3.3M | 55 |
| Solo | Rp 0.5-1M | Rp 0.7-1M | Rp 0.2-0.3M | Rp 1.4-2.3M | 45 |

### Living Cost Index (Jakarta = 100)

| City | Index | vs Jakarta |
|------|-------|------------|
| Jakarta | 100 | - |
| Bali (Denpasar) | 75 | 25% cheaper |
| Surabaya | 70 | 30% cheaper |
| Medan | 65 | 35% cheaper |
| Bandung | 63 | 37% cheaper |
| Yogyakarta | 50 | 50% cheaper |
| Solo | 45 | 55% cheaper |

### Specific Comparisons

**Bandung vs Surabaya**:
- LivingCost.org data: Bandung 3% cheaper than Surabaya
- Bandung: Rp 536/month baseline vs Surabaya: Rp 549/month
- Bandung food costs lower; Surabaya transport slightly higher

**Jakarta vs Bali**:
- Common perception: Bali cheaper
- Reality: Bali 20-30% cheaper but not dramatically
- Bali extras: tourism-driven prices, seasonal spikes

### Cost Components Breakdown

**Housing (Kost)**:
| City Tier | Monthly Range |
|-----------|---------------|
| Jakarta Premium | Rp 3-8M |
| Jakarta Standard | Rp 1.5-3M |
| Tier 1 Cities | Rp 0.8-2M |
| Tier 2/3 Cities | Rp 0.4-1.2M |

**Food**:
- Self-cooking: 40-60% cheaper than eating out
- Warteg: Rp 15-25K per meal
- Restaurant (casual): Rp 35-75K per meal
- Restaurant (mid): Rp 75-200K per meal

## Exact Formulas / Numbers (if applicable)
```typescript
interface CostOfLivingParams {
  city: string;
  lifestyle: 'modest' | 'standard' | 'comfortable';
  housingType: 'kost' | 'apartment' | 'house';
}

const CITY_INDEX: Record<string, number> = {
  jakarta: 100,
  surabaya: 70,
  bandung: 63,
  yogya: 50,
  bali: 75,
  medan: 65,
  solo: 45,
};

function calculateAdjustedSalary(jakartaSalary: number, targetCity: string): number {
  const index = CITY_INDEX[targetCity] || 65;
  return jakartaSalary * (index / 100);
}

function calculateMinimumLivingSalary(city: string): number {
  const baseMinimum = {
    jakarta: 5500000,
    surabaya: 3850000,
    bandung: 3465000,
    yogya: 2750000,
    bali: 4125000,
    medan: 3575000,
  };
  return baseMinimum[city] || 3500000;
}
```

## Edge Cases and Common Mistakes
- Using Jakarta prices for all cities
- Not accounting for family vs single household
- Ignoring transport costs (major Jakarta expense)
- Seasonal price variations (Bali tourism spikes)

## cekwajar.id Implementation Notes
- **File to update**: `src/lib/cost-of-living.ts` or Supabase `cost_of_living_data` table
- **Function to modify/create**: `getCostOfLiving(city, lifestyle)` and `calculateAdjustedSalary()`
- **Data source to query**: Supabase `col_benchmarks` table
- **Update frequency**: Annual update, or when significant inflation changes
- **Legion action**: Can compile from Numbeo, LivingCost.org, and local sources

## Monetization Angle
- Relocation salary calculator tools
- Cost-of-living adjusted salary comparisons
- City guides for job seekers

## Sources and Cross-References
- Sources: LivingCost.org, Traveloka, Instagram cost guides
- Related: #045 BPS Wages, #049 Remote Work Premium, #054 Inflation
