---
title: Aturan Cuti
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
summary: .cekwajar.id payroll system harus track hak cuti dan menghitung jika ada
  pembayaran cuti yang belum diambil saat PHK.особливо важливо untuk memastikan tidak
  adahutang cuti yang terabaikan.
wikilinks: []
confidence: medium
source: research
---

# Aturan Cuti Tahunan, Cuti Melitakan, Cuti Sakit di Indonesia

## Why This Matters for cekwajar.id
.cekwajar.id payroll system harus track hak cuti dan menghitung jika ada pembayaran cuti yang belum diambil saat PHK.особливо важливо untuk memastikan tidak adahutang cuti yang terabaikan.

## Core Knowledge

### Jenis-Jenis Cuti di Indonesia

#### 1. Cuti Tahunan (UU 13/2003 Pasal 79)

| Masa Kerja | Hak Cuti Tahunan |
|------------|------------------|
| ≥ 1 tahun | Minimal 12 hari kerja |
| ≥ 8 tahun tertentu | 1 hari tambahan |

**Ketentuan**:
- Cuti tahunan tidak dapat diuangkan, kecuali saat PHK
- Sisa cuti dapat menambah ke tahun berikutnya maksimal 50% dari hak

#### 2. Cuti Melahirkan (UU 13/2003 Pasal 82 + UU 4/2024)

**UU 13/2003 (lama)**:
- 3 bulan (1,5 bulan sebelum + 1,5 bulan sesudah)

**UU 4/2024 Kesejahteraan Ibu dan Anak (KIA)**:
- **Hamil**: 1,5 bulan sebelum melahirkan
- **Melahirkan**: 1,5 bulan sesudah melahirkan  
- **Masa 1000 HPK**: Tambahan hingga 6 bulan total (sesuai kebijakan perusahaan)

#### 3. Cuti Sakit (UU 13/2003 Pasal 81)

| Jenis | Keterangan |
|-------|------------|
| Cuti sakit < 14 hari | Berdasarkan surat dokter |
| Cuti sakit 14-30 hari | Berdasarkan surat dokter + konfirmasi |
| Cuti sakit > 30 hari | Diperiksa tim dokter |

**Pemberi kerja wajib membayargaji selama cuti sakit**:

#### 4. Cuti Haid
- Maksimal 2 hari per bulan

#### 5. Cuti Keguguran
- 1,5 bulan (sesuai surat dokter)

#### 6. Cuti Bersama
- Ditetapkan oleh pemerintah
- Upah tetap dibayar

```typescript
interface CutiHak {
  jenisCuti: 'tahunan' | 'melahirkan' | 'sakit' | 'haid' | 'keguguran' | 'besardan';
  jumlahHari: number;
  berbayar: boolean;
  masaKerja?: number;
}

function hitungHakCutiTahunan(masaKerjaTahun: number): number {
  if (masaKerjaTahun >= 8) {
    return 13; // 12 + 1 hari tambahan
  }
  return 12;
}

function hitungCutiMelahirkan(
  sesuaiUU: boolean = true, // true = UU 13/2003, false = UU 4/2024
  tambahanHPK: number = 0
): number {
  if (sesuaiUU) {
    return 90; // 3 bulan
  }
  return 90 + (tambahanHPK * 30); // Bisa sampai 6 bulan
}
```

## Exact Formulas / Numbers (if applicable)

### TypeScript Implementation
```typescript
interface Employee {
  id: string;
  hireDate: Date;
  leaveBalances: {
    tahunan: number;
    sakit: number;
    melahirkan: number;
  };
}

interface LeaveEntitlement {
  jenis: string;
  totalDays: number;
  usedDays: number;
  remainingDays: number;
  canBeEncashed: boolean;
}

function getLeaveEntitlements(
  employee: Employee,
  asOfDate: Date
): LeaveEntitlement[] {
  const masaKerjaTahun = hitungTahun(employee.hireDate, asOfDate);
  
  return [
    {
      jenis: 'Cuti Tahunan',
      totalDays: hitungHakCutiTahunan(masaKerjaTahun),
      usedDays: employee.leaveBalances.tahunan,
      remainingDays: Math.max(0, hitungHakCutiTahunan(masaKerjaTahun) - employee.leaveBalances.tahunan),
      canBeEncashed: false // Cannot be encashed except on PHK
    },
    {
      jenis: 'Cuti Sakit',
      totalDays: -1, // Unlimited based on medical need
      usedDays: employee.leaveBalances.sakit,
      remainingDays: -1,
      canBeEncashed: false
    },
    {
      jenis: 'Cuti Melahirkan',
      totalDays: 90,
      usedDays: employee.leaveBalances.melahirkan,
      remainingDays: 90 - employee.leaveBalances.melahirkan,
      canBeEncashed: false
    }
  ];
}

function hitungKompenCuti(
  sisaCutiHari: number,
  dailyWage: number
): number {
  // Pembayaran cuti tahunan saat PHK
  return sisaCutiHari * dailyWage;
}

function hitungTahun(masuk: Date, akhir: Date): number {
  const diffMs = akhir.getTime() - masuk.getTime();
  return Math.floor(diffMs / (1000 * 60 * 60 * 24 * 365));
}
```

### Pembayaran Gaji Selama Cuti Sakit
```typescript
function hitungGajiCutiSakit(
  dailyWage: number,
  sickLeaveDays: number,
  isPaidLeave: boolean
): number {
  if (!isPaidLeave) return 0;
  
  if (sickLeaveDays <= 14) {
    return sickLeaveDays * dailyWage; // 100% upah
  } else if (sickLeaveDays <= 30) {
    return sickLeaveDays * dailyWage; // 100% upah
  } else {
    // Above 30 days - check company policy
    return sickLeaveDays * dailyWage * 0.75; // 75% - depends on policy
  }
}
```

## Edge Cases and Common Mistakes

1. **Cuti tahunan tidak diambil**: Akan hangus jika tidak digunakan, kecuali menambah saldo tahun berikutnya (max 50%)
2. **Cuti sakit tidak perlu surat dokter untuk < 14 hari**: Tetap memerlukan
3. **PHK saat masih punya saldo cuti**: Wajib dibayarkan uang kompensasi
4. **Cuti melahirkan hanya untuk pekerja tetap**: PKWT juga berhak

## cekwajar.id Implementation Notes

- **File to update**: `src/lib/hr/leave-management.ts`
- **Function to modify/create**: `calculateLeaveBalance()`, `calculateLeaveEncashment()`
- **Data source to query**: Employee attendance/leave records
- **Update frequency**: Per pay period or when leave is taken
- **Legion action**: YES - can track and alert on leave balances

## Monetization Angle
- Leave management system
- Automated accrual calculations
- Compliance reporting for HR audits

## Sources and Cross-References
- UU 13/2003 Pasal 79-82
- UU 4/2024 tentang Kesejahteraan Ibu dan Anak
- Related: PP 35/2021 (UPH saat PHK)
