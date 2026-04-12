---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/tax/029-pph21-direksi-komisaris-tidak-tetap.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:01.522302"
}
---

---
source_id: 029
title: "PPh 21 Direksi Komisaris Tidak Tetap - Tarif Pasal 17"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://ortax.org/penghitungan-pph-pasal-21-atas-anggota-dewan-komisaris-atau-dewan-pengawas"
last_verified: "2026-04-11"
tags: [pph21, direksi, komisaris, dewan-komisaris, pasal-17]
cekwajar_impact: HIGH
legion_can_act: YES
---

# PPh 21 Direksi Komisaris Tidak Tetap - Tarif Pasal 17

## Why This Matters for cekwajar.id
Board members (direksi/komisaris) who are **not employees** receive irregular income and are taxed using **different rules** — directly using Pasal 17 progressive rates (not TER). This is a common calculation error in startup/corporate payroll systems.

## Core Knowledge

**Two types of board member taxation:**

### 1. Board Member Who is Also Fixed Employee
- Receives regular salary → use **TER Bulanan** like normal employee
- Taxed together with their employee income

### 2. Board Member Who is NOT an Employee (non-fixed)
- Receives irregular/occasional payments → use **Pasal 17 progressive directly**
- DPP (dasar pengenaan pajak) = 50% of gross income per payment
- No cumulative calculation across payments throughout year

**Key difference:**
| Type | TER Applicable | Calculation Method |
|------|---------------|-------------------|
| Fixed employee + board | Yes (Jan–Nov) | TER × monthly gross |
| Non-fixed board only | No (always Pasal 17) | 50% × DPP × progressive rate |

**Kode Objek Pajak:**
- 21-100-10: For non-fixed board members

**Progressive rates (Pasal 17):**
- 5% for PKP up to Rp 60M
- 15% for Rp 60M–250M
- 25% for Rp 250M–500M
- 30% for above Rp 500M

## Exact Formulas / Numbers (if applicable)

```typescript
// Non-fixed board member tax calculation
interface BoardMemberTaxResult {
  grossIncome: number;
  dpp: number;  // 50% of gross
  pkp: number;
  taxAmount: number;
}

function calculateNonFixedBoardTax(
  grossPerPayment: number,
  hasNPWP: boolean = true
): BoardMemberTaxResult {
  const dpp = grossPerPayment * 0.5;
  const pkp = dpp; // No PTKP deduction for non-employee
  const rate = getProgressiveRate(pkp);
  const adjustedRate = hasNPWP ? rate : rate * 1.20;
  
  const taxAmount = Math.round(pkp * adjustedRate);
  
  return {
    grossIncome: grossPerPayment,
    dpp,
    pkp,
    taxAmount
  };
}

function getProgressiveRate(pkp: number): number {
  if (pkp <= 60_000_000) return 0.05;
  if (pkp <= 250_000_000) return 0.15;
  if (pkp <= 500_000_000) return 0.25;
  return 0.30;
}

// For fixed employee board member
function calculateFixedBoardWithEmployeeTax(
  monthlyBoardFee: number,
  monthlySalary: number,
  ptkpCode: string,
  terTable: TERTable
): number {
  const combinedGross = monthlyBoardFee + monthlySalary;
  const terRate = lookupTERForGross(combinedGross, terTable);
  return Math.round(combinedGross * terRate);
}
```

## Edge Cases and Common Mistakes

1. **Confusing fixed vs non-fixed board**: Board who attends meetings regularly may still be "non-fixed" for tax purposes
2. **Applying TER to non-fixed board**: TER only applies to fixed employees; non-fixed board uses Pasal 17 directly
3. **Forgetting 50% DPP**: Non-fixed board uses only 50% of income as taxable base
4. **Not applying NPWP surcharge**: Non-NPWP board members get 20% higher rates
5. **Cumulative vs per-payment**: Each payment calculated separately for non-fixed board (not cumulative annual)

## cekwajar.id Implementation Notes

- **File to update**: `src/tax/board-member-calculator.ts`
- **Function to modify/create**: `calculateNonFixedBoardTax()`, `calculateFixedBoardMemberTax()`
- **Data source to query**: `board_members.board_fee`, `board_members.is_fixed_employee` (Supabase)
- **Update frequency**: Per meeting/payment event for non-fixed; monthly for fixed
- **Legion action**: Can auto-detect board member type; can calculate tax per payment event

## Monetization Angle

- Board member compensation is high-value → accurate calculation is critical
- Startups with founding boards often have complex compensation structures
- Professional services pricing for corporate clients with board fee calculation needs

## Sources and Cross-References

- Official URL: https://ortax.org/penghitungan-pph-pasal-21-atas-anggota-dewan-komisaris-atau-dewan-pengawas
- PMK 168/2023
- Related: 022-pph17-pasal-17-progresif (progressive rates)
