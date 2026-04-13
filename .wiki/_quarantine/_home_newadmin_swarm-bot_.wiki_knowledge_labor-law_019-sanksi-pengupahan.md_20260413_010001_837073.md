---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/labor-law/019-sanksi-pengupahan.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.837094"
}
---

---
source_id: 019
title: "Sanksi Pidana Pengupahan di Bawah Upah Minimum"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://www.kompas.com/tren/read/2023/11/22/183000865/denda-hingga-penjara-ini-sanksi-perusahaan-yang-beri-gaji-di-bawah-upah"
last_verified: "2026-04-11"
tags: [sanksi,pidana,upah-minimum,pelanggaran,denda,pengupahan]
cekwajar_impact: CRITICAL
legion_can_act: NO
---

# Sanksi Pidana Pengupahan di Bawah Upah Minimum

## Why This Matters for cekwajar.id
.cekwajar.id payroll system MUST prevent paying employees below minimum wage. Violations carry CRIMINAL penalties including imprisonment and fines, not just administrative sanctions. This is the highest risk area for labor law compliance.

## Core Knowledge

### Dasar Hukum Sanksi

1. **UU 13/2003 Pasal 90** - Pengusaha wajib membayar upah sesuai ketentuan minimum
2. **UU 13/2003 Pasal 78** - Larangan pelanggaran waktu kerja dan upah
3. **UU Cipta Kerja (UU 6/2023) Pasal 81 angka 63** - Sanksi pidana
4. **PP 36/2021 Pasal 61** - Sanksi keterlambatan pembayaran upah

### Sanksi Pidana untuk Upah di Bawah Minimum

**Pasal 88E UU Ketenagakerjaan ( setelah perubahan UU Cipta Kerja)**:

| Jenis Sanksi | Besaran |
|--------------|---------|
| **Pidana penjara** | Minimal 1 tahun, Maksimal 4 tahun |
| **Pidana denda** | Minimal Rp 100.000.000, Maksimal Rp 400.000.000 |

**Pasal 186 UU 13/2003 (sebelum perubahan)**:
- Pidana kurungan: 1-12 bulan
- Denda: Rp 100.000 - Rp 1.000.000

```typescript
interface WageViolation {
  employeeId: string;
  companyId: string;
  violationType: 'below_minimum' | 'late_payment' | 'non_payment';
  period: { start: Date; end: Date };
  amountUnderpaid: number;
  numberOfEmployees: number;
}

interface ViolationPenalty {
  imprisonmentYears: { min: number; max: number };
  fineAmount: { min: number; max: number };
  additionalSanctions: string[];
}

function getPenaltiesForViolation(
  violation: WageViolation
): ViolationPenalty {
  if (violation.violationType === 'below_minimum') {
    return {
      imprisonmentYears: { min: 1, max: 4 },
      fineAmount: { min: 100000000, max: 400000000 },
      additionalSanctions: [
        'Sanksi administratif dari Kemenaker',
        'Wajib bayar selisih upah + bunga',
        'Dapat dicabut izin usaha'
      ]
    };
  }
  
  if (violation.violationType === 'late_payment') {
    return {
      imprisonmentYears: { min: 0, max: 0 },
      fineAmount: { min: 0, max: 0 },
      additionalSanctions: [
        'Bunga 1% per hari dari upah yang terlambat',
        'Sanksi administratif'
      ]
    };
  }
  
  return {
    imprisonmentYears: { min: 1, max: 4 },
    fineAmount: { min: 100000000, max: 400000000 },
    additionalSanctions: ['Criminal prosecution']
  };
}
```

### Sanksi Administratif (Selain Pidana)

**PP 36/2021 Pasal 61**:
- Teguran tertulis
- Pembatasan kegiatan usaha
- Pembekuan kegiatan usaha
- Pencabutan izin usaha

```typescript
interface AdminPenalty {
  severity: 'warning' | 'restriction' | 'suspension' | 'revocation';
  description: string;
}

function getAdminPenalties(violationCount: number): AdminPenalty[] {
  if (violationCount === 1) {
    return [{ severity: 'warning', description: 'Teguran tertulis' }];
  }
  if (violationCount === 2) {
    return [{ severity: 'restriction', description: 'Pembatasan kegiatan usaha' }];
  }
  if (violationCount === 3) {
    return [{ severity: 'suspension', description: 'Pembekuan kegiatan usaha' }];
  }
  return { severity: 'revocation', description: 'Pencabutan izin usaha' };
}
```

