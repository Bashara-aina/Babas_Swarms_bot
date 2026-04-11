---
source_id: 056
title: "Levels.fyi Business Model Teardown"
source_type: COMPETITOR_ANALYSIS
authority: INDUSTRY
url: "https://www.levels.fyi/2024/"
last_verified: "2026-04-11"
tags: [levels-fyi, salary-data, tech-compensation, stock-options, career-ladder, transparency, us-markets]
cekwajar_impact: HIGH
legion_can_act: YES
---

# Levels.fyi Business Model Teardown

## Why This Matters for cekwajar.id
Levels.fyi has become THE source for tech industry salary transparency, especially for FAANG-level compensation. Their 2024 report shows median SWE L3 at $600K total comp (including stock). This proves that detailed level-based salary data with stock/bonus breakdowns drives massive user engagement.

## Core Knowledge

### Business Model Canvas

| Block | Content |
|-------|---------|
| **Value Proposition** | Real-time, user-reported total compensation (salary + stock + bonus) by company and level |
| **Customer Segments** | Tech workers negotiating offers (free), Employers buying benchmarking data (paid) |
| **Revenue Streams** | Career services (negotiation coaching), Employer data sales, API access for HR software |
| **Key Activities** | Crowdsourced salary collection, Standardized leveling system, Annual reports |
| **Key Resources** | 1M+ data points, Standardized level taxonomy (L1-L7), Mobile app |

### 2024 Key Compensation Data (USD)
| Level | Top Company | Total Compensation |
|-------|------------|-------------------|
| L1 (Entry) | Hudson River Trading | $410,000 |
| L2 (Mid) | Databricks | $380,000 |
| L3 (Senior) | Databricks | $600,000 |
| L4 (Staff) | OpenAI | $860,000 |
| L5 (Principal) | Facebook | $1,455,000 |

### Revenue Model
- **Negotiation Services**: $500-2000 per coaching engagement, helped 900+ people in 2024
- **Data API**: Enterprise pricing for compensation benchmarking tools
- **Employer Talent Pool**: Recruitment tools using their salary data

## Exact Formulas / Numbers (if applicable)

```typescript
// Levels.fyi Total Compensation Formula
interface CompensationBreakdown {
  baseSalary: number;
  stockRSU: number;  // Annual value
  bonus: number;     // Annual signing or performance bonus
}

function calculateTotalCompensation(c: CompensationBreakdown): number {
  return c.baseSalary + c.stockRSU + c.bonus;
}

// Leveling Standardization
const levelMapping = {
  "L1": { years: "0-2", title: "Entry Level Engineer" },
  "L2": { years: "2-5", title: "Software Engineer" },
  "L3": { years: "5+", title: "Senior Engineer" },
  "L4": { years: "10+", title: "Staff Engineer" },
  "L5": { years: "15+", title: "Principal Engineer" }
};

// Location-based adjustment (San Francisco Bay Area baseline)
function adjustForLocation(baseComp: number, targetCity: string): number {
  const multipliers = {
    "San Francisco": 1.0,
    "Seattle": 0.92,
    "New York": 0.85,
    "Austin": 0.75,
    "Jakarta": 0.15  // Indonesian market adjustment
  };
  return baseComp * (multipliers[targetCity] || 0.7);
}
```

## Edge Cases and Common Mistakes
- **Data bias**: Only captures tech industry, heavily skewed toward FAANG-level companies
- **Self-selection**: Users who negotiate hard are over-represented
- **Stock value volatility**: RSU values change with stock price
- **Missing context**: Doesn't capture work-life balance, career growth opportunities

## cekwajar.id Implementation Notes
- **File to update**: `swarms_bot/platforms/telegram/handlers/compensation_handler.py`
- **Function to modify/create**: `calculate_total_comp()`, `get_level_standard()`
- **Data source to query**: `compensation_data` Supabase table
- **Update frequency**: Real-time user submissions
- **Legion action**: Can build level-based comparison system; needs Bashara for international calibration

## Monetization Angle
1. **Salary negotiation coaching**: Rp500k-2M per session, high conversion from free tools
2. **Employer benchmarking subscriptions**: B2B SaaS for HR departments
3. **Resume review services**: Rp150k per review
4. **Affiliate job board**: Commission on successful hires

## Sources and Cross-References
- Official 2024 Report: https://www.levels.fyi/2024/
- Community discussion on monetization: https://www.levels.fyi/community/thread/5H6O4M/how-levels-is-making-money