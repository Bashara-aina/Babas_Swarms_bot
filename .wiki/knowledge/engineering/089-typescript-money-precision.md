---
source_id: 089
title: "TypeScript Financial Calculation Precision with Decimal.js"
source_type: ENGINEERING
authority: INDUSTRY
url: "https://dev.to/benjamin_renoux/financial-precision-in-javascript-handle-money-without-losing-a-cent-1chc"
last_verified: "2026-04-11"
tags: [typescript, decimal.js, financial, money, precision, payroll, pph21]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# TypeScript Financial Calculation Precision with Decimal.js

## Why This Matters for cekwajar.id
cekwajar.id calculates:
- **PPH 21** (income tax) — wrong calculation = user pays wrong tax
- **BPJS contributions** — wrong amounts = legal non-compliance  
- **Take-home pay** — rounding errors = employee disputes

JavaScript's native `Number` type uses floating-point arithmetic. `0.1 + 0.2 = 0.30000000000000004`. For financial calculations, this is **unacceptable**.

## Core Knowledge

### The Problem with Number
```typescript
// WRONG - Float precision issues
const a = 0.1;
const b = 0.2;
console.log(a + b); // 0.30000000000000004

// WRONG - Large number precision loss
const salary = 15000000.00;
console.log(salary * 1.05); // 15749999.999999998

// WRONG - Currency operations
const deduction = 0.1;
const gross = 10000000;
console.log(gross - (gross * deduction)); // 999999.9999999999
```

### Solution: Decimal.js
```bash
npm install decimal.js
```

### Basic Usage
```typescript
import Decimal from 'decimal.js';

// Enable precise mode
Decimal.set({ precision: 20, rounding: Decimal.ROUND_HALF_UP });

// PPH 21 calculation example
function calculatePTKP(yearlyIncome: number): number {
  const ptkp = new Decimal(yearlyIncome);
  // PTKP 2024 for unmarried without dependents: Rp 54,000,000
  const PTKP_SINGLE = new Decimal(54000000);
  return ptkp.minus(PTKP_SINGLE).toNumber();
}

function calculateTaxableIncome(yearlyIncome: number): number {
  const ptkpDeduction = new Decimal(54000000);
  const ptkp = new Decimal(yearlyIncome).minus(ptkpDeduction);
  
  if (ptkp.lte(0)) return 0;
  
  // Progressive tax rates 2024
  let tax = new Decimal(0);
  
  // 5% for first Rp 60,000,000
  const bracket1 = new Decimal(60000000);
  const taxable1 = Decimal.min(ptkp, bracket1);
  tax = tax.plus(taxable1.times(0.05));
  
  // 15% for next Rp 190,000,000 (60M - 250M)
  if (ptkp.gt(bracket1)) {
    const bracket2 = new Decimal(190000000);
    const remaining = Decimal.min(ptkp.minus(bracket1), bracket2);
    tax = tax.plus(remaining.times(0.15));
  }
  
  // 25% for next Rp 250,000,000 (250M - 500M)
  if (ptkp.gt(bracket1.plus(bracket2))) {
    const bracket3 = new Decimal(250000000);
    const remaining = Decimal.min(
      ptkp.minus(bracket1).minus(bracket2),
      bracket3
    );
    tax = tax.plus(remaining.times(0.25));
  }
  
  // 30% for next Rp 500,000,000 (500M - 5B)
  if (ptkp.gt(bracket1.plus(bracket2).plus(bracket3))) {
    const bracket4 = new Decimal(4500000000);
    const remaining = Decimal.min(
      ptkp.minus(bracket1).minus(bracket2).minus(bracket3),
      bracket4
    );
    tax = tax.plus(remaining.times(0.30));
  }
  
  // 35% above 5B
  if (ptkp.gt(5000000000)) {
    const remaining = ptkp.minus(5000000000);
    tax = tax.plus(remaining.times(0.35));
  }
  
  return tax.toNumber();
}
```

