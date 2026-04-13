---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/labor-law/010-pp-pesangon-35-2021.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.857088"
}
---

---
source_id: 010
title: "PP 35 Tahun 2021 tentang Penyelesaian Perselisihan Hubungan Industrial"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://peraturan.bpk.go.id/Details/154582"
last_verified: "2026-04-11"
tags: [pp35-2021,pesangon,phk,uph,pengakhiran-hubungan-kerja]
cekwajar_impact: CRITICAL
legion_can_act: NO
---

# PP 35 Tahun 2021 tentang Penyelesaian Perselisihan Hubungan Industrial

## Why This Matters for cekwajar.id
PP 35/2021 mengatur kompensasi PHK yang meliputi uang pesangon (UP), uang penghargaan masa kerja (UPMK), dan uang penggantian hak (UPH). System harus calculate dengan tepat karena salah hitung adalah dispute utama.

## Core Knowledge

### Jenis Kompensasi PHK

1. **Uang Pesangon (UP)**
2. **Uang Penghargaan Masa Kerja (UPMK)**
3. **Uang Penggantian Hak (UPH)**

### Rumus Uang Pesangon (Pasal 40)

```typescript
interface PHKDetails {
  masaKerjaBulan: number;
  totalUpah: number; // Upah pokok + tunjangan tetap
  alasanPHK: string;
}

function hitungUangPesangon(details: PHKDetails): number {
  const { masaKerjaBulan, totalUpah } = details;
  const masaKerjaTahun = masaKerjaBulan / 12;
  
  // Rumus berdasarkan masa kerja (formula PP 35/2021)
  if (masaKerjaTahun < 1) {
    return totalUpah * 1;      // 1 bulan
  } else if (masaKerjaTahun < 2) {
    return totalUpah * 2;      // 2 bulan
  } else if (masaKerjaTahun < 3) {
    return totalUpah * 3;      // 3 bulan
  } else if (masaKerjaTahun < 4) {
    return totalUpah * 4;      // 4 bulan
  } else if (masaKerjaTahun < 5) {
    return totalUpah * 5;      // 5 bulan
  } else if (masaKerjaTahun < 6) {
    return totalUpah * 6;      // 6 bulan
  } else if (masaKerjaTahun < 7) {
    return totalUpah * 7;      // 7 bulan
  } else if (masaKerjaTahun < 8) {
    return totalUpah * 8;      // 8 bulan
  } else {
    return totalUpah * 10;     // maksimal 10 bulan
  }
}
```

### Rumus Uang Penghargaan Masa Kerja (Pasal 41)

```typescript
function hitungUPMK(masaKerjaBulan: number, totalUpah: number): number {
  const masaKerjaTahun = Math.floor(masaKerjaBulan / 12);
  
  if (masaKerjaTahun < 1) {
    return 0;
  } else if (masaKerjaTahun < 2) {
    return totalUpah * 1;      // 1 bulan
  } else if (masaKerjaTahun < 3) {
    return totalUpah * 2;      // 2 bulan
  } else if (masaKerjaTahun < 4) {
    return totalUpah * 3;      // 3 bulan
  } else if (masaKerjaTahun < 5) {
    return totalUpah * 4;      // 4 bulan
  } else if (masaKerjaTahun < 6) {
    return totalUpah * 5;      // 5 bulan
  } else if (masaKerjaTahun < 7) {
    return totalUpah * 6;      // 6 bulan
  } else if (masaKerjaTahun < 8) {
    return totalUpah * 7;      // 7 bulan
  } else {
    return totalUpah * 8;     // maksimal 8 bulan
  }
}
```

### Uang Penggantian Hak (UPH) (Pasal 46)

UPH meliputi:
1. Cuti tahunan yang belum diambil
2. Biaya pulang ke tempat diterima bekerja
3. Hal lain yang diatur dalam perjanjian kerja, PK, atau PP

```typescript
interface HakUPH {
  sisaCutiHari: number;
  biayaPulang: number;
  otherRights: number;
  dailyWage: number;
}

function hitungUPH(hak: HakUPH): number {
  return (
    (hak.sisaCutiHari * hak.dailyWage) +
    hak.biayaPulang +
    hak.otherRights
  );
}
```

