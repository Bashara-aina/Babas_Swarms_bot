---
title: BPJS Reference Indonesia
type: concept
project: cekwajar
sources: [030-bpjs-kesehatan.md, 031-bpjs-ketenagakerjaan-iuran.md, 032-batas-upah.md, 033-jht-klaim.md, 034-jp-manfaat.md, 035-bpu.md, 036-sanksi.md, 037-integrasi-payroll.md, 038-kelas-rawat.md, 039-kris.md]
related: [[intent-routing]], [[vector-search]]
confidence: high
last_compiled: 2026-04-13
status: stub
tags: [bpjs-kesehatan, bpjs-ketenagakerjaan, jht, jp, jkk, jkm, jkp, kesehatan, tenaga-kerja, payroll, iuran, klaim, sanksi, integrasi]
word_count: 2150
---

# BPJS Reference Indonesia

## Overview

This document covers all aspects of BPJS (Badan Penyelenggara Jaminan Sosial) in Indonesia, including both BPJS Kesehatan (health insurance) and BPJS Ketenagakerjaan (labor insurance). These are mandatory social security programs for all Indonesian workers and employers.

---

## 1. BPJS Kesehatan (Health Insurance)

### 1.1 Iuran BPJS Kesehatan 2024: Perhitungan untuk Pekerja Swasta

#### Why This Matters
BPJS Kesehatan is a mandatory deduction for every employee in Indonesia. Incorrect calculation causes compliance violations, employee complaints, and potential penalties. This is a core payroll feature that must be accurate to the rupiah.

#### Peserta Penerima Upah (PPU) - Swasta
Berdasarkan Perpres No. 59 Tahun 2024 dan Perpres No. 82 Tahun 2018:

**Iuran sebesar 5% dari gaji/upah per bulan:**
- 4% ditanggung pemberi kerja (perusahaan)
- 1% ditanggung peserta (potongan gaji)

#### Kategori Peserta Lainnya:
1. **PNS/TNI/Polri**: 5% (4% pemberi kerja, 1% peserta)
2. **Keluarga Tambahan** (anak ke-4+, ayah, ibu, mertua): 1% dari gaji per orang per bulan, dibayar pekerja
3. **Peserta Mandiri (Bukan Penerima Upah)**:
   - Kelas I: Rp 150.000/bulan
   - Kelas II: Rp 100.000/bulan
   - Kelas III: Rp 42.000/bulan (dengan bantuan iuran pemerintah Rp 7.000)

#### Pembayaran Iuran
- Paling lambat tanggal 10 setiap bulan
- Tidak ada denda keterlambatan sejak 1 Juli 2016
- Denda pelayanan 5% dari biaya diagnosa awal × bulan tertunggak (maks 12 bulan, maks Rp 30 juta)

---

### 1.2 Kelas Rawat BPJS Kesehatan: Perbedaan Kelas 1, 2, dan 3

#### Kelas dan Iuran BPJS Kesehatan (Sebelum KRIS)

| Kelas | Iuran/Bulan | Fasilitas Ruang Rawat |
|-------|-------------|---------------------|
| Kelas I | Rp 150.000 | Kamar yang lebih luas, maksimal 2-4 orang |
| Kelas II | Rp 100.000 | Kamar sedang, maksimal 4-6 orang |
| Kelas III | Rp 42.000 (subsidi pemerintah Rp 7.000) | Kamar lebih kecil, 6-10 orang |

