***
title: "Wajar Slip — Payslip Decoder & Compliance Auditor — Full Spec"
***

# Wajar Slip — Complete Technical Specification

## Purpose
Decodes a payslip (via OCR or manual entry), recalculates PPh21 + BPJS
from scratch using 2026 Indonesian tax law, and flags violations from
minor discrepancies to illegal deductions.

## OCR Pipeline

```
Step 1 → Image Preprocessing
         - Deskew (rotate to alignment)
         - Binarization (B/W for clarity)
         - Upscaling (2× if < 300 DPI)
         - Denoising (remove scanning artifacts)

Step 2 → Region Detection (Custom Model — trained on 500+ Indonesian payslips)
         - Sections: Header, Employee Info, Earnings, Deductions, Net Pay

Step 3 → OCR (Tesseract v5 Fine-Tuned)
         - Currency regex: /IDR\s?[0-9]{1,3}(,[0-9]{3})*/
         - Checksum: Total Earnings − Total Deductions = Net Salary

Step 4 → Validation & Fallback
         - If variance > 5%: flag for manual review
```

### OCR Confidence Thresholds
| Confidence | Action |
|------------|--------|
| 90–100% | Auto-accept |
| 70–89% | Show with "Apakah ini benar?" |
| 50–69% | Show all fields for verification |
| < 50% | Fallback to manual entry |

## PPh21 Calculation Engine (2026)

### Two Methods
| Method | When | Formula |
|--------|------|---------|
| **TER** | Regular monthly salary (PMK 168/2023) | Fixed effective rate from Tabel A/B/C |
| **Progressive** | December, bonus, THR months | Stepped 5 brackets |

### Progressive Brackets (UU HPP 7/2021)
| Annual PKP | Rate |
|------------|------|
| IDR 0 – 60,000,000 | 5% |
| IDR 60,000,001 – 250,000,000 | 15% |
| IDR 250,000,001 – 500,000,000 | 25% |
| IDR 500,000,001 – 5,000,000,000 | 30% |
| > IDR 5,000,000,000 | 35% |

### PTKP (PMK 66/2023 — frozen 2026)
| Status | Annual PTKP | Monthly PTKP |
|--------|------------|--------------|
| TK/0 | IDR 54,000,000 | IDR 4,500,000 |
| K/0 | IDR 58,500,000 | IDR 4,875,000 |
| K/1 | IDR 63,000,000 | IDR 5,250,000 |
| K/2 | IDR 67,500,000 | IDR 5,625,000 |
| K/3 | IDR 72,000,000 | IDR 6,000,000 |

### Step-by-Step Progressive Calculation
```
STEP 1: Gross Monthly Income
        = Gaji Pokok + Taxable Allowances
        NOTE: Natura meals/transport ≤ IDR 1M/month → NON-TAXABLE (PMK 66/2023)

STEP 2: Annualize = Gross Monthly × 12

STEP 3: Deductions
        - Biaya Jabatan: min(Gross × 5%, IDR 500,000/month) × 12
        - BPJS Kesehatan: min(salary, 12,000,000) × 1% × 12

STEP 4: Net Income = Annual Gross − Biaya Jabatan − BPJS Kesehatan

STEP 5: PKP = max(Net Income − PTKP, 0)

STEP 6: Apply Progressive Brackets (stepped, NOT flat rate)

STEP 7: Monthly PPh21 = Annual Tax ÷ 12

STEP 8: No NPWP? → multiply by 1.20 (20% surcharge, UU PPh Pasal 21 ayat 5a)
```

### Worked Example: Budi Santoso | K/1 | Gaji IDR 15,000,000
```
Gross:           IDR 15,800,000 (incl. cash transport IDR 500K + pulsa IDR 300K)
Biaya Jabatan:   IDR 500,000/month
BPJS Kesehatan:  IDR 120,000/month
Annual Gross:    IDR 189,600,000
Annual Biaya J:  IDR 6,000,000
Annual BPJS:     IDR 1,440,000
Net Income:      IDR 182,160,000
PTKP K/1:        IDR 63,000,000
PKP:             IDR 119,160,000

Tax:
  IDR 60M × 5%  = IDR 3,000,000
  IDR 59.16M × 15% = IDR 8,874,000
  Annual PPh21 = IDR 11,874,000
  Monthly PPh21 = IDR 989,500
```

## BPJS Calculation

### BPJS Ketenagakerjaan
| Component | Employee | Employer | Cap |
|-----------|----------|----------|-----|
| JHT | 2.0% | 3.7% | None |
| JP | 1.0% | 2.0% | IDR 9,559,600/month |
| JKK | 0% | 0.24%–1.74% (risk class) | None |
| JKM | 0% | 0.3% | None |

### BPJS Kesehatan
| Contributor | Rate | Cap |
|-------------|------|-----|
| Employee | 1% | IDR 12,000,000/month |
| Employer | 4% (+1%/child, max 5) | IDR 12,000,000/month |

## Allowance Classification: Taxable vs Non-Taxable

| Type | Cash (Tunai) | In-Kind (Natura) |
|------|-------------|-----------------|
| Tunjangan Makan | 🔴 Fully Taxable | ✅ Exempt ≤ IDR 1M/month |
| Tunjangan Transport | 🔴 Fully Taxable | ✅ Exempt ≤ IDR 1M/month |
| Tunjangan Keluarga | 🔴 Fully Taxable | N/A |
| Bonus/Komisi | 🔴 Fully Taxable | N/A |

> Natura exemption requires ACTUAL facility (company cafeteria, shuttle),
> NOT a cash reimbursement.

## Compliance Violation Detection (8 Categories)

| Code | Severity | Rule | Action |
|------|----------|------|--------|
| E001 | 🚨 CRITICAL | Salary < UMR/UMK | Report to Dinas Ketenagakerjaan |
| E002 | 🚨 CRITICAL | BPJS JHT mismatch (tol: IDR 5K) | Recalculate + back-pay |
| E003 | 🚨 CRITICAL | BPJS Kesehatan mismatch (tol: IDR 2K) | Recalculate + back-pay |
| W001 | ⚠️ WARNING | PPh21 over-deducted (tol: IDR 50K/year) | Claim refund via SPT |
| W002 | ⚠️ WARNING | PPh21 under-deducted | Adjust December SPT |
| W003 | ⚠️ WARNING | THR missing in Ramadan/December | Manual HR verification |
| W004 | ⚠️ WARNING | Overtime multiplier violation (1.5×/2.0×/3.0×) | Recalculate per UU 13/2003 |
| I001 | ℹ️ INFO | Potongan lain-lain without itemized breakdown | Request documentation |

## Tax Optimization (Premium)

1. **Biaya Jabatan Verification** — Saving: IDR 23.5K–25K/month
2. **Tax Status Accuracy** — Every K-status saves ~IDR 150K/year
3. **Natura Restructuring** — Convert cash transport/meal to facility: saves ~IDR 50K+/month
4. **Additional Pension** — Up to 5% income, fully deductible; saves IDR 30K–75K/month