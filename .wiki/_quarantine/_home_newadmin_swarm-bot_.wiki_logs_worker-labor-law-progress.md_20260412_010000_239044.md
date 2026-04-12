---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/worker-labor-law-progress.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:00.239075"
}
---

# Worker Labor Law Progress Log

## Task: Create 19 Wiki Pages for Indonesian Labor Law (Domain 019)

**Started**: 2026-04-11
**Worker**: @worker (Bashara)
**Domain**: Indonesian Labor Law (019 files: 001-uu-ketenagakerjaan-13-2003 through 019-sanctions-enforcement)

---

## Progress Update: ✅ ALL 19 FILES COMPLETED

### Files Created:

| # | Source ID | File | Status |
|---|-----------|------|--------|
| 1 | 001 | `001-uu-ketenagakerjaan-13-2003.md` | ✅ Done |
| 2 | 002 | `002-uu-cipta-kerja-11-2020.md` | ✅ Done |
| 3 | 003 | `003-pp-pengupahan-36-2021.md` | ✅ Done |
| 4 | 004 | `004-pp-pengupahan-51-2023.md` | ✅ Done |
| 5 | 005 | `005-ump-2025-provinsi.md` | ✅ Done |
| 6 | 006 | `006-umk-2025-kabupaten-kota.md` | ✅ Done |
| 7 | 007 | `007-permenaker-struktur-skala-upah.md` | ✅ Done |
| 8 | 008 | `008-uu-sjsn-40-2004.md` | ✅ Done |
| 9 | 009 | `009-kepmenaker-upah-lembur.md` | ✅ Done |
| 10 | 010 | `010-pp-pesangon-35-2021.md` | ✅ Done |
| 11 | 011 | `011-permenaker-thr.md` | ✅ Done |
| 12 | 012 | `012-aturan-cuti.md` | ✅ Done |
| 13 | 013 | `013-pkwt-pkwtt-kontrak.md` | ✅ Done |
| 14 | 014 | `014-tunjangan-wajib.md` | ✅ Done |
| 15 | 015 | `015-uu-pph-36-2008-ptkp.md` | ✅ Done |
| 16 | 016 | `016-umsp-umsk.md` | ✅ Done |
| 17 | 017 | `017-aturan-wfh.md` | ✅ Done |
| 18 | 018 | `018-gaji-tka.md` | ✅ Done |
| 19 | 019 | `019-sanksi-pengupahan.md` | ✅ Done |

---

## Implementation Notes

### CRITICAL Impact Files (cekwajar_impact: CRITICAL):
- 001: UU 13/2003 - Base labor law
- 002: UU Cipta Kerja - Contract changes
- 003-004: PP 36/2021 & PP 51/2023 - Wage calculations
- 005-006: UMP/UMK 2025 - Current minimum wage data
- 008: UU SJSN - BPJS contributions
- 010: PP 35/2021 - PHK/severance
- 015: UU PPh 36/2008 - PTKP/PPh 21
- 019: Sanctions - Criminal penalties

### Legion_can_act: YES (10 files):
- 003-006, 007, 009, 011, 013-014, 016-017

### Legion_can_act: NO (9 files):
- 001-002, 008, 010, 012, 015, 018-019

---

## Sources Used:
- peraturan.bpk.go.id (official regulation database)
- satudata.kemnaker.go.id (Kemnaker official data)
- jdih.kemnaker.go.id (legal database)
- Various HR/payroll compliance websites

---

## Next Steps:
1. Reviewer to verify content accuracy
2. Bashara to integrate TypeScript code blocks into codebase
3. Supabase tables need schema updates for:
   - regional_minimum_wages (UMP/UMK/UMSK)
   - bpjs_registrations
   - employee_contracts