### BPJS Calculation
```typescript
import Decimal from 'decimal.js';

interface BPJSContributions {
  kesehatan: number;
  ketenagakerjaan: { jht: number; jp: number; jkk: number; jkm: number };
}

function calculateBPJS(monthlySalary: number): BPJSContributions {
  Decimal.set({ precision: 20, rounding: Decimal.ROUND_HALF_UP });
  
  const salary = new Decimal(monthlySalary);
  const maxSalary = new Decimal(12000000); // Max for BPJS Kesehatan 2024
  
  // Actual salary for contribution (capped at max)
  const actualSalary = Decimal.min(salary, maxSalary);
  
  // Rates 2024
  // BPJS Kesehatan: 5% (1% employee, 4% employer) - for checking
  // For now we show employee portion
  const kesehatanRate = new Decimal(0.01); // 1% employee
  
  // BPJS Ketenagakerjaan
  const jhtRate = new Decimal(0.02); // 2% employee
  const jpRate = new Decimal(0.01); // 1% employee  
  const jkkRate = new Decimal(0.0024); // 0.24% employee (admin fee)
  const jkmRate = new Decimal(0.0003); // 0.03% employee
  
  return {
    kesehatan: actualSalary.times(kesehatanRate).toNumber(),
    ketenagakerjaan: {
      jht: actualSalary.times(jhtRate).toNumber(),
      jp: actualSalary.times(jpRate).toNumber(),
      jkk: actualSalary.times(jkkRate).toNumber(),
      jkm: actualSalary.times(jkmRate).toNumber(),
    },
  };
}
```

### Utility Functions
```typescript
// lib/money.ts
import Decimal from 'decimal.js';

Decimal.set({
  precision: 20,
  rounding: Decimal.ROUND_HALF_UP,
  toExpNeg: -9,
  toExpPos: 21,
});

/**
 * Add two monetary values
 */
export function addMoney(a: number, b: number): number {
  return new Decimal(a).plus(b).toNumber();
}

/**
 * Subtract two monetary values
 */
export function subtractMoney(a: number, b: number): number {
  return new Decimal(a).minus(b).toNumber();
}

/**
 * Multiply monetary value by a factor (e.g., tax rate)
 */
export function multiplyMoney(value: number, factor: number): number {
  return new Decimal(value).times(factor).toNumber();
}

/**
 * Divide monetary value
 */
export function divideMoney(value: number, divisor: number): number {
  return new Decimal(value).dividedBy(divisor).toNumber();
}

/**
 * Round to nearest Rupiah (no decimals)
 */
export function roundToRupiah(value: number): number {
  return new Decimal(value)
    .toDecimalPlaces(0, Decimal.ROUND_HALF_UP)
    .toNumber();
}

/**
 * Format as Indonesian Rupiah
 */
export function formatRupiah(value: number): string {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}
```

## Exact Formulas / Numbers (if applicable)

### PPH 21 Brackets 2024
| Taxable Income (Yearly) | Rate |
|------------------------|------|
| 0 - Rp 60,000,000 | 5% |
| Rp 60,000,001 - Rp 250,000,000 | 15% |
| Rp 250,000,001 - Rp 500,000,000 | 25% |
| Rp 500,000,001 - Rp 5,000,000,000 | 30% |
| > Rp 5,000,000,000 | 35% |

### PTKP 2024
| Status | PTKP Value |
|--------|------------|
| TK/0 (Unmarried, no dependents) | Rp 54,000,000 |
| TK/1 | Rp 58,500,000 |
| K/0 (Married, no dependents) | Rp 58,500,000 |
| K/1 | Rp 63,000,000 |
| K/2 | Rp 67,500,000 |
| K/3 | Rp 72,000,000 |

## Edge Cases and Common Mistakes

### Common Mistakes
1. **Using Number for currency**: `0.1 + 0.2 !== 0.3` in JavaScript
2. **Wrong rounding mode**: Always use `ROUND_HALF_UP` for currency
3. **Not capping salaries**: BPJS has max salary caps
4. **Integer overflow**: Large numbers lose precision (use string if > 2^53)
5. **Floating point in JSON**: Never store money as JSON floats

### TypeScript Strict Mode Setup
```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictPropertyInitialization": true,
    "exactOptionalPropertyTypes": true
  }
}
```

## cekwajar.id Implementation Notes

- **File to update**: `lib/money.ts`, `lib/tax.ts`, `lib/bpjs.ts`
- **Function to modify/create**: `calculateTaxableIncome()`, `calculateBPJS()`, all money operations
- **Data source to query**: Employee salary data from database
- **Update frequency**: Per payroll run
- **Legion action**: Can implement calculations, needs Bashara review for tax regulation compliance

## Monetization Angle
Accurate tax and contribution calculations:
- Prevents legal non-compliance penalties
- Builds trust with HR/finance departments
- Critical differentiator vs spreadsheet-based solutions

## Sources and Cross-References
- Decimal.js: https://github.com/MikeMcl/decimal.js
- PPH 21 Rates: DJP Kemenkeu 2024
- BPJS Rates: BP Jamsostek 2024
