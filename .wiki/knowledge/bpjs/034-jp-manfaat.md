---
title: Jp Manfaat
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- bpjs
created: '2026-04-14'
updated: '2026-04-14'
summary: Jaminan Pensiun provides monthly income after retirement or in case of disability/death.
  The benefit calculation is complex (actuarial formula) and the wage cap affects
  contributions. Understanding...
wikilinks: []
confidence: medium
source: research
---

# Jaminan Pensiun (JP) BPJS: Manfaat Bulanan dan Formula Perhitungan

## Why This Matters for cekwajar.id
Jaminan Pensiun provides monthly income after retirement or in case of disability/death. The benefit calculation is complex (actuarial formula) and the wage cap affects contributions. Understanding this helps build accurate retirement planning and termination modules.

## Core Knowledge

### Jenis Manfaat JP

#### 1. Manfaat Pensiun (Bulanan)
Diberikan kepada peserta yang:
- Memasuki usia pensiun (56 tahun)
- Mengalami cacat total tetap
- Meninggal dunia (kepada janda/duda/anak)

**Formula Manfaat Pensiun:**
```
MP = 1% × MI × PDP × FP

Dimana:
MP = Manfaat Pensiun per bulan
MI = Masa Iur (bulan ke-i, max 20 tahun untuk pensiunan lama)
PDP = Penghasilan Dasar Pensiun (rata-rata 3 tahun terakhir, di-cap)
FP = Faktor Pengali (berdasarkan usia saat mulai menerima manfaat)
```

**Batas manfaat minimum**: Rp 300.000/bulan (sesuai PP 45/2015)

#### 2. Manfaat Pensiun Lump Sum (Sekaligus)
Untuk peserta dengan masa iur pendek atau pilihan pembayaran sekaligus.

#### 3. Manfaat Cacat
Jika cacat sebelum masa iur cukup, mendapat manfaat cacat.

#### 4. Manfaat Meninggal
50% dari formula manfaat pensiun untuk ahli waris.

### Batas Penghasilan untuk Perhitungan JP

**Batas atas upah**: Rp 10.547.400/bulan (berlaku Maret 2025)

Jika upah di atas batas, perhitungan menggunakan batas tersebut.

### Usia Pensiun
- **Usia normal**: 56 tahun
- **Early retirement**: Bisa dari 45 tahun dengan syarat tertentu
- **Deferred**: Ditunda maksimal sampai 65 tahun

## Exact Formulas / Numbers (if applicable)
```typescript
interface JpBenefitCalculation {
  averageSalary3Years: number;  // Rata-rata 3 tahun terakhir (di-cap)
  cappedSalary: number;         // Upah yang digunakan (min with cap)
  monthsContributed: number;    // Masa iur dalam bulan
  retirementAge: number;        // Usia saat mulai pensiun
  monthlyBenefit: number;      // Manfaat bulanan
  lumpSumBenefit?: number;     // Manfaat sekaligus (jika ada)
}

function calculateMonthlyPensionBenefit(params: {
  monthlySalaries: number[];  // Gaji 36 bulan terakhir
  retirementAge: number;
  contributionMonths: number;
  annualReturnRate?: number;   // Tingkat pengembangan (default dari BPJS)
}): JpBenefitCalculation {
  
  const JP_CAP = 10_547_400;
  
  // Hitung rata-rata 3 tahun (36 bulan terakhir)
  const last36 = params.monthlySalaries.slice(-36);
  const avg36 = last36.reduce((a, b) => a + b, 0) / last36.length;
  
  // Apply wage cap
  const cappedSalary = Math.min(avg36, JP_CAP);
  
  // Masa Iur (dibagi 12 untuk konversi tahun ke bulan effect)
  // Max 20 tahun untuk formula
  const maxMonths = 20 * 12;  // 240 bulan
  const effectiveMonths = Math.min(params.contributionMonths, maxMonths);
  
  // Faktor pengali berdasarkan usia (formula aktuarial sederhana)
  const fp = calculateActuarialFactor(params.retirementAge);
  
  // Formula: 1% x MI/12 x PDP x FP
  const monthlyBenefit = 0.01 * (effectiveMonths / 12) * cappedSalary * fp;
  
  // Minimum benefit Rp 300.000
  const finalBenefit = Math.max(monthlyBenefit, 300_000);
  
  return {
    averageSalary3Years: Math.round(avg36),
    cappedSalary,
    monthsContributed: params.contributionMonths,
    retirementAge: params.retirementAge,
    monthlyBenefit: Math.round(finalBenefit)
  };
}

function calculateActuarialFactor(age: number): number {
  // Faktor pengali berdasarkan tabel aktuarial
  // Ini adalah perkiraan sederhana, actual dari tabel BPJS
  if (age <= 56) return 1.0;
  if (age <= 60) return 0.95;
  if (age <= 65) return 0.85;
  return 0.75;
}
```

## Edge Cases and Common Mistakes
1. **Not applying cap**: Using actual salary instead of capped for average calculation
2. **Wrong 3-year average**: Should be last 36 months, not calendar year
3. **Confusing with JHT**: JP is different program, different benefit formula
4. **Minimum benefit**: Know Rp 300.000 minimum, not all get higher
5. **Early retirement reduced benefits**: Factor decreases if retired before 56

## cekwajar.id Implementation Notes
- **File to update**: `src/modules/hr/retirement.ts` or benefit calculation module
- **Function to modify/create**: `calculateMonthlyPension(salaries: number[], age: number, months: number): PensionBenefit`
- **Data source to query**: Historical salary data (3 years), employee birth date for age calculation
- **Update frequency**: Cap changes annually; formula rarely changes
- **Legion action**: Can build simulation module for employees to estimate their pension; needs actual salary history data

## Monetization Angle
- Retirement planning tool for employees
- HR module for termination/deceased employee benefits
- Integration with payroll for accurate DPLK/pension deductions

## Sources and Cross-References
- Official URL: https://www.bpjsketenagakerjaan.go.id/
- PP No. 45 Tahun 2015 tentang JP
- Related: 031-bpjs-ketenagakerjaan-iuran.md, 032-batas-upah.md
