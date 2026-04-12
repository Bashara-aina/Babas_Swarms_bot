---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/bpjs/035-bpu.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:01.626862"
}
---

---
source_id: 035
title: "BPU BPJS Ketenagakerjaan: Bukan Penerima Upah (Pekerja Mandiri)"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://www.bpjsketenagakerjaan.go.id/bukan-penerima-upah.html"
last_verified: "2026-04-11"
tags: [bpjs-ketenagakerjaan, bpu, pekerja-mandiri, freelancer, ojek-online, labor-law]
cekwajar_impact: HIGH
legion_can_act: YES
---

# BPU BPJS Ketenagakerjaan: Bukan Penerima Upah (Pekerja Mandiri)

## Why This Matters for cekwajar.id
BPU covers gig workers, freelancers, ojek online, and self-employed who don't have an employer deducting BPJS. cekwajar.id may need to handle this segment if they expand to serving micro-businesses or gig economy platforms.

## Core Knowledge

### Siapa Itu BPU?
Bukan Penerima Upah adalah workers who don't receive regular salary/wage from employer:
- Pedagang kaki langit
- Pengusaha kecil
- Ojek online (Grab, Gojek)
- Freelancer/konsultan independent
- Pekerja paruh waktu tanpa ikatan kerja

### Program yang Tersedia untuk BPU
1. **JHT** (Jaminan Hari Tua)
2. **JKK** (Jaminan Kecelakaan Kerja)
3. **JKM** (Jaminan Kematian)

**Tidak tersedia untuk BPU**: JP (Jaminan Pensiun) dan JKP (Jaminan Kehilangan Pekerjaan)

### Iuran BPU

#### JHT BPU
| Plan | Iuran/Bulan | Keterangan |
|------|-------------|------------|
| Basic | Rp 36.800 | 3 program (JHT+JKK+JKM) |
| Extended | varies | Based on selected coverage |

#### JKK BPU
Rate depends on sector risk:
- Sektor transportasi: implementation of 50% dryanan for period Jan 2026 - Mar 2027
- Luar sektor transportasi: 50% dryanan Apr 2026 - Dec 2026

#### JKM BPU
Sebesar Rp 6.800 per bulan (perhitungan tetap)

### Pendaftaran BPU
1. **Online**: Melalui website BPJS Ketenagakerjaan, pilih "Bukan Penerima Upah"
2. **Kantor cabang**: Isi formulir 1A
3. **Mitra (Grab, Gojek, Shopee)**: Pendaftaran through platform collaboration
4. ** Agen (BRILink, POS)**: Through retail agents

### Pembayaran Iuran BPU
- Periodik: 1, 3, 6, atau 12 bulan
- Channels: ATM, mobile banking, e-wallet (OVO, Dana, GoPay), retail (Alfamart, Indomaret)
- Autodebit available untuk convenience

## Exact Formulas / Numbers (if applicable)
```typescript
interface BpuPlan {
  program: 'JHT_ONLY' | 'JHT_JKK' | 'JHT_JKM' | 'ALL_THREE';
  baseContribution: number;
  jkkRate?: number;  // risk-based if applicable
}

const BPU_BASE_IURAN = {
  JHT_ONLY: {
    1_month: 36000,
    3_month: 108000,
    6_month: 216000,
    12_month: 432000
  },
  ALL_THREE: {
    // Basic Rp 36.800 + JKM Rp 6.800 = Rp 43.600
    1_month: 43600,
    3_month: 130800,
    6_month: 261600,
    12_month: 523200
  }
};

// JKK rates for BPU (contoh sector risiko)
const BPU_JKK_RATES = {
  LOW_RISK: 0.0024,      // administrasi
  MEDIUM_RISK: 0.0054,   // transportasi ringan
  HIGH_RISK: 0.0089     // konstruksi
};

function calculateBpuContribution(
  plan: 'JHT_ONLY' | 'ALL_THREE',
  months: 1 | 3 | 6 | 12
): { total: number; breakdown: object } {
  const base = plan === 'JHT_ONLY' 
    ? BPU_BASE_IURAN.JHT_ONLY[months]
    : BPU_BASE_IURAN.ALL_THREE[months];
  
  return {
    total: base,
    breakdown: {
      jht: plan === 'JHT_ONLY' ? base : 36000 * months,
      jkm: plan === 'ALL_THREE' ? 6800 * months : 0
    }
  };
}
```

## Edge Cases and Common Mistakes
1. **Beda dari PU**: BPU tidak bisa dapat JP dan JKP
2. **Minimum payment**: Must pay for at least 1 month advance
3. **Grace period**: If unpaid, coverage becomes inactive but can be reactivated
4. **Overlapping with PU**: If someone becomes PU, they must switch registration
5. **Wrong sector for JKK**: BPU must choose correct risk sector for JKK rate

## cekwajar.id Implementation Notes
- **File to update**: `src/modules/payroll/bpu-module.ts` (if needed for gig platform integration)
- **Function to modify/create**: `calculateBpuContribution(plan: BpuPlan, months: number): BpuContribution`
- **Data source to query**: BPU plans from configuration, not changing frequently
- **Update frequency**: Rates change rarely; when there are dryanan programs
- **Legion action**: Can build BPU payment calculator for platform integration

## Monetization Angle
- Gig economy platforms may need BPU calculation for their drivers/workers
- Micro-business accounting software may integrate BPU payment tracking
- Commission for helping BPU participants pay through platform

## Sources and Cross-References
- Official URL: https://www.bpjsketenagakerjaan.go.id/bukan-penerima-upah.html
- Related: 031-bpjs-ketenagakerjaan-iuran.md (same programs, different calculation)