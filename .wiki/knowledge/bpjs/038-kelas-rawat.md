---
title: Kelas Rawat
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
summary: While payroll systems mainly deal with contribution calculations, understanding
  class benefits helps provide employee benefits information. Note that Perpres 59/2024
  is phasing out these classes in...
wikilinks: []
confidence: medium
source: research
---

# Kelas Rawat BPJS Kesehatan: Perbedaan Kelas 1, 2, dan 3

## Why This Matters for cekwajar.id
While payroll systems mainly deal with contribution calculations, understanding class benefits helps provide employee benefits information. Note that Perpres 59/2024 is phasing out these classes in favor of KRIS (Kelas Rawat Inap Standar).

## Core Knowledge

### Kelas dan Iuran BPJS Kesehatan (Sebelum KRIS)

| Kelas | Iuran/Bulan | Fasilitas Ruang Rawat |
|-------|-------------|---------------------|
| Kelas I | Rp 150.000 | Kamar yang lebih luas, maksimal 2-4 orang |
| Kelas II | Rp 100.000 | Kamar sedang, maksimal 4-6 orang |
| Kelas III | Rp 42.000 (subsidi pemerintah Rp 7.000) | Kamar lebih kecil, 6-10 orang |

### Pembagian Iuran untuk PU (Penerima Upah):
- 5% dari upah total (untuk employee's family coverage)
- 4% perusahaan + 1% karyawan

### Keluarga Tambahan:
- Anak ke-4+, ayah, ibu, mertua: 1% dari upah per orang
- Kerabat lain (saudara, ART): sesuai kelas yang dipilih

### Fasilitas yang Tidak Dipengaruhi Kelas:
1. **Faskes Tingkat 1**: Sama untuk semua kelas (Puskesmas, klinik pratama, dokter umum)
2. **Rawat Jalan**: Tidak ada perbedaan kelas untuk rawat jalan
3. **IKD (Instalasi Gawat Darurat)**: Tidak ada perbedaan
4. **Pemeriksaan penunjang**: Sama

### Fasilitas yang Dipengaruhi Kelas:
- Ruang rawat inap
- Kapasitas kamar
- Tingkat kenyamanan

## Exact Formulas / Numbers (if applicable)
```typescript
interface BpjsKesehatanClass {
  class: 'KELAS_1' | 'KELAS_2' | 'KELAS_3';
  monthlyPremium: number;
  governmentSubsidy: number;
  employeePortion: number;  // untuk PU, ini bagian pekerja
  maxRoomCapacity: number; // jumlah tempat tidur per kamar
}

const BPJS_CLASSES = {
  KELAS_1: {
    monthlyPremium: 150000,
    governmentSubsidy: 0,  // tidak disubsidi
    employeePortion: 150000,  // untuk peserta mandiri
    maxRoomCapacity: 4
  },
  KELAS_2: {
    monthlyPremium: 100000,
    governmentSubsidy: 0,
    employeePortion: 100000,
    maxRoomCapacity: 6
  },
  KELAS_3: {
    monthlyPremium: 42000,
    governmentSubsidy: 7000,  // dari pemerintah
    employeePortion: 35000,  // peserta bayar
    maxRoomCapacity: 10
  }
};

// Kalkulasi iuran keluarga tambahan
function calculateAdditionalFamilyContribution(
  baseSalary: number,
  relationType: 'CHILD_4+' | 'PARENT' | 'OTHER'
): { contribution: number; paidBy: 'EMPLOYEE' } {
  const ADDITIONAL_RATE = 0.01; // 1% dari upah
  
  return {
    contribution: Math.floor(baseSalary * ADDITIONAL_RATE),
    paidBy: 'EMPLOYEE'  // selalu ditanggung pekerja
  };
}
```

## Edge Cases and Common Mistakes
1. **KRIS coming**: System will replace classes, need to prepare for transition
2. **Keluarga tambahan**: Jangan hitung 5%, hanya 1% untuk keluarga tambahan
3. **Kelas III government subsidy**: Pemerintah bayar Rp 7.000, peserta hanya Rp 35.000
4. **Upgrade/downgrade**: Peserta bisa_REQUEST change of class, processed annually
5. **Newborn**: Bayi yang baru lahir mengikuti kelas orang tua

## cekwajar.id Implementation Notes
- **File to update**: `src/modules/hr/benefits/bpjs-health.ts`
- **Function to modify/create**: `getBpjsKesehatanClass(classLevel: string): BpjsKesehatanClass`
- **Data source to query**: Class selection from employee profile; KRIS migration status from government
- **Update frequency**: Rarely changes; monitor KRIS implementation for future updates
- **Legion action**: Can provide transition module when KRIS fully implemented

## Monetization Angle
- Employee self-service portal for class selection
- HR reporting on benefit costs per employee
- Integration with benefits module

## Sources and Cross-References
- Official URL: https://bpjs-kesehatan.go.id/
- Perpres No. 59 Tahun 2024 tentang KRIS
- Related: 039-kris-bpjs.md, 030-bpjs-kesehatan.md