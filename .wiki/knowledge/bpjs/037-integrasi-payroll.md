---
source_id: 037
title: "Integrasi BPJS dengan Payroll: E-Payment System dan Remitansi"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://www.bpjsketenagakerjaan.go.id/artikel/18917/artikel-bayar-iuran-bpjs-ketenagakerjaan-makin-mudah-dengan-eps-serta-kanal-pembayarannya.bpjs"
last_verified: "2026-04-11"
tags: [bpjs, payroll, integrasi, eps, payment, remittance, hrtech, software]
cekwajar_impact: HIGH
legion_can_act: YES
---

# Integrasi BPJS dengan Payroll: E-Payment System dan Remitansi

## Why This Matters for cekwajar.id
For a payroll SaaS like cekwajar.id, integrating with BPJS payment systems is critical. Understanding EPS (Electronic Payment System), virtual accounts, and payment channels enables accurate deduction calculation and compliance reporting.

## Core Knowledge

### E-Payment System (EPS) BPJS Ketenagakerjaan

EPS is the electronic system for making BPJS contribution payments. Employers receive a billing code (kode iuran) for each payment period.

#### Kanal Pembayaran EPS:
1. **Bank persepsi**: BRI, BNI, BTN, Bank Mandiri, CIMB, dll
2. **Virtual Account**: Untuk internet banking dan mobile banking
3. **ATM**: Melalui menu pembayaran BPJS
4. **Teller**: Di kantor bank

#### Langkah Pembayaran via EPS:
1. Buat kode iuran melalui aplikasi SIPP atau EPS
2. Pilih periode pembayaran
3. Bayar melalui kanal yang tersedia
4. Konfirmasi dan simpan bukti pembayaran

### Sistem Kode Iuran

#### Untuk PU (Penerima Upah):
- Kode berdasarkan NPP (Nomor Pokok Perusahaan) + periode
- Dihasilkan dari aplikasi SIPP atau melalui kantor cabang

#### Untuk BPU (Bukan Penerima Upah):
- Menggunakan NIK (16 digit) sebagai identifier
- Bayar sesuai dengan kode yang didapat saat pendaftaran

### Virtual Account Numbering
```
BRI: 1234567890123456
BNI: 1234567890
Mandiri: 23996 + kode iuran
```

### Autodebit
BPJS menyediakan layanan autodebit untuk方便:
- Tanggal 1-28 setiap bulan
- Melalui bank atau e-wallet
- Minimal 1 bulan periode

### Format Remittance
For payroll integration, remittance data typically includes:
- Employee NIK
- Monthly salary
- Program type (JHT, JP, JKK, JKM, JKP)
- Contribution amounts (employee + employer)
- Period (month/year)

## Exact Formulas / Numbers (if applicable)
```typescript
interface BpjsRemittanceData {
  companyNpp: string;
  period: string;  // YYYYMM format
  employeeContributions: {
    nik: string;
    salary: number;
    jhtEmployee: number;
    jpEmployee: number;
    totalEmployee: number;
  }[];
  employerContributions: {
    nik: string;
    jhtEmployer: number;
    jkk: number;
    jkm: number;
    jpEmployer: number;
    jkpFromJkk: number;
    totalEmployer: number;
  }[];
  grandTotal: {
    employee: number;
    employer: number;
    grand: number;
  };
}

function generateRemittanceBatch(employees: PayrollEmployee[]): BpjsRemittanceData {
  const period = getCurrentPeriod(); // YYYYMM
  
  const employeeContributions = employees.map(emp => ({
    nik: emp.nik,
    salary: emp.monthlySalary,
    jhtEmployee: Math.floor(emp.monthlySalary * 0.02),
    jpEmployee: Math.floor(Math.min(emp.monthlySalary, JP_CAP) * 0.01),
    totalEmployee: 0 // calculated below
  }));
  
  // Calculate totals
  employeeContributions.forEach(ec => {
    ec.totalEmployee = ec.jhtEmployee + ec.jpEmployee;
  });
  
  return {
    companyNpp: COMPANY_NPP,
    period,
    employeeContributions,
    employerContributions: [], // similar structure
    grandTotal: calculateGrandTotal(employeeContributions, employerContributions)
  };
}

// Example remittance format for bank transfer
const REMITTANCE_FORMAT = {
  header: "REMITTANCE|BPJS-TK|{NPP}|{PERIOD}|{TOTAL_RECORD}",
  detail: "REC|{NIK}|{SALARY}|{JHT_EMP}|{JP_EMP}|{JHT_EMP}|{JKK}|{JKM}|{JP_EMP}|{JKP}",
  footer: "TOTAL|{TOTAL_EMPLOYEE}|{TOTAL_EMPLOYER}|{GRAND_TOTAL}"
};
```

## Edge Cases and Common Mistakes
1. **Kode iuran expired**: Kode iuran hanya valid untuk periode tertentu
2. **Payment date**: Harus bayar sebelum tanggal 10, bukan tanggal jatuh tempo
3. **Batch size**: Ada limits pada jumlah employee per batch submission
4. **Currency**: Semua dalam Rupiah, tidak ada desimal (bulatkan)
5. **Correction**: Jika salah bayar, harus minta correction dari BPJS

## cekwajar.id Implementation Notes
- **File to update**: `src/integrations/bpjs/bpjs-remittance.ts`
- **Function to modify/create**: `generateRemittanceFile(period: string): RemittanceFile`
- **Data source to query**: Employee master data, payroll records, payment history
- **Update frequency**: Monthly for remittance; EPS code generation as needed
- **Legion action**: Can build integration module with bank APIs for auto-payment

## Monetization Angle
- Bulk payment processing for companies with many employees
- Automated reporting and compliance features
- Premium integration with accounting software (Jurnal, Accurate, dll)

## Sources and Cross-References
- Official URL: https://www.bpjsketenagakerjaan.go.id/eps.html
- SIPP Application: https://sipp.bpjsketenagakerjaan.go.id/
- Related: 031-bpjs-ketenagakerjaan-iuran.md
