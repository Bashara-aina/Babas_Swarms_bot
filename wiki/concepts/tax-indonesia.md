---
title: Tax Indonesia PPh 21
type: concept
status: active
tags: [pph21, pph17, ptkp, ter, biaya-jabatan, bonus, thr, natura, npwp, pajak, indonesia, bpjs, labor-law, cekwajar, pmk168]
created: 2026-04-13
updated: 2026-04-13
summary: "Indonesian PPh 21 (income tax on employment) uses two calculation methods: TER (Tarif Efektif Rata-rata) for monthly withholding per PMK 168/2023, and progressive rates per UU HPP No.7/2021 (amending UU 36/2008 Pasal 17) for December true-up and final reconciliation. TER simplifies monthly calculation by using pre-computed effective rates by PTKP category, but December requires full progressive recalculation with credit for all TER paid."
wikilinks:
  - [[bpjs-reference]]
  - [[labor-law-indonesia]]
  - [[cekwajar-id]]
  - [[cekwajar-verdict-engine]]
confidence: high
source: research
---

# Tax Indonesia PPh 21

## TL;DR

Indonesian PPh 21 (income tax on employment) is calculated using two systems: the TER (Tarif Efektif Rata-rata) method per PMK 168/2023 for monthly withholding — where tax = gross × applicable TER rate based on PTKP category (A/B/C) — and the progressive bracket method per UU HPP No.7/2021 for December true-up reconciliation. Key deductions before tax: PTKP (PTKP status × annual, ranging IDR 54M-72M), Biaya Jabatan (5% of gross, max IDR 500K/month), and if applicable, pension contributions. Monthly TER is an approximation; December reconciles using full progressive rates with credit for all TER paid Jan-Nov.

---

## 1. PTKP (Penghasilan Tidak Kena Pajak)

### 1.1 PTKP Values

PTKP establishes the non-taxable income threshold. Rates per PMK 101/PMK.010/2016 (unchanged since 2016):

| Status | Kode | Annual PTKP | Monthly Equivalent |
|--------|------|-------------|-------------------|
| Tidak Kawin, 0 tanggungan | TK/0 | IDR 54,000,000 | IDR 4,500,000 |
| Tidak Kawin, 1 tanggungan | TK/1 | IDR 58,500,000 | IDR 4,875,000 |
| Tidak Kawin, 2 tanggungan | TK/2 | IDR 63,000,000 | IDR 5,250,000 |
| Tidak Kawin, 3 tanggungan | TK/3 | IDR 67,500,000 | IDR 5,625,000 |
| Kawin, 0 tanggungan | K/0 | IDR 58,500,000 | IDR 4,875,000 |
| Kawin, 1 tanggungan | K/1 | IDR 63,000,000 | IDR 5,250,000 |
| Kawin, 2 tanggungan | K/2 | IDR 67,500,000 | IDR 5,625,000 |
| Kawin, 3 tanggungan | K/3 | IDR 72,000,000 | IDR 6,000,000 |

**Tanggungan definition**: Children (max 3) who live with taxpayer, have no independent income, and are fully supported. Adopted children count.

### 1.2 PTKP Selection Logic

```python
def get_ptkp_values(ptkp_status: str, spouse_working: bool = False) -> dict:
    """
    Return annual and monthly PTKP based on status.
    
    If spouse is also working and income is merged (K/I), PTKP is doubled
    for the spouse portion (K/I/0 = TK/0 × 2, etc.).
    """
    ptkp_annual_base = {
        'TK/0': 54_000_000, 'TK/1': 58_500_000, 'TK/2': 63_000_000, 'TK/3': 67_500_000,
        'K/0': 58_500_000, 'K/1': 63_000_000, 'K/2': 67_500_000, 'K/3': 72_000_000
    }.get(ptkp_status, 54_000_000)
    
    if spouse_working:
        # K/I status: spouse PTKP is added separately
        ptkp_annual = ptkp_annual_base + 54_000_000
    else:
        ptkp_annual = ptkp_annual_base
    
    return {
        'annual': ptkp_annual,
        'monthly': ptkp_annual / 12
    }
```

---

## 2. TER Method (Monthly Withholding)

### 2.1 TER Concept

PMK 168/2023 introduced TER (Tarif Efektif Rata-rata) to simplify monthly PPh 21 calculation. Instead of applying progressive brackets monthly, employers use pre-computed effective rates.

**Three TER Categories**:

| Category | PTKP Status | Annual PTKP |
|----------|-------------|-------------|
| **A** | TK/0, TK/1, K/0 | ≤ IDR 58,500,000 |
| **B** | TK/2, K/1 | IDR 58,500,001 – 67,500,000 |
| **C** | TK/3, K/2, K/3 | > IDR 67,500,000 |

### 2.2 TER Tables (PMK 168/2023 Lampiran A/B/C)

**Category A (PTKP TK/0, TK/1, K/0)**:

