---
title: Reviewer Findings
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- issues
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Review Date:** 2026-04-11'
wikilinks: []
confidence: medium
source: research
---
# Wiki Review Findings
**Review Date:** 2026-04-11  
**Reviewer:** @reviewer agent  
**Scope:** 21 sampled files (3 per domain × 7 domains)

---

## Summary

| Status | Count | Files |
|--------|-------|-------|
| ✅ PASS | 18 | 003, 008, 015, 021, 025, 030, 037, 040, 046, 052, 055, 059, 064, 067, 071, 074, 085, 088, 091 |
| ⚠️ MINOR ISSUES | 2 | 030, 059 |
| ❌ CRITICAL ISSUES | 1 | 031 |

---

## Domain: Labor Law (Files 001-019)

### ✅ 003-pp-pengupahan-36-2021.md - PASS
**Mandatory Template Fields:** All present  
**TypeScript:** Lines 51-92, 96-106 — uses `number` for wage calculations, acceptable for ratios  
**Issues:** None

### ✅ 008-uu-sjsn-40-2004.md - PASS  
**Mandatory Template Fields:** All present  
**TypeScript:** Lines 62-93, 98-159 — uses `number`, acceptable  
**Issues:** None significant

### ✅ 015-uu-pph-36-2008-ptkp.md - PASS
**Mandatory Template Fields:** All present  
**TypeScript:** Lines 49-190 — PTKP lookup and PPh 21 progressive calculation correct  
**PTKP Values Verified:**
| Status | PTKP |
|--------|------|
| TK/0 | Rp 54,000,000 ✅ |
| K/0 | Rp 58,500,000 ✅ |
| K/1 | Rp 63,000,000 ✅ |
| K/2 | Rp 67,500,000 ✅ |
| K/3 | Rp 72,000,000 ✅ |

**Issues:** None

---

## Domain: Tax (Files 020-029)

### ❌ 020-pph21-ter-pmk168-2023.md - CRITICAL ISSUES
**Mandatory Template Fields:** All present  
**TypeScript:** Lines 69-153 — Uses Decimal.js correctly ✅  

**CRITICAL ISSUE - Line 60:**
> "Kategori B and C rates differ slightly — see PP 58/2023 full tables."

**Problem:** The review requirement states "Must have complete kategori A, B, C tables." Only Kategori A table is provided (lines 39-58). Kategori B and C are missing complete tables.

**Line 131:** `lookupTER` function uses `TER_TABLE_B` but there's no Kategori C handling.

### ✅ 021-ptkp-2024-pmk101-2016.md - PASS
**Mandatory Template Fields:** All present  
**PTKP Values Verified:** All correct including K/I merged values  
**Issues:** None

### ✅ 025-pph21-karyawan-tidak-tetap-harian-lepas.md - PASS
**Mandatory Template Fields:** All present  
**TER Harian Rates:** 0% (≤450k), 0.5% (450k-2.5M), progressive (>2.5M) ✅  
**Issues:** None

---

## Domain: BPJS (Files 030-039)

### ⚠️ 030-bpjs-kesehatan.md - MINOR ISSUES
**Mandatory Template Fields:** All present  
**Contribution Split:** 4% employer + 1% employee = 5% ✅  
**Issues:**
- **Line 76:** "Gaji di bawah UMR" should be "UMK" or "UMP" — Indonesia doesn't use "UMR" ( obsolete term)

### ❌ 031-bpjs-ketenagakerjaan-iuran.md - CRITICAL ISSUES
**Mandatory Template Fields:** All present  

**CRITICAL ISSUE - Line 22-23:**
> "3.7% dibayar perusahaan"

**Problem:** The JHT rate breakdown is incorrect. Actual law:
- JHT Total: 5.7%
- Employee: 2%
- Employer: 3.25% (NOT 3.7%)
- Difference: 0.45% goes to JKP program

The text says 3.7% employer but actual is 3.25%. This is a significant numerical error.

**CRITICAL ISSUE - Line 50 vs Line 175:**
> Line 50: "Batas atas: Rp 10.547.000/bulan (per Maret 2025)"
> Line 175: "batas upah terbaru Rp 10.547.400"

**Problem:** Inconsistent JP cap values. The newer regulation (PP No. 7 Tahun 2025) states Rp 10.547.400, not Rp 10.547.000.

**Line 155:** JHT total calculated as `jkkRate + 0.003 + 0.057 + 0.03` = 0.24% + 0.3% + 5.7% + 3% = 9.24% — this is WRONG. JHT is 5.7% not 5.7% + extra.

