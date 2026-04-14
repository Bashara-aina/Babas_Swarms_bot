---
title: Saas Metrics Benchmarks
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- business
created: '2026-04-14'
updated: '2026-04-14'
summary: Understanding SaaS metrics enables proper financial modeling and investor
  readiness for cekwajar.id. The core unit economics determine sustainability and
  growth potential.
wikilinks: []
confidence: medium
source: research
---

# SaaS Metrics MRR Churn LTV CAC Benchmark 2024

## Why This Matters for cekwajar.id
Understanding SaaS metrics enables proper financial modeling and investor readiness for cekwajar.id. The core unit economics determine sustainability and growth potential.

## Core Knowledge

### Key SaaS Metrics Definitions

| Metric | Formula | Target Range |
|--------|---------|-------------|
| **MRR** | Monthly Recurring Revenue | $10K-100K+ |
| **ARR** | Annual Recurring Revenue (MRR × 12) | $120K-1.2M+ |
| **Churn Rate** | Customers lost / Total customers | <5% monthly |
| **LTV** | (ARPU × Gross Margin) / Churn Rate | 3× CAC minimum |
| **CAC** | Total Sales & Marketing Cost / New Customers | Varies by segment |
| **LTV:CAC** | Lifetime Value / Customer Acquisition Cost | >3:1 healthy |
| **NRR** | Net Revenue Retention | >100% |

### 2024 SaaS Benchmarks by Segment

| Segment | LTV Range | CAC Range | LTV:CAC |
|---------|-----------|-----------|---------|
| **SMB** | $15K-$40K | $5K-$15K | 2.5:1 - 4:1 |
| **Mid-Market** | $50K-$150K | $15K-$50K | 3:1 - 5:1 |
| **Enterprise** | $300K-$1M+ | $50K-$200K | 3:1 - 7:1 |

### The Magic Ratio
- **Healthy LTV:CAC**: 3:1 or greater
- **<3:1 Warning**: Acquiring customers costs too much
- **>5:1 Opportunity**: Could spend more on acquisition
- **Median across all segments**: 3.2:1

### MRR Growth Benchmarks
- **Good**: 10-15% month-over-month
- **Great**: 15-25% month-over-month  
- **Excellent**: >25% month-over-month (requires strong unit economics)

## Exact Formulas / Numbers (if applicable)
```typescript
// SaaS Metric Calculations
interface SaaSMetrics {
  mrr: number;
  arr: number;
  arpu: number;           // Average Revenue Per User
  grossMargin: number;     // Typically 70-80% for SaaS
  churnRate: number;      // Monthly churn (decimal)
  cac: number;
  ltv: number;
  ltvCacRatio: number;
}

// Calculate LTV
function calculateLTV(metrics: SaaSMetrics): number {
  return (metrics.arpu * metrics.grossMargin) / metrics.churnRate;
}

// Calculate LTV:CAC Ratio
function calculateLTVCAC(ltv: number, cac: number): number {
  return ltv / cac;
}

// Calculate CAC Payback Period (months)
function calculateCACPayback(cac: number, mrr: number): number {
  return cac / (mrr / cac); // Simplified
}

// Calculate Net Revenue Retention
function calculateNRR(
  startingMRR: number,
  expansionMRR: number,
  contractionMRR: number,
  churnedMRR: number
): number {
  return ((startingMRR + expansionMRR - contractionMRR - churnedMRR) 
          / startingMRR) * 100;
}

// Example: SMB SaaS with $100 ARPU, 70% margin, 3% churn, $50 CAC
const exampleLTV = calculateLTV({
  arpu: 100,
  grossMargin: 0.70,
  churnRate: 0.03
});
console.log(`LTV: $${exampleLTV.toFixed(2)}`);
console.log(`LTV:CAC: ${calculateLTVCAC(exampleLTV, 50).toFixed(2)}:1`);
```

## Edge Cases and Common Mistakes
1. **Ignoring churn**: 5% monthly churn = 46% annual customer loss
2. **Gross margin assumption**: Often assume 70% but calculate accurately
3. **LTV formula**: Must use churn rate (not retention rate)
4. **CAC includes all costs**: Don't forget product, support, overhead
5. **Confusing ARR with MRR**: ARR = MRR × 12 only if no price changes

## cekwajar.id Implementation Notes
- **File to update**: `core/metrics.py`, `handlers/dashboard.py`
- **Function to modify/create**: `calculate_saas_metrics()`, `track_mrr_growth()`
- **Data source to query**: Supabase `subscriptions`, `customers`, `invoices` tables
- **Update frequency**: Daily metrics aggregation, weekly review
- **Legion action**: Can autonomously generate metrics reports and alerts

## Monetization Angle
- SaaS metrics dashboard as a product feature
- Benchmark reports for specific verticals ($500-2000/report)
- Unit economics consulting for Indonesian startups
- Investor-ready financial modeling service

## Sources and Cross-References
- Baremetrics: https://baremetrics.com/blog/saas-metrics-checklist-kpis-founders-should-track
- HubiFi B2B SaaS Benchmarks: https://www.hubifi.com/blog/b2b-saas-benchmarks
- RevPartners Cheat Sheet: https://revpartners.io/hubfs/PDFs/SaaS%20Metric%20Cheat%20sheet.pdf
- Optifai LTV Benchmarks: https://optifai.ai/learn/questions/b2b-saas-ltv-benchmark/
- Last verified: 2026-04-11
