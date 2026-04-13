---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/labor-law/001-uu-ketenagakerjaan-13-2003.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.824155"
}
---

---
source_id: 001
title: "UU 13 Tahun 2003 Undang-Undang Ketenagakerjaan Indonesia"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://peraturan.bpk.go.id/Details/43013"
last_verified: "2026-04-11"
tags: [labor-law,uu13-2003,ketenagakerjaan,hubungan-kerja,perlindungan-pekerja]
cekwajar_impact: CRITICAL
legion_can_act: NO
---

# UU 13 Tahun 2003 Undang-Undang Ketenagakerjaan Indonesia

## Why This Matters for cekwajar.id
This is the foundational labor law in Indonesia that establishes the core rights and obligations of workers and employers. All payroll calculations, PPh 21 computations, and employee benefits must comply with this law. Any violations can result in legal penalties and back-pay claims.

## Core Knowledge

### Ruang Lingkup UU Ketenagakerjaan No. 13 Tahun 2003

Undang-Undang Nomor 13 Tahun 2003 tentang Ketenagakerjaan merupakan undang-undang dasar yang mengatur seluruh aspek hubungan kerja di Indonesia. UU ini mencakup:

1. **Perencanaan Tenaga Kerja** - Informasi dan pengembangan SDM
2. **Pelatihan Kerja** - Sertifikasi dan standar kompetensi
3. **Penempatan Tenaga Kerja** - Lembaga penempatan tenaga kerja
4. **Penggunaan Tenaga Kerja Asing (TKA)** - Izin dan pembatasan
5. **Hubungan Kerja** - Perjanjian kerja, PKWT, PKWTT
6. **Perlindungan Pekerja** - Keselamatan, kesehatan, kesejahteraan
7. **Pengupahan** - Upah minimum, struktur gaji
8. **Hubungan Industrial** - Serikat pekerja, bipartit, tripartit
9. **Pembinaan dan Pengawasan** - Sanksi dan penegakan hukum

### Jenis Kontrak Kerja

| Jenis | Keterangan |
|-------|------------|
| **PKWTT** | Perjanjian Kerja Waktu Tidak Tertentu (tetap) |
| **PKWT** | Perjanjian Kerja Waktu Tertentu (kontrak/kontrak) |

### Hak Pekerja Utama
- Hak atas pekerjaan yang layak
- Hak atas upah minimum
- Hak cuti (tahunan, sakit, melahirkan)
- Hak keselamatan dan kesehatan kerja (K3)
- Hak berasuransi (BPJS Kesehatan, BPJS Ketenagakerjaan)
- Hak pesangon saat PHK

### Pasal Penting
- **Pasal 59**: PKWT tidak dapat mensyaratkan masa percobaan
- **Pasal 60**: PKWTT dapat mensyaratkan masa percobaan maksimal 3 bulan
- **Pasal 90**: Pengusaha wajib membayar upah sesuai ketentuan minimum
- **Pasal 153**: Larangan PHK sepihak tanpa kompensasi

## Exact Formulas / Numbers (if applicable)

### Perhitungan Masa Kerja
```typescript
interface MasaKerja {
  tanggalMasuk: Date;
  tanggalAkhir: Date;
  tahun: number;
  bulan: number;
  hari: number;
}

function hitungMasaKerja(masuk: Date, akhir: Date): MasaKerja {
  const diffMs = akhir.getTime() - masuk.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const tahun = Math.floor(diffDays / 365);
  const sisaHari = diffDays % 365;
  const bulan = Math.floor(sisaHari / 30);
  const hari = sisaHari % 30;
  
  return { tahun, bulan, hari };
}
```

## Edge Cases and Common Mistakes

1. **Masa percobaan PKWT**:UU 13/2003 Pasal 59 ayat (1)明确规定 PKWT tidak boleh memiliki masa percobaan. Jika ada clause probation, bisa dianggap sebagai pelanggaran.
2. **Kontrak diperpanjang berkali-kali**: Sebelum UU Cipta Kerja, perpanjangan PKWT maksimal 2x. Sekarang setelah PP 35/2021, bisa maksimal 5 tahun total.
3. **Upah di bawah UMK**: Tetap bayar meskipun perjanjian kerja menyebut lebih rendah - ketentuan UMK bersifat imperative.
4. **THR tidak termasuk upah**: THR adalah tunjangan wajib terpisah dari perhitungan upah pokok untuk pesangon.

## cekwajar.id Implementation Notes

- **File to update**: `src/lib/payroll/labor-law.ts` (new file)
- **Function to modify/create**: `validateEmploymentContract()`, `calculateMaxContractPeriod()`
- **Data source to query**: Local reference data for labor law constants
- **Update frequency**: Static reference, update when regulation changes
- **Legion action**: NO - requires legal review for each client

## Monetization Angle
- Compliance checking module for HR software
- Contract validity verification API
- Risk assessment for non-compliant companies

## Sources and Cross-References
- Official URL: https://peraturan.bpk.go.id/Details/43013
- Last regulation update: Diubah oleh UU No. 6 Tahun 2023
- Related: UU Cipta Kerja 11/2020, PP 35/2021, PP 36/2021
