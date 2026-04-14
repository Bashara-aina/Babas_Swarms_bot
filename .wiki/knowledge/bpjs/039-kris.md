---
source_id: 039
title: "KRIS BPJS Kesehatan: Kelas Rawat Inap Standar dan Implementasi 2025"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://www.cermati.com/artikel/kris-vs-kelas-bpjs"
last_verified: "2026-04-11"
tags: [bpjs-kesehatan, kris, kelas-rawat-inap-standar, rumah-sakit, implementasi-2025, hrtech]
cekwajar_impact: HIGH
legion_can_act: YES
---

# KRIS BPJS Kesehatan: Kelas Rawat Inap Standar dan Implementasi 2025

## Why This Matters for cekwajar.id
KRIS (Kelas Rawat Inap Standar) is the new system replacing class 1, 2, 3 in 2025. While this is primarily about healthcare service delivery (not payroll), understanding KRIS helps provide complete employee benefits information and prepare for future integration.

## Core Knowledge

### Apa Itu KRIS?
Kelas Rawat Inap Standar (KRIS) adalah sistem baru yang menghapus pembedaan kelas rawat inap berdasarkan iuran. Semua peserta JKN akan mendapat standar pelayanan rawat inap yang sama.

### Dasar Hukum
- **Perpres No. 59 Tahun 2024**: Perubahan ketiga atas Perpres No. 82/2018 tentang Jaminan Kesehatan
- **Target implementasi**: Paling lambat 30 Juni 2025 (diundur dari 1 Juli 2025)

### 12 Kriteria Fasilitas Rawat Inap KRIS
Rumah sakit harus memenuhi 12 standar minimum:

1. **Ventilasi udara**: Sirkulasi udara yang memadai
2. **Pencahayaan ruangan**: Cukup cahaya alami/artificial
3. **Kelengkapan tempat tidur**: Sesuai standar RS
4. **Tirai/partisi antar tempat tidur**: Untuk privasi
5. **Kamar mandi dalam ruangan**: Untuk rawat inap
6. **Pembuangan limbah**: Sistem yang proper
7. **Jarak antar tempat tidur**: Minimal 1,5 meter
8. **Ruang sirkulasi udara**: Kompartemen yang baik
9. **Tempat tidur sesuai standar**: UKURAN minimum
10. **Alat komunikasi internal RS**: Untuk kondisi darurat
11. **Sistem oksigen sentral**: Untuk perawatan
12. **Dukungan listrik cadangan**:Untuk emergensi

### Kapasitas Kamar
- **KRIS**: Maksimal 4 orang per kamar
- **Lama (Kelas 3)**: Bisa sampai 6-10 orang

### Dampak untuk Peserta
1. **Pelayanan lebih merata**: Tidak ada diskriminasi berdasarkan kelas
2. **Fasilitas RS harus upgrade**: Rumah sakit harus penuhi 12 kriteria
3. **Iuran masih dalam discussion**: Belum ada kepastian perubahan iuran

### Status Implementasi (2025)
- 1.436 rumah sakit sudah memenuhi 12 kriteria (57,28%)
- Target: 100% rumah sakitreu sesuai KRIS pada akhir 2025
- Beberapa RS masih dalam proses adaptasi

## Exact Formulas / Numbers (if applicable)
```typescript
interface KrisCriteria {
  ventilation: boolean;
  lighting: boolean;
  bedEquipment: boolean;
  bedPartition: boolean;
  privateBathroom: boolean;
  wasteDisposal: boolean;
  bedDistance: number;  // minimal 1.5 meter
  airCirculation: boolean;
  standardBed: boolean;
  internalCommunication: boolean;
  centralOxygen: boolean;
  backupPower: boolean;
}

interface KrisCompliance {
  hospitalId: string;
  hospitalName: string;
  totalCriteria: number;  // harus 12
  metCriteria: number;
  isCompliant: boolean;
  compliancePercentage: number;
}

function checkKrisCompliance(criteria: KrisCriteria): KrisCompliance {
  const criteriaList = [
    criteria.ventilation,
    criteria.lighting,
    criteria.bedEquipment,
    criteria.bedPartition,
    criteria.privateBathroom,
    criteria.wasteDisposal,
    criteria.bedDistance >= 1.5,
    criteria.airCirculation,
    criteria.standardBed,
    criteria.internalCommunication,
    criteria.centralOxygen,
    criteria.backupPower
  ];
  
  const metCriteria = criteriaList.filter(Boolean).length;
  
  return {
    totalCriteria: 12,
    metCriteria,
    isCompliant: metCriteria === 12,
    compliancePercentage: (metCriteria / 12) * 100
  };
}

// Catatan: Data ini untuk referensi, cekwajar.id tidak perlu implementasi ini
// kecuali jika ada module untuk tracking RS compliance
```

## Edge Cases and Common Mistakes
1. **Timing confusion**: KRIS implementation has been delayed multiple times
2. **Misunderstanding on iuran**: Tidak semua peserta paham bahwa iuran mungkin berubah
3. **RS belum ready**: Banyak RS masih dalam proses memenuhi kriteria
4. **Grace period**: RS bisa apply sebagian KRIS sambil menyelesaikan kriteria
5. **Upgrade desire**: Peserta kelas 1/2 mungkin ingin naik kelas, perlu asuransi tambahan

## cekwajar.id Implementation Notes
- **File to update**: `src/modules/hr/benefits/kris-module.ts` (optional)
- **Function to modify/create**: `getKrisStatus(employeeId: string): KrisInformation`
- **Data source to query**: This is healthcare-side data, not payroll; limited use in cekwajar.id unless providing employee benefits info
- **Update frequency**: Monitor BPJS Kesehatan announcements for iuran changes
- **Legion action**: Can create informational module for employees about KRIS

## Monetization Angle
- Employee benefits portal showing healthcare coverage
- Informational content about KRIS changes
- Integration with employee self-service for healthcare queries

## Sources and Cross-References
- Official URL: https://bpjs-kesehatan.go.id/
- Perpres No. 59 Tahun 2024
- Related: 038-kelas-rawat.md, 030-bpjs-kesehatan.md