### Faktor Pengali Berdasarkan Alasan PHK

| Alasan PHK | UP | UPMK | UPH |
|------------|-----|------|-----|
| Resign (oleh pekerja) | 0 | 0 | Ya |
| Masa kontrak habis | 0.5x | Ya | Ya |
| PHK oleh perusahaan (efisiensi) | 1x | Ya | Ya |
| PHK karena Merger | 1x | Ya | Ya |
| Perusahaan pailit | 1x | Ya | Ya |
| Kesalahan berat | 0 | 0 | Ya |

## Exact Formulas / Numbers (if applicable)

### Complete PHK Compensation Calculator
```typescript
interface PHKCompensation {
  alasanPHK: 
    | 'resign'
    | 'contract_expired'
    | 'company_efficiency'
    | 'merger'
    | 'bankruptcy'
    | 'serious_misconduct';
  masaKerjaBulan: number;
  upahPokok: number;
  tunjanganTetap: number;
  sisaCutiHari: number;
  jarakTempuhPulang: number;
}

function calculateTotalPHKCompensation(data: PHKCompensation): {
  uangPesangon: number;
  uangPenghargaanMasaKerja: number;
  uangPenggantianHak: number;
  total: number;
  breakdown: string[];
} {
  const totalUpah = data.upahPokok + data.tunjanganTetap;
  const dailyWage = totalUpah / 30;
  
  let uangPesangon = 0;
  let uangPenghargaanMasaKerja = 0;
  
  // Calculate based on reason
  if (data.alasanPHK === 'serious_misconduct') {
    // No UP or UPMK for serious misconduct
    uangPesangon = 0;
    uangPenghargaanMasaKerja = 0;
  } else if (data.alasanPHK === 'resign') {
    // Resign - no UP, negotiate for UPMK
    uangPesangon = 0;
    uangPenghargaanMasaKerja = 0; // Unless negotiated
  } else {
    // Standard calculation
    const faktorPengali = data.alasanPHK === 'contract_expired' ? 0.5 : 1;
    uangPesangon = hitungUangPesangon(data) * faktorPengali;
    uangPenghargaanMasaKerja = hitungUPMK(data.masaKerjaBulan, totalUpah);
  }
  
  const uangPenggantianHak = 
    (data.sisaCutiHari * dailyWage) +
    data.jarakTempuhPulang;
  
  return {
    uangPesangon: Math.round(uangPesangon),
    uangPenghargaanMasaKerja: Math.round(uangPenghargaanMasaKerja),
    uangPenggantianHak: Math.round(uangPenggantianHak),
    total: Math.round(uangPesangon + uangPenghargaanMasaKerja + uangPenggantianHak),
    breakdown: [
      `UP: ${Math.round(uangPesangon)}`,
      `UPMK: ${Math.round(uangPenghargaanMasaKerja)}`,
      `UPH: ${Math.round(uangPenggantianHak)}`
    ]
  };
}
```

## Edge Cases and Common Mistakes

1. **Masa kerja dihitung wrong**: Gunakan kalender, bukan tanggal ke tanggal
2. ** THR tidak termasuk dalam dasar perhitungan pesangon**: Hanya pokok + tunjangan tetap
3. **Uang makan dan transport termasuk**: Tidak, jika berdasarkan kehadiran (tidak tetap)
4. **PHK karena ошибка perusahaan**: Tidak otomatis kehilangan pesangon

## cekwajar.id Implementation Notes

- **File to update**: `src/lib/payroll/phk-calculator.ts`
- **Function to modify/create**: `calculatePHKCompensation()`, `getApplicableMultiplier()`
- **Data source to query**: Employee records, attendance for leave balance
- **Update frequency**: On termination event
- **Legion action**: NO - requires HR/legal review per case

## Monetization Angle
- PHK calculator for HR departments
- Dispute prevention through accurate calculations
- Compliance documentation generator

## Sources and Cross-References
- Official URL: https://peraturan.bpk.go.id/Details/154582
- Related: UU 13/2003, UU 11/2020, PP 36/2021