| Gross Monthly (IDR) | TER % |
|---------------------|-------|
| 0 – 4,500,000 | 0% |
| 4,500,001 – 5,000,000 | 0.25% |
| 5,000,001 – 6,000,000 | 0.50% |
| 6,000,001 – 7,000,000 | 0.75% |
| 7,000,001 – 8,000,000 | 1.00% |
| 8,000,001 – 9,000,000 | 1.50% |
| 9,000,001 – 10,000,000 | 2.00% |
| 10,000,001 – 12,000,000 | 2.50% |
| 12,000,001 – 15,000,000 | 3.00% |
| 15,000,001 – 18,000,000 | 3.50% |
| 18,000,001 – 22,000,000 | 4.00% |
| 22,000,001 – 25,000,000 | 4.50% |
| 25,000,001 – 30,000,000 | 5.00% |
| 30,000,001 – 35,000,000 | 6.00% |
| 35,000,001 – 40,000,000 | 7.00% |
| 40,000,001 – 45,000,000 | 8.00% |
| 45,000,001 – 50,000,000 | 9.00% |
| > 50,000,000 | 10.00% |

**Category B (PTKP TK/2, K/1)** — slightly lower rates due to higher PTKP.

**Category C (PTKP TK/3, K/2, K/3)** — lowest rates.

### 2.3 TER Calculation Implementation

```python
TER_TABLE_A = [
    (4_500_000, 0.0),
    (5_000_000, 0.0025),
    (6_000_000, 0.005),
    (7_000_000, 0.0075),
    (8_000_000, 0.01),
    (9_000_000, 0.015),
    (10_000_000, 0.02),
    (12_000_000, 0.025),
    (15_000_000, 0.03),
    (18_000_000, 0.035),
    (22_000_000, 0.04),
    (25_000_000, 0.045),
    (30_000_000, 0.05),
    (35_000_000, 0.06),
    (40_000_000, 0.07),
    (45_000_000, 0.08),
    (50_000_000, 0.09),
    (float('inf'), 0.10),
]

def get_ter_category(ptkp_annual: int) -> str:
    """Determine TER category based on annual PTKP."""
    if ptkp_annual <= 58_500_000:
        return 'A'
    elif ptkp_annual <= 67_500_000:
        return 'B'
    else:
        return 'C'

def calculate_ter_rate(gross_monthly: int, category: str) -> float:
    """Look up TER rate from table based on gross and category."""
    table = TER_TABLES[category]  # A, B, or C
    for threshold, rate in table:
        if gross_monthly <= threshold:
            return rate
    return 0.10  # Default for >50M

def calculate_pph21_ter(gross_monthly: int, ptkp_annual: int) -> int:
    """
    Calculate monthly PPh 21 using TER method per PMK 168/2023.
    """
    category = get_ter_category(ptkp_annual)
    ter_rate = calculate_ter_rate(gross_monthly, category)
    return round(gross_monthly * ter_rate)
```

### 2.4 TER Example

```
Scenario: K/1 status (PTKP = IDR 63,000,000/year), gross = IDR 10,000,000/month

Category: B (PTKP between 58.5M and 67.5M)
TER for 10M (Category B): 2.0%
PPh21 = 10,000,000 × 0.02 = IDR 200,000/month
```

---

## 3. Progressive Method (December True-Up)

### 3.1 When Progressive Is Used

1. **December reconciliation**: True-up using full progressive rates with credit for TER paid
2. **Final employment month**: When employment terminates
3. **Employees with multiple employers**: Combined income calculation
4. **Bonus/THR month**: Combined with regular salary

### 3.2 Progressive Tax Brackets

Per UU HPP No.7/2021 (amending UU 36/2008 Pasal 17):

| Bracket | Annual PKP (IDR) | Rate |
|---------|-----------------|------|
| I | 0 – 60,000,000 | 5% |
| II | 60,000,001 – 250,000,000 | 15% |
| III | 250,000,001 – 500,000,000 | 25% |
| IV | 500,000,001 – 5,000,000,000 | 30% |
| V | > 5,000,000,000 | 35% |

### 3.3 Progressive Calculation Implementation

```python
BRACKET_THRESHOLDS = [0, 60_000_000, 250_000_000, 500_000_000, 5_000_000_000]
BRACKET_RATES = [0.05, 0.15, 0.25, 0.30, 0.35]

def calculate_progressive_tax(pkp_annual: int, has_npwp: bool = True) -> int:
    """
    Calculate annual PPh 21 using stepped progressive rates.
    Only income above each threshold is taxed at the higher rate.
    """
    tax = 0
    remaining_pkp = pkp_annual
    
    for i, rate in enumerate(BRACKET_RATES):
        if remaining_pkp <= 0:
            break
        
        lower = BRACKET_THRESHOLDS[i]
        upper = BRACKET_THRESHOLDS[i + 1] if i < len(BRACKET_THRESHOLDS) - 1 else float('inf')
        
        taxable_in_bracket = min(remaining_pkp, upper - lower)
        tax += taxable_in_bracket * rate
        remaining_pkp -= taxable_in_bracket
    
    if not has_npwp:
        tax *= 1.20  # 20% surcharge for missing NPWP
    
    return round(tax)
```

### 3.4 December True-Up Formula

```python
def calculate_december_trueup(
    monthly_gross: list[int],  # Jan through Nov gross
    ptkp_annual: int,
    has_npwp: bool,
    has_pension: bool = False,
    pension_contribution_monthly: int = 0
) -> dict:
    """
    December true-up calculation:
    1. Sum annual gross
    2. Deduct biaya jabatan (5%, max 500K/month)
    3. Deduct pension if applicable
    4. Apply PTKP
    5. Calculate progressive tax
    6. Credit TER paid Jan-Nov
    7. Result is December withholding
    """
    # Annualize
    annual_gross = sum(monthly_gross)
    
    # Biaya jabatan: 5% of each month, capped at 500K/month, 6M/year
    annual_biaya_jabatan = min(
        sum(min(g * 0.05, 500_000) for g in monthly_gross),
        6_000_000
    )
    
    # Pension deduction (if applicable)
    annual_pension = pension_contribution_monthly * 12
    annual_pension = min(annual_pension, 2_400_000)  # Cap per year
    
    # Calculate PKP
    pkp_annual = max(
        annual_gross - annual_biaya_jabatan - annual_pension - ptkp_annual,
        0
    )
    
    # Progressive tax for full year
    annual_progressive_tax = calculate_progressive_tax(pkp_annual, has_npwp)
    
    # TER paid Jan-Nov
    category = get_ter_category(ptkp_annual)
    ter_paid = sum(
        calculate_ter_rate(g, category) * g
        for g in monthly_gross
    )
    
    # December adjustment
    december_tax = annual_progressive_tax - round(ter_paid)
    
    return {
        'annual_gross': annual_gross,
        'biaya_jabatan': annual_biaya_jabatan,
        'pension_deduction': annual_pension,
        'pkp_annual': pkp_annual,
        'annual_progressive_tax': annual_progressive_tax,
        'ter_paid_jan_nov': round(ter_paid),
        'december_withholding': max(december_tax, 0),
        'is_refund': december_tax < 0
    }
```

---

## 4. Biaya Jabatan (5% Deduction)

### 4.1 Rules

- **Rate**: 5% of gross monthly salary
- **Monthly cap**: IDR 500,000
- **Annual cap**: IDR 6,000,000
- **Purpose**: Standard expense deduction for employment-related costs
- **Applicable to**: Pegawai tetap (permanent employees) only

### 4.2 Example

```
Gross = IDR 8,000,000/month
Biaya Jabatan = min(8,000,000 × 0.05, 500,000) = min(400,000, 500,000) = IDR 400,000

Taxable income = 8,000,000 - 400,000 - PTKP(K/1) 5,250,000 = IDR 2,350,000
```

---

## 5. Special Cases

### 5.1 THR and Bonus (Penghasilan Tidak Teratur)

Per PMK 168/2023, THR and bonus in the same month as regular salary are combined for TER calculation:

```python
def calculate_month_with_thr(
    regular_gross: int,
    thr_amount: int,
    ptkp_annual: int
) -> int:
    """
    When THR is paid in same month as regular salary:
    Combine for TER calculation in that month.
    """
    combined_gross = regular_gross + thr_amount
    return calculate_pph21_ter(combined_gross, ptkp_annual)
```

### 5.2 Non-Resident Foreign Workers (TKA)

| Scenario | Tax Treatment |
|----------|---------------|
| TKA with NPWP | Normal PPh 21 rates |
| TKA without NPWP (≤183 days) | PPh 26: 20% flat on gross |
| Treaty country (e.g., Singapore, Japan) | Reduced treaty rate (10-15%) |

### 5.3 Daily Workers (Pegawai Tidak Tetap)

TER Harian applies to daily-paid workers:

| Daily Gross | TER Rate |
|-------------|----------|
| ≤ IDR 450,000 | 0% |
| IDR 450,001 – 2,500,000 | 0.5% |
| > IDR 2,500,000 | Use Pasal 17 progressive on 50% of daily gross |

---

## 6. Regulatory Reference Table

| Regulation | Subject | Key Point |
|------------|---------|------------|
| UU HPP No.7/2021 | Tax amendment | Updated brackets, removed 35% top bracket ceiling |
| UU 36/2008 Pasal 17 | Progressive rates | 5-bracket progressive system |
| PMK 168/2023 | TER method | Monthly withholding tables by PTKP category |
| PMK 101/2016 | PTKP values | Static since 2016 |
| PMK 66/2023 | Natura | Taxable allowances changed July 2023 |

---

## Related Articles

- [[bpjs-reference]] — Deductions that affect gross salary before PPh21
- [[labor-law-indonesia]] — Employment classification affecting tax treatment
- [[cekwajar-id]] — Project using these calculations
- [[cekwajar-verdict-engine]] — Implementation of TER + progressive in verdict pipeline
