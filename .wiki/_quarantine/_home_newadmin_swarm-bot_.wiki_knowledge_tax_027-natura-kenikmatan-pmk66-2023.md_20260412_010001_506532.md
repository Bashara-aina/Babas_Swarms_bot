---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/tax/027-natura-kenikmatan-pmk66-2023.md",
  "reason": "daily_fast_scan: score=0.200 < 0.3",
  "score": 0.2,
  "quarantined_at": "2026-04-12T01:00:01.506555"
}
---

---
source_id: 027
title: "Natura dan Kenikmatan PMK 66/2023 - Objek Pajak PPh 21"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://jdih.kemenkeu.go.id/api/download/dce5daf1-d4e5-4bd1-bc4e-2c086ae33c04/2023pmkeuangan066.pdf"
last_verified: "2026-04-11"
tags: [natura, kenikmatan, pmk66, objek-pajak, pph21]
cekwajar_impact: MEDIUM
legion_can_act: YES
---

# Natura dan Kenikmatan PMK 66/2023 - Objek Pajak PPh 21

## Why This Matters for cekwajar.id
Natura (non-cash benefits like meals, transportation, equipment) provided to employees are **now taxable** as of July 2023 under PMK 66/2023. Employers must include natura value in gross income and calculate appropriate PPh 21. Failure to do so results in under-taxation and potential DJP penalties.

## Core Knowledge

**PMK 66/2023 Key Points:**

**Taxable Nature (became taxable since July 1, 2023):**
- Meals/lunch allowances
- Transportation allowances
- Housing allowances
- Any non-cash benefits given regularly

**Exempt Nature (not taxable if ≤ Rp 2,000,000/month):**
- Work equipment: laptops, tools, safety gear
- Work facilities: company cars for work use, mobile phones for work
- Uniforms/work clothing
- Medical facilities for work-related injuries

**Key change:** Before PMK 66/2023, most natura was tax-free. Now regular natura benefits are taxable.

**Calculation:**
```
Taxable natura = Fair market value of benefit
Added to gross monthly income → Apply TER
```

**Employer's obligation:**
- Calculate value of natura provided
- Withhold PPh 21 on natura value
- Report in DGT Form 1721

## Exact Formulas / Numbers (if applicable)

```typescript
// Natura tax calculation
const NATURA_EXEMPT_THRESHOLD = 2_000_000;

interface NaturaBenefit {
  type: 'meal' | 'transport' | 'housing' | 'equipment' | 'other';
  description: string;
  monthlyValue: number;
  isExempt: boolean;
}

function calculateNaturaTax(
  benefits: NaturaBenefit[],
  terRate: number
): { totalNatura: number; taxableNatura: number; taxOnNatura: number } {
  let totalNatura = 0;
  let taxableNatura = 0;
  
  for (const benefit of benefits) {
    totalNatura += benefit.monthlyValue;
    
    if (!benefit.isExempt) {
      taxableNatura += benefit.monthlyValue;
    }
  }
  
  return {
    totalNatura,
    taxableNatura,
    taxOnNatura: Math.round(taxableNatura * terRate)
  };
}

// Check exempt status
function isNaturaExempt(benefit: NaturaBenefit): boolean {
  // Equipment and work facilities are generally exempt
  if (['equipment'].includes(benefit.type)) {
    return benefit.monthlyValue <= NATURA_EXEMPT_THRESHOLD;
  }
  return false;
}
```

## Edge Cases and Common Mistakes

1. **Assuming all natura is exempt**: Only specific work equipment/facilities qualify; meal/transport allowances are taxable
2. **Not valuing natura correctly**: Must use fair market value, not just cost to company
3. **Exceeding Rp 2M threshold**: Amount above Rp 2M/month becomes taxable
4. **Mixed personal/work use**: Apportionment needed; only work portion is exempt
5. **Not reporting in DGT**: Natura must be reported in annual tax reconciliation

## cekwajar.id Implementation Notes

- **File to update**: `src/tax/natura-calculator.ts`
- **Function to modify/create**: `calculateNaturaTax()`, `isNaturaExempt()`
- **Data source to query**: `employee_benefits.natura_type`, `employee_benefits.monthly_value` (Supabase)
- **Update frequency**: Per benefit period (monthly for ongoing benefits)
- **Legion action**: Can flag natura benefits during payroll; can calculate tax automatically

## Monetization Angle

- Natura taxation adds complexity → premium payroll tier for companies with heavy benefits
- Benefits administration module can include natura calculation
- Compliance reporting for DJP audits

## Sources and Cross-References

- Official URL: https://jdih.kemenkeu.go.id/api/download/dce5daf1-d4e5-4bd1-bc4e-2c086ae33c04/2023pmkeuangan066.pdf
- PP 55/2022
- Related: 020-pph21-ter-pmk168-2023 (tax calculation)
