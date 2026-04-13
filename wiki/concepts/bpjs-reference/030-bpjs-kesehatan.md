---
source_id: 030
title: "Iuran BPJS Kesehatan 2024: Perhitungan untuk Pekerja Swasta"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://www.liputan6.com/bisnis/read/5595301/daftar-lengkap-iuran-bpjs-kesehatan-2024-dan-dendanya"
last_verified: "2026-04-11"
tags: [bpjs-kesehatan, iuran, pph21, umr, labor-law, saas, hrtech, payroll]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# Iuran BPJS Kesehatan 2024: Perhitungan untuk Pekerja Swasta

## Why This Matters for cekwajar.id
BPJS Kesehatan is a mandatory deduction for every employee in Indonesia. Incorrect calculation causes compliance violations, employee complaints, and potential penalties. This is a core payroll feature that must be accurate to the rupiah.

## Core Knowledge

### Peserta Penerima Upah (PPU) - Swasta
Berdasarkan Perpres No. 59 Tahun 2024 dan Perpres No. 82 Tahun 2018:

**Iuran sebesar 5% dari gaji/upah per bulan:**
- 4% ditanggung pemberi kerja (perusahaan)
- 1% ditanggung peserta (potongan gaji)

### Kategori Peserta Lainnya:
1. **PNS/TNI/Polri**: 5% (4% pemberi kerja, 1% peserta)
2. **Keluarga Tambahan** (anak ke-4+, ayah, ibu, mertua): 1% dari gaji per orang per bulan, dibayar pekerja
3. **Peserta Mandiri (Bukan Penerima Upah)**:
   - Kelas I: Rp 150.000/bulan
   - Kelas II: Rp 100.000/bulan
   - Kelas III: Rp 42.000/bulan (dengan bantuan iuran pemerintah Rp 7.000)

### Pembayaran Iuran
- Paling lambat tanggal 10 setiap bulan
- Tidak ada denda keterlambatan sejak 1 Juli 2016
- Denda pelayanan 5% dari biaya diagnosa awal × bulan tertunggak (maks 12 bulan, maks Rp 30 juta)

## Exact Formulas / Numbers (if applicable)
```typescript
// BPJS Kesehatan - Pekerja Swasta (Penerima Upah)
interface BpjsKesehatanEmployee {
  grossSalary: number;
  bpjsHealth: {
    employerContribution: number;  // 4% dari gaji
    employeeContribution: number;  // 1% dari gaji
    totalIuran: number;           // 5% dari gaji
  }
}

function calculateBpjsKesehatan(grossSalary: number): BpjsKesehatanEmployee {
  const employerRate = 0.04;  // 4% pemberi kerja
  const employeeRate = 0.01; // 1% karyawan
  
  const employerContribution = Math.floor(grossSalary * employerRate);
  const employeeContribution = Math.floor(grossSalary * employeeRate);
  
  return {
    grossSalary,
    bpjsHealth: {
      employerContribution,
      employeeContribution,
      totalIuran: employerContribution + employeeContribution
    }
  };
}

// Contoh: Gaji Rp 6.000.000
// employer: Rp 240.000
// employee: Rp 60.000
// total: Rp 300.000
```

## Edge Cases and Common Mistakes
1. **Gaji di bawah UMR**: Tetap dihitung dari gaji aktual, bukan UMR
2. **Keluarga tambahan**: Salah hitung 1% bukan 5% (hanya keluarga tambahan yang 1%)
3. **Bulan pertama kerja**: Iuran dihitung proporsional dari tanggal masuk
4. **Multi-job**: Jika karyawan punya 2 pekerjaan, each employer menghitung terpisah
5. **Upah tidak teratur**: Yang dihitung adalah upah teratur (bukan tunjangan tidak tetap)

## cekwajar.id Implementation Notes
- **File to update**: `src/core/payroll/calculations.ts` or `src/lib/bpjs.ts`
- **Function to modify/create**: `calculateBpjsKesehatan(salary: number): BpjsContribution`
- **Data source to query**: Employee master data (upah bulanan), not from external API
- **Update frequency**: When regulation changes (typically every few years)
- **Legion action**: Can update calculation logic when Perpres changes; needs Bashara for config file changes

## Monetization Angle
- Accurate BPJS calculation prevents compliance violations and penalties
- Monthly reporting to HR provides audit trail for tax purposes
- Integration with PPh 21 calculation (BPJS kesehatan 1% adalah deductible expense)

## Sources and Cross-References
- Official URL: https://bpjs-kesehatan.go.id/
- Perpres No. 59 Tahun 2024 (Perubahan ketiga atas Perpres 82/2018)
- Related: 038-kelas-rawat-bpjs.md, 039-kris-bpjs.md