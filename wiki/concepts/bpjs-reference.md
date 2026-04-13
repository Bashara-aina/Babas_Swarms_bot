---
title: BPJS Reference Indonesia
type: concept
status: active
tags: [bpjs-kesehatan, bpjs-ketenagakerjaan, jht, jp, jkk, jkm, jkp, kesehatan, tenaga-kerja, payroll, iuran, klaim, sanksi, integrasi, cekwajar]
created: 2026-04-13
updated: 2026-04-13
summary: BPJS is Indonesia's mandatory social security system covering health (BPJS Kesehatan) and employment insurance (BPJS Ketenagakerjaan). The system requires 5.7% JHT + 3% JP + employer-paid JKK/JKM contributions from salaries, all subject to caps that change annually.
wikilinks:
  - [[labor-law-indonesia]]
  - [[tax-indonesia]]
  - [[cekwajar-id]]
  - [[market-data-indonesia]]
confidence: high
source: research
---

# BPJS Reference Indonesia

## TL;DR

BPJS (Badan Penyelenggara Jaminan Sosial) is Indonesia's mandatory social security system comprising BPJS Kesehatan (health insurance) and BPJS Ketenagakerjaan (employment insurance). For cekwajar.id's Wajar Slip tool, the critical calculations are the 6-component BPJS deduction engine: JHT employee (2%) + employer (3.7%), JP employee (1%) + employer (2%), plus employer-paid JKK (0.24–1.74%) and JKM (0.30%). All component calculations use salary caps — JP capped at IDR 9,559,600/month (2023 figure, updated annually) and BPJS Kesehatan capped at IDR 12,000,000/month. PMK 168/2023 and PP 46/2015 / PP 45/2015 form the regulatory basis for these calculations.

---

## 1. BPJS Ketenagakerjaan (Employment Insurance)

### 1.1 The 6-Component System

BPJS Ketenagakerjaan comprises four programs under one administrator:

| Component | Employee Pays | Employer Pays | Salary Cap | Legal Basis |
|-----------|--------------|---------------|------------|-------------|
| **JHT** (Jaminan Hari Tua) | 2% | 3.7% | None | PP 46/2015 |
| **JP** (Jaminan Pensiun) | 1% | 2% | IDR 9,559,600/month | PP 45/2015 |
| **JKK** (Jaminan Kecelakaan Kerja) | 0% | 0.24–1.74% (risk-based) | None | PP 44/2015 |
| **JKM** (Jaminan Kematian) | 0% | 0.30% | None | PP 44/2015 |

**Critical note for cekwajar.id**: JKK and JKM are employer-only contributions and do NOT appear on employee payslips. Only JHT and JP employee portions are visible as deductions.

### 1.2 JHT Formula

```
JHT_employee = min(gaji_pokok + tunjangan_tetap, salary_no_cap) × 0.02
JHT_employer = min(gaji_pokok + tunjangan_tetap, salary_no_cap) × 0.037
```

**Example** (salary IDR 8,000,000):
- JHT employee: IDR 8,000,000 × 0.02 = **IDR 160,000**
- JHT employer: IDR 8,000,000 × 0.037 = **IDR 296,000**

### 1.3 JP Formula (with Salary Cap)

```
JP_cap = IDR 9,559,600  # Updated annually per Permenaker

JP_employee = min(gaji_pokok, JP_cap) × 0.01
JP_employer = min(gaji_pokok, JP_cap) × 0.02
```

**Example** (salary IDR 10,000,000, cap IDR 9,559,600):
- JP employee: IDR 9,559,600 × 0.01 = **IDR 95,596** (not IDR 100,000)
- JP employer: IDR 9,559,600 × 0.02 = **IDR 191,192**

### 1.4 JKK Risk Classification

JKK rates vary by workplace risk level. Employers self-declare their risk class:

| Risk Class | Rate | Example Industries |
|------------|------|-------------------|
| Very Low (Klasse I) | 0.24% | Office/admin staff |
| Low (Klasse II) | 0.54% | Cashiers, cleaning |
| Medium (Klasse III) | 0.89% | Production operators |
| High (Klasse IV) | 1.27% | Factory workers |
| Very High (Klasse V) | 1.74% | Construction, mining |

**cekwajar.id default**: Use 0.54% (Low risk) as default unless industry indicates otherwise.

### 1.5 Total BPJS Ketenagakerjaan on Payslip

For Wajar Slip's violation detection (V01, V02, V07), the total visible BPJS Ketenagakerjaan deduction is:

```
total_bpjs_tk_employee = JHT_employee + JP_employee
                        = (salary × 0.02) + (min(salary, JP_cap) × 0.01)
```

**Combined rate**: For salaries below the JP cap: `salary × 0.03`. For salaries above cap: `min(salary, JP_cap) × 0.03`.

---

## 2. BPJS Kesehatan (Health Insurance)

### 2.1 Rates and Caps

| Component | Rate | Salary Cap | Legal Basis |
|-----------|------|------------|------------|
| Employee contribution | 1% | IDR 12,000,000 | Perpres 82/2018 |
| Employer contribution | 4% | IDR 12,000,000 | Perpres 82/2018 |

**Formula**:
```
BPJS_Kes_employee = min(gaji_pokok + tunjangan_tetap, IDR 12,000,000) × 0.01
```

**Example** (salary IDR 10,000,000):
- Employee: IDR 10,000,000 × 0.01 = **IDR 100,000**

**Example** (salary IDR 15,000,000):
- Employee: IDR 12,000,000 × 0.01 = **IDR 120,000** (capped)

### 2.2 BPJS Kesehatan Cap Update History

The salary cap for BPJS Kesehatan has been updated several times:
- 2015: IDR 4,000,000
- 2016: IDR 5,000,000
- 2018: IDR 10,000,000
- 2020: IDR 12,000,000 (current)

**cekwajar.id implementation**: Hard-code IDR 12,000,000 with `effective_date` field for future updates.

---

## 3. Complete 6-Component Calculation Engine

From block_01_verdict_algorithm.md, the complete formula for Wajar Slip's payslip decoder:

```python
def calculate_bpjs_6_component(gross_salary: int, jkk_rate: float = 0.0054) -> dict:
    """
    Calculate all 6 BPJS components for Indonesian payslip verification.
    All rates per current regulations (PP 46/2015, PP 45/2015, PP 44/2015, Perpres 82/2018).
    
    Args:
        gross_salary: Monthly gross salary (gaji pokok + fixed allowances)
        jkk_rate: JKK rate based on risk class (default 0.54% for low-risk)
    
    Returns:
        Dictionary with all 6 components and totals
    """
    JP_CAP = 9_559_600  # Updated annually
    KESEHATAN_CAP = 12_000_000
    
    # JHT (Jaminan Hari Tua) - PP 46/2015
    jht_employee = gross_salary * 0.02
    jht_employer = gross_salary * 0.037
    
    # JP (Jaminan Pensiun) - PP 45/2015, capped
    capped_for_jp = min(gross_salary, JP_CAP)
    jp_employee = capped_for_jp * 0.01
    jp_employer = capped_for_jp * 0.02
    
    # JKK (Jaminan Kecelakaan Kerja) - employer only, PP 44/2015
    jkk_employer = gross_salary * jkk_rate
    
    # JKM (Jaminan Kematian) - employer only, PP 44/2015
    jkm_employer = gross_salary * 0.003
    
    # BPJS Kesehatan - Perpres 82/2018, capped
    capped_for_kes = min(gross_salary, KESEHATAN_CAP)
    kesehatan_employee = capped_for_kes * 0.01
    kesehatan_employer = capped_for_kes * 0.04
    
    return {
        "jht": {"employee": round(jht_employee), "employer": round(jht_employer)},
        "jp": {"employee": round(jp_employee), "employer": round(jp_employer), "capped": capped_for_jp < gross_salary},
        "jkk": {"employer": round(jkk_employer)},
        "jkm": {"employer": round(jkm_employer)},
        "kesehatan": {"employee": round(kesehatan_employee), "employer": round(kesehatan_employer)},
        "total_employee_visible": round(jht_employee + jp_employee + kesehatan_employee),
        "total_employer": round(jht_employer + jp_employer + jkk_employer + jkm_employer + kesehatan_employer)
    }
```

---

## 4. Violation Detection (V-Codes)

From master_analysis_cekwajar.md Section 4.3, the following violations are detectable:

| Code | Violation | Detection Logic |
|------|-----------|-----------------|
| **V01** | BPJS JHT tidak dipotong | Extracted JHT = 0 AND salary > 0 |
| **V02** | BPJS underpaid | Extracted JHT < (0.02 × salary × 0.95) |
| **V05** | BPJS Kesehatan tidak ada | Extracted Kes = 0 AND salary > 0 |
| **V07** | BPJS JP tidak ada | Extracted JP = 0 AND salary > 0 AND age < 56 |

**Note**: V03 (PPh21 missing), V04 (PPh21 underpaid), and V06 (UMK violation) are tax/labor law violations, not purely BPJS.

---

## 5. Salary Cap Update Mechanism

BPJS salary caps change annually. The implementation must use a rate table with `effective_date`:

```sql
CREATE TABLE bpjs_rate_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    component TEXT NOT NULL,  -- 'JP' or 'KESEHATAN'
    cap_amount INTEGER NOT NULL,
    effective_date DATE NOT NULL,
    source_regulation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Query current rates
SELECT cap_amount FROM bpjs_rate_schedule 
WHERE component = 'JP' 
AND effective_date <= CURRENT_DATE 
ORDER BY effective_date DESC 
LIMIT 1;
```

**cekwajar operational requirement**: Check Kemnaker/BPJS website quarterly for regulatory changes. Rate changes require manual validation before deployment — no automated rate updates.

---

## 6. Regulatory Reference Table

| Regulation | What It Covers | Key Numbers |
|------------|-----------------|-------------|
| PP 46/2015 | JHT rates | Employee 2%, Employer 3.7% |
| PP 45/2015 | JP rates + cap | Employee 1%, Employer 2%, Cap IDR 9,559,600 |
| PP 44/2015 | JKK/JKM rates | JKK 0.24–1.74%, JKM 0.30% (employer only) |
| Perpres 82/2018 | BPJS Kesehatan | Employee 1%, Employer 4%, Cap IDR 12,000,000 |
| PMK 168/2023 | TER method for PPh21 | Applied after gross → PTKP → taxable income |

---

## Related Articles

- [[labor-law-indonesia]] — Employment law basis for mandatory BPJS enrollment
- [[tax-indonesia]] — PPh21 calculations that interact with gross salary before BPJS
- [[market-data-indonesia]] — Market salary data for Wajar Gaji benchmarks
- [[cekwajar-id]] — Project using these calculations in Wajar Slip