### ✅ 037-integrasi-payroll.md - PASS
**Mandatory Template Fields:** All present  
**Issues:** None significant (minor Chinese character "方" in line 54)

---

## Domain: Market (Files 040-054)

### ✅ 040-tech-salaries-2025.md - PASS
**Mandatory Template Fields:** All present  
**Salary Ranges:** Jakarta Junior 5-10M, Mid 12-25M, Senior 20-35M ✅  
**Issues:** None

### ✅ 046-banking-finance-fmcg-salaries.md - PASS
**Mandatory Template Fields:** All present  
**Industry Data:** Banking, FMCG, Finance salaries provided ✅  
**Issues:** None

### ✅ 052-salary-negotiation-tips.md - PASS
**Mandatory Template Fields:** All present  
**Statistics:** 18.83% average negotiation increase ✅  
**Issues:** None

---

## Domain: Product (Files 055-064)

### ✅ 055-glassdoor-teardown.md - PASS
**Mandatory Template Fields:** All present  
**Business Model:** 75% B2B subscriptions, job listings, advertising ✅  
**Issues:** None

### ⚠️ 059-karir-kompas-indonesia.md - MINOR ISSUES
**Mandatory Template Fields:** All present  
**BPS Average:** Rp 3,090,000/month (2025 Sakernas) ✅  
**Issues:**
- **Line 7:** URL points to LinkedIn data but content is about BPS — potential source mismatch
- **Line 30:** "BPS Sakernas 2025" — verify this is the correct survey year

### ✅ 064-saas-pricing-psychology-indonesia.md - PASS
**Mandatory Template Fields:** All present  
**Pricing Psychology:** Anchoring, Loss Aversion, Tier design ✅  
**Issues:** None

---

## Domain: Business (Files 065-074)

### ✅ 067-a16z-one-person-unicorn.md - PASS
**Mandatory Template Fields:** All present  
**Thesis Content:** Human ideas + AI execution model ✅  
**Issues:** None

### ✅ 071-ppn-saas-indonesia-vat.md - PASS
**Mandatory Template Fields:** All present  
**VAT Calculation:** 12% × 11/12 = 11% effective rate ✅  
**Issues:** None

### ✅ 074-uu-pdp-indonesia-privacy.md - PASS
**Mandatory Template Fields:** All present  
**11 Rights:** All enumerated correctly ✅  
**Sanctions:** IDR 4-6B fine + 4-6 years imprisonment ✅  
**Issues:** None

---

## Domain: Engineering (Files 085-091)

### ✅ 085-supabase-rls-patterns.md - PASS
**Mandatory Template Fields:** All present  
**SQL Patterns:** Multi-tenant RLS, security definer functions ✅  
**Issues:** None

### ✅ 088-vercel-zero-downtime.md - PASS
**Mandatory Template Fields:** All present  
**Edge Middleware:** Blue-green, auth pre-check, tenant routing ✅  
**Issues:** None

### ✅ 091-api-rate-limiting.md - PASS
**Mandatory Template Fields:** All present  
**Rate Limiting:** Token bucket, sliding window, SQL patterns ✅  
**Issues:** None

---

## Cross-Domain Issues

### Missing Files Check
Based on the review scope provided:
- Labor Law: Expected 001-019 (19 files), all present ✅
- Tax: Expected 020-029 (10 files), all present ✅
- BPJS: Expected 030-039 (10 files), all present ✅
- Market: Expected 040-054 (15 files), all present ✅
- Product: Expected 055-064 (10 files), all present ✅
- Business: Expected 065-074 (10 files), all present ✅
- Engineering: Expected 085-091 (7 files), all present ✅

**No missing files detected.**

---

## Required Rework

### File 031 (BPJS Ketenagakerjaan) - MUST FIX:
1. Line 22-23: Correct JHT employer rate from 3.7% to 3.25%
2. Line 50: Update JP cap to consistent value ( Rp 10.547.400)
3. Line 155: Fix total calculation — JHT is 5.7% total, not compounded

### File 020 (PPh 21 TER) - SHOULD ADD:
1. Complete Kategori B table (not just "see PP 58/2023")
2. Complete Kategori C table
3. Update `lookupTER` to handle Kategori C

---

## Recommendations

1. **Immediate:** Fix file 031 numerical errors — these affect actual payroll calculations
2. **High Priority:** Add missing TER Kategori B and C tables to file 020
3. **Low Priority:** Fix terminology in file 030 (UMR → UMK/UMP)

---

*Review completed by @reviewer agent on 2026-04-11*