#### Pembagian Iuran untuk PU (Penerima Upah):
- 5% dari upah total (untuk employee's family coverage)
- 4% perusahaan + 1% karyawan

#### Keluarga Tambahan:
- Anak ke-4+, ayah, ibu, mertua: 1% dari upah per orang
- Kerabat lain (saudara, ART): sesuai kelas yang dipilih

#### Fasilitas yang Tidak Dipengaruhi Kelas:
1. **Faskes Tingkat 1**: Sama untuk semua kelas (Puskesmas, klinik pratama, dokter umum)
2. **Rawat Jalan**: Tidak ada perbedaan kelas untuk rawat jalan
3. **IKD (Instalasi Gawat Darurat)**: Tidak ada perbedaan
4. **Pemeriksaan penunjang**: Sama

---

### 1.3 KRIS BPJS Kesehatan: Kelas Rawat Inap Standar dan Implementasi 2025

#### Apa Itu KRIS?
Kelas Rawat Inap Standar (KRIS) adalah sistem baru yang menghapus pembedaan kelas rawat inap berdasarkan iuran. Semua peserta JKN akan mendapat standar pelayanan rawat inap yang sama.

#### Dasar Hukum
- **Perpres No. 59 Tahun 2024**: Perubahan ketiga atas Perpres No. 82/2018 tentang Jaminan Kesehatan
- **Target implementasi**: Paling lambat 30 Juni 2025 (diundur dari 1 Juli 2025)

#### 12 Kriteria Fasilitas Rawat Inap KRIS
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
12. **Dukungan listrik cadangan**: Untuk emergensi

#### Kapasitas Kamar
- **KRIS**: Maksimal 4 orang per kamar
- **Lama (Kelas 3)**: Bisa sampai 6-10 orang

#### Dampak untuk Peserta
1. **Pelayanan lebih merata**: Tidak ada diskriminasi berdasarkan kelas
2. **Fasilitas RS harus upgrade**: Rumah sakit harus penuhi 12 kriteria
3. **Iuran masih dalam discussion**: Belum ada kepastian perubahan iuran

#### Status Implementasi (2025)
- 1.436 rumah sakit sudah memenuhi 12 kriteria (57,28%)
- Target: 100% rumah sakit sesuai KRIS pada akhir 2025
- Beberapa RS masih dalam proses adaptasi

---

## 2. BPJS Ketenagakerjaan (Labor Insurance)

### 2.1 Iuran BPJS Ketenagakerjaan: JHT, JP, JKK, JKM untuk Karyawan Swasta

#### Why This Matters
BPJS Ketenagakerjaan is a mandatory program with 5 sub-programs (JHT, JP, JKK, JKM, JKP), each with different rates, caps, and employer/employee splits. Incorrect calculation leads to non-compliance, employee disputes, and potential penalties.

#### 1. Jaminan Hari Tua (JHT)
**Iuran: 5.7% dari upah sebulan**
- 2% dibayar pekerja
- 3.7% dibayar perusahaan
- Tidak ada batas atas (upa penuh)

**Manfaat**: Uang tunai saat:
- Usia 56 tahun
- PHK
- Cacat total tetap
- Meninggal dunia

#### 2. Jaminan Kecelakaan Kerja (JKK)
**Iuran: 0.24% - 1.74% dari upah** (berdasarkan tingkat risiko, ditanggung perusahaan)
- Sangat rendah: 0.24% (staff administrasi)
- Rendah: 0.54% (kasir, cleaning)
- Sedang: 0.89% (operator produksi)
- Tinggi: 1.27% (pekerja pabrik)
- Sangat tinggi: 1.74% (konstruksi, tambang)

**Catatan**: Industri padat karya (makanan, minuman, tekstil, furnitur) dapat keringanan 50% untuk periode tertentu.

#### 3. Jaminan Kematian (JKM)
**Iuran: 0.30% dari upah** (ditanggung perusahaan)
**Total manfaat**: Rp 42 juta + beasiswa anak hingga Rp 174 juta

#### 4. Jaminan Pensiun (JP)
**Iuran: 3% dari upah**
- 1% dibayar pekerja
- 2% dibayar perusahaan
- **Batas atas**: Rp 10.547.400/bulan (per Maret 2025)

**Manfaat**: Uang bulanan atau sekaligus saat usia pensiun/cacat/meninggal

#### 5. Jaminan Kehilangan Pekerjaan (JKP)
**Iuran: 0.36% dari upah**
- Pemerintah Pusat: 0.22%
- Rekomposisi JKK: 0.14%
- **Tidak ada iuran dari pekerja**

**Manfaat**: 60% upah selama 6 bulan + info lowongan + pelatihan

---

### 2.2 Batas Upah BPJS Ketenagakerjaan: JP Cap dan Perhitungan Maksimum

#### Batas Atas Upah JP (2025)
**Mulai 1 Maret 2025**: Rp 10.547.400/bulan

Ini adalah batas tertinggi upah yang digunakan sebagai dasar perhitungan iuran JP.

#### Mekanisme Penyesuaian
- BPJS Ketenagakerjaan menyesuaikan setiap tahun menggunakan faktor pengali: 1 + (tingkat inflasi/GDP growth)
- Kenaikan 2025: ~5.03% dari sebelumnya Rp 8.939.700

#### Program dengan Batas Atas
| Program | Batas Atas | Berlaku Sejak |
|---------|------------|---------------|
| JP | Rp 10.547.400 | Maret 2025 |
| JKK | Tidak ada | - |
| JKM | Tidak ada | - |
| JHT | Tidak ada | - |

#### Perhitungan Jika Upah di Atas Cap
```
Upah aktual: Rp 15.000.000
Batas atas JP: Rp 10.547.400

Iuran JP dihitung dari: Rp 10.547.400 (BUKAN Rp 15.000.000)
- Employee (1%): Rp 105.474
- Employer (2%): Rp 210.948
- Total: Rp 316.422
```

---

### 2.3 Klaim JHT BPJS Ketenagakerjaan: Syarat, Manfaat, dan Simulasi Pencairan

#### Syarat Klaim JHT (Peserta PU)

##### 1. Klaim 100% (Penuh)
- **Usia 56 tahun** (usia pensiun)
- **Cacat total tetap**
- **Meninggal dunia** (ke ahli waris)
- **Meninggalkan NKRI selamanya** (WNI atau WNA)
- **PHK** (Pemutusan Hubungan Kerja)
- **Mengundurkan diri** (untuk kondisi tertentu)

##### 2. Klaim Sebagian (Maksimal 30%)
- **Persiapan pensiun**: Maksimal 10% dari saldo, harus punya masa kepesertaan min. 10 tahun
- **Membeli rumah**: Maksimal 30% dari saldo untuk rumah pertama, harus punya masa kepesertaan min. 10 tahun

##### 3. Klaim 0% (Tidak bisa diambil)
- Masih bekerja dan tidak termasuk kriteria di atas
- Mengundurkan diri tapi belum 1 bulan setelah berhenti bekerja

#### Dokumen yang Dibutuhkan

**Untuk PHK:**
- Formulir klaim JHT
- KTP asli
- Kartu BPJS Ketenagakerjaan
- Surat keterangan PHK dari perusahaan
- Buku tabungan (untuk transfer)

---

### 2.4 Jaminan Pensiun (JP) BPJS: Manfaat Bulanan dan Formula Perhitungan

#### Jenis Manfaat JP

##### 1. Manfaat Pensiun (Bulanan)
Diberikan kepada peserta yang:
- Memasuki usia pensiun (56 tahun)
- Mengalami cacat total tetap
- Meninggal dunia (kepada janda/duda/anak)

**Formula Manfaat Pensiun:**
```
MP = 1% × MI × PDP × FP

Dimana:
MP = Manfaat Pensiun per bulan
MI = Masa Iur (bulan ke-i, max 20 tahun untuk pensiunan lama)
PDP = Penghasilan Dasar Pensiun (rata-rata 3 tahun terakhir, di-cap)
FP = Faktor Pengali (berdasarkan usia saat mulai menerima manfaat)
```

**Batas manfaat minimum**: Rp 300.000/bulan (sesuai PP 45/2015)

##### 2. Manfaat Pensiun Lump Sum (Sekaligus)
Untuk peserta dengan masa iur pendek atau pilihan pembayaran sekaligus.

##### 3. Manfaat Cacat
Jika cacat sebelum masa iur cukup, mendapat manfaat cacat.

##### 4. Manfaat Meninggal
50% dari formula manfaat pensiun untuk ahli waris.

#### Batas Penghasilan untuk Perhitungan JP
**Batas atas upah**: Rp 10.547.400/bulan (berlaku Maret 2025)

#### Usia Pensiun
- **Usia normal**: 56 tahun
- **Early retirement**: Bisa dari 45 tahun dengan syarat tertentu
- **Deferred**: Ditunda maksimal sampai 65 tahun

---

### 2.5 BPU BPJS Ketenagakerjaan: Bukan Penerima Upah (Pekerja Mandiri)

#### Siapa Itu BPU?
Bukan Penerima Upah adalah workers who don't receive regular salary/wage from employer:
- Pedagang kaki langit
- Pengusaha kecil
- Ojek online (Grab, Gojek)
- Freelancer/konsultan independent
- Pekerja paruh waktu tanpa ikatan kerja

#### Program yang Tersedia untuk BPU
1. **JHT** (Jaminan Hari Tua)
2. **JKK** (Jaminan Kecelakaan Kerja)
3. **JKM** (Jaminan Kematian)

**Tidak tersedia untuk BPU**: JP (Jaminan Pensiun) dan JKP (Jaminan Kehilangan Pekerjaan)

#### Iuran BPU

##### JHT BPU
| Plan | Iuran/Bulan | Keterangan |
|------|-------------|------------|
| Basic | Rp 36.800 | 3 program (JHT+JKK+JKM) |
| Extended | varies | Based on selected coverage |

##### JKK BPU
Rate depends on sector risk:
- Sektor transportasi: implementation of 50% keringanan for period Jan 2026 - Mar 2027
- Luar sektor transportasi: 50% keringanan Apr 2026 - Dec 2026

##### JKM BPU
Sebesar Rp 6.800 per bulan (perhitungan tetap)

---

### 2.6 Sanksi Perusahaan Tidak Daftar BPJS: Denda, Pidana, dan Larangan Layanan Publik

#### Sanksi Administratif (PP 86 Tahun 2013)

##### 1. Teguran Tertulis
Langkah pertama, perusahaan mendapat peringatan untuk mendaftarkan karyawannya.

##### 2. Denda
Denda keterlambatan pembayaran iuran:
- Denda pelayanan: 5% dari biaya diagnosa awal × bulan tertunggak
- Maksimum: Rp 30.000.000
- Denda untuk PPU ditanggung pemberi kerja

##### 3. Tidak Mendapat Pelayanan Publik Tertentu
Perusahaan yang belum terdaftar dapat dibatasi akses layanan publik seperti:
- izin usaha
- rekomendasi tender
- layanan perizinan tertentu

#### Sanksi Pidana (UU BPJS)

##### 1. Tidak Mendaftarkan Pekerja
- **Pidana kurungan**: Maksimal 1 tahun
- **Pidana denda**: Maksimal Rp 50.000.000

##### 2. Tidak Membayar Iuran
- **Pidana kurungan**: Maksimal 2 tahun
- **Pidana denda**: Maksimal Rp 100.000.000

##### 3. Pemberi kerja yang tidak mendaftarkan atau tidak terus membayar iuran:
- **Pidana penjara**: Maksimal 8 tahun
- **Pidana denda**: Maksimal Rp 1.000.000.000

---

### 2.7 Integrasi BPJS dengan Payroll: E-Payment System dan Remitansi

#### E-Payment System (EPS) BPJS Ketenagakerjaan

EPS is the electronic system for making BPJS contribution payments. Employers receive a billing code (kode iuran) for each payment period.

##### Kanal Pembayaran EPS:
1. **Bank persepsi**: BRI, BNI, BTN, Bank Mandiri, CIMB, dll
2. **Virtual Account**: Untuk internet banking dan mobile banking
3. **ATM**: Melalui menu pembayaran BPJS
4. **Teller**: Di kantor bank

##### Langkah Pembayaran via EPS:
1. Buat kode iuran melalui aplikasi SIPP atau EPS
2. Pilih periode pembayaran
3. Bayar melalui kanal yang tersedia
4. Konfirmasi dan simpan bukti pembayaran

#### Sistem Kode Iuran

##### Untuk PU (Penerima Upah):
- Kode berdasarkan NPP (Nomor Pokok Perusahaan) + periode
- Dihasilkan dari aplikasi SIPP atau melalui kantor cabang

##### Untuk BPU (Bukan Penerima Upah):
- Menggunakan NIK (16 digit) sebagai identifier
- Bayar sesuai dengan kode yang didapat saat pendaftaran

#### Virtual Account Numbering
```
BRI: 1234567890123456
BNI: 1234567890
Mandiri: 23996 + kode iuran
```

#### Autodebit
BPJS menyediakan layanan autodebit untuk kenyamanan:
- Tanggal 1-28 setiap bulan
- Melalui bank atau e-wallet
- Minimal 1 bulan periode

---

## 3. Implementation Notes for cekwajar.id

### Core Functions to Implement

#### BPJS Kesehatan Calculation
```typescript
interface BpjsKesehatanEmployee {
  grossSalary: number;
  bpjsHealth: {
    employerContribution: number;  // 4% dari gaji
    employeeContribution: number;  // 1% dari gaji
    totalIuran: number;           // 5% dari gaji
  }
}

function calculateBpjsKesehatan(grossSalary: number): BpjsKesehatanEmployee {
  const employerRate = 0.04;  // 4% pemberi kerja
  const employeeRate = 0.01; // 1% karyawan
  
  const employerContribution = Math.floor(grossSalary * employerRate);
  const employeeContribution = Math.floor(grossSalary * employeeRate);
  
  return {
    grossSalary,
    bpjsHealth: {
      employerContribution,
      employeeContribution,
      totalIuran: employerContribution + employeeContribution
    }
  };
}

// Contoh: Gaji Rp 6.000.000
// employer: Rp 240.000
// employee: Rp 60.000
// total: Rp 300.000
```

#### BPJS Ketenagakerjaan Calculation
```typescript
interface BpjsTkContribution {
  jht: {
    employee: number;   // 2% dari upah
    employer: number;   // 3.7% dari upah
    total: number;      // 5.7%
  };
  jkk: {
    rate: number;       // 0.24% - 1.74% berdasarkan risiko
    employer: number;   // 100% ditanggung perusahaan
  };
  jkm: {
    employer: number;   // 0.30%
  };
  jp: {
    employee: number;   // 1%
    employer: number;   // 2%
    total: number;      // 3%
    cap: number;        // Rp 10.547.400
  };
  jkp: {
    government: number;  // 0.22%
    fromJkk: number;    // 0.14%
  };
}

const JP_CAP_2025 = 10_547_400;

function calculateBpjsTk(
  monthlySalary: number,
  jkkRiskRate: number = 0.54  // default: rendah
): BpjsTkContribution {
  const JHT_EMPLOYEE_RATE = 0.02;
  const JHT_EMPLOYER_RATE = 0.037;
  const JKK_RATE = jkkRiskRate;
  const JKM_RATE = 0.003;
  const JP_EMPLOYEE_RATE = 0.01;
  const JP_EMPLOYER_RATE = 0.02;
  const JKP_GOV_RATE = 0.0022;
  const JKP_FROM_JKK_RATE = 0.0014;

  const jhtEmployee = Math.floor(monthlySalary * JHT_EMPLOYEE_RATE);
  const jhtEmployer = Math.floor(monthlySalary * JHT_EMPLOYER_RATE);
  const jkkEmployer = Math.floor(monthlySalary * JKK_RATE);
  const jkmEmployer = Math.floor(monthlySalary * JKM_RATE);

  const jpCappedSalary = Math.min(monthlySalary, JP_CAP_2025);
  const jpEmployee = Math.floor(jpCappedSalary * JP_EMPLOYEE_RATE);
  const jpEmployer = Math.floor(jpCappedSalary * JP_EMPLOYER_RATE);

  const jkpGov = Math.floor(monthlySalary * JKP_GOV_RATE);
  const jkpFromJkk = Math.floor(monthlySalary * JKP_FROM_JKK_RATE);

  return {
    jht: {
      employee: jhtEmployee,
      employer: jhtEmployer,
      total: jhtEmployee + jhtEmployer
    },
    jkk: {
      rate: JKK_RATE,
      employer: jkkEmployer
    },
    jkm: {
      employer: jkmEmployer
    },
    jp: {
      employee: jpEmployee,
      employer: jpEmployer,
      total: jpEmployee + jpEmployer,
      cap: JP_CAP_2025,
      usedCap: jpCappedSalary < monthlySalary
    },
    jkp: {
      government: jkpGov,
      fromJkk: jkpFromJkk
    }
  };
}
```

### Files to Update
- `src/core/payroll/calculations.ts` - BPJS Kesehatan calculation
- `src/core/payroll/bpjs-tk.ts` - BPJS Ketenagakerjaan calculation
- `src/config/bpjs-rates.ts` - Rate configuration and JP cap

### Edge Cases to Handle
1. **Gaji di bawah UMR**: Tetap dihitung dari gaji aktual, bukan UMR
2. **JP cap not applied**: Gaji di atas Rp 10.547.400 harus di-cap
3. **JKK rate wrong**: Mapping berdasarkan jabatan/tingkat risiko
4. **Keluarga tambahan**: Jangan hitung 5%, hanya 1% untuk keluarga tambahan
5. **Multi-job**: If karyawan punya 2 pekerjaan, each employer menghitung terpisah

---

## 4. Common Mistakes to Avoid

1. **Forgot to cap JP**: Calculate JP from actual salary instead of capped salary
2. **Wrong iuran split**: Using wrong percentages for employee vs employer
3. **Missing JKP**: JKP is not from employee, don't deduct from salary
4. **BPU vs PU confusion**: BPU doesn't have JP and JKP programs
5. **Using outdated cap**: Hardcode old cap instead of reading from config
6. **KRIS transition**: Prepare for class system replacement

---

## 5. Sources and References

- Official URL: https://www.bpjsketenagakerjaan.go.id/
- Official URL: https://bpjs-kesehatan.go.id/
- Perpres No. 59 Tahun 2024 (Perubahan ketiga atas Perpres 82/2018)
- PP No. 6 Tahun 2025 tentang JKK dan JKM
- PP No. 7 Tahun 2025 tentang JP (batas upah terbaru)
- UU No. 24 Tahun 2011 tentang BPJS
- PP No. 86 Tahun 2013 tentang Sanksi Administratif
- PP No. 45 Tahun 2015 tentang JP