---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/architecture/cekwajar-verdict-engine.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-08T01:00:00.397403"
}
---

---
title: cekwajar-verdict-engine
type: architecture
status: active
tags: [cekwajar, verdict-algorithm, pph21, bpjs, violation-detection, freemium-gate]
created: 2026-04-13
updated: 2026-04-13
summary: The cekwajar.id verdict engine is a 7-stage pipeline that transforms raw payslip data into a compliance verdict. It validates input, calculates PPh21 (TER method + progressive true-up), calculates 6-component BPJS, detects 7 violation types (V01-V07), computes confidence scores, applies freemium gating, and outputs structured verdict JSON.
wikilinks:
  - [[projects/cekwajar-id]]
  - [[concepts/tax-indonesia]]
  - [[concepts/bpjs-reference]]
  - [[concepts/freemium-gate]]
confidence: high
source: implementation
---

# cekwajar Verdict Engine Architecture

## TL;DR

The cekwajar.id verdict engine processes payslip data through a 7-stage pipeline: input validation → PPh21 TER calculation → PPh21 progressive annual true-up → 6-component BPJS calculation → violation detection (V01–V07) → confidence scoring → freemium gate → verdict output. The engine uses PMK 168/2023 TER method for monthly withholding, UU HPP No.7/2021 progressive brackets for December true-up, and PP 46/2015/PP 45/2015 for BPJS. Freemium gating hides IDR shortfall amounts from free users, showing only violation codes.

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    VERDICT ENGINE PIPELINE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  1. INPUT    │───▶│  2. PPh21    │───▶│  3. PPh21    │       │
│  │  VALIDATION │    │  TER CALC    │    │  PROGRESSIVE │       │
│  │              │    │  (PMK 168)   │    │  (UU HPP)    │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                    │               │
│         ▼                   ▼                    ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  4. BPJS     │───▶│  5. VIOLATION│───▶│  6. CONFIDENCE│      │
│  │  6-COMPONENT│    │  DETECTION   │    │  SCORING     │       │
│  │  CALC        │    │  (V01-V07)   │    │              │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                            │                    │
│                                            ▼                    │
│                                   ┌──────────────┐              │
│                                   │  7. FREEMIUM │              │
│                                   │  GATE        │              │
│                                   └──────────────┘              │
│                                            │                    │
│                                            ▼                    │
│                                   ┌──────────────┐              │
│                                   │  8. VERDICT  │              │
│                                   │  OUTPUT JSON │              │
│                                   └──────────────┘              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Stage 1: Input Validation

### 2.1 Required Fields

| Field | Type | Validation |
|-------|------|------------|
| gaji_pokok | integer | > 0 |
| tunjangan | object | ≥ 0 per component |
| ptkp_status | enum | TK/0, TK/1, TK/2, TK/3, K/0, K/1, K/2, K/3 |
| city | string | Must be in UMK database (514 cities) |
| period | object | {month: 1-12, year: 2020-2030} |

### 2.2 Allowance Classification

From payslip input, classify each allowance:

```typescript
interface AllowanceClassification {
  name: string;
  amount: number;
  is_taxable: boolean;      // Subject to PPh21
  is_bpjs_subject: boolean; // Subject to BPJS
  is_umk_relevant: boolean; // Counts toward minimum wage
  is_thr_relevant: boolean; // Counts toward THR calculation
}
```

Default classification (user can override):
- Tunjangan Makan: taxable=true, bpjs=true
- Tunjangan Transport (cash): taxable=true, bpjs=true  
- Tunjangan Transport (natura): taxable=false, bpjs=false
- Tunjangan Keluarga: taxable=true, bpjs=true
- Tunjangan Shift/Lembur: taxable=true, bpjs=false

### 2.3 Gross Salary Calculation

```python
def calculate_gross_salary(gaji_pokok: int, allowances: list[Allowance]) -> int:
    """
    Gross salary for PPh21 and BPJS calculation.
    Only includes allowances marked as bpjs_subject=True.
    """
    gross = gaji_pokok
    for allowance in allowances:
        if allowance.is_bpjs_subject:
            gross += allowance.amount
    return gross
```

---

## 3. Stage 2: PPh21 TER Calculation (Monthly)

### 3.1 TER Method Overview

