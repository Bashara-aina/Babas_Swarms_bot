---
source_id: 006
title: "UMK 2025 Upah Minimum Kabupaten/Kota Seluruh Indonesia"
source_type: MARKET_DATA
authority: OFFICIAL_GOV
url: "https://satudata.kemnaker.go.id/data/kumpulan-data/2252"
last_verified: "2026-04-11"
tags: [umk2025,upah-minimum-kabupaten-kota,labor-law,pengupahan]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# UMK 2025 Upah Minimum Kabupaten/Kota Seluruh Indonesia

## Why This Matters for cekwajar.id
UMK 2025 adalah standarupah minimum yang lebih tinggi dari UMP untuk wilayah kabupaten/kota. Perusahaan yang beroperasi di wilayah dengan UMK wajib membayar worker minimal sesuai UMK yang berlaku, bukan hanya UMP.

## Core Knowledge

### Perbedaan UMP dan UMK

| Aspek | UMP | UMK |
|-------|-----|-----|
| Cakupan | Provinsi | Kabupaten/Kota |
| Nilai | Lebih rendah | Lebih tinggi dari UMP |
| Penetapan | Gubernur | Gubernur (berdasarkan rekomendasi) |
| Dasar | Permenaker 16/2024 | Keputusan Gubernur |

### Ketentuan Utama UMK 2025

1. UMK harus lebih tinggi dari UMP provinsi
2. Ditetapkan oleh Gubernur paling lambat 21 November 2024
3. Berlaku 1 Januari 2025
4. Berdasarkan formula PP 51/2023

### Contoh UMK 2025 (Sepuluh Tertinggi)

| No | Wilayah | UMK 2025 (Rp) |
|----|---------|---------------|
| 1 | Kota Bekasi | 5.999.443 |
| 2 | Kabupaten Bekasi | 5.938.885 |
| 3 | Kota Depok | 5.195.722 |
| 4 | Kota Bogor | 5.126.897 |
| 5 | Kabupaten Bogor | 5.396.761 |
| 6 | Kota Tangerang | 4.901.117 |
| 7 | Kota Jakarta Timur | 5.396.760 |
| 8 | Kota Jakarta Barat | 5.396.760 |
| 9 | Kota Surabaya | 4.725.479 |
| 10 | Kabupaten Karawang | 5.268.326 |

### Contoh UMK 2025 (Sepuluh Terendah)

| No | Wilayah | UMK 2025 (Rp) |
|----|---------|---------------|
| 1 | Banjarnegara | 2.169.349 |
| 2 | Wonogiri | 2.169.349 |
| 3 | Blora | 2.169.349 |
| 4 | Rembang | 2.169.349 |
| 5 | Grobogan | 2.169.349 |
| 6 | Pati | 2.169.349 |
| 7 | Kendal | 2.169.349 |
| 8 | Batang | 2.169.349 |
| 9 | Pekalongan | 2.169.349 |
| 10 | Pemalang | 2.169.349 |

```typescript
interface UMKData {
  kodeKabupatenKota: string;
  namaKabupatenKota: string;
  kodeProvinsi: string;
  umk2024: number;
  umk2025: number;
  tanggalBerlaku: Date;
  sumber: string;
}

function getEffectiveWage(
  employeeLocation: string,
  umkMap: Map<string, number>,
  umpMap: Map<string, number>
): number {
  const umk = umkMap.get(employeeLocation);
  const ump = umpMap.get(employeeLocation);
  
  // UMK digunakan jika ada, jika tidak gunakan UMP
  return umk || ump || 0;
}

function validateMinimumWage(
  totalCompensation: number,
  employeeLocation: string,
  umkMap: Map<string, number>,
  umpMap: Map<string, number>
): { compliant: boolean; requiredWage: number; shortfall: number } {
  const requiredWage = getEffectiveWage(employeeLocation, umkMap, umpMap);
  return {
    compliant: totalCompensation >= requiredWage,
    requiredWage,
    shortfall: Math.max(0, requiredWage - totalCompensation)
  };
}
```

## Exact Formulas / Numbers (if applicable)

### TypeScript Implementation
```typescript
interface WageComplianceCheck {
  employeeId: string;
  locationCode: string;
  baseSalary: number;
  fixedAllowances: number;
  nonFixedAllowances: number;
  umkRequired: number;
  umpRequired: number;
}

function calculateTotalCompensation(check: Omit<WageComplianceCheck, 'umkRequired' | 'umpRequired'>): number {
  // Non-fixed allowances (meal, transport based on attendance) are not included in minimum wage calculation
  return check.baseSalary + check.fixedAllowances;
}

function checkMinimumWageCompliance(
  check: WageComplianceCheck,
  umkData: Map<string, number>,
  umpData: Map<string, number>
): {
  isCompliant: boolean;
  applicableMinimum: number;
  totalCompensation: number;
  shortfall: number;
  violationType: 'UMK' | 'UMP' | null;
} {
  const umk = umkData.get(check.locationCode);
  const ump = umpData.get(check.locationCode);
  const applicableMinimum = umk || ump || 0;
  const totalComp = calculateTotalCompensation(check);
  
  return {
    isCompliant: totalComp >= applicableMinimum,
    applicableMinimum,
    totalCompensation: totalComp,
    shortfall: Math.max(0, applicableMinimum - totalComp),
    violationType: totalComp < applicableMinimum ? (umk ? 'UMK' : 'UMP') : null
  };
}
```

## Edge Cases and Common Mistakes

1. **Perusahaan di provinsi dengan UMK lebih rendah**: Tetap harus bayar UMK wilayah tersebut
2. **Karyavan transferred ke wilayah berbeda**: Upah minimum yang berlaku adalah sesuai lokasi kerja baru
3. **Tunjangan tidak tetap**: Tidak dihitung untuk memenuhi minimum wage
4. **Kontrak menyatakan "gross-up" tapi kurang dari UMK**: Tetap violate hukum

## cekwajar.id Implementation Notes

- **File to update**: `src/data/umk-2025.json` (or Supabase table `regional_minimum_wages`)
- **Function to modify/create**: `getUMKByCity()`, `validateCityMinimumWage()`
- **Data source to query**: Supabase `regional_minimum_wages` table
- **Update frequency**: Annual (November/December)
- **Legion action**: YES - can auto-sync with official government API

## Monetization Angle
- Multi-location payroll compliance dashboard
- Automated alerts when employee relocated to higher minimum wage area
- Cost projection for expansion to new cities

## Sources and Cross-References
- Official URL: https://satudata.kemnaker.go.id/data/kumpulan-data/2252
- Dasar Hukum: PP 51/2023, Permenaker 16/2024
- Related: UMP 2025, UMSP/UMSK 2025
