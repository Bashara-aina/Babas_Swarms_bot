# BPJS Knowledge Base Progress Log

**Created**: 2026-04-11
**Domain**: Indonesian BPJS Calculations (030-039)
**Status**: ✅ COMPLETE

## Tasks Completed
| Source ID | File | Status | Notes |
|-----------|------|--------|-------|
| 030 | 030-bpjs-kesehatan.md | ✅ DONE | Iuran 5% (4% employer, 1% employee) |
| 031 | 031-bpjs-ketenagakerjaan-iuran.md | ✅ DONE | JHT 5.7%, JKK 0.24-1.74%, JKM 0.3%, JP 3% (capped), JKP 0.36% |
| 032 | 032-batas-upah.md | ✅ DONE | JP cap Rp 10.547.400 since March 2025 |
| 033 | 033-jht-klaim.md | ✅ DONE | Full claim at 56yo/PHK/disability/death; partial 30% for house |
| 034 | 034-jp-manfaat.md | ✅ DONE | Formula: 1% x MI x PDP x FP, min Rp 300k/month |
| 035 | 035-bpu.md | ✅ DONE | Bukan Penerima Upah - freelancers, ojek online |
| 036 | 036-sanksi.md | ✅ DONE | Admin (teguran, denda), Pidana (kurungan, denda, penjara) |
| 037 | 037-integrasi-payroll.md | ✅ DONE | EPS, virtual account, autodebit |
| 038 | 038-kelas-rawat.md | ✅ DONE | Kelas 1 (Rp150k), 2 (Rp100k), 3 (Rp42k) |
| 039 | 039-kris.md | ✅ DONE | 12 criteria, implementation target Dec 2025 |

## Summary

### Key Data Points Documented:

**BPJS Kesehatan (030):**
- 5% of salary: 4% employer, 1% employee
- For private employees (Penerima Upah)

**BPJS Ketenagakerjaan (031):**
- JHT: 5.7% (2% employee, 3.7% employer) - no cap
- JKK: 0.24-1.74% based on risk - employer only
- JKM: 0.30% - employer only
- JP: 3% (1% employee, 2% employer) - **capped at Rp 10,547,400**
- JKP: 0.36% (0.22% gov, 0.14% from JKK) - no employee contribution

**Batas Upah (032):**
- JP wage cap: Rp 10,547,400/month (updated March 2025)

**JHT Claims (033):**
- Full: 56yo, PHK, disability, death
- Partial: 30% max for house purchase (10yr+ membership)

**JP Benefits (034):**
- Formula: MP = 1% × MI × PDP × FP
- Minimum: Rp 300,000/month

**BPU (035):**
- Workers without employer: freelancers, ojek drivers
- Programs: JHT, JKK, JKM (no JP, no JKP)

**Sanksi (036):**
- Admin: warning, fine, public service ban
- Criminal: 1-8 years prison, up to Rp 1B fine

**Payroll Integration (037):**
- EPS system for payment
- Virtual account for banks
- Autodebit available

**Kelas Rawat (038):**
- Class 1: Rp 150k, up to 4 per room
- Class 2: Rp 100k, up to 6 per room
- Class 3: Rp 42k (subsidized), up to 10 per room

**KRIS (039):**
- 12 criteria for standardized care
- Target: end 2025 for full implementation

## Files Created
```
.wiki/knowledge/bpjs/
├── 030-bpjs-kesehatan.md
├── 031-bpjs-ketenagakerjaan-iuran.md
├── 032-batas-upah.md
├── 033-jht-klaim.md
├── 034-jp-manfaat.md
├── 035-bpu.md
├── 036-sanksi.md
├── 037-integrasi-payroll.md
├── 038-kelas-rawat.md
└── 039-kris.md
```

## Implementation Status for cekwajar.id

### CRITICAL Features:
- [x] 030 - BPJS Kesehatan calculation (5%)
- [x] 031 - All 5 BPJS TK programs with correct rates
- [x] 032 - JP wage cap enforcement

### HIGH Priority Features:
- [x] 033 - JHT claim eligibility checking
- [x] 035 - BPU calculation (for future gig platform support)
- [x] 036 - Compliance and sanctions information
- [x] 037 - Payroll integration (EPS/remittance)
- [x] 038 - Class benefits information
- [x] 039 - KRIS transition information

### Legion Capability:
- Can update rate configurations when regulations change
- Can build simulation modules for employees
- Needs Bashara for config file changes and external API connections

**Execution Completed**: 2026-04-11