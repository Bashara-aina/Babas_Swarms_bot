---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/tax/024-pph21-bonus-thr-penghasilan-tidak-teratur.md",
  "reason": "daily_fast_scan: score=0.200 < 0.3",
  "score": 0.2,
  "quarantined_at": "2026-04-12T01:00:01.526374"
}
---

---
source_id: 024
title: "PPh 21 Bonus dan THR - Penghasilan Tidak Teratur"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://klikpajak.id/blog/pajak-bonus-karyawan/"
last_verified: "2026-04-11"
tags: [pph21, bonus, thr, penghasilan-tidak-teratur, ter, pajak]
cekwajar_impact: HIGH
legion_can_act: YES
---

# PPh 21 Bonus dan THR - Penghasilan Tidak Teratur

## Why This Matters for cekwajar.id
Bonus and THR (Tunjangan Hari Raya) are **irregular income** that must be added to the monthly gross income in the month received, then taxed using the applicable TER rate. Miscalculating this results in wrong tax deduction and employee complaints during holiday seasons.

## Core Knowledge

Since 2024 (PMK 168/2023), bonus and THR are **no longer taxed separately** — they must be combined with regular salary in the month received.

**Key rules:**
- Bonus/THR + regular salary in same month → combined gross income
- Apply TER based on combined income for that month
- December: use Pasal 17 progressive + credit all TER paid Jan–Nov

**TER for bonus/THR month:**
- If combined gross pushes into higher TER bracket, the higher rate applies
- Example: Regular salary Rp8M + Bonus Rp13M = Rp21M combined → TER A at ~4%

**Common bonus types:**
1. Bonus kinerja (performance bonus)
2. Bonus tahunan (annual bonus)  
3. Bonus referral
4. THR (religious holiday allowance)
5. Tantiem (board bonuses)

## Exact Formulas / Numbers (if applicable)

```typescript
// Bonus/THR PPh 21 calculation
interface BonusTaxResult {
  taxOnSalary: number;
  taxOnBonus: number;
  totalTax: number;
  netBonus: number;
}

function calculateBonusTax(
  monthlySalary: number,
  bonusAmount: number,
  ptkpCode: string,
  terTable: TERTable
): BonusTaxResult {
  // Combine for the month received
  const combinedGross = monthlySalary + bonusAmount;
  
  // Get TER for combined income
  const terRate = lookupTERForGross(combinedGross, terTable);
  
  // Separate calculations for transparency
  const taxOnSalary = Math.round(monthlySalary * terRate);
  const taxOnBonus = Math.round(bonusAmount * terRate);
  
  return {
    taxOnSalary,
    taxOnBonus,
    totalTax: taxOnSalary + taxOnBonus,
    netBonus: bonusAmount - taxOnBonus
  };
}

// December reconciliation for bonus
function calculateDecemberWithBonus(
  grossAnnual: number,
  bonusTotal: number,
  biayaJabatan: number,
  iuranPensiun: number,
  ptkpAnnual: number,
  taxesPaidJanToNov: number
): { pkp: number; annualTax: number; adjustment: number } {
  const netoAnnual = grossAnnual + bonusTotal - biayaJabatan - iuranPensiun;
  const pkp = Math.max(0, netoAnnual - ptkpAnnual);
  const annualTax = calculateProgressiveTax(pkp);
  const adjustment = annualTax - taxesPaidJanToNov;
  
  return { pkp, annualTax, adjustment };
}
```

## Edge Cases and Common Mistakes

1. **Treating bonus separately**: Before 2024 could calculate bonus separately; now MUST combine with salary
2. **December bonus not reconciled**: If bonus paid in December, still need December reconciliation using Pasal 17
3. **Not applying correct TER bracket**: Large bonus may push monthly income into higher TER bracket
4. **THR below PTKP threshold**: If total annual income < PTKP, no tax on THR
5. **Multiple bonuses in same year**: Each bonus event is combined with salary in that specific month

## cekwajar.id Implementation Notes

- **File to update**: `src/tax/bonus-thr-calculator.ts`
- **Function to modify/create**: `calculateBonusTax()`, `calculateDecemberWithBonus()`
- **Data source to query**: `payroll.bonus_amount`, `payroll.thr_amount` (Supabase)
- **Update frequency**: Per event (typically annual for THR, random for bonus)
- **Legion action**: Can auto-calculate during payroll; can warn when bonus pushes into higher bracket

## Monetization Angle

- Holiday payroll is high-stress period for HR → premium for accurate auto-calculation
- THR tax miscalculation is a top employee complaint driver
- Bundle with payslip generation for complete bonus/THR workflow

## Sources and Cross-References

- Official URL: https://klikpajak.id/blog/pajak-bonus-karyawan/
- Related: 020-pph21-ter-pmk168-2023 (TER calculation)
- Related: 022-pph17-pasal-17-progresif (December reconciliation)
