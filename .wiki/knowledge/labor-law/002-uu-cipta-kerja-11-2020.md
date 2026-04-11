---
source_id: 002
title: "UU 11 Tahun 2020 Cipta Kerja Perubahan UU Ketenagakerjaan"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://peraturan.bpk.go.id/Details/149750"
last_verified: "2026-04-11"
tags: [labor-law,uu11-2020,cipta-kerja,omnibus-law,perubahan-ketenagakerjaan]
cekwajar_impact: CRITICAL
legion_can_act: NO
---

# UU 11 Tahun 2020 Cipta Kerja Perubahan UU Ketenagakerjaan

## Why This Matters for cekwajar.id
UU Cipta Kerja merupakan "omnibus law" yang mengubah signifikan ketentuan ketenagakerjaan, termasuk PKWT, pesangon, dan THR. Payroll system harus mengikuti formula terbaru yang ditetapkan PP turunan untuk menghindari kalkulasi salah.

## Core Knowledge

### 9 Perubahan Utama dalam UU Cipta Kerja Bidang Ketenagakerjaan

1. **Perubahan PKWT (Perjanjian Kerja Waktu Tertentu)**
   - Jangka waktu maksimal 5 tahun (dari 2 tahun + 1 perpanjangan)
   - Perpanjangan PKWT wajib melewati masa tenggang 30 hari
   - Tidak ada lagi konsep "perpanjangan kedua" - sekarang "perubahan"

2. **Alih Daya (Outsourcing)**
   -Perubahan机理 pelaksanaan alih daya
   - Perlindungan hak pekerja alih daya disamakan

3. **Penggunaan Tenaga Kerja Asing (TKA)**
   - Simplifikasi perizinan TKA
   - Pengutamaan tenaga kerja lokal

4. **Mekanisme PHK**
   - Perubahan rumus pesangon (dihitung dengan formula baru)
   - Uang penggantian hak (UPH) yang harus dibayar

5. **Pengupahan**
   -Kebijakan upah minimum berdasarkan formula PP 36/2021
   - Struktur dan skala upah wajib dipublikasikan

6. **Hubungan Industrial**
   - Penyederhanaan prosedur perselisihan
   - Peran mediator dan arbitrator

7. **Jaminan Sosial**
   -Integrasi dengan BPJS

8. **Sanksi Administratif**
   - Denda administratif untuk pelanggaran ketenagakerjaan

9. **Ketenagakerjaan sektor tertentu**
   - Pelaut, penerbangan, pertambangan memiliki aturan khusus

### Status UU Cipta Kerja
- UU 11/2020 ditetapkan 2 November 2020
- Kemudian dicabut oleh UU 6/2023 (Penetapan Perppu 2/2022)
- Ketentuan-ketentuan masih menjadi referensi karena banyak PP turunan yang tidak berubah

## Exact Formulas / Numbers (if applicable)

### Perubahan Rumus Pesangon (Berdasarkan PP 35/2021)
```typescript
interface PHKCompensation {
  alasanPHK: string;
  masaKerjaTahun: number;
  UpahPokok: number;
  tunjanganTetap: number;
}

function hitungPesangonPP35({
  masaKerjaTahun,
  UpahPokok,
  tunjanganTetap
}: PHKCompensation): number {
  const totalUpah = UpahPokok + tunjanganTetap;
  
  // Rumus berdasarkan masa kerja
  if (masaKerjaTahun < 1) {
    return totalUpah * 1; // 1 bulan upah
  } else if (masaKerjaTahun < 2) {
    return totalUpah * 2; // 2 bulan upah
  } else if (masaKerjaTahun < 3) {
    return totalUpah * 3; // 3 bulan upah
  } else if (masaKerjaTahun < 4) {
    return totalUpah * 4; // 4 bulan upah
  } else if (masaKerjaTahun < 5) {
    return totalUpah * 5; // 5 bulan upah
  } else if (masaKerjaTahun < 6) {
    return totalUpah * 6; // 6 bulan upah
  } else if (masaKerjaTahun < 7) {
    return totalUpah * 7; // 7 bulan upah
  } else if (masaKerjaTahun < 8) {
    return totalUpah * 8; // 8 bulan upah
  } else {
    return totalUpah * 10; // maksimal 10 bulan upah
  }
}
```

## Edge Cases and Common Mistakes

1. **PHK karena kesalah berat**: Tidak mendapat pesangon, hanya UPH
2. **PHK karena resign**: Mungkin tidak dapat pesangon penuh - harus negosiasi
3. **Upah lembur tidak termasuk komponen pesangon**: Hanya upah pokok + tunjangan tetap
4. **Kontrak habis masa berlaku**: Wajib diberi kesempatan bekerja ulang atau mendapat kompensasi

## cekwajar.id Implementation Notes

- **File to update**: `src/lib/payroll/phk-calculator.ts`
- **Function to modify/create**: `calculatePHKCompensation()`, `validatePKWTDuration()`
- **Data source to query**: Static regulation constants
- **Update frequency**: When PP turunan is updated
- **Legion action**: NO - legal interpretation required

## Monetization Angle
- PHK calculator for HR departments
- Compliance dashboard for contract renewals
- Automated reminder system for contract expiry

## Sources and Cross-References
- Official URL: https://peraturan.bpk.go.id/Details/149750
- Status: Dicabut oleh UU 6/2023, namun PP turunan masih berlaku
- Related: UU 6/2023, PP 35/2021, PP 36/2021
