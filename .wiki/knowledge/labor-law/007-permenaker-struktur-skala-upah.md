---
source_id: 007
title: "Permenaker 1 Tahun 2017 Struktur dan Skala Upah"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://peraturan.bpk.go.id/Details/146240"
last_verified: "2026-04-11"
tags: [permenaker-1-2017,struktur-skala-upah,阶梯-gaji,gaji-rangking]
cekwajar_impact: HIGH
legion_can_act: YES
---

# Permenaker 1 Tahun 2017 Struktur dan Skala Upah

## Why This Matters for cekwajar.id
Setiap perusahaan wajib memiliki struktur dan skalaupah yang dipublikasikan kepada worker. cekwajar.id harus dapat generate dan memvalidasi strukturupah sesuai ketentuan Permenaker 1/2017 untuk memastikan payroll system compliance.

## Core Knowledge

### Kewajiban Struktur dan Skala Upah

Menurut Permenaker 1/2017:
1. Setiap perusahaan wajib menyusun struktur dan skalaupah
2. Struktur dan skalaupah wajib dipublikasikan di tempat kerja
3. Berlaku untuk semua pekerja/buruh dengan hubungan kerja
4. Disusun berdasarkan golongan/jabatan

### Tahapan Penyusunan (Pasal 4)

**Tahap 1**: Siapkan Daftar Jabatan dan Upah
- Nomor urut
- Nama jabatan
- Upah masing-masing jabatan

**Tahap 2**: Hitung Nilai Relatif
- Metode Rangking Sederhana
- Metode Dua Titik
- Metode Poin Faktor

**Tahap 3**: Gambarkan dalam Grafik

### Metode Penyusunan

#### 1. Metode Rangking Sederhana
```typescript
interface JabatanUpah {
  nomorUrut: number;
  namaJabatan: string;
  jumlahUpah: number;
}

function metodeRangkingSederhana(daftarJabatan: JabatanUpah[]): {
  golongan: number;
  jabatan: string;
  upahMin: number;
  upahMax: number;
}[] {
  // Urutkan berdasarkan upah
  const sorted = [...daftarJabatan].sort((a, b) => a.jumlahUpah - b.jumlahUpah);
  
  // Bagi menjadi 3-5 golongan
  const jumlahGolongan = 5;
  const perGolongan = Math.ceil(sorted.length / jumlahGolongan);
  
  const hasil: Array<{ golongan: number; jabatan: string; upahMin: number; upahMax: number }> = [];
  
  for (let i = 0; i < jumlahGolongan; i++) {
    const start = i * perGolongan;
    const end = Math.min(start + perGolongan, sorted.length);
    const group = sorted.slice(start, end);
    
    if (group.length > 0) {
      hasil.push({
        golongan: i + 1,
        jabatan: group.map(j => j.namaJabatan).join(', '),
        upahMin: group[0].jumlahUpah,
        upahMax: group[group.length - 1].jumlahUpah
      });
    }
  }
  
  return hasil;
}
```

#### 2. Metode Dua Titik
```typescript
function metodeDuaTitik(
  daftarJabatan: JabatanUpah[],
  titikBawah: number, // Persentil bawah (misal 40)
  titikAtas: number    // Persentil atas (misal 60)
): { golongan: number; jabatan: string; upahMin: number; upahMax: number }[] {
  const sorted = [...daftarJabatan].sort((a, b) => a.jumlahUpah - b.jumlahUpah);
  const n = sorted.length;
  
  const idxBawah = Math.floor(n * titikBawah / 100);
  const idxAtas = Math.floor(n * titikAtas / 100);
  
  const upahBawah = sorted[idxBawah].jumlahUpah;
  const upahAtas = sorted[idxAtas].jumlahUpah;
  
  // Gradient = (Upah Atas - Upah Bawah) / (n - 1)
  const gradient = (upahAtas - upahBawah) / (n - 1);
  
  return sorted.map((jabatan, i) => ({
    golongan: i + 1,
    jabatan: jabatan.namaJabatan,
    upahMin: Math.round(upahBawah + (i * gradient)),
    upahMax: Math.round(upahBawah + ((i + 1) * gradient))
  }));
}
```

### Rasio Upah (Pasal 8)
```typescript
interface RasioUpah {
  rasioTertinggiTerendah: number;
  perusahaanSize: 'kecil' | 'menengah' | 'besar';
}

function hitungRasioUpah(structure: Array<{ golongan: number; upahMin: number; upahMax: number }>): number {
  const semuaUpah = structure.flatMap(g => [g.upahMin, g.upahMax]);
  return Math.max(...semuaUpah) / Math.min(...semuaUpah);
}

function validateRasio(rasio: number, companySize: 'kecil' | 'menengah' | 'besar'): boolean {
  const batasMaksimum = {
    kecil: 10,      // Rasio maksimal 10:1
    menengah: 15,   // Rasio maksimal 15:1
    besar: 20       // Rasio maksimal 20:1
  };
  return rasio <= batasMaksimum[companySize];
}
```

## Exact Formulas / Numbers (if applicable)

### Rumus Gradient (Metode Dua Titik)
```
G = (U_atas - U_bawah) / (n - 1)
```
Dimana:
- G = Gradient
- U_atas = Upah pada persentil atas
- U_bawah = Upah pada persentil bawah
- n = Jumlah jabatan

### Upah per Golongan
```
U_i = U_bawah + (i × G)
```
Dimana i = 0, 1, 2, ..., n-1

## Edge Cases and Common Mistakes

1. **Perusahaan baru tidak punya data**: Gunakan strukturupah dari perusahaan sejenis atau asosiasi
2. **Rasio terlalu tinggi**: Bisa diaudit dan diminta perbaikan
3. **Tidak dipublikasikan**: Termasuk pelanggaran administratif
4. **Struktur tidak update**: Wajib diperbarui saat ada perubahan organizational structure

## cekwajar.id Implementation Notes

- **File to update**: `src/lib/payroll/wage-structure.ts`
- **Function to modify/create**: `generateWageStructure()`, `validateWageRatio()`
- **Data source to query**: Company organizational data, historical salary data
- **Update frequency**: When organizational structure changes or annually
- **Legion action**: YES - can generate and audit wage structures

## Monetization Angle
- Wage structure builder tool for SMEs
- Compliance reporting untuk audit ketenagakerjaan
- Salary benchmarking against industry standards

## Sources and Cross-References
- Official URL: https://peraturan.bpk.go.id/Details/146240
- Related: PP 36/2021, UU 13/2003
