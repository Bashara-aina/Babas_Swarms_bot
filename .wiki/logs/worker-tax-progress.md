---
title: Worker Tax Progress
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Domain:** Indonesian Tax - PPh 21 Calculation'
wikilinks: []
confidence: medium
source: research
---
# Worker Tax Progress Log - PPh 21 Calculation (020-029)

**Date:** 2026-04-11  
**Domain:** Indonesian Tax - PPh 21 Calculation  
**Worker:** @worker (Bashara)

## Task Overview
Create 10 wiki pages in `.wiki/knowledge/tax/` directory for Indonesian PPh 21 tax calculation knowledge base.

## Progress

| Source ID | File | Status | Notes |
|-----------|------|--------|-------|
| 020 | 020-pph21-ter-pmk168-2023.md | ✅ DONE | TER tables, PMK 168/2023 |
| 021 | 021-ptkp-2024-pmk101-2016.md | ✅ DONE | PTKP values table |
| 022 | 022-pph17-pasal-17-progresif.md | ✅ DONE | 5 bracket progressive rates |
| 023 | 023-biaya-jabatan-pph21-5-persen.md | ✅ DONE | 5% / Rp500k monthly cap |
| 024 | 024-pph21-bonus-thr-penghasilan-tidak-teratur.md | ✅ DONE | Bonus/THR taxation |
| 025 | 025-pph21-karyawan-tidak-tetap-harian-lepas.md | ✅ DONE | Daily/weekly workers |
| 026 | 026-npwp-wajib-pajak-sanksi-tidak-punya.md | ✅ DONE | 20% surcharge |
| 027 | 027-natura-kenikmatan-pmk66-2023.md | ✅ DONE | Natura taxation |
| 028 | 028-spt-tahunan-pph-orang-pribadi.md | ✅ DONE | SPT filing & deadline |
| 029 | 029-pph21-direksi-komisaris-tidak-tetap.md | ✅ DONE | Board member taxation |

## Search Queries Used
1. PMK 168 2023 PPh 21 TER tarif efektif rata-rata tabel
2. PTKP 2024 nilai terbaru PMK 101 2016 update
3. tarif PPh pasal 17 progresif 5 bracket 2024
4. biaya jabatan PPh 21 5 persen 500 ribu per bulan
5. PPh 21 bonus THR penghasilan tidak teratur cara hitung 2024
6. PPh 21 karyawan tidak tetap harian lepas freelancer cara hitung
7. NPWP wajib pajak sanksi tidak punya NPWP 20 persen lebih
8. natura kenikmatan PPh 21 PMK 66 2023 objek pajak
9. SPT tahunan PPh orang pribadi cara lapar deadline 2025
10. PPh 21 direksi komisaris tidak tetap tarif pasal 17 langsung

## Key Sources Fetched
- https://klikpajak.id/blog/pengertian-ptkp/
- https://ortax.org/mengenal-tarif-pph-pasal-17-dalam-menghitung-pph-21
- https://klikpajak.id/blog/biaya-jabatan-pph-21/
- https://klikpajak.id/blog/pajak-bonus-karyawan/
- https://ortax.org/penghitungan-pph-21-atas-upah-tenaga-kerja-lepas

## Issues Encountered
- Web search rate limiting (3 retries needed with cooldown)
- Some official JDIH URLs returned 404 (used alternative sources)

## Next Steps
- Write completion report to `.wiki/logs/worker-tax-complete.md`
