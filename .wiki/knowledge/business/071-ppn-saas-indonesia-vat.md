---
title: Ppn Saas Indonesia Vat
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
summary: As a SaaS product serving Indonesian businesses, cekwajar.id MUST correctly
  handle PPN (VAT) on digital services. Non-compliance risks penalties and legal issues.
  Understanding the 12% VAT (effecti...
wikilinks: []
confidence: medium
source: research
---

# PPN 11% SaaS Software Indonesia VAT Digital Service

## Why This Matters for cekwajar.id
As a SaaS product serving Indonesian businesses, cekwajar.id MUST correctly handle PPN (VAT) on digital services. Non-compliance risks penalties and legal issues. Understanding the 12% VAT (effective January 2025) is mandatory.

## Core Knowledge

### Indonesian VAT on Digital Services - Updated 2025

| Aspect | Old Rate (Pre-2025) | New Rate (Jan 2025+) |
|--------|---------------------|----------------------|
| **VAT Rate** | 10% | 12% |
| **Deemed VAT Base** | 10/11 of payment | 11/12 of payment |
| **Effective Rate** | 10% | 11% |

**Key Formula**:
```
VAT = 12% × 11/12 × Gross Payment = 11% of Gross Payment
```

Example: Rp 110,000 subscription
- VAT portion: Rp 110,000 × 11/12 × 12% = Rp 11,000
- Total: Rp 121,000 (customer pays)

### PMSE (Per_MODULE Elektronik) Providers

Foreign digital service providers (Spotify, Netflix, SaaS companies) must:
1. **Register with Tax Directorate General** as PMSE VAT Collector
2. **Collect 12% VAT** from Indonesian customers
3. **Remit VAT monthly** to tax authorities
4. **Report cross-border digital transactions** annually

### Who Must Pay VAT on Digital Services?

**Indonesian Businesses (B2B)**:
- Can claim input VAT credit
- Must register for VAT if annual turnover > Rp 4.8 billion

**Indonesian Consumers (B2C)**:
- VAT added at point of sale
- Cannot claim input credit

### Exemptions and Thresholds
- **Small businesses**: Annual turnover < Rp 4.8 billion exempt from VAT
- **Specific digital services**: Some education, health digital services may be exempt

### Compliance Requirements for SaaS

| Requirement | Deadline | Penalty |
|-------------|----------|---------|
| VAT Registration | Before first transaction | Administrative sanction |
| Monthly VAT Return (SPM) | 15th of following month | Fine for late filing |
| Annual PMSE Report | End of January | Fine for late report |
| VAT Collection | Real-time | 2% penalty per month |

## Exact Formulas / Numbers (if applicable)
```typescript
// Indonesian VAT Calculation for SaaS
interface VATCalculation {
  baseAmount: number;       // In IDR (before VAT)
  vatRate: number;          // 0.12 (12%)
  vatBaseRatio: number;    // 11/12
  totalVAT: number;
  grossAmount: number;      // What customer pays
}

// Calculate VAT on digital service
function calculateIndonesianVAT(baseAmount: number): VATCalculation {
  const vatRate = 0.12;
  const vatBaseRatio = 11 / 12;
  
  // VAT = 12% × 11/12 × base = 11% of base
  const totalVAT = baseAmount * vatRate * vatBaseRatio;
  const grossAmount = baseAmount + totalVAT;
  
  return {
    baseAmount,
    vatRate,
    vatBaseRatio,
    totalVAT,
    grossAmount
  };
}

// Example: Rp 100,000 SaaS subscription
const example = calculateIndonesianVAT(100000);
console.log(`Base: Rp ${example.baseAmount}`);
console.log(`VAT (12% × 11/12): Rp ${example.totalVAT}`);
console.log(`Customer pays: Rp ${example.grossAmount}`);
```

## Edge Cases and Common Mistakes
1. **Forgetting 11/12 ratio**: VAT base is deemed (not actual VAT portion)
2. **Wrong VAT rate**: Confusing 10% vs 12% (2025 update)
3. **Not registering PMSE**: Foreign providers must register before serving Indonesian customers
4. **Missing monthly deadline**: 15th of month deadline is strict
5. **B2B vs B2C confusion**: Different treatment for VAT input credit

## cekwajar.id Implementation Notes
- **File to update**: `billing/invoice_service.py`, `config/tax_rules.yaml`
- **Function to modify/create**: `calculate_vat()`, `generate_tax_report()`, `validate_vat_registration()`
- **Data source to query**: Supabase `invoices`, `transactions` tables
- **Update frequency**: Real-time VAT calculation on each transaction
- **Legion action**: Can autonomously generate VAT reports and reminders

## Monetization Angle
- VAT compliance automation for SaaS ($50-200/month)
- Automated invoice generation with correct VAT
- Monthly/quarterly VAT filing service
- Tax consultation for Indonesian digital businesses

## Sources and Cross-References
- Official URL: https://www.pajak.go.id/en/digitaltax
- VAT on Digital Goods: https://www.avalara.com/us/en/vatlive/country-guides/asia/indonesia/indonesian-vat-electronic-services.html
- ASEAN Briefing: https://www.aseanbriefing.com/news/indonesias-updated-vat-system-for-cross-border-digital-services/
- Indonesia VAT update (July 2025): https://www.vatupdate.com/2025/07/30/indonesia-revamps-vat-system-for-cross-border-digital-services-key-changes-and-compliance-guide/
- Last regulation update: January 2025 (VAT increased from 10% to 12%)
- Last verified: 2026-04-11
