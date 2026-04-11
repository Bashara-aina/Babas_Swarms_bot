---
source_id: 022
title: "PPh Pasal 17 Ayat 1 Huruf a - Tarif Progresif 5 Bracket"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://ortsax.org/mengenal-tarif-pph-pasal-17-dalam-menghitung-pph-21"
last_verified: "2026-04-11"
tags: [pph21, pph17, progresif, tarif, pajak, labor-law]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# PPh Pasal 17 Ayat 1 Huruf a - Tarif Progresif 5 Bracket

## Why This Matters for cekwajar.id
PPh Pasal 17 progressive rates are used for **December reconciliation** (annual true-up) and for all non-TER calculations. This is the definitive tax rate table that determines the final tax amount employees owe. Every payroll system must implement this correctly.

## Core Knowledge

**Pasal 17 UU PPh No. 36/2008** establishes progressive income tax rates for individual taxpayers (employees).

**5 Bracket Progressive Tax Rates:**

| Lapisan | Penghasilan Kena Pajak (PKP) Tahunan | Tarif |
|---------|--------------------------------------|-------|
| I | Rp 0 – Rp 60,000,000 | 5% |
| II | Rp 60,000,001 – Rp 250,000,000 | 15% |
| III | Rp 250,000,001 – Rp 500,000,000 | 25% |
| IV | Rp 500,000,001 – Rp 5,000,000,000 | 30% |
| V | > Rp 5,000,000,000 | 35% |

**Important notes:**
- Rates are **progressive** (graduated) — only the income above each threshold is taxed at the higher rate
- Used for: December reconciliation, employees with >Rp 2.5M daily, bukan pegawai, mantan pegawai
- When combined with no NPWP: add 20% surcharge to each bracket rate

**Comparison with old rates (before 2024):**
- Old bracket 1: 5% for Rp 0–Rp 50M
- New bracket 1: 5% for Rp 0–Rp 60M (adjusted for inflation)
- The Rp 10M adjustment reflects purchasing power changes since 2009

## Exact Formulas / Numbers (if applicable)

```typescript
// Progressive tax calculation (Pasal 17 ayat 1 huruf a)
// Used for December reconciliation and non-TER calculations

interface TaxBracket {
  minPKP: number;
  maxPKP: number;
  rate: number;
}

const TAX_BRACKETS: TaxBracket[] = [
  { minPKP: 0,          maxPKP: 60_000_000,    rate: 0.05 },
  { minPKP: 60_000_001, maxPKP: 250_000_000,   rate: 0.15 },
  { minPKP: 250_000_001,maxPKP: 500_000_000,   rate: 0.25 },
  { minPKP: 500_000_001,maxPKP: 5_000_000_000, rate: 0.30 },
  { minPKP: 5_000_000_001, maxPKP: Infinity,    rate: 0.35 },
];

function calculateProgressiveTax(pkp: number, hasNPWP: boolean = true): number {
  let tax = 0;
  let remainingPKP = pkp;
  
  for (const bracket of TAX_BRACKETS) {
    if (remainingPKP <= 0) break;
    
    const bracketSize = bracket.maxPKP === Infinity 
      ? remainingPKP 
      : bracket.maxPKP - bracket.minPKP + 1;
    const taxableInBracket = Math.min(remainingPKP, bracketSize);
    const rate = hasNPWP ? bracket.rate : bracket.rate * 1.20;
    
    tax += taxableInBracket * rate;
    remainingPKP -= taxableInBracket;
  }
  
  return Math.round(tax);
}

// December reconciliation calculation
function calculateDecemberReconciliation(
  grossAnnual: number,
  biayaJabatan: number,
  iuranPensiun: number,
  ptkpAnnual: number,
  taxesPaidJanToNov: number
): { pkp: number; taxAnnual: number; taxCredit: number; adjustment: number } {
  const netoAnnual = grossAnnual - biayaJabatan - iuranPensiun;
  const pkp = Math.max(0, netoAnnual - ptkpAnnual);
  const taxAnnual = calculateProgressiveTax(pkp);
  const taxCredit = taxesPaidJanToNov;
  const adjustment = taxAnnual - taxCredit;
  
  return { pkp, taxAnnual, taxCredit, adjustment };
}
```

## Edge Cases and Common Mistakes

1. **Forgetting 20% surcharge for no NPWP**: If employee lacks NPWP, ALL brackets increase by 20%
2. **Applying wrong cumulative method**: Progressive means each layer is taxed separately, not the whole amount at one rate
3. **Confusing PTKP with PKP**: PTKP is the threshold; PKP = neto - PTKP
4. **December calculation errors**: TER is only for Jan–Nov; December ALWAYS uses Pasal 17 progressive
5. **Not crediting withheld taxes**: December adjustment = Annual tax - taxes already paid

## cekwajar.id Implementation Notes

- **File to update**: `src/tax/pph17-progressive.ts`
- **Function to modify/create**: `calculateProgressiveTax()`, `calculateDecemberReconciliation()`
- **Data source to query**: `payroll.annual_gross`, `payroll.monthly_tax_withheld` (Supabase)
- **Update frequency**: Static unless UU PPh amended; last changed 2009
- **Legion action**: Can compute December adjustments automatically; can flag under/over-withholding

## Monetization Angle

- Progressive tax engine is core to accurate payroll SaaS
- December "tax settlement" feature differentiates from simple payroll tools
- Bundle with e-Bupot for complete annual reconciliation workflow

## Sources and Cross-References

- Official URL: https://ortax.org/mengenal-tarif-pph-pasal-17-dalam-menghitung-pph-21
- UU PPh No. 36/2008 Pasal 17
- Related: 020-pph21-ter-pmk168-2023 (monthly TER)
- Related: 021-ptkp-2024-pmk101-2016 (PTKP values)
