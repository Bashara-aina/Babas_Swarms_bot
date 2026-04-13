---
source_id: 036
title: "Sanksi Perusahaan Tidak Daftar BPJS: Denda, Pidana, dan Larangan Layanan Publik"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://www.niaga.asia/perusahaan-tidak-daftar-bpjs-ketenagakerjaan-dan-kesehatan-dapat-disanksi-pidana-dan-denda/"
last_verified: "2026-04-11"
tags: [bpjs, sanksi, denda, pidana, perusahaan, kepatuhan, labor-law, compliance]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# Sanksi Perusahaan Tidak Daftar BPJS: Denda, Pidana, dan Larangan Layanan Publik

## Why This Matters for cekwajar.id
Employers who fail to register employees to BPJS face severe consequences. Understanding these sanctions helps ensure compliance and prevents legal risks for businesses using cekwajar.id for payroll.

## Core Knowledge

### Sanksi Administratif (PP 86 Tahun 2013)

#### 1. Teguran Tertulis
Langkah pertama, perusahaan mendapat peringatan untuk mendaftarkan karyawannya.

#### 2. Denda
Denda keterlambatan pembayaran iuran:
- Denda pelayanan: 5% dari biaya diagnosa awal × bulan tertunggak
- Maksimum: Rp 30.000.000
- Denda untuk PPU ditanggung pemberi kerja

#### 3. Tidak Mendapat Pelayanan Publik Tertentu
Perusahaan yang belum terdaftar dapat dibatasi akses layanan publik seperti:
- izin usaha
- rekomendasi tender
- layanan perizinan tertentu

### Sanksi Pidana (UU BPJS)

#### 1. Tidak Mendaftarkan Pekerja
- **Pidana kurungan**: Maksimal 1 tahun
- **Pidana denda**: Maksimal Rp 50.000.000

#### 2. Tidak Membayar Iuran
- **Pidana kurungan**: Maksimal 2 tahun
- **Pidana denda**: Maksimal Rp 100.000.000

#### 3. Pemberi kerja yang tidak mendaftarkan atau tidak terus membayar iuran:
- **Pidana penjara**: Maksimal 8 tahun
- **Pidana denda**: Maksimal Rp 1.000.000.000

### Sanksi BPJS Kesehatan vs BPJS Ketenagakerjaan
Both programs have similar sanction structures. For BPJS Kesehatan specifically:
- Perusahaan wajib mendaftarkan seluruh karyawan
- Iuran 5% dari upah (4% perusahaan, 1% karyawan)

## Exact Formulas / Numbers (if applicable)
```typescript
// Denda keterlambatan BPJS Kesehatan
interface BpjsLatePaymentPenalty {
  monthsOverdue: number;    // maksimal 12 bulan
  initialDiagnosisCost: number;  // biaya diagnosa awal rawat inap
  penaltyPercentage: number; // 5%
  maxPenalty: number;        // Rp 30.000.000
  calculatedPenalty: number;
}

function calculateLatePaymentPenalty(
  initialDiagnosisCost: number,
  monthsOverdue: number
): BpjsLatePaymentPenalty {
  const PENALTY_RATE = 0.05;
  const MAX_MONTHS = 12;
  const MAX_PENALTY = 30_000_000;
  
  const effectiveMonths = Math.min(monthsOverdue, MAX_MONTHS);
  const penalty = initialDiagnosisCost * PENALTY_RATE * effectiveMonths;
  
  return {
    monthsOverdue: effectiveMonths,
    initialDiagnosisCost,
    penaltyPercentage: PENALTY_RATE * 100,
    maxPenalty: MAX_PENALTY,
    calculatedPenalty: Math.min(penalty, MAX_PENALTY)
  };
}

// Contoh:
// Biaya diagnosa awal: Rp 5.000.000
// Bulan tertunggak: 6 bulan
// Denda: 5% x 5.000.000 x 6 = Rp 1.500.000
```

## Edge Cases and Common Mistakes
1. **Perusahaan baru**: Harusnya daftar dalam 30 hari setelah merekrut karyawan
2. **Karyawan baru**: Harus didaftarkan maksimal 30 hari setelah mulai kerja
3. **Potongan gaji**: Jangan lupa potong 1% dari karyawan untuk BPJS Kesehatan
4. **Perubahan data**: Jika ada perubahan data perusahaan/karyawan, harus update ke BPJS
5. **Reset sanksi**: Sanksi teguran akan reset jika perusahaan menyelesaikan tunggakan

## cekwajar.id Implementation Notes
- **File to update**: `src/modules/compliance/bpjs-compliance.ts`
- **Function to modify/create**: `checkRegistrationStatus(companyId: string): ComplianceStatus`
- **Data source to query**: Company registration date, employee count, payment history
- **Update frequency**: As regulations change; compliance module needs periodic review
- **Legion action**: Can provide alerts when employee count changes to remind registration duty

## Monetization Angle
- Compliance reporting feature for HR modules
- Audit trail for employers to show they are compliant
- Avoid legal risks that could affect business operations

## Sources and Cross-References
- Official URL: https://www.bpjsketenagakerjaan.go.id/, https://bpjs-kesehatan.go.id/
- UU No. 24 Tahun 2011 tentang BPJS
- PP No. 86 Tahun 2013 tentang Sanksi Administratif
- Related: 030-bpjs-kesehatan.md, 031-bpjs-ketenagakerjaan-iuran.md