Per PMK 168/2023, monthly PPh21 for employees uses Tarif Efektif Rata-rata (TER):

```
PPh21_monthly = Gross_Monthly × TER_category
```

TER is determined by PTKP status category:

| TER Category | PTKP Status | Annual PTKP |
|--------------|-------------|-------------|
| A | TK/0, TK/1, K/0 | ≤ IDR 58,500,000 |
| B | TK/2, K/1 | IDR 58,500,001 – 67,500,000 |
| C | TK/3, K/2, K/3 | > IDR 67,500,000 |

### 3.2 TER Table (Category A)

From tax-indonesia.md and PMK 168/2023 Lampiran A:

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

### 3.3 TER Calculation Implementation

```python
def calculate_pph21_ter(gross_monthly: int, ptkp_status: str) -> int:
    """
    Calculate PPh21 using TER method per PMK 168/2023.
    Returns monthly tax withholding amount.
    """
    category = get_ter_category(ptkp_status)
    ter_rate = lookup_ter_rate(gross_monthly, category)
    return round(gross_monthly * ter_rate)
```

---

## 4. Stage 3: PPh21 Progressive True-Up (December)

### 4.1 December True-Up Requirement

TER is an approximation. In December (or final employment month), employers must reconcile using the full progressive rates per UU HPP No.7/2021 and credit all TER paid in prior months.

### 4.2 Progressive Tax Brackets

```python
BRACKETS = [
    (60_000_000, 0.05),      # 5% on first 60M
    (250_000_000, 0.15),     # 15% on 60M-250M  
    (500_000_000, 0.25),     # 25% on 250M-500M
    (5_000_000_000, 0.30),   # 30% on 500M-5B
    (float('inf'), 0.35),     # 35% on >5B
]

def calculate_progressive_tax(annual_pkp: int, has_npwp: bool = True) -> int:
    """
    Calculate annual PPh21 using stepped progressive rates per UU 36/2008 Pasal 17.
    """
    tax = 0
    remaining = annual_pkp
    
    thresholds = [0, 60_000_000, 250_000_000, 500_000_000, 5_000_000_000]
    rates = [0.05, 0.15, 0.25, 0.30, 0.35]
    
    for i in range(len(rates)):
        if remaining <= 0:
            break
        bracket_size = thresholds[i+1] - thresholds[i] if i < len(thresholds)-1 else float('inf')
        taxable_in_bracket = min(remaining, bracket_size)
        tax += taxable_in_bracket * rates[i]
        remaining -= taxable_in_bracket
    
    if not has_npwp:
        tax *= 1.20  # 20% surcharge
    
    return round(tax)
```

### 4.3 December True-Up Formula

```python
def calculate_december_trueup(
    gross_months: list[int],  # Jan-Nov gross
    ptkp_annual: int,
    ptkp_status: str,
    npwp: bool
) -> dict:
    """
    December true-up reconciliation:
    1. Calculate annual taxable income
    2. Apply progressive rates for full year
    3. Credit TER paid Jan-Nov
    4. Result is December withholding (or refund)
    """
    # Step 1: Annual gross + biaya jabatan
    annual_gross = sum(gross_months)
    biaya_jabatan_annual = min(annual_gross * 0.05, 6_000_000)
    pkp_annual = max(annual_gross - ptkp_annual - biaya_jabatan_annual, 0)
    
    # Step 2: Progressive tax for full year
    annual_tax = calculate_progressive_tax(pkp_annual, npwp)
    
    # Step 3: Monthly TER paid
    ter_paid = sum(calculate_pph21_ter(g, ptkp_status) for g in gross_months)
    
    # Step 4: December adjustment
    december_tax = max(annual_tax - ter_paid, 0)
    
    return {
        "annual_gross": annual_gross,
        "biaya_jabatan": biaya_jabatan_annual,
        "pkp_annual": pkp_annual,
        "annual_tax_progressive": annual_tax,
        "ter_paid_jan_nov": ter_paid,
        "december_withholding": december_tax,
        "is_refund": annual_tax < ter_paid
    }
```

---

## 5. Stage 4: BPJS 6-Component Calculation

From [[concepts/bpjs-reference]], the 6 components:

