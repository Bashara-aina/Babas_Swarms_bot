---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/worker-labor-law-complete.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:00.079422"
}
---

# Worker Labor Law Complete - Final Report

## Task: Create 19 Wiki Pages for Indonesian Labor Law

**Completed**: 2026-04-11
**Worker**: @worker (Bashara)
**Domain**: Indonesian Labor Law (019 files: 001-uu-ketenagakerjaan-13-2003 through 019-sanctions-enforcement)

---

## Executive Summary

✅ **STATUS: COMPLETE** - All 19 wiki pages have been successfully created in `.wiki/knowledge/labor-law/`

---

## Deliverables

### 19 Wiki Pages Created:

| # | Source | Title | cekwajar_impact |
|---|--------|-------|-----------------|
| 001 | UU 13/2003 | UU Ketenagakerjaan Indonesia | CRITICAL |
| 002 | UU 11/2020 | UU Cipta Kerja Perubahan | CRITICAL |
| 003 | PP 36/2021 | Pengupahan | CRITICAL |
| 004 | PP 51/2023 | Perubahan Pengupahan | CRITICAL |
| 005 | UMP 2025 | Upah Minimum Provinsi | CRITICAL |
| 006 | UMK 2025 | Upah Minimum Kab/Kota | CRITICAL |
| 007 | Permenaker 1/2017 | Struktur Skala Upah | HIGH |
| 008 | UU 40/2004 | Sistem Jaminan Sosial | CRITICAL |
| 009 | Kepmenaker 102/2004 | Upah Lembur | HIGH |
| 010 | PP 35/2021 | Pesangon/PHK | CRITICAL |
| 011 | Permenaker 6/2016 | THR | HIGH |
| 012 | Aturan Cuti | Cuti Tahunan/Melahirkan/Sakit | MEDIUM |
| 013 | PKWT/PKWTT | Kontrak Kerja | HIGH |
| 014 | Tunjangan | Tunjangan Wajib | HIGH |
| 015 | UU PPh 36/2008 | PTKP & PPh 21 | CRITICAL |
| 016 | UMSP/UMSK | Upah Minimum Sektoral | HIGH |
| 017 | WFH Rules | Remote Work Indonesia | MEDIUM |
| 018 | TKA | Gaji Tenaga Kerja Asing | HIGH |
| 019 | Sanksi | Pidana Pengupahan | CRITICAL |

---

## Key Technical Implementations

### TypeScript Code Blocks Included:
- All formulas with 6 decimal precision
- Complete function implementations for:
  - UMP/UMK validation
  - Overtime calculation (1/173 formula)
  - PHK compensation (UP + UPMK + UPH)
  - THR calculation (proportional)
  - PPh 21 calculation (progressive tax)
  - BPJS contribution calculation
  - Leave balance tracking

### Compliance Areas Covered:
- Minimum wage validation
- Overtime rules
- Contract classification
- Leave entitlements
- Tax calculations
- Criminal penalties for violations

---

## Sources Referenced

| Source Type | Count | Examples |
|-------------|-------|----------|
| Official Govt (BPK) | 12 | peraturan.bpk.go.id |
| Kemnaker Data | 3 | satudata.kemnaker.go.id |
| JDIH | 2 | jdih.kemnaker.go.id |
| HR/Payroll Sites | 7 | hukumonline, gajimu, Mekari, dll |

---

## Implementation Recommendations for cekwajar.id

### Immediate Actions Required:
1. **Supabase Schema Updates**:
   - `regional_minimum_wages` table (UMP/UMK/UMSK data)
   - `employee_contracts` table (PKWT/PKWTT tracking)
   - `leave_balances` table (for PHK compensation)

2. **Core Payroll Module** (`src/lib/payroll/`):
   - `wage-compliance.ts` - UMK validation
   - `overtime-calculator.ts` - Lembur calculation
   - `phk-calculator.ts` - Pesangon calculation
   - `pph21-calculator.ts` - Tax calculation
   - `bpjs-calculator.ts` - Contribution calculation

3. **HR Module** (`src/lib/hr/`):
   - `contract-management.ts` - Contract expiry tracking
   - `leave-management.ts` - Leave balance
   - `work-arrangement.ts` - WFH tracking

### Legion Autonomous Actions (YES):
- Auto-update UMK/UMP data annually
- Generate and validate wage structures
- Calculate THR and overtime
- Track contract expiry dates
- Classify allowances
- Match employees to sectoral wages

### Requires Human Review (NO):
- TKA cases (legal complexity)
- PHK calculations (case-by-case)
- Contract disputes
- Union negotiations

---

## Risk Assessment

### CRITICAL Risk Areas:
1. **019 - Sanksi Pengupahan**: Criminal penalties for below-minimum wages
2. **003-006 - Wage Calculations**: Wrong UMK = non-compliance
3. **015 - PPh 21**: Tax calculation errors = penalties
4. **010 - PHK**: Wrong severance = labor disputes

### HIGH Priority:
- Implement UMK validation before every payroll run
- Add contract expiry alerts
- Create PTKP update mechanism

---

## Verification

All 19 files:
- ✅ Follow MANDATORY TEMPLATE format
- ✅ Include TypeScript code blocks
- ✅ Use official regulation URLs
- ✅ Tagged with cekwajar_impact level
- ✅ Marked with legion_can_act status
- ✅ Proper 3-digit file naming

---

## Logs Written

- `.wiki/logs/worker-labor-law-progress.md` - Progress tracking
- `.wiki/logs/worker-labor-law-complete.md` - This completion report

---

**Worker Task Complete**. Ready for @planner review and @reviewer verification.
