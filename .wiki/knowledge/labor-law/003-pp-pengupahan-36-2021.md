---
source_id: 003
title: "PP 36 Tahun 2021 tentang Pengupahan"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://peraturan.bpk.go.id/Details/161909"
last_verified: "2026-04-11"
tags: [labor-law,pp36-2021,pengupahan,upah-minimum,struktur-upah]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# PP 36 Tahun 2021 tentang Pengupahan

## Why This Matters for cekwajar.id
PP 36/2021 adalah dasar perhitungan upah minimum dan struktur gaji di Indonesia. Payroll system harus mengimplementasikan formula ini untuk menghitung kepatuhan terhadap UMK/UMP dan memastikan tidak ada worker yang dibayar di bawah minimum.

## Core Knowledge

### Ruang Lingkup PP 36/2021

1. **Kebijakan Pengupahan**
2. **Penetapan Upah** (satuan waktu/satuan hasil)
3. **Struktur dan Skala Upah**
4. **Upah Minimum**
5. **Upah Terendah**
6. **Upah Lembur**
7. **Pembayaran Upah**
8. **Pelaporan Pengupahan**

### Formula Perhitungan Upah Minimum (Sebelum PP 51/2023)

```
UMn = UMt × (1 + α)
```
Dimana:
- UMn = Upah Minimum tahun depan
- UMt = Upah Minimum tahun berjalan
- α = Penyesuaian (inflasi + pertumbuhan ekonomi)

Dengan variabel:
- Batas atas (BA) = UMt × 1,10
- Batas bawah (BB) = UMt × 0,90

### Komponen Upah yang Diperhitungkan

Menurut PP 36/2021 Pasal 9:
- **Upah pokok** minimal 75% dari total upah
- **Tunjangan tetap** maksimal 25% dari total upah

```typescript
interface UpahComponents {
  upahPokok: number;
  tunjanganTetap: number;
  tunjanganTidakTetap: number;
}

function hitungTotalUpah({ upahPokok, tunjanganTetap, tunjanganTidakTetap }: UpahComponents): number {
  return upahPokok + tunjanganTetap + tunjanganTidakTetap;
}

function validateUpahPokok(totalUpah: number, upahPokok: number): boolean {
  const minimumPokok = totalUpah * 0.75;
  return upahPokok >= minimumPokok;
}
```

### Jatuh Tempo Pembayaran Upah
- Pembayaran interval maksimal 1 bulan
- Jika terlambat, dikenakan bunga 1% per hari dari upah yang terlambat dibayar

## Exact Formulas / Numbers (if applicable)

### Formula Upah Per Jam
```typescript
function hitungUpahPerJam(upahSebulan: number): number {
  // Dasar: 173 jam per bulan ( untuk 40 jam/minggu × 52 minggu / 12 bulan )
  return upahSebulan / 173;
}

function hitungUpahPerJamDetail(upahSebulan: number): {
  perJam: number;
  perJamLembur1: number;  // 1.5x
  perJamLemburLebih: number; // 2x
} {
  const perJam = upahSebulan / 173;
  return {
    perJam: Math.round(perJam * 1000000) / 1000000,
    perJamLembur1: Math.round(perJam * 1.5 * 1000000) / 1000000,
    perJamLemburLebih: Math.round(perJam * 2 * 1000000) / 1000000
  };
}
```

### Formula Upah Minimum dengan PP 51/2023 (Yang berlaku sekarang)
```typescript
// PP 51/2023 menghapus batas atas dan bawah
function hitungUpahMinimum2024(
  umt: number,           // Upah Minimum tahun berjalan
  inflasi: number,        // Inflasi (desimal, misal 0.03 untuk 3%)
  pertumbuhanEko: number  // Pertumbuhan ekonomi (desimal, misal 0.05 untuk 5%)
): number {
  const alpha = inflasi + pertumbuhanEko;
  return Math.round(umt * (1 + alpha));
}
```

## Edge Cases and Common Mistakes

1. **Tunjangan tidak tetap sebagai komponen upah**: Jika tunjangan makan/transport berdasarkan kehadiran, tidak termasuk dalam perhitungan upah minimum
2. **Kontrak kerja menyebut "gross" tapi komponen dijelaskan": Harus dijumlahkan semua komponen tetap untuk memastikan di atas UMK
3. **Perusahaan baru yang belum punya struktur upah**: Wajib menyusun struktur dan skala upah dalam 6 bulan setelah berdiri
4. **Penggunaan "rate" harian/jam": Harus dikonversi ke bulanan untuk cek kepatuhan UMK

## cekwajar.id Implementation Notes

- **File to update**: `src/lib/payroll/wage-compliance.ts`
- **Function to modify/create**: `calculateMinimumWageCompliance()`, `validateWageStructure()`
- **Data source to query**: Supabase table `regional_minimum_wages`
- **Update frequency**: Annually (November) for wage updates
- **Legion action**: YES - can auto-update UMK data from official sources

## Monetization Angle
- Automated minimum wage compliance checking
- Real-time alerts when employee wages fall below UMK
- Payroll audit trail for labor law compliance

## Sources and Cross-References
- Official URL: https://peraturan.bpk.go.id/Details/161909
- Diubah oleh: PP 51/2023
- Related: UU 13/2003, UU 11/2020, Permenaker 1/2017
