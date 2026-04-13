---
source_id: 014
title: "Tunjangan Wajib dan Tunjangan Umum Karyawan Indonesia"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://www.talenta.co/blog/contoh-tunjangan-tetap-karyawan-yang-harus-diketahui/"
last_verified: "2026-04-11"
tags: [tunjangan,tunjangan-tetap,tunjangan-tidak-tetap,tunjangan-jabatan,tunjangan-makan,thr]
cekwajar_impact: HIGH
legion_can_act: YES
---

# Tunjangan Wajib dan Tunjangan Umum Karyawan Indonesia

## Why This Matters for cekwajar.id
Klasifikasi tunjangan (tetap vs tidak tetap) mempengaruhi banyak calculation: dasarupah minimum, perhitunganpesangon, iuran BPJS, dan PPh 21. Mistakes in classification lead to compliance issues.

## Core Knowledge

### Jenis-Jenis Tunjangan

#### A. Tunjangan Wajib (Yang diatur undang-undang)

| Tunjangan | Dasar Hukum | Keterangan |
|-----------|------------|------------|
| **THR** | Permenaker 6/2016 | 1 bulan upah (atau proporsional) |
| **BPJS Kesehatan** | UU 40/2011 | 4% dari pemberi kerja |
| **BPJS Ketenagakerjaan** | UU 40/2004 | JKK, JKM, JHT, JP |
| **Tunjangan Pensiun** | Opsional | Bisa jadi wajib untuk perusahaan tertentu |

#### B. Tunjangan Tidak Tetap (Tidak dihitung sebagai dasarupah)

| Tunjangan | Keterangan |
|-----------|------------|
| **Uang makan** | Jika berdasarkan kehadiran |
| **Uang transport** | Jika berdasarkan kehadiran |
| **Tunjangan komunikasi** | Jika berdasarkan penggunaan |

#### C. Tunjangan Tetap (Dihitung sebagai dasarupah)

| Tunjangan | Keterangan |
|-----------|------------|
| **Tunjangan jabatan** | Sudah pasti setiap bulan |
| **Tunjangan keluarga** | Sudah pasti setiap bulan |
| **Tunjangan kinerja** | Jika tetap/bulan |

### Perbedaan Kunci

```
Tunjangan Tetap = Diperhitungkan dalam:
  - Dasar upah minimum
  - Perhitungan pesangon
  - Perhitungan iuran BPJS
  - Dasar perhitungan PPh 21

Tunjangan Tidak Tetap = TIDAK diperhitungkan dalam:
  - Dasar upah minimum
  - Perhitungan pesangon
  - Perhitungan iuran BPJS
  - (tetapi tetap kena PPh 21)
```

```typescript
interface Tunjangan {
  nama: string;
  jumlah: number;
  jenis: 'tetap' | 'tidak-tetap';
  qualifiesAs: 'basic' | 'allowance';
}

function hitungKomponenUpah(tunjanganList: Tunjangan[]): {
  dasarUpahMin: number;  // Untuk perhitungan UMK
  dasarBPJS: number;     // Untuk perhitungan iuran
  dasarPesangon: number;  // Untuk perhitungan PHK
} {
  let dasarUpahMin = 0;
  let dasarBPJS = 0;
  let dasarPesangon = 0;
  
  for (const t of tunjanganList) {
    if (t.jenis === 'tetap') {
      dasarUpahMin += t.jumlah;
      dasarBPJS += t.jumlah;
      dasarPesangon += t.jumlah;
    }
    // Tunjangan tidak tetap tidak masuk komponen
  }
  
  return { dasarUpahMin, dasarBPJS, dasarPesangon };
}
```

## Exact Formulas / Numbers (if applicable)

### TypeScript Implementation
```typescript
enum AllowanceType {
  FIXED = 'fixed',           // Tetap - included in calculations
  NON_FIXED = 'non-fixed'    // Tidak tetap - excluded from calculations
}

interface Allowance {
  id: string;
  name: string;
  amount: number;
  type: AllowanceType;
  frequency: 'monthly' | 'daily' | 'per-use';
  condition: 'always' | 'attendance-based' | 'usage-based';
}

function classifyAllowance(
  name: string,
  amount: number,
  frequency: string,
  condition: string
): AllowanceType {
  // Always included regardless of amount
  if (['tunjangan jabatan', 'tunjangan keluarga', 'tunjangan kendaraan'].includes(name.toLowerCase())) {
    return AllowanceType.FIXED;
  }
  
  // Based on attendance/usage - not included
  if (condition === 'attendance-based' || condition === 'usage-based') {
    return AllowanceType.NON_FIXED;
  }
  
  // If always given regardless - included
  if (frequency === 'monthly' && condition === 'always') {
    return AllowanceType.FIXED;
  }
  
  return AllowanceType.NON_FIXED;
}

function calculateComponentsForCalculations(
  basicSalary: number,
  allowances: Allowance[]
): {
  minimumWageBase: number;
  bpjsBase: number;
  severanceBase: number;
  pph21Gross: number;
} {
  const includedAllowances = allowances
    .filter(a => a.type === AllowanceType.FIXED)
    .reduce((sum, a) => sum + a.amount, 0);
  
  return {
    minimumWageBase: basicSalary + includedAllowances,
    bpjsBase: basicSalary + includedAllowances, // capped at 12jt
    severanceBase: basicSalary + includedAllowances,
    pph21Gross: basicSalary + allowances.reduce((sum, a) => sum + a.amount, 0) // all allowances included in PPh
  };
}

// Note: PPh 21 includes ALL allowances (both fixed and non-fixed)
// But minimum wage, BPJS, and severance ONLY include fixed allowances
```

### Batas Maksimum BPJS
```typescript
const BPJS_SALARY_CAP = 12000000; // 12 juta

function calculateBPJSContributions(
  basicSalary: number,
  fixedAllowances: number,
  riskLevel: 'rendah' | 'sedang' | 'tinggi'
): {
  health: { employee: number; employer: number };
  employment: { jkk: number; jkm: number; jht: number; jp: number };
} {
  const bpjsBase = Math.min(basicSalary + fixedAllowances, BPJS_SALARY_CAP);
  
  const jkkRate = { rendah: 0.0024, sedang: 0.0054, tinggi: 0.0127 };
  
  return {
    health: {
      employee: bpjsBase * 0.01,
      employer: bpjsBase * 0.04
    },
    employment: {
      jkk: bpjsBase * jkkRate[riskLevel],
      jkm: bpjsBase * 0.003,
      jht: bpjsBase * 0.057,
      jp: bpjsBase * 0.03
    }
  };
}
```

## Edge Cases and Common Mistakes

1. **Tunjangan makan bulanan tetap**: Jika jumlah tetap per bulan, classified as tetap. Jika berdasarkan kehadiran, non-tetap.
2. **Tunjangan transport adjustment**: Jika perusahaan memberi "uang bensin" berdasarkan jarak, tetap non-tetap.
3. **Komunikasi quarterly allowance**: Jika secara berkala dan pasti, classified sebagai tetap.
4. **Tunjangan kinerja (bonus)**: Tidak termasuk tetap karena terkait performance.

## cekwajar.id Implementation Notes

- **File to update**: `src/lib/payroll/allowance-classifier.ts`
- **Function to modify/create**: `classifyAllowance()`, `calculateAllBases()`
- **Data source to query**: Allowance configuration per company
- **Update frequency**: When allowance structure changes
- **Legion action**: YES - can auto-classify allowances based on rules

## Monetization Angle
- Allowance classification engine
- Compliance calculator for multiple purposes
- Audit trail for payroll decisions

## Sources and Cross-References
- UU 13/2003
- PP 36/2021
- UU 40/2004 (SJSN)
- UU 40/2011 (BPJS)
- Permenaker 6/2016 (THR)
