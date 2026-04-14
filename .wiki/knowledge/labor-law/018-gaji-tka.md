---
title: Gaji Tka
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
summary: .cekwajar.id payroll system harus handle taxation untuk TKA yang berbeda
  dari WNI. TKA umumnya subject to PPh 26 (bukan PPh 21), dan ada aturan_IMT specific
  tentang sponsorship dan permit.
wikilinks: []
confidence: medium
source: research
---

# Gaji dan Aturan TKA Tenaga Kerja Asing di Indonesia

## Why This Matters for cekwajar.id
.cekwajar.id payroll system harus handle taxation untuk TKA yang berbeda dari WNI. TKA umumnya subject to PPh 26 (bukan PPh 21), dan ada aturan_IMT specific tentang sponsorship dan permit.

## Core Knowledge

### Definisi TKA

Tenaga Kerja Asing (TKA) = Orang asing yang bekerja di Indonesia berdasarkan visa kerja.

### Aturan Utama TKA

1. **RPTKA** - Rencana Penggunaan Tenaga Kerja Asing (wajib dari Kemenaker)
2. **Visa kerja** - Single entry atau limited stay
3. **Kontrak PKWT** - Harus dengan waktu tertentu (tidak bisa PKWTT)
4. **Wajib berpaspor** dari negara asal
5. **Maksimal masa kerja** - Sesuai RPTKA, bisa diperpanjang

### Kewajiban Pemberi Kerja TKA

1. **Membayar Dana Kompensasi** = USD 100/bulan or ~Rp 1.500.000
2. **Menguruskan izin tinggal** (KITAS)
3. **Memberikan upah sesuai standard** (minimal UMK)
4. **Melaporkan ke Disnaker** setempat

### Perpajakan TKA

**TKA dengan NPWP** → PPh 21
**TKA tanpa NPWP (183 hari)** → PPh 26 (20% dari gross)

```typescript
interface TKAData {
  employeeId: string;
  passportCountry: string;
  isResident: boolean;  // Di Indonesia > 183 hari = resident
  hasNPWP: boolean;
  rptkaNumber: string;
  rptkaExpiry: Date;
  compensationFee: number;  // USD 100/bulan
}

function hitungPajakTKA(
  tka: TKAData,
  monthlyIncome: number
): { pajakType: 'PPh21' | 'PPh26'; pajakSetahun: number } {
  if (tka.hasNPWP || tka.isResident) {
    // PPh 21 seperti WNI
    return { pajakType: 'PPh21', pajakSetahun: hitungPPh21WNI(monthlyIncome) };
  } else {
    // PPh 26 - 20% dari gross tanpa pengurangan
    const grossSetahun = monthlyIncome * 12;
    return { 
      pajakType: 'PPh26', 
      pajakSetahun: grossSetahun * 0.20 
    };
  }
}

function hitungPPh21WNI(gajiBulanan: number): number {
  // Simplified - actual calculation needs PTKP, biaya jabatan, etc
  const netoSetahun = (gajiBulanan * 12) - 6000000 - 2400000; // simplified
  const pkp = Math.max(0, netoSetahun - 54000000);
  return hitungTarifProgresif(pkp);
}
```

## Exact Formulas / Numbers (if applicable)

### TypeScript Implementation
```typescript
interface TKAEmployee {
  id: string;
  nationality: string;
  residencyDaysThisYear: number;
  hasNPWP: boolean;
  monthlySalary: number;
  allowances: number;
  isRPPAuthorized: boolean;
}

interface TKATaxCalculation {
  employeeId: string;
  taxType: 'PPh21' | 'PPh26';
  grossAnnual: number;
  deductions: number;
  pkp: number;
  annualTax: number;
  monthlyTax: number;
}

function calculateTKATax(employee: TKAEmployee): TKATaxCalculation {
  const grossAnnual = (employee.monthlySalary + employee.allowances) * 12;
  
  // Determine tax type
  const isResident = employee.residencyDaysThisYear > 183;
  const taxType = (isResident || employee.hasNPWP) ? 'PPh21' : 'PPh26';
  
  let deductions = 0;
  let pkp = 0;
  let annualTax = 0;
  
  if (taxType === 'PPh21') {
    // Same as Indonesian employee
    deductions = 6000000 + 2400000; // Biaya jabatan + iuran pensiun simplified
    pkp = Math.max(0, grossAnnual - deductions - 54000000);
    annualTax = hitungTarifProgresif(pkp);
  } else {
    // PPh 26: 20% of gross without deductions
    annualTax = grossAnnual * 0.20;
  }
  
  return {
    employeeId: employee.id,
    taxType,
    grossAnnual,
    deductions,
    pkp: taxType === 'PPh21' ? pkp : grossAnnual,
    annualTax: Math.round(annualTax),
    monthlyTax: Math.round(annualTax / 12)
  };
}

interface TKACompliance {
  employeeId: string;
  hasRPTA: boolean;
  compensationFeePaid: boolean;
  salaryAboveUMK: boolean;
  visaValid: boolean;
  violations: string[];
}

function checkTKACompliance(
  employee: TKAEmployee,
  umkLocation: number
): TKACompliance {
  const violations: string[] = [];
  
  if (!employee.isRPPAuthorized) {
    violations.push('Tidak memiliki RPTKA yang masih berlaku');
  }
  
  if (employee.monthlySalary < umkLocation) {
    violations.push(`Gaji di bawah UMK locale (${umkLocation})`);
  }
  
  return {
    employeeId: employee.id,
    hasRPTA: employee.isRPPAuthorized,
    compensationFeePaid: true, // Should check actual payment
    salaryAboveUMK: employee.monthlySalary >= umkLocation,
    visaValid: true, // Should check expiry
    violations
  };
}
```

## Edge Cases and Common Mistakes

1. **TKA without NPWP**: Tetap harus punya NPWP jika > 183 hari
2. **RPTKA tidak diperpanjang**: Berakhir bersamaan dengan KITAS
3. **Gaji di bawah UMK**: TKA juga harus dibayar minimal UMK
4. **Dana kompensasi tidak dibayar**: Sanksi administrative dan criminal

## cekwajar.id Implementation Notes

- **File to update**: `src/lib/payroll/tka-tax-calculator.ts`
- **Function to modify/create**: `calculateTKATax()`, `checkTKACompliance()`
- **Data source to query**: Employee nationality, residency data, RPTKA info
- **Update frequency**: Per pay period and when residency status changes
- **Legion action**: NO - requires HR/legal specialist for TKA cases

## Monetization Angle
- TKA tax calculator for HR departments
- Compliance checking for expat employment
- RPTKA tracking and renewal reminders

## Sources and Cross-References
- UU 13/2003 Pasal 42-49
- UU 11/2020 (UU 6/2023)
- PP 35/2021
- PMK tentang NPWP TKA
