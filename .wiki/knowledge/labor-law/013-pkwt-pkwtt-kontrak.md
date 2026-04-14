---
title: Pkwt Pkwtt Kontrak
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
summary: .cekwajar.id HR module harus properly classify employee type (PKWT vs PKWTT)
  dan track contract expiry dates. Contract workers (PKWT) tidak boleh punya masa
  percobaan dan ada batasan durasi maksimal.
wikilinks: []
confidence: medium
source: research
---

# PKWT PKWTT Aturan Kontrak Kerja Masa Percobaan Indonesia

## Why This Matters for cekwajar.id
.cekwajar.id HR module harus properly classify employee type (PKWT vs PKWTT) dan track contract expiry dates. Contract workers (PKWT) tidak boleh punya masa percobaan dan ada batasan durasi maksimal.

## Core Knowledge

### Definisi PKWT dan PKWTT

| Aspek | PKWT | PKWTT |
|-------|------|-------|
| Nama Lengkap | Perjanjian Kerja Waktu Tertentu | Perjanjian Kerja Waktu Tidak Tertentu |
| Jenis | Kontrak/Kontak | Tetap/Permanen |
| Masa Kerja | Terbatas | Tidak terbatas |
| Masa Percobaan | **Tidak boleh** | Boleh, maks 3 bulan |
| PHK | Ada kompensasi | Ada kompensasi |

### Dasar Hukum

**UU 13/2003**:
- Pasal 59: PKWT tidak dapat mensyaratkan masa percobaan
- Pasal 60: PKWTT dapat mensyaratkan masa percobaan maksimal 3 bulan

**UU Cipta Kerja 11/2020 (sekarang UU 6/2023)**:
- Perubahan ketentuan PKWT:
  - Jangka waktu maksimal 5 tahun (termasuk perpanjangan)
  - Perpanjangan PKWT harus melewati masa tenggang 30 hari
  - Tidak ada lagi "perpanjangan kedua"

### Batasan PKWT

| Aspek | Aturan |
|-------|--------|
| Durasi maksimal | 5 tahun (dari awal hingga akhir kontrak + perpanjangan) |
| Perpanjangan | Boleh, setelah masa tenggang 30 hari |
| Masa percobaan | **Tidak boleh** |
| Minimum durasi | Tidak ada minimum (bisa 1 hari) |

### Aturan Masa Percobaan (Probation) untuk PKWTT

```typescript
interface PKWTTContract {
  employeeId: string;
  contractStart: Date;
  probationPeriod: number; // dalam bulan, maks 3
  isPermanent: boolean;
}

function validateProbationPeriod(
  probationMonths: number
): { valid: boolean; error?: string } {
  if (probationMonths > 3) {
    return { 
      valid: false, 
      error: 'Masa percobaan maksimal 3 bulan' 
    };
  }
  if (probationMonths < 0) {
    return { 
      valid: false, 
      error: 'Masa percobaan tidak boleh negatif' 
    };
  }
  return { valid: true };
}

function validatePKWTDuration(
  contractStart: Date,
  contractEnd: Date
): { valid: boolean; totalMonths: number; error?: string } {
  const diffMs = contractEnd.getTime() - contractStart.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const totalMonths = diffDays / 30;
  
  if (totalMonths > 60) {
    return { 
      valid: false, 
      totalMonths,
      error: 'Durasi PKWT maksimal 5 tahun (60 bulan)' 
    };
  }
  
  return { valid: true, totalMonths };
}
```

## Exact Formulas / Numbers (if applicable)

### TypeScript Implementation
```typescript
enum ContractType {
  PKWT = 'PKWT',
  PKWTT = 'PKWTT'
}

interface ContractValidation {
  isValid: boolean;
  contractType: ContractType;
  duration: {
    months: number;
    days: number;
  };
  violations: string[];
  warnings: string[];
}

function validateContract(
  type: ContractType,
  startDate: Date,
  endDate: Date | null,
  hasProbation: boolean,
  probationMonths: number = 0
): ContractValidation {
  const violations: string[] = [];
  const warnings: string[] = [];
  
  // Check probation
  if (type === ContractType.PKWT && hasProbation) {
    violations.push('PKWT tidak boleh memiliki masa percobaan (Pasal 59 UU 13/2003)');
  }
  
  if (type === ContractType.PKWTT && probationMonths > 3) {
    violations.push('Masa percobaan PKWTT maksimal 3 bulan (Pasal 60 UU 13/2003)');
  }
  
  // Check duration for PKWT
  let duration = { months: 0, days: 0 };
  if (type === ContractType.PKWT && endDate) {
    const diffMs = endDate.getTime() - startDate.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    duration = {
      months: Math.floor(diffDays / 30),
      days: diffDays % 30
    };
    
    if (duration.months > 60) {
      violations.push('Durasi PKWT maksimal 60 bulan (5 tahun)');
    }
    
    // Warning for 30-day gap
    if (diffDays > 30 && !endDate) {
      warnings.push('Perpanjangan PKWT wajib melewati masa tenggang 30 hari');
    }
  }
  
  return {
    isValid: violations.length === 0,
    contractType: type,
    duration,
    violations,
    warnings
  };
}
```

## Edge Cases and Common Mistakes

1. **PKWT dengan clause probation**: Void - tidak sah
2. **Kontrak diperpanjang melewati 5 tahun**: Automatically menjadi PKWTT
3. **30 days gap tidak dipenuhi**: Masih violation
4. **PKWTT probation 6 bulan**: Lebih dari 3 bulan adalah violation

## cekwajar.id Implementation Notes

- **File to update**: `src/lib/hr/contract-management.ts`
- **Function to modify/create**: `validateContract()`, `getContractExpiryDate()`
- **Data source to query**: Employee contract records
- **Update frequency**: Per contract period
- **Legion action**: YES - can auto-detect contract type and alert on expiry

## Monetization Angle
- Contract lifecycle management
- Automated renewal/expiry alerts
- Compliance dashboard for contract violations

## Sources and Cross-References
- UU 13/2003 Pasal 59-60
- UU 11/2020 (sekarang UU 6/2023)
- PP 35/2021
