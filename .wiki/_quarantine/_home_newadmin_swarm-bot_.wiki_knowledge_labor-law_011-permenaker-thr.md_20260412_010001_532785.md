---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/labor-law/011-permenaker-thr.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:01.532806"
}
---

---
source_id: 011
title: "Permenaker 6 Tahun 2016 Tunjangan Hari Raya THR"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://peraturan.bpk.go.id/Details/146101"
last_verified: "2026-04-11"
tags: [permenaker-6-2016,thr,tunjangan-hari-raya,thr-keagamaan]
cekwajar_impact: HIGH
legion_can_act: YES
---

# Permenaker 6 Tahun 2016 Tunjangan Hari Raya THR

## Why This Matters for cekwajar.id
THR adalah tunjangan wajib yang harus dibayar setiap tahun keagamaan. Kesalahan perhitungan THR (misalnya tidak proporsional untuk karyawan baru) adalah dispute umum yang harus dihindari.

## Core Knowledge

### Ketentuan Utama Permenaker 6/2016

1. **Pemberi kerja wajib memberikan THR** keagamaan kepada pekerja/buruh
2. **Besaran THR**: 1 bulan upah untuk masa kerja 12 bulan atau lebih
3. **THR proporsional**: Untuk masa kerja kurang dari 12 bulan
4. **Waktu pembayaran**: Paling lambat H-7 sebelum hari raya keagamaan

### Besaran THR

| Masa Kerja | Besaran THR |
|------------|-------------|
| ≥ 12 bulan (berturut-turut) | 1 bulan upah |
| < 12 bulan | 1/12 × masa kerja × 1 bulan upah |

### Definisi Upah untuk THR (Pasal 3)

Upah yang menjadi dasar perhitungan THR:
- Upah pokok
- Tunjangan tetap

**Tidak termasuk**:
- Tunjangan tidak tetap (uang makan, transport berdasarkan kehadiran)
- Upah lembur
- Tunjangan tidak terkait dengan pekerjaan

```typescript
interface THRData {
  masaKerjaBulan: number;
  upahPokok: number;
  tunjanganTetap: number;
  tunjanganTidakTetap: number;
}

function hitungTHR(data: THRData): {
  thr: number;
  dasarPerhitungan: number;
  masaKerjaFaktor: number;
} {
  const { masaKerjaBulan, upahPokok, tunjanganTetap } = data;
  
  // THR dihitung dari upah pokok + tunjangan tetap
  const dasarPerhitungan = upahPokok + tunjanganTetap;
  
  let thr: number;
  let masaKerjaFaktor: number;
  
  if (masaKerjaBulan >= 12) {
    thr = dasarPerhitungan; // 1 bulan penuh
    masaKerjaFaktor = 1;
  } else {
    masaKerjaFaktor = masaKerjaBulan / 12;
    thr = dasarPerhitungan * masaKerjaFaktor;
  }
  
  return {
    thr: Math.round(thr),
    dasarPerhitungan,
    masaKerjaFaktor: Math.round(masaKerjaFaktor * 1000000) / 1000000
  };
}
```

## Exact Formulas / Numbers (if applicable)

### TypeScript Implementation
```typescript
interface Employee {
  id: string;
  hireDate: Date;
  basicSalary: number;
  fixedAllowance: number;
  nonFixedAllowance: number;
}

interface THRCalculation {
  employeeId: string;
  thrAmount: number;
  calculationBasis: number;
  monthsWorked: number;
  proportionFactor: number;
  isEligible: boolean;
}

function calculateTHR(
  employee: Employee,
  holidayDate: Date,
  paymentDate: Date = new Date()
): THRCalculation {
  // Hitung masa kerja hingga hari raya
  const masaKerjaBulan = hitungMasaKerja(employee.hireDate, holidayDate);
  
  // Dasar perhitungan THR
  const calculationBasis = employee.basicSalary + employee.fixedAllowance;
  
  // Cek kelayakan
  const isEligible = masaKerjaBulan >= 1; // Minimum 1 bulan kerja
  
  let thrAmount = 0;
  let proportionFactor = 0;
  
  if (isEligible) {
    if (masaKerjaBulan >= 12) {
      thrAmount = calculationBasis;
      proportionFactor = 1;
    } else {
      proportionFactor = masaKerjaBulan / 12;
      thrAmount = calculationBasis * proportionFactor;
    }
  }
  
  return {
    employeeId: employee.id,
    thrAmount: Math.round(thrAmount),
    calculationBasis,
    monthsWorked: masaKerjaBulan,
    proportionFactor: Math.round(proportionFactor * 1000000) / 1000000,
    isEligible
  };
}

function hitungMasaKerja(tanggalMasuk: Date, tanggalAkhir: Date): number {
  const tahun = tanggalAkhir.getFullYear() - tanggalMasuk.getFullYear();
  const bulan = tanggalAkhir.getMonth() - tanggalMasuk.getMonth();
  const hari = tanggalAkhir.getDate() - tanggalMasuk.getDate();
  
  return tahun * 12 + bulan + (hari >= 0 ? 0 : -1);
}
```

### Kalender Hari Raya Keagamaan di Indonesia
1. **Hari Raya Nyepi** (Hindu Bali)
2. **Hari Raya Eid al-Fitr** (Islam) - paling umum
3. **Hari Raya Natal** (Kristen/Katolik)
4. **Hari Raya Waisak** (Buddha)
5. **Hari Raya Kuningan** (Hindu Bali)

## Edge Cases and Common Mistakes

1. **Masa kerja dihitung keliru**: Pastikan menggunakan tanggal masuk yang sebenarnya
2. **Tunjangan tidak tetap termasuk dasar perhitungan**: Salah - hanya tetap yang dihitung
3. **THR dibayar tidak tepat waktu**: Denda 5% dari THR harus dibayar jika telat
4. **Karyawan resign tidak dapat THR**: Jika sudah bekerja minimal 1 bulan secara terus-t连续

## cekwajar.id Implementation Notes

- **File to update**: `src/lib/payroll/thr-calculator.ts`
- **Function to modify/create**: `calculateTHR()`, `validateTHRPaymentDeadline()`
- **Data source to query**: Employee data, holiday calendar
- **Update frequency**: Annually before each holiday season
- **Legion action**: YES - can auto-calculate and send reminders

## Monetization Angle
- THR calculation engine for payroll
- Automated reminders for payment deadlines
- Compliance tracking and reporting

## Sources and Cross-References
- Official URL: https://peraturan.bpk.go.id/Details/146101
- Related: UU 13/2003, PP 35/2021