```python
def calculate_bpjs_6_component(gross_salary: int, jkk_rate: float = 0.0054) -> dict:
    JP_CAP = 9_559_600
    KESEHATAN_CAP = 12_000_000
    
    capped_jp = min(gross_salary, JP_CAP)
    capped_kes = min(gross_salary, KESEHATAN_CAP)
    
    return {
        "jht_employee": round(gross_salary * 0.02),
        "jht_employer": round(gross_salary * 0.037),
        "jp_employee": round(capped_jp * 0.01),
        "jp_employer": round(capped_jp * 0.02),
        "jkk_employer": round(gross_salary * jkk_rate),
        "jkm_employer": round(gross_salary * 0.003),
        "kesehatan_employee": round(capped_kes * 0.01),
        "kesehatan_employer": round(capped_kes * 0.04),
        "total_employee_visible": round(gross_salary * 0.02 + capped_jp * 0.01 + capped_kes * 0.01),
    }
```

---

## 6. Stage 5: Violation Detection (V01-V07)

### 6.1 Violation Matrix

From master_analysis_cekwajar.md Section 4.3:

| Code | Violation | Detection Logic | Severity |
|------|-----------|-----------------|----------|
| V01 | BPJS JHT tidak dipotong | extracted_JHT == 0 AND salary > 0 | CRITICAL |
| V02 | BPJS underpaid | extracted_JHT < (0.02 × salary × 0.95) | HIGH |
| V03 | PPh21 tidak dipotong | extracted_PPh21 == 0 AND expected_PPh21 > 50,000 | HIGH |
| V04 | PPh21 kurang dipotong | abs(extracted - expected) > 50,000 | MED |
| V05 | BPJS Kesehatan tidak ada | extracted_Kes == 0 AND salary > 0 | HIGH |
| V06 | Gaji di bawah UMK | gaji_pokok < UMK[city] | CRITICAL |
| V07 | BPJS JP tidak ada | extracted_JP == 0 AND salary > 0 AND age < 56 | MED |

### 6.2 Violation Detection Implementation

```python
def detect_violations(
    extracted: dict,
    calculated: dict,
    gaji_pokok: int,
    city: str,
    age: int
) -> list[dict]:
    violations = []
    
    # V01: Missing JHT
    if extracted.get('jht', 0) == 0 and gaji_pokok > 0:
        violations.append({
            "code": "V01",
            "severity": "CRITICAL",
            "message": "BPJS JHT tidak ditemukan pada slip Anda. Potongan 2% dari gaji pokok wajib dilakukan oleh perusahaan.",
            "regulation": "PP 46/2015"
        })
    
    # V02: JHT underpaid
    expected_jht = gaji_pokok * 0.02
    if extracted.get('jht', 0) < expected_jht * 0.95:
        violations.append({
            "code": "V02", 
            "severity": "HIGH",
            "message": f"BPJS JHT yang dipotong (IDR {extracted['jht']:,}) lebih rendah dari yang seharusnya (IDR {expected_jht:,.0f}).",
            "regulation": "PP 46/2015"
        })
    
    # V03: Missing PPh21
    if extracted.get('pph21', 0) == 0 and calculated['pph21_ter'] > 50_000:
        violations.append({
            "code": "V03",
            "severity": "HIGH", 
            "message": f"PPh21 tidak ditemukan, padahal seharusnya dipotong IDR {calculated['pph21_ter']:,.0f}.",
            "regulation": "UU 36/2008 Pasal 21"
        })
    
    # V04: PPh21 underpaid
    if abs(extracted.get('pph21', 0) - calculated['pph21_ter']) > 50_000:
        diff = extracted.get('pph21', 0) - calculated['pph21_ter']
        violations.append({
            "code": "V04",
            "severity": "MED",
            "message": f"PPh21 berbeda IDR {abs(diff):,} dari perhitungan kami.",
            "regulation": "UU 36/2008 Pasal 21"
        })
    
    # V05: Missing BPJS Kesehatan
    if extracted.get('kesehatan', 0) == 0 and gaji_pokok > 0:
        violations.append({
            "code": "V05",
            "severity": "HIGH",
            "message": "BPJS Kesehatan tidak ditemukan. Potongan 1% wajib dilakukan.",
            "regulation": "Perpres 82/2018"
        })
    
    # V06: Below UMK
    umk = get_umk(city)
    if gaji_pokok < umk:
        violations.append({
            "code": "V06",
            "severity": "CRITICAL",
            "message": f"Gaji pokok Anda (IDR {gaji_pokok:,}) di bawah UMK {city} (IDR {umk:,}).",
            "regulation": "PP 36/2021"
        })
    
    # V07: Missing JP
    if extracted.get('jp', 0) == 0 and gaji_pokok > 0 and age < 56:
        violations.append({
            "code": "V07",
            "severity": "MED",
            "message": "BPJS JP tidak ditemukan. Potongan 1% seharusnya ada.",
            "regulation": "PP 45/2015"
        })
    
    return violations
```

