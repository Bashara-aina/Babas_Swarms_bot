---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/bpjs/032-batas-upah.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.909215"
}
---

---
source_id: 032
title: "Batas Upah BPJS Ketenagakerjaan: JP Cap dan Perhitungan Maksimum"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://www.bpjsketenagakerjaan.go.id/artikel/18913/artikel-berapa-besaran-iuran-jht,-jkk,-jkm,-jp-dan-jkp"
last_verified: "2026-04-11"
tags: [bpjs-ketenagakerjaan, batas-atas, jp-cap, upah-tertinggi, pph21, labor-law]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# Batas Upah BPJS Ketenagakerjaan: JP Cap dan Perhitungan Maksimum

## Why This Matters for cekwajar.id
Jaminan Pensiun (JP) has a wage cap - salaries above this cap are calculated as if they were at the cap level. This is a critical detail that affects both employer costs and employee net pay. Missing this cap means over-calculating JP contributions for high-income employees.

## Core Knowledge

### Batas Atas Upah JP (2025)
**Mulai 1 Maret 2025**: Rp 10.547.400/bulan

Ini adalah batas tertinggi upah yang digunakan sebagai dasar perhitungan iuran JP.

### Mekanisme Penyesuaian
- BPJS Ketenagakerjaan menyesuaikan setiap tahun menggunakan faktor pengali: 1 + (tingkat inflasi/GDP growth)
- Kenaikan 2025: ~5.03% dari sebelumnya Rp 8.939.700

### Program dengan Batas Atas
| Program | Batas Atas | Berlaku Sejak |
|---------|------------|---------------|
| JP | Rp 10.547.400 | Maret 2025 |
| JKK | Tidak ada | - |
| JKM | Tidak ada | - |
| JHT | Tidak ada | - |

### Perhitungan Jika Upah di Atas Cap
```
Upah aktual: Rp 15.000.000
Batas atas JP: Rp 10.547.400

Iuran JP dihitung dari: Rp 10.547.400 (BUKAN Rp 15.000.000)
- Employee (1%): Rp 105.474
- Employer (2%): Rp 210.948
- Total: Rp 316.422
```

### Perbedaan Batas Atas dan Manfaat Pensiun
- **Batas atas iuran**: Hanya untuk perhitungan iuran, membatasi kontribusi
- **Manfaat pensiun**: Mengikuti formula aktuarial, tidak necessarily capped

## Exact Formulas / Numbers (if applicable)
```typescript
const JP_CAP_2025 = 10_547_400;

function calculateJpContribution(monthlySalary: number): {
  cappedSalary: number;
  employeeContribution: number;
  employerContribution: number;
  totalContribution: number;
  wasCapped: boolean;
} {
  const JHT_EMPLOYEE_RATE = 0.01;  // 1%
  const JHT_EMPLOYER_RATE = 0.02;   // 2%

  const cappedSalary = Math.min(monthlySalary, JP_CAP_2025);
  const wasCapped = monthlySalary > JP_CAP_2025;

  const employeeContribution = Math.floor(cappedSalary * JHT_EMPLOYEE_RATE);
  const employerContribution = Math.floor(cappedSalary * JHT_EMPLOYER_RATE);

  return {
    cappedSalary,
    employeeContribution,
    employerContribution,
    totalContribution: employeeContribution + employerContribution,
    wasCapped
  };
}

// Test cases:
// Gaji Rp 5.000.000 -> cappedSalary: Rp 5.000.000, wasCapped: false
// Gaji Rp 12.000.000 -> cappedSalary: Rp 10.547.400, wasCapped: true
// Gaji Rp 10.547.400 -> cappedSalary: Rp 10.547.400, wasCapped: false
```

## Edge Cases and Common Mistakes
1. **Forgot to cap**: Calculate JP from actual salary instead of capped salary
2. **Using outdated cap**: Hardcode old cap instead of reading from config
3. **Confusing cap with benefits**: JP cap is for iuran calculation, benefits follow different formula
4. **Missing annual update**: Not checking for new cap every March
5. **Salary changes mid-year**: When employee gets raise above cap, recalculate from effective date

## cekwajar.id Implementation Notes
- **File to update**: `src/config/bpjs-rates.ts` or environment config
- **Function to modify/create**: `getJpCap(year: number): number` - reads from config or API
- **Data source to query**: Government regulation, typically announced in February, effective March
- **Update frequency**: Annually (March each year)
- **Legion action**: Can auto-detect new cap by monitoring BPJS announcement; notify Bashara to update config

## Monetization Angle
- High earners (income above cap) need accurate calculation to avoid over-deduction
- Audit trail showing cap was properly applied prevents employee disputes
- Integration with payroll for net salary accuracy

## Sources and Cross-References
- Official URL: https://www.bpjsketenagakerjaan.go.id/
- PP No. 6 Tahun 2025 tentang Penyesuaian Iuran JP
- Surat Edaran Batas Upah JP Tahun 2025
- Related: 031-bpjs-ketenagakerjaan-iuran.md, 034-jp-manfaat.md