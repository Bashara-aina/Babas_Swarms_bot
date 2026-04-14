---
title: Labor Law Indonesia
type: concept
status: active
tags: [labor-law, ketenagakerjaan, pengupahan, ump, umk, bpjs, thr, pesangon, cuti, pkwt, pkwtt, pph21, ptkp, tka, sanksi, indonesia, cekwajar]
created: 2026-04-13
updated: 2026-04-13
summary: "Indonesian labor law centers on UU 13/2003 (primary employment statute) and its implementing regulations. For cekwajar.id's Wajar Slip tool, the critical rules are: PKWT vs PKWTT employment classification, UMK/UMP minimum wage compliance (514 cities, updated annually), 75/25 wage component split (minimum 75% must be base salary), and mandatory benefit calculations including THR (1 month salary after 12 months) and BPJS (5 components)."
wikilinks:
  - [[./concepts/bpjs-reference]]
  - [[./concepts/tax-indonesia]]
  - [[projects/cekwajar-id]]
  - [[./concepts/market-data-indonesia]]
confidence: high
source: research
---

# Labor Law Indonesia

## TL;DR

Indonesian labor law is anchored by UU 13/2003 (Manpower Act) which establishes employment rights, minimum wages, and termination rules. For Wajar Slip's violation detection, the critical rules are: employment classification (PKWT = fixed-term contract max 5 years; PKWTT = permanent), minimum wage compliance (UMK for 514 cities/kabupaten, updated annually each November-December), the 75/25 wage component rule (base salary must be ≥75% of total compensation per PP 36/2021), and mandatory THR calculation. Below-UMK salaries trigger V06 violation regardless of other factors — this is a legal fact, not an estimate.

---

## 1. Employment Classification

### 1.1 PKWT vs PKWTT

| Aspect | PKWT (Kontrak) | PKWTT (Tetap) |
|--------|----------------|---------------|
| Full name | Perjanjian Kerja Waktu Tertentu | Perjanjian Kerja Waktu Tidak Tertentu |
| Duration | Fixed term (max 5 years including extensions) | Indefinite |
| Probation | **Not allowed** (Pasal 59 ayat 3) | Max 3 months (Pasal 60) |
| Extension | Allowed, but total cannot exceed 5 years | N/A |
| Termination compensation | 1 month salary per remaining contract year | Pesangon based on years of service |
| THR | Proportional to contract duration | Full 1 month after 12 months |

**Key legal nuance**: Under UU 13/2003 Pasal 59, probation is explicitly forbidden for PKWT. Any contract designated as PKWT with probation clause is legally invalid — the worker is considered PKWTT from day one.

### 1.2 Contract Duration Limits

Per UU 11/2020 (Cipta Kerja) amending UU 13/2003:
- Maximum total PKWT duration: **5 years** (including all extensions)
- After 5 years, worker must be given PKWTT or the contract is automatically converted
- Extension requires minimum 30-day notice before contract expiry

### 1.3 Outsourcing (Alih Daya)

Workers through outsourcing companies (perusahaan alih daya) must receive待遇 equivalent to in-house workers doing the same job (Pasal 64-66 UU 13/2003). This affects salary comparisons for benchmarking.

---

## 2. Minimum Wage System (UMK/UMP)

### 2.1 UMK vs UMP Hierarchy

Indonesia's minimum wage system operates at two levels:

```
Upah Minimum
├── UMK (Upah Minimum Kabupaten/Kota) — applies to specific kota/kabupaten
└── UMP (Upah Minimum Provinsi) — applies to rest of province

Note: UMK ≥ UMP always. Some provinces have sektoral (sector-specific) minimums
      called UMSP (Provinsi) or UMSK (Kabupaten/Kota) that can be higher.
```

### 2.2 2025 UMK Figures (Reference)

From Kemnaker data used by cekwajar.id:

| City | UMK 2025 (IDR) | vs Jakarta |
|------|----------------|------------|
| Kota Bekasi | 5,999,443 | +24% |
| Kota Depok | 5,195,722 | +8% |
| DKI Jakarta | 4,820,000 | baseline |
| Kota Surabaya | 3,470,000 | -28% |
| Kota Bandung | 3,210,000 | -33% |
| Kota Medan | 3,570,000 | -26% |