---

## 7. Stage 6: Confidence Scoring

### 7.1 Confidence Factors

```
confidence_score = f(ocr_confidence, data_completeness, calculation_agreement)

Where:
- ocr_confidence: 0.0-1.0 from OCR pipeline (AUTO_ACCEPT=0.92, SOFT_CHECK=0.80, MANUAL_REQUIRED=0.70)
- data_completeness: % of required fields successfully extracted
- calculation_agreement: how closely extracted deductions match calculated values
```

### 7.2 Confidence Levels

| Score | Level | Interpretation |
|-------|-------|----------------|
| 90-100 | High | OCR auto-accepted, all fields match, full confidence |
| 70-89 | Medium-High | OCR soft-check or minor variance |
| 40-69 | Medium | Manual entry or significant variance |
| <40 | Low | Insufficient data for reliable verdict |

---

## 8. Stage 7: Freemium Gate

### 8.1 Freemium Tiers

From master_analysis_cekwajar.md Section 1.2 and req_01_master_prd.md Section 4.4:

| Feature | Free | Basic IDR 29K | Pro IDR 79K |
|---------|------|--------------|-------------|
| PPh21 calculation | ✅ | ✅ | ✅ |
| BPJS calculation | ✅ | ✅ | ✅ |
| Violation codes (V01-V07) | First 1 only | All | All |
| IDR shortfall amounts | ❌ | ✅ | ✅ |
| OCR upload | 1/lifetime | 10/month | Unlimited |
| Audit history | None | 3 months | Unlimited |

### 8.2 Gate Logic

```python
def apply_freemium_gate(verdict: dict, user_tier: str) -> dict:
    """
    Strip sensitive amounts from verdict based on user tier.
    Free users see violation codes only, not IDR amounts.
    """
    if user_tier == "free":
        return {
            **verdict,
            "violations": [
                {"code": v["code"], "severity": v["severity"]}  # No message, no amount
                for v in verdict["violations"]
            ],
            "show_amounts": False
        }
    return {**verdict, "show_amounts": True}
```

---

## 9. Verdict Output Schema

```json
{
  "requestId": "uuid-v4",
  "timestamp": "ISO-8601",
  "status": "VERDICT_GENERATED",
  "verdict": {
    "overall": "COMPLIANT | VIOLATIONS_FOUND | BELOW_UMK",
    "violation_count": 2,
    "critical_count": 1
  },
  "calculations": {
    "gross_salary": 9400000,
    "pph21_ter_monthly": 189000,
    "pph21_progressive_annual": 2268000,
    "bpjs": {
      "jht_employee": 188000,
      "jp_employee": 95596,
      "kesehatan_employee": 94000,
      "total_employee": 377596
    }
  },
  "violations": [
    {
      "code": "V06",
      "severity": "CRITICAL", 
      "message": "Gaji pokok Anda (IDR 3,500,000) di bawah UMK Bekasi (IDR 5,999,443).",
      "regulation": "PP 36/2021"
    }
  ],
  "confidence": {
    "score": 92,
    "level": "HIGH",
    "factors": ["ocr_auto_accept", "all_fields_extracted"]
  },
  "freemium": {
    "gate_applied": false,
    "user_tier": "pro"
  }
}
```

---

## Related Articles

- [[projects/cekwajar-id]] — Project using this engine
- [[concepts/tax-indonesia]] — PPh21 TER and progressive calculation details
- [[concepts/bpjs-reference]] — 6-component BPJS calculation details
- [[concepts/freemium-gate]] — Freemium access control pattern
