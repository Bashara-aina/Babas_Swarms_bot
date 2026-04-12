---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/labor-law/008-uu-sjsn-40-2004.md",
  "reason": "daily_fast_scan: score=0.200 < 0.3",
  "score": 0.2,
  "quarantined_at": "2026-04-12T01:00:01.536035"
}
---

---
source_id: 008
title: "UU 40 Tahun 2004 Sistem Jaminan Sosial Nasional SJSN"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://peraturan.bpk.go.id/Details/40787"
last_verified: "2026-04-11"
tags: [uu40-2004,sjsn,bpjs,jaminan-sosial,kesehatan,pensiun]
cekwajar_impact: CRITICAL
legion_can_act: NO
---

# UU 40 Tahun 2004 Sistem Jaminan Sosial Nasional SJSN

## Why This Matters for cekwajar.id
UU 40/2004 adalah dasar hukum penyelenggaraan jaminan sosial di Indonesia melalui BPJS. Setiap perusahaan wajib mendaftarkan employee ke BPJS Kesehatan dan BPJS Ketenagakerjaan. Kalkulasi payroll harus memperhitungkan iuran dan validasi keikutsertaan.

## Core Knowledge

### Program Jaminan Sosial di Indonesia

1. **BPJS Kesehatan** - Jaminan Kesehatan
2. **BPJS Ketenagakerjaan** - 4 program:
   - Jaminan Kecelakaan Kerja (JKK)
   - Jaminan Kematian (JKM)
   - Jaminan Hari Tua (JHT)
   - Jaminan Pensiun (JP)

### Prinsip SJSN

1. **Gotong Royong** - Peserta membantu peserta lain
2. **Nirlaba** - Tidak bertujuan mencari keuntungan
3. **Keterbukaan** - Informasi terbuka untuk peserta
4. **Ke-hatihan** - Pengelolaan dilakukan secara prudent
5. **Aktabilitas** - Bertanggung jawab kepada peserta

### Iuran BPJS Kesehatan (Pasal 22)

| Kategori | Iuran |
|----------|-------|
| Pekerja Penerima Upah | 5% dari gaji (dibagi: 4% pemberi kerja + 1% pekerja) |
| Pekerja bukan penerima upah | Sesuai kemampuan |
| Bukan pekerja (mandiri) | Rp 35.000 - Rp 80.000/bulan |

### Iuran BPJS Ketenagakerjaan

**Jaminan Kecelakaan Kerja (JKK)**
- Tingkat risiko rendah: 0.24% dari upah
- Tingkat risiko sedang: 0.54% dari upah
- Tingkat risiko tinggi: 1.27% dari upah
- Seluruhnya dibayar oleh pemberi kerja

**Jaminan Kematian (JKM)**
- 0.30% dari upah (ditanggung pemberi kerja)

**Jaminan Hari Tua (JHT)**
- 5.7% dari upah (3.25% pemberi kerja + 2% pekerja)

**Jaminan Pensiun (JP)**
- 3% dari upah (2% pemberi kerja + 1% pekerja)

```typescript
interface BPJSContribution {
  bpjsKesehatan: number;
  bpjsKetenagakerjaan: {
    jkk: number;
    jkm: number;
    jht: number;
    jp: number;
  };
}

function hitungIuranBPJS(
  totalUpah: number,
  riskLevel: 'rendah' | 'sedang' | 'tinggi'
): BPJSContribution {
  const jkkRate = {
    rendah: 0.0024,
    sedang: 0.0054,
    tinggi: 0.0127
  };
  
  return {
    bpjsKesehatan: totalUpah * 0.05,
    bpjsKetenagakerjaan: {
      jkk: totalUpah * jkkRate[riskLevel],
      jkm: totalUpah * 0.003,
      jht: totalUpah * 0.057,
      jp: totalUpah * 0.03
    }
  };
}
```

## Exact Formulas / Numbers (if applicable)

### TypeScript Implementation
```typescript
interface Employee {
  id: string;
  totalUpah: number;
  riskLevel: 'rendah' | 'sedang' | 'tinggi';
  isBPJSHealth: boolean;
  isBPJSEmployment: boolean;
}

interface BPJSCalculation {
  health: {
    portionEmployer: number;
    portionEmployee: number;
    total: number;
  };
  employment: {
    jkk: number;
    jkm: number;
    jht: {
      employer: number;
      employee: number;
      total: number;
    };
    jp: {
      employer: number;
      employee: number;
      total: number;
    };
    total: number;
  };
  totalContribution: number;
}

function calculateAllBPJS(employee: Employee): BPJSCalculation {
  const { totalUpah, riskLevel } = employee;
  
  const jkkRate = { rendah: 0.0024, sedang: 0.0054, tinggi: 0.0127 };
  
  return {
    health: {
      portionEmployer: totalUpah * 0.04,
      portionEmployee: totalUpah * 0.01,
      total: totalUpah * 0.05
    },
    employment: {
      jkk: totalUpah * jkkRate[riskLevel],
      jkm: totalUpah * 0.003,
      jht: {
        employer: totalUpah * 0.0325,
        employee: totalUpah * 0.02,
        total: totalUpah * 0.0525
      },
      jp: {
        employer: totalUpah * 0.02,
        employee: totalUpah * 0.01,
        total: totalUpah * 0.03
      },
      total: totalUpah * (jkkRate[riskLevel] + 0.003 + 0.057 + 0.03)
    },
    totalContribution: totalUpah * (0.05 + jkkRate[riskLevel] + 0.003 + 0.057 + 0.03)
  };
}
```

### Upah yang Dijadikan Dasar Iuran
Menurut PP 46/2015 dan perubahannya:
- Upah pokok
- Tunjangan tetap
- Tidak termasuk tunjangan tidak tetap

## Edge Cases and Common Mistakes

1. **Tunjangan tidak tetap dihitung sebagai dasar iuran**: Tidak benar - hanya upah pokok + tunjangan tetap
2. **BPJS di atas batas maksimum**: Batas maksimum iuran adalah 12jt x 5% = Rp 600.000
3. **Perubahan karyawan tidak dilaporkan**: Wajib dilaporkan maksimal 7 hari kerja
4. **Nilai klaim tidak sesuai**: Perlu validasi against schedule of benefits

## cekwajar.id Implementation Notes

- **File to update**: `src/lib/payroll/bpjs-calculator.ts`
- **Function to modify/create**: `calculateBPJSContribution()`, `validateBPJSRegistration()`
- **Data source to query**: BPJS API (if available) or Supabase `bpjs_registrations` table
- **Update frequency**: Monthly for active employees, when salary changes
- **Legion action**: NO - requires integration with BPJS systems

## Monetization Angle
- Automated BPJS contribution calculation
- Compliance dashboard for employer obligations
- Integration with accounting/payroll system

## Sources and Cross-References
- Official URL: https://peraturan.bpk.go.id/Details/40787
- Diubah oleh: UU 24/2011 (BPJS), PP 46/2015
- Related: BPJS Kesehatan Act, BPJS Ketenagakerjaan Act
