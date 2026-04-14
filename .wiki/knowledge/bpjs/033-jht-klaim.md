---
title: Jht Klaim
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- bpjs
created: '2026-04-14'
updated: '2026-04-14'
summary: While cekwajar.id focuses on payroll calculations, understanding JHT claim
  conditions is essential for HR modules. When employees leave (resign, laid off,
  retire), they may claim JHT. Knowing the r...
wikilinks: []
confidence: medium
source: research
---

# Klaim JHT BPJS Ketenagakerjaan: Syarat, Manfaat, dan Simulasi Pencairan

## Why This Matters for cekwajar.id
While cekwajar.id focuses on payroll calculations, understanding JHT claim conditions is essential for HR modules. When employees leave (resign, laid off, retire), they may claim JHT. Knowing the rules helps build accurate employee lifecycle management and termination calculations.

## Core Knowledge

### Syarat Klaim JHT (Peserta PU)

#### 1. Klaim 100% (Penuh)
- **Usia 56 tahun** (usia pensiun)
- **Cacat total tetap**
- **Meninggal dunia** (ke ahli waris)
- **Meninggalkan NKRI selamanya** (WNI atau WNA)
- **PHK** (Pemutusan Hubungan Kerja)
- **Mengundurkan diri** (这适用于特定条件)

#### 2. Klaim Sebagian (Maksimal 30%)
- **Persiapan pensiun**: Maksimal 10% dari saldo, harus punya masa kepesertaan min. 10 tahun
- **Membeli rumah**: Maksimal 30% dari saldo untukdp rumah pertama, harus punya masa kepesertaan min. 10 tahun

#### 3. Klaim 0% (Tidak bisa diambil)
- Masih bekerja dan tidak termasuk kriteria di atas
- Mengundurkan diri tapi belum 1 bulan setelah berhenti bekerja

### Dokumen yang Dibutuhkan

**Untuk PHK:**
- Formulir klaim JHT
- KTP asli
- Kartu BPJS Ketenagakerjaan
- Surat keterangan PHK dari perusahaan
- Buku tabungan (untuk transfer)

**Untuk 30% (persiapan rumah):**
- Formulir klaim JHT
- KTP asli
- Kartu BPJS Ketenagakerjaan
- Surat keterangan akan买的 rumah /熔斯特拉克斯
- Dokumen tambahan untuk validasi

### Mekanisme Perhitungan Saldo JHT
Saldo JHT = Total iuran (pekerja + perusahaan) + hasil pengembangan

Pengembangan dilakukan oleh BPJS Investasi dengan bagi hasil tertentu.

## Exact Formulas / Numbers (if applicable)
```typescript
interface JhtClaimRequest {
  claimType: 'FULL' | 'PARTIAL_PENSION' | 'PARTIAL_HOUSE';
  reason: 'RETIREMENT' | 'PHK' | 'DISABILITY' | 'DEATH' | 'OVERSEAS' | 'RESIGNATION';
  employeeId: string;
  monthsOfMembership: number;  // masa kepesertaan
  partialPercentage?: number;  // untuk klaim sebagian (max 30)
}

interface JhtBalance {
  employeeContributions: number;  // 2% x bulan
  employerContributions: number;  // 3.7% x bulan
  developmentReturns: number;     // hasil pengembangan
  totalBalance: number;
}

function validateJhtClaim(request: JhtClaimRequest, balance: JhtBalance): {
  eligible: boolean;
  maxClaimable: number;
  reason: string;
} {
  // Cek kelayakan klaim
  if (request.claimType === 'FULL') {
    const eligibleReasons = ['RETIREMENT', 'PHK', 'DISABILITY', 'DEATH', 'OVERSEAS'];
    if (!eligibleReasons.includes(request.reason)) {
      return { eligible: false, maxClaimable: 0, reason: 'Reason not eligible for full claim' };
    }
    return { eligible: true, maxClaimable: balance.totalBalance, reason: 'Full claim approved' };
  }

  if (request.claimType === 'PARTIAL_HOUSE') {
    if (request.monthsOfMembership < 120) {  // 10 tahun
      return { eligible: false, maxClaimable: 0, reason: 'Minimum 10 years membership required' };
    }
    const maxClaimable = balance.totalBalance * 0.30;
    return { eligible: true, maxClaimable, reason: '30% for house purchase approved' };
  }

  if (request.claimType === 'PARTIAL_PENSION') {
    if (request.monthsOfMembership < 120) {
      return { eligible: false, maxClaimable: 0, reason: 'Minimum 10 years membership required' };
    }
    const maxClaimable = balance.totalBalance * 0.10;
    return { eligible: true, maxClaimable, reason: '10% for pension preparation approved' };
  }

  return { eligible: false, maxClaimable: 0, reason: 'Invalid claim type' };
}
```

## Edge Cases and Common Mistakes
1. **Mengundurkan diri**: Ada masa tunggu 1 bulan setelah berhenti bekerja
2. **PHK vs mengundurkan diri**: Bedanya di dokumen yang diperlukan dan waktu pencairan
3. **Klaim 30% tidak bisa sekaligus**: Harus ada bukti tujuan (rumah/pensiun)
4. **Multi-employer**: Jika bekerja di beberapa perusahaan, saldo JHT tetap bisa diakumulasi
5. **Transfer keluar**: JHT tidak bisa di-transfer ke BPJS lain, hanya di-consolidate saat klaim

## cekwajar.id Implementation Notes
- **File to update**: `src/modules/hr/employee-lifecycle.ts` or termination module
- **Function to modify/create**: `checkJhtClaimEligibility(employeeId: string): ClaimEligibility`
- **Data source to query**: Employee membership start date, claim history from external BPJS API
- **Update frequency**: Rarely changes; check when there are regulatory updates
- **Legion action**: Can provide API integration placeholder for BPJS claim status; needs external API connection for actual balance

## Monetization Angle
- HR module for employee termination can include JHT claim guidance
- Reporting for employees leaving company
- Integration with exit interview and final settlement calculations

## Sources and Cross-References
- Official URL: https://www.bpjsketenagakerjaan.go.id/cara-klaim.html
- Permenaker No. 2 Tahun 2022 tentang JHT
- Related: 031-bpjs-ketenagakerjaan-iuran.md
