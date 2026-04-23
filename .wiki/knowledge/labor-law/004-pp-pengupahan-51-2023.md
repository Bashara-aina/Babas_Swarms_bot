---
title: Pp Pengupahan 51 2023
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- labor-law
created: '2026-04-14'
updated: '2026-04-14'
summary: PP 51/2023 membawa perubahan signifikan yaitu penghapusan batas atas dan
 batas bawah dalam formula perhitungan upah minimum. Ini mempengaruhi cara cekwajar.id
 memvalidasi kepatuhan dan menghitung p...
wikilinks: []
confidence: medium
source: research
---

# PP 51 Tahun 2023 Perubahan Kedua PP 36/2021 Pengupahan

## Why This Matters for cekwajar.id
PP 51/2023 membawa perubahan signifikan yaitu penghapusan batas atas dan batas bawah dalam formula perhitungan upah minimum. Ini mempengaruhi cara cekwajar.id memvalidasi kepatuhan dan menghitung penyesuaian upah tahunan.

## Core Knowledge

### Perubahan Utama PP 51/2023 dari PP 36/2021

1. **Penghapusan Batas Atas dan Bawah**
 - PP 36/2021 menggunakan: BA = UMt × 1,10 dan BB = UMt × 0,90
 - PP 51/2023 menghapus variabel ini
 - Sekarang menggunakan formula yang lebih sederhana

2. **Variabel Baru dalam Formula**
 - Pertumbuhan ekonomi (δ)
 - Inflasi (π)
 - ( = pertumbuhan ekonomi yang melebihi ekspektasi)

3. **Dewan Pengupahan**
 - Peran dewan pengupahan daerah diperkuat
 - Recommends penyesuaian upah minimum kepada Gubernur

### Formula Baru (PP 51/2023)

```
UM_{n+1} = UM_n × (1 + α')
```

Dimana:
- UM_{n+1} = Upah Minimum tahun berikutnya
- UM_n = Upah Minimum tahun berjalan
- α' = δ + π + () 

Dengan penjelasan:
- δ (delta) = Pertumbuhan ekonomi
- π (pi) = Inflasi
- () = berupa selisih pertumbuhan ekonomi riil terhadap pertumbuhan ekonomi potensial

### Nilai alpha maksimal 10%
```typescript
const ALPHA_MAX = 0.10; // 10%

function hitungPenyesuaianUpahMinimum(
 umTahunBerjalan: number,
 pertumbuhanEko: number,
 inflasi: number,
 : number = 0
): number {
 const alpha = Math.min(
 pertumbuhanEko + inflasi +,
 ALPHA_MAX
 );
 return Math.round(umTahunBerjalan * (1 + alpha));
}
```

## Exact Formulas / Numbers (if applicable)

### Implementasi TypeScript untuk PP 51/2023
```typescript
interface PenyesuaianUpahMinimum {
 umTahunBerjalan: number;
 pertumbuhanEko: number; // dalam desimal (0.05 = 5%)
 inflasi: number; // dalam desimal (0.03 = 3%)
 : number; // dalam desimal
 provKabCode: string;
 tahun: number;
}

function hitungUMDenganPP51(params: PenyesuaianUpahMinimum): {
 umBaru: number;
 alpha: number;
 komponenAlpha: {
 pertumbuhanEko: number;
 inflasi: number;
 : number;
 };
} {
 const { umTahunBerjalan, pertumbuhanEko, inflasi, } = params;
 
 const alpha = Math.min(
 pertumbuhanEko + inflasi +,
 0.10 // maksimal 10%
 );
 
 return {
 umBaru: Math.round(umTahunBerjalan * (1 + alpha)),
 alpha: Math.round(alpha * 1000000) / 1000000,
 komponenAlpha: {
 pertumbuhanEko: Math.round(pertumbuhanEko * 1000000) / 1000000,
 inflasi: Math.round(inflasi * 1000000) / 1000000,
 : Math.round( * 1000000) / 1000000
 }
 };
}
```

## Edge Cases and Common Mistakes

1. **Tidak memperhitungkan**: Pertumbuhan ekonomi di atas potensial bisa menambah α'
2. **Alpha melebihi 10%**: Dibatasi menjadi 10% meskipun penjumlahan komponen lebih tinggi
3. **Provinsi vs Kabupaten/Kota**: UMK harus lebih tinggi dari UMP, UMK sektoral harus lebih tinggi dari UMK
4. **Timing penetapan**: Harus ditetapkan paling lambat 21 November tahun berjalan

## cekwajar.id Implementation Notes

- **File to update**: `src/lib/payroll/wage-calculator.ts`
- **Function to modify/create**: `calculateRegionalMinimumWage()`, `getAlphaComponents()`
- **Data source to query**: BPS untuk data pertumbuhan ekonomi dan inflasi
- **Update frequency**: Annual, update November
- **Legion action**: YES - can fetch and process official wage data

## Monetization Angle
- Wage forecasting and planning tools
- Regional wage comparison analytics
- Automated compliance reporting for audit

## Sources and Cross-References
- Official URL: https://peraturan.bpk.go.id/Details/270269
- Mengubah: PP 36/2021
- Related: PP 49/2025 (Perubahan Kedua), Permenaker 16/2024
