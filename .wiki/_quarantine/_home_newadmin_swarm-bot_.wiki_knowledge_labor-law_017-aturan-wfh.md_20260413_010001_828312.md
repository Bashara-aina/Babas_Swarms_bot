---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/labor-law/017-aturan-wfh.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.828333"
}
---

---
source_id: 017
title: "Aturan WFH Work From Home Kerja Remote Indonesia"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://www.hukumonline.com/berita/a/dorong-efisiensi-energi--menaker-imbau-perusahaan-terapkan-wfh-sehari-seminggu-lt69cde7862cb21/"
last_verified: "2026-04-11"
tags: [wfh,remote-work,kerja-remote,ketenagakerjaan]
cekwajar_impact: MEDIUM
legion_can_act: YES
---

# Aturan WFH Work From Home Kerja Remote Indonesia

## Why This Matters for cekwajar.id
.cekwajar.id HR module harus accommodate work arrangement yang fleksibel termasuk WFH dan remote work. Payroll calculation tidak berubah karena aturanupah tetap sama, tapi system harus track lokasi kerja untuk kepatuhan.

## Core Knowledge

### Status Regulasi WFH di Indonesia

**Saat ini belum ada UU spesifik** yang mengatur WFH secara komprehensif. Yang ada adalah:

1. **Surat Edaran Menaker** - Imbauan, bukan mengikat
2. **UU 13/2003** - Hanya mengatur waktu kerja, tidak spesifik lokasi
3. **UU Cipta Kerja** - Juga tidak atur WFH secara eksplisit
4. **Perpres 21/2023** - Khusus untuk ASN tentang hari kerja

### Ketentuan Umum WFH

Dari SE Menaker terbaru dan praktik umum:

1. **Upah tetap dibayar penuh** meskipun WFH
2. **Hak pekerja tetap sama** dengan working from office
3. **Company wajib menyediakan fasilitas** jika WFH mandatory
4. **Jam kerja tetap berlaku** - tidak lebih fleksibel dari yang diatur

```typescript
interface WorkArrangement {
  employeeId: string;
  arrangementType: 'office' | 'wfh' | 'hybrid' | 'remote';
  wfhDaysPerWeek?: number;
  remoteLocation?: string;
  isMandatory?: boolean;
}

function validateWorkArrangement(
  arrangement: WorkArrangement
): { valid: boolean; warnings: string[] } {
  const warnings: string[] = [];
  
  if (arrangement.arrangementType === 'wfh' || arrangement.arrangementType === 'hybrid') {
    // WFH tidak mengubah hak pekerja
    warnings.push('Upah tetap dibayarkan sesuai ketentuan');
    warnings.push('Hak THR, BPJS, dan cuti tetap berlaku');
  }
  
  if (arrangement.arrangementType === 'remote') {
    warnings.push('Pastikan agreement tertulis untuk remote work');
    warnings.push('Klarifikasi beban kerja dan ekspektasi');
  }
  
  return { valid: true, warnings };
}
```

### Jam Kerja untuk WFH

| Sistem Kerja | Jam per Hari | Total Jam/Minggu |
|--------------|--------------|------------------|
| 5 hari × 8 jam | 8 | 40 |
| 6 hari × 7 jam | 7 | 40 |

**Jika WFH lebih dari jam kerja**:
- Dianggap lembur
- Harus dibayar upah lembur

```typescript
function validateWorkHours(
  arrangementType: string,
  workingHours: number,
  standardHours: number = 8
): { overtimeHours: number; shouldPayOvertime: boolean } {
  if (workingHours > standardHours) {
    return {
      overtimeHours: workingHours - standardHours,
      shouldPayOvertime: true
    };
  }
  return { overtimeHours: 0, shouldPayOvertime: false };
}
```

## Exact Formulas / Numbers (if applicable)

### TypeScript Implementation
```typescript
interface WFHPolicy {
  companyId: string;
  allowsWFH: boolean;
  maxWFHDaysPerWeek: number;
  mandatoryEquipmentProvided: boolean;
  allowanceProvided: boolean;
  allowanceAmount: number;
}

interface EmployeeWorkLog {
  employeeId: string;
  date: Date;
  location: 'office' | 'home' | 'client' | 'other';
  hoursWorked: number;
}

function calculateWFHCompliance(
  employeeId: string,
  workLogs: EmployeeWorkLog[],
  policy: WFHPolicy
): {
  totalDaysWorked: number;
  wfhDays: number;
  officeDays: number;
  avgHoursPerDay: number;
  hasOvertime: boolean;
  policyViolations: string[];
} {
  const wfhLogs = workLogs.filter(log => log.location === 'home');
  const officeLogs = workLogs.filter(log => log.location === 'office');
  
  const violations: string[] = [];
  
  if (wfhLogs.length > policy.maxWFHDaysPerWeek * 4) { // per month approx
    violations.push(`WFH days exceed policy limit of ${policy.maxWFHDaysPerWeek} days/week`);
  }
  
  const totalHours = workLogs.reduce((sum, log) => sum + log.hoursWorked, 0);
  const avgHours = totalHours / workLogs.length;
  
  if (avgHours > 8) {
    violations.push('Average working hours exceed standard 8 hours');
  }
  
  return {
    totalDaysWorked: workLogs.length,
    wfhDays: wfhLogs.length,
    officeDays: officeLogs.length,
    avgHoursPerDay: avgHours,
    hasOvertime: avgHours > 8,
    policyViolations: violations
  };
}
```

## Edge Cases and Common Mistakes

1. **WFH = tidak dapat uang makan**: Tidakbenar - wennuang makan adalah tunjangan tetap, tetap dibayar
2. **Company potong gaji karena WFH**: Illegal - upah tidak boleh dikurangi karena lokasi kerja
3. **Tidak ada batas jam kerja saat WFH**: Tetap 40 jam/minggu, lebih dari itu = lembur
4. **Remote work agreement lisan**: Should always get written agreement

## cekwajar.id Implementation Notes

- **File to update**: `src/lib/hr/work-arrangement.ts`
- **Function to modify/create**: `validateWFHPolicy()`, `trackWorkLocation()`
- **Data source to query**: Employee work logs, company policy settings
- **Update frequency**: Per attendance entry
- **Legion action**: YES - can track and validate work arrangements

## Monetization Angle
- Work arrangement management module
- Remote work policy builder
- Compliance tracking for flexible work

## Sources and Cross-References
- UU 13/2003
- UU 11/2020 (sekarang UU 6/2023)
- SE Menaker terbaru tentang WFH