### 2.3 UMK Update Cycle

UMK is set annually through this process:
1. **October-November**: Provincial governments collect wage council (dewan pengupahan) recommendations
2. **November-December**: Governors issue UMK decrees (SK Gubernur) for following year
3. **January 1**: New UMK takes effect

**cekwajar.id implementation**: UMK data must be refreshed each December. Use previous year UMK + official inflation adjustment as fallback if new UMK hasn't been published.

### 2.4 UMK Violation Detection (V06)

From master_analysis_cekwajar.md, V06 is triggered when:

```
IF gaji_pokok < UMK[kota]: 
    trigger V06 violation
    verdict = "Tidak Wajar Hukum" (Not Legally Fair)
```

**Critical distinction**: V06 checks **gaji pokok** (base salary), not total compensation. Allowances are not counted toward UMK compliance — only the base salary component.

---

## 3. Wage Component Rules

### 3.1 The 75/25 Split (PP 36/2021 Pasal 9)

Under PP 36/2021 on Wages, formal employment must adhere to:

```
Upah Pokok (Base Salary) ≥ 75% of Total Monthly Compensation
Tunjangan Tetap (Fixed Allowances) ≤ 25% of Total Monthly Compensation
```

**Example** (valid payslip):
- Base salary: IDR 8,000,000 (80% ✓)
- Fixed allowance (transport): IDR 2,000,000 (20% ✓)
- **Total**: IDR 10,000,000

**Example** (invalid — base too low):
- Base salary: IDR 6,000,000 (60% ✗ — violates 75% rule)
- Fixed allowance: IDR 4,000,000 (40%)
- Total: IDR 10,000,000
- **Violation**: Base salary must be ≥ IDR 7,500,000

### 3.2 Allowances Classification

| Type | Examples | Included in UMK | Subject to PPh21 | Subject to BPJS |
|------|----------|-----------------|------------------|-----------------|
| Tunjangan Tetap (fixed) | Tunjangan jabatan, tunjangan keluarga | Yes | Yes | Yes |
| Tunjangan Tidak Tetap | Uang makan (by attendance), transport (by attendance) | No | Yes | No |
| Natura (in-kind) | Meal provision, company shuttle | No | No (≤1M/month) | No |

**For UMK compliance**: Only gaji pokok matters. Allowances are additional.

**For BPJS/PPh21 calculation**: Gross salary includes base + taxable allowances.

---

## 4. THR (Tunjangan Hari Raya)

### 4.1 THR Entitlement Rules

Per Permenaker 6/2016, THR is mandatory for all workers with work relationship:

| Condition | THR Entitlement |
|-----------|----------------|
| ≥12 consecutive months | 1 month salary |
| <12 months | 1/12 × months worked × 1 month salary |
| Resigned before 30 days before Eid | No THR (if contract allows) |

### 4.2 Definition of "Salary" for THR

THR calculation uses (per Pasal 3 Permenaker 6/2016):
- Upah pokok (100%)
- Tunjangan tetap (fixed allowances)

**Excluded from THR calculation**:
- Overtime pay
- Non-fixed allowances (uang makan, transport by attendance)
- Bonus (non-monthly)
- Benefits not tied to employment

### 4.3 Payment Timing

THR must be paid **no later than H-7** (7 days before Eid al-Fitr or other religious holiday for which the THR is given).

---

## 5. Termination and Severance (Pesangon)

### 5.1 Compensation Components on PHK

Under PP 35/2021 (as amended from UU 13/2003), termination triggers three payments:

| Component | Abbreviation | Basis |
|-----------|-------------|-------|
| Uang Pesangon | UP | Years of service × monthly wage |
| Uang Penghargaan Masa Kerja | UPMK | Years of service × monthly wage |
| Uang Penggantian Hak | UPH | Unused leave, home trip allowance |

### 5.2 Pesangon Formula (UP)