### Perhitungan Denda keterlambatan

```typescript
function hitungDendaKeterlambatan(
  jumlahUpahTerlambat: number,
  jumlahHariTerlambat: number
): number {
  const bungaPerHari = 0.01; // 1% per hari
  return jumlahUpahTerlambat * bungaPerHari * jumlahHariTerlambat;
}

function hitungTotalTanggungJawab(
  selisihUpah: number,
  jumlahBulan: number,
  bunga: number
): number {
  return selisihUpah * jumlahBulan + bunga;
}
```

## Exact Formulas / Numbers (if applicable)

### TypeScript Implementation
```typescript
interface WageComplianceCheck {
  employeeId: string;
  locationCode: string;
  basicSalary: number;
  fixedAllowances: number;
  umkRequired: number;
}

interface ViolationResult {
  isViolation: boolean;
  violationType: 'BELOW_MIN' | 'LATE_PAYMENT' | 'COMPLIANT';
  underpaymentAmount: number;
  potentialPenalties: {
    imprisonment: { min: number; max: number };
    fines: { min: number; max: number };
    adminSanctions: string[];
  };
  recommendedAction: string;
}

function checkWageViolation(
  employee: WageComplianceCheck
): ViolationResult {
  const totalCompensation = employee.basicSalary + employee.fixedAllowances;
  
  if (totalCompensation < employee.umkRequired) {
    const underpayment = employee.umkRequired - totalCompensation;
    
    return {
      isViolation: true,
      violationType: 'BELOW_MIN',
      underpaymentAmount: underpayment,
      potentialPenalties: {
        imprisonment: { min: 1, max: 4 },
        fines: { min: 100000000, max: 400000000 },
        adminSanctions: [
          'Teguran tertulis',
          'Pembatasan kegiatan usaha',
          'Pembekuan kegiatan usaha'
        ]
      },
      recommendedAction: 'SEGERA SESUAIKAN UPAH KE UMK. RISIKO PIDANA!'
    };
  }
  
  return {
    isViolation: false,
    violationType: 'COMPLIANT',
    underpaymentAmount: 0,
    potentialPenalties: {
      imprisonment: { min: 0, max: 0 },
      fines: { min: 0, max: 0 },
      adminSanctions: []
    },
    recommendedAction: 'Compliant - no action required'
  };
}

function generateComplianceAlert(
  violations: ViolationResult[]
): string[] {
  return violations
    .filter(v => v.isViolation)
    .map(v => 
      `ALERT: ${v.violationType} - Potential fines up to Rp ${v.potentialPenalties.fines.max.toLocaleString()} and imprisonment ${v.potentialPenalties.imprisonment.min}-${v.potentialPenalties.imprisonment.max} years`
    );
}
```

## Edge Cases and Common Mistakes

1. **Tunjangan tidak tetap tidak termasuk**: Jika classification salah, perusahaan bisa tertipu karena以为自己 compliant padahal tidak
2. **Upah termasuk tunjangan: TRUE** - total compensation (pokok + tetap) harus ≥ UMK
3. **"Gross" agreement tapi below UMK**: Tetap violate - hukum adalah absolute
4. **Pembayaran dengan cara "pinjaman"**: Jika employee terima kurang dari UMK, tetap violation

## cekwajar.id Implementation Notes

- **File to update**: `src/lib/compliance/wage-violation-detector.ts`
- **Function to modify/create**: `detectWageViolation()`, `getPotentialPenalties()`
- **Data source to query**: Payroll data + UMK/UMP reference data
- **Update frequency**: Per pay run - MUST validate before payment
- **Legion action**: NO - this requires immediate human attention

## Monetization Angle
- Real-time wage compliance checking BEFORE payment
- Violation risk assessment dashboard
- Audit trail untuk legal defense

## Sources and Cross-References
- UU 13/2003 Pasal 90, 186
- UU 6/2023 (UU Cipta Kerja) Pasal 81
- PP 36/2021 Pasal 61
- Related: UMP, UMK, PP 35/2021
