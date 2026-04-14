---
source_id: 031
title: "Iuran BPJS Ketenagakerjaan: JHT, JP, JKK, JKM untuk Karyawan Swasta"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://www.bpjsketenagakerjaan.go.id/artikel/18913/artikel-berapa-besaran-iuran-jht,-jkk,-jkm,-jp-dan-jkp"
last_verified: "2026-04-11"
tags: [bpjs-ketenagakerjaan, iuran, jht, jp, jkk, jkm, pph21, labor-law, saas, hrtech]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# Iuran BPJS Ketenagakerjaan: JHT, JP, JKK, JKM untuk Karyawan Swasta

## Why This Matters for cekwajar.id
BPJS Ketenagakerjaan is a mandatory program with 5 sub-programs (JHT, JP, JKK, JKM, JKP), each with different rates, caps, and employer/employee splits. Incorrect calculation leads to non-compliance, employee disputes, and potential penalties. This is a core payroll feature.

## Core Knowledge

### 1. Jaminan Hari Tua (JHT)
**Iuran: 5.7% dari upah sebulan**
- 2% dibayar pekerja
- 3.7% dibayar perusahaan
- Tidak ada batas atas (upa penuh)

**Manfaat**: Uang tunai saat:
- Usia 56 tahun
- PHK
- Cacat total tetap
- Meninggal dunia

### 2. Jaminan Kecelakaan Kerja (JKK)
**Iuran: 0.24% - 1.74% dari upah** (berdasarkan tingkat risiko, ditanggung perusahaan)
- Sangat rendah: 0.24% (staff administrasi)
- Rendah: 0.54% (kasir, cleaning)
- Sedang: 0.89% (operator produksi)
- Tinggi: 1.27% (pekerja pabrik)
- Sangat tinggi: 1.74% (konstruksi, tambang)

**Catatan**: Industri padat karya (makanan, minuman, tekstil, furnitur) dapat keringanan 50% untuk periode tertentu.

### 3. Jaminan Kematian (JKM)
**Iuran: 0.30% dari upah** (ditanggung perusahaan)
**Total manfaat**: Rp 42 juta + beasiswa anak hingga Rp 174 juta

### 4. Jaminan Pensiun (JP)
**Iuran: 3% dari upah**
- 1% dibayar pekerja
- 2% dibayar perusahaan
- **Batas atas**: Rp 10.547.000/bulan (per Maret 2025)

**Manfaat**: Uang bulanan atau sekaligus saat usia pensiun/cacat/meninggal

### 5. Jaminan Kehilangan Pekerjaan (JKP)
**Iuran: 0.36% dari upah**
- Pemerintah Pusat: 0.22%
- Rekomposisi JKK: 0.14%
- **Tidak ada iuran dari pekerja**

**Manfaat**: 60% upah selama 6 bulan + info lowongan + pelatihan

## Exact Formulas / Numbers (if applicable)
```typescript
// BPJS Ketenagakerjaan - Semua Program
interface BpjsTkContribution {
  jht: {
    employee: number;   // 2% dari upah
    employer: number;   // 3.7% dari upah
    total: number;      // 5.7%
  };
  jkk: {
    rate: number;       // 0.24% - 1.74% berdasarkan risiko
    employer: number;   // 100% ditanggung perusahaan
  };
  jkm: {
    employer: number;   // 0.30%
  };
  jp: {
    employee: number;   // 1%
    employer: number;   // 2%
    total: number;      // 3%
    cap: number;        // Rp 10.547.000
  };
  jkp: {
    government: number;  // 0.22%
    fromJkk: number;    // 0.14%
  };
}

function calculateBpjsTk(
  monthlySalary: number,
  jkkRiskRate: number = 0.54  // default: rendah
): BpjsTkContribution {
  const JHT_EMPLOYEE_RATE = 0.02;
  const JHT_EMPLOYER_RATE = 0.037;
  const JKK_RATE = jkkRiskRate;
  const JKM_RATE = 0.003;
  const JP_EMPLOYEE_RATE = 0.01;
  const JP_EMPLOYER_RATE = 0.02;
  const JP_CAP = 10_547_000;
  const JKP_GOV_RATE = 0.0022;
  const JKP_FROM_JKK_RATE = 0.0014;

  const jhtEmployee = Math.floor(monthlySalary * JHT_EMPLOYEE_RATE);
  const jhtEmployer = Math.floor(monthlySalary * JHT_EMPLOYER_RATE);

  const jkkEmployer = Math.floor(monthlySalary * JKK_RATE);

  const jkmEmployer = Math.floor(monthlySalary * JKM_RATE);

  const jpCappedSalary = Math.min(monthlySalary, JP_CAP);
  const jpEmployee = Math.floor(jpCappedSalary * JP_EMPLOYEE_RATE);
  const jpEmployer = Math.floor(jpCappedSalary * JP_EMPLOYER_RATE);

  const jkpGov = Math.floor(monthlySalary * JKP_GOV_RATE);
  const jkpFromJkk = Math.floor(monthlySalary * JKP_FROM_JKK_RATE);

  return {
    jht: {
      employee: jhtEmployee,
      employer: jhtEmployer,
      total: jhtEmployee + jhtEmployer
    },
    jkk: {
      rate: JKK_RATE,
      employer: jkkEmployer
    },
    jkm: {
      employer: jkmEmployer
    },
    jp: {
      employee: jpEmployee,
      employer: jpEmployer,
      total: jpEmployee + jpEmployer,
      cap: JP_CAP,
      usedCap: jpCappedSalary < monthlySalary
    },
    jkp: {
      government: jkpGov,
      fromJkk: jkpFromJkk
    }
  };
}

// Contoh: Gaji Rp 6.000.000, risiko rendah (0.54%)
// JHT: employee Rp 120.000, employer Rp 222.000, total Rp 342.000
// JKK: Rp 32.400
// JKM: Rp 18.000
// JP: employee Rp 60.000, employer Rp 120.000, total Rp 180.000
// JKP: pemerintah Rp 13.200, dari JKK Rp 8.400
```

## Edge Cases and Common Mistakes
1. **JP cap not applied**: Gaji di atas Rp 10.547.000 harus di-cap, bukan dihitung penuh
2. **JKK rate wrong**: Tidak semua karyawan punya risiko 0.54% - perlu mapping berdasarkan jabatan
3. **JKP double counting**: JKP bukan dari pekerja, tidak boleh potong dari gaji
4. **Industri keringanan**: Jangan lupa cek apakah perusahaan masuk daftar industri padat karya
5. **Pro rate bulan pertama**: Jika masuk tengah bulan, hitung proporsional

## cekwajar.id Implementation Notes
- **File to update**: `src/core/payroll/bpjs-tk.ts` or similar
- **Function to modify/create**: `calculateAllBpjsTk(salary: number, riskCategory: RiskCategory): BpjsTkContribution`
- **Data source to query**: Risk category from employee job type, JP cap from regulation config
- **Update frequency**: JP cap changes annually (typically March); JKK rates rarely change
- **Legion action**: Can update with new regulation; needs Bashara for rate table config

## Monetization Angle
- Mandatory compliance = reliable recurring revenue
- Accurate calculation prevents penalties and employee disputes
- Reporting for HR audit and tax purposes

## Sources and Cross-References
- Official URL: https://www.bpjsketenagakerjaan.go.id/
- PP No. 6 Tahun 2025 tentang JKK dan JKM
- PP No. 7 Tahun 2025 tentang JP (batas upah terbaru Rp 10.547.400)
- Related: 032-batas-upah.md, 033-jht-klaim.md, 034-jp-manfaat.md
