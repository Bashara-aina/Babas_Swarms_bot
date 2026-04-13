---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/labor-law/005-ump-2025-provinsi.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.797982"
}
---

---
source_id: 005
title: "UMP 2025 Upah Minimum Provinsi Seluruh Indonesia"
source_type: MARKET_DATA
authority: OFFICIAL_GOV
url: "https://satudata.kemnaker.go.id/infografik/88"
last_verified: "2026-04-11"
tags: [ump2025,upah-minimum-provinsi,ump,labor-law,pengupahan]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# UMP 2025 Upah Minimum Provinsi Seluruh Indonesia

## Why This Matters for cekwajar.id
UMP 2025 adalah data terbaru yang wajib digunakan untuk memvalidasi kepatuhanupah minimum. Dengan kenaikan rata-rata 6,5%, system harus melakukan update otomatis untuk memastikan tidak ada employee yangupah-nya di bawah standard.

## Core Knowledge

### Ketentuan Utama UMP 2025

1. **Dasar Hukum**: Permenaker Nomor 16 Tahun 2024
2. **Kenaikan Rata-rata**: 6,5% dari UMP 2024
3. **Berlaku**: 1 Januari 2025

### Daftar UMP 2025 Seluruh Provinsi

| No | Provinsi | UMP 2025 (Rp) |
|----|---------|---------------|
| 1 | Aceh | 3.811.127 |
| 2 | Sumatra Utara | 3.174.526 |
| 3 | Sumatra Barat | 3.189.546 |
| 4 | Riau | 3.575.622 |
| 5 | Jambi | 3.194.837 |
| 6 | Sumatra Selatan | 3.334.981 |
| 7 | Bengkulu | 2.812.202 |
| 8 | Lampung | 2.914.834 |
| 9 | Bangka Belitung | 3.415.527 |
| 10 | Kepulauan Riau | 3.640.739 |
| 11 | DKI Jakarta | 5.396.760 |
| 12 | Jawa Barat | 4.942.018 |
| 13 | Jawa Tengah | 2.169.349 |
| 14 | DI Yogyakarta | 2.279.965 |
| 15 | Jawa Timur | 4.304.265 |
| 16 | Banten | 2.831.383 |
| 17 | Bali | 2.996.561 |
| 18 | Nusa Tenggara Barat | 2.655.105 |
| 19 | Nusa Tenggara Timur | 2.271.654 |
| 20 | Kalimantan Barat | 3.104.962 |
| 21 | Kalimantan Tengah | 3.335.005 |
| 22 | Kalimantan Selatan | 3.429.165 |
| 23 | Kalimantan Timur | 3.561.075 |
| 24 | Kalimantan Utara | 3.700.177 |
| 25 | Sulawesi Utara | 3.446.742 |
| 26 | Sulawesi Tengah | 2.878.626 |
| 27 | Sulawesi Selatan | 3.446.742 |
| 28 | Sulawesi Tenggara | 2.949.346 |
| 29 | Gorontalo | 2.842.558 |
| 30 | Sulawesi Barat | 2.871.654 |
| 31 | Maluku | 3.274.338 |
| 32 | Maluku Utara | 3.245.478 |
| 33 | Papua | 3.864.838 |
| 34 | Papua Barat | 3.864.838 |
| 35 | Papua Tengah | 3.580.000 |
| 36 | Papua Pegunungan | 3.580.000 |
| 37 | Papua Barat Daya | 3.580.000 |

### Formula Kenaikan UMP
```typescript
function hitungUMP2025(ump2024: number, kenaikanPersen: number = 0.065): number {
  return Math.round(ump2024 * (1 + kenaikanPersen));
}

function validasiUMP(upah: number, umpProvinsi: number): {
  compliant: boolean;
  deficit: number;
} {
  return {
    compliant: upah >= umpProvinsi,
    deficit: Math.max(0, umpProvinsi - upah)
  };
}
```

## Exact Formulas / Numbers (if applicable)

### TypeScript Interface
```typescript
interface UMPData {
  kodeProvinsi: string;
  namaProvinsi: string;
  ump2024: number;
  ump2025: number;
  tanggalBerlaku: Date;
  sumber: string;
}

interface ValidasiKepatuhanUMP {
  employeeId: string;
  provinceCode: string;
  currentWage: number;
  ump2025: number;
  isCompliant: boolean;
  shortfall: number;
}

function bulkValidateUMP(
  employees: Array<{ id: string; province: string; wage: number }>,
  umpMap: Map<string, number>
): ValidasiKepatuhanUMP[] {
  return employees.map(emp => ({
    employeeId: emp.id,
    provinceCode: emp.province,
    currentWage: emp.wage,
    ump2025: umpMap.get(emp.province) || 0,
    isCompliant: emp.wage >= (umpMap.get(emp.province) || 0),
    shortfall: Math.max(0, (umpMap.get(emp.province) || 0) - emp.wage)
  }));
}
```

## Edge Cases and Common Mistakes

1. **Apakahupah include tunjangan?**: Yang diperbandingkan adalah total compensation, termasuk tunjangan tetap
2. **Karyawan baru tidak penuh 1 tahun**: Tetap berhak atas UMK proporsional
3. **Freelancer/tenaga harian**: Tidak termasuk dalam ketentuan UMK
4. **UMK lebih tinggi dari UMP**: UMK adalah standar minimum untuk kabupaten/kota

## cekwajar.id Implementation Notes

- **File to update**: `src/data/ump-2025.json` (or Supabase table `regional_minimum_wages`)
- **Function to modify/create**: `getUMPByProvince()`, `validateEmployeeWage()`
- **Data source to query**: Supabase `regional_minimum_wages` table
- **Update frequency**: Annual (November/December)
- **Legion action**: YES - can auto-sync with Kemnaker API

## Monetization Angle
- Automated compliance alerts when wages fall belowUMP
- Payroll audit tools for labor law compliance
- Regional wage benchmarking reports

## Sources and Cross-References
- Official URL: https://satudata.kemnaker.go.id/infografik/88
- Permenaker 16/2024 tentang Penetapan Upah Minimum 2025
- Related: PP 36/2021, PP 51/2023, UMK 2025