```python
def calculate_up(masa_kerja_bulan: int, total_upah: int) -> int:
    """
    Calculate Uang Pesangon per PP 35/2021 Pasal 40.
    
    Multipliers:
    - <1 year: 1x monthly wage
    - 1-2 years: 2x monthly wage
    - 2-3 years: 3x monthly wage
    ... up to 9+ years: 10x monthly wage (maximum)
    """
    tahun = masa_kerja_bulan / 12
    
    if tahun < 1: multiplier = 1
    elif tahun < 2: multiplier = 2
    elif tahun < 3: multiplier = 3
    elif tahun < 4: multiplier = 4
    elif tahun < 5: multiplier = 5
    elif tahun < 6: multiplier = 6
    elif tahun < 7: multiplier = 7
    elif tahun < 8: multiplier = 8
    else: multiplier = 9  # Max is 9x for PP 35/2021 (vs 10x in old UU 13/2003)
    
    return total_upah * multiplier
```

### 5.3 UPMK Formula

```python
def calculate_upmk(masa_kerja_bulan: int, total_upah: int) -> int:
    tahun = masa_kerja_bulan / 12
    
    if tahun < 1: multiplier = 0  # No UPMK if <1 year
    elif tahun < 2: multiplier = 1
    elif tahun < 3: multiplier = 2
    elif tahun < 4: multiplier = 3
    elif tahun < 5: multiplier = 4
    elif tahun < 6: multiplier = 5
    elif tahun < 7: multiplier = 6
    elif tahun < 8: multiplier = 7
    else: multiplier = 8  # Max 8 months
    
    return total_upah * multiplier
```

---

## 6. Work Hours and Overtime

### 6.1 Standard Work Hours

| System | Hours/Week | Hours/Day | Max Regular |
|--------|-----------|-----------|-------------|
| 6 days | 40 | 7 | 7 hours |
| 5 days | 40 | 8 | 8 hours |

### 6.2 Overtime Rates

Per Kepmenaker 102/2004 and PP 35/2021:

**Regular day overtime** (hours exceeding daily max):
- First hour: 1.5× hourly rate
- Subsequent hours: 2× hourly rate

**Rest day overtime** (Sunday/national holiday):
- 5-day system: First 8 hours = 2×, subsequent = 3×
- 6-day system: First 7 hours = 2×, subsequent = 3×

**Hourly rate formula**:
```
upah_per_jam = total_upah_bulanan / 173
```

(173 = standard monthly hours: 40 hrs/week × 52 weeks / 12 months)

---

## 7. Legal Framework Hierarchy

For Wajar Slip's compliance engine, apply rules in this priority order:

```
1. UMK/UMP (regional minimum) — overrides all other calculations
   ↓
2. PP 36/2021 (wage component rules) — 75/25 split
   ↓  
3. PP 46/2015, PP 45/2015 (BPJS rates) — calculate deductions
   ↓
4. UU 36/2008 (PPh 21) — calculate tax
   ↓
5. Permenaker 6/2016 (THR) — check if due
   ↓
6. PP 35/2021 (termination) — not applicable for active employees
```

---

## 8. Regulatory Reference Table

| Regulation | Subject | Key Point for cekwajar.id |
|------------|---------|---------------------------|
| UU 13/2003 | Manpower (base law) | Employment rights, termination rules |
| UU 11/2020 (UU 6/2023) | Cipta Kerja | Extended PKWT to 5 years |
| PP 36/2021 | Wages | 75/25 wage split, wage policies |
| PP 51/2023 | Wage amendment | Removed upper/lower bounds from formula |
| PP 35/2021 | PHK/Outsourcing | Severance formulas |
| PP 46/2015 | JHT | 2% employee, 3.7% employer |
| PP 45/2015 | JP | 1% employee, 2% employer, cap |
| PP 44/2015 | JKK/JKM | Risk-based rates |
| Permenaker 6/2016 | THR | 1 month salary after 12 months |
| Permenaker 1/2017 | Wage structure | Companies must publish salary bands |
| Kepmenaker 102/2004 | Overtime | Hourly rate calculations |

---

## Related Articles

- [[./concepts/bpjs-reference]] — Social security calculations that interact with wage rules
- [[./concepts/tax-indonesia]] — PPh21 calculations on gross salary
- [[projects/cekwajar-id]] — Project applying these rules in Wajar Slip
- [[./concepts/market-data-indonesia]] — Market salary benchmarks for Wajar Gaji
