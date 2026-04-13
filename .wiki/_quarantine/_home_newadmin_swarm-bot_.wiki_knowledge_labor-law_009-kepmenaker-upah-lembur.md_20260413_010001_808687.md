---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/labor-law/009-kepmenaker-upah-lembur.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.808713"
}
---

---
source_id: 009
title: "Kepmenaker 102 Tahun 2004 Waktu Kerja Lembur dan Upah Lembur"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://jdih.kemnaker.go.id/asset/data_puu/peraturan_file_186.pdf"
last_verified: "2026-04-11"
tags: [kepmenaker-102-2004,upah-lembur,waktu-kerja-lembur,lembur,overtime]
cekwajar_impact: HIGH
legion_can_act: YES
---

# Kepmenaker 102 Tahun 2004 Waktu Kerja Lembur dan Upah Lembur

## Why This Matters for cekwajar.id
Perhitunganupah lembur yang salah adalah salah satu violation paling umum. System harus implement rumus dengan tepat: 1/173 × upp sebulan sebagai dasar, dengan multiplier 1.5x untuk jam pertama dan 2x untuk jam berikutnya.

## Core Knowledge

### Dasar Hukum
- Kepmenaker 102/2004
- UU 13/2003 Pasal 78
- PP 35/2021 (perubahan)

### Waktu Kerja Standard

| Sistem | Jam per Minggu | Jam per Hari |
|--------|----------------|--------------|
| 6 hari × 7 jam | 40 | 7 |
| 5 hari × 8 jam | 40 | 8 |

### Waktu Kerja Lembur
Lembur adalah pekerjaan yang melebihi waktu kerja standard:
- Lebih dari 7 jam/hari untuk sistem 6 hari
- Lebih dari 8 jam/hari untuk sistem 5 hari
- Lebih dari 40 jam/minggu

### Formula Dasar Perhitungan

**Upah Setara Jam (Sejam)**
```
Upah sejam = Upah sebulan / 173
```

**Dasar Upah Sebulan** (Pasal 9):
- Upah pokok 100%
- Atau 75% dari total jika ada tunjangan

```typescript
function hitungUpahSejam(upahPokok: number, tunjanganTetap: number): number {
  const dasarUpah = upahPokok + tunjanganTetap;
  return dasarUpah / 173;
}

function hitungUpahSejamV2(upahPokok: number, totalUpah: number): number {
  // Jika tunjangan tetap > 25%, yang dihitung 75% dari total
  const tunjanganTetap = totalUpah - upahPokok;
  const komponenUpah = tunjanganTetap > (totalUpah * 0.25) 
    ? totalUpah * 0.75 
    : upahPokok + tunjanganTetap;
  return komponenUpah / 173;
}
```

## Exact Formulas / Numbers (if applicable)

### Rumus Upah Lembur

**Pada Hari Kerja Biasa**
```typescript
interface LemburHariBiasa {
  jamPertama: number;    // 1.5x
  jamBerikutnya: number; // 2x
  upahSejam: number;
}

function hitungLemburHariBiasa(lembur: LemburHariBiasa): number {
  const { jamPertama, jamBerikutnya, upahSejam } = lembur;
  return (jamPertama * 1.5 * upahSejam) + (jamBerikutnya * 2 * upahSejam);
}
```

**Pada Hari Libur Minggu/Hari Raya (Sistem 5 Hari × 8 Jam)**
```typescript
function hitungLemburHariLibur5Hari(jamLembur: number, upahSejam: number): number {
  if (jamLembur <= 8) {
    // Jam pertama 2x
    return jamLembur * 2 * upahSejam;
  } else {
    // Jam pertama 8 jam 2x, sisanya 3x
    return (8 * 2 * upahSejam) + ((jamLembur - 8) * 3 * upahSejam);
  }
}
```

**Pada Hari Libur Minggu/Hari Raya (Sistem 6 Hari × 7 Jam)**
```typescript
function hitungLemburHariLibur6Hari(jamLembur: number, upahSejam: number): number {
  if (jamLembur <= 7) {
    // Jam pertama 2x
    return jamLembur * 2 * upahSejam;
  } else if (jamLembur <= 8) {
    // Jam pertama 7 jam 2x, sisanya 3x
    return (7 * 2 * upahSejam) + ((jamLembur - 7) * 3 * upahSejam);
  } else {
    // Jam pertama 8 jam (7 jam 2x + 1 jam 3x), sisanya 4x
    return (7 * 2 * upahSejam) + (1 * 3 * upahSejam) + ((jamLembur - 8) * 4 * upahSejam);
  }
}
```

### Tabel Rate Lembur (Peraturan Lama)
| Waktu Lembur | Rate |
|--------------|------|
| Jam pertama lembur | 1.5x |
| Jam ke-2 dan seterusnya | 2x |
| Hari kerja ke-1 saat istirahat mingguan | 2x |
| Hari kerja ke-2 dan ke-3 | 3x |
| Hari raya keagamaan (hari pertama) | 2x |
| Hari raya keagamaan (hari ke-2 dan seterusnya) | 3x |

## Edge Cases and Common Mistakes

1. **Tidak membedakan "hari kerja" dan "hari libur"**: Rate berbeda!
2. **Tidak menghitung componentes "upah" dengan benar**: Apakah termasuk tunjangan tetap?
3. **Melebihi batas lembur**: Maksimal 4 jam/hari dan 18 jam/minggu
4. **Lembur pada hari nyata.libur**: Rate berbeda dengan lembur hari biasa

## cekwajar.id Implementation Notes

- **File to update**: `src/lib/payroll/overtime-calculator.ts`
- **Function to modify/create**: `calculateOvertimePay()`, `validateOvertimeHours()`
- **Data source to query**: Employee attendance/location data
- **Update frequency**: Per pay period
- **Legion action**: YES - can auto-calculate from attendance data

## Monetization Angle
- Real-time overtime tracking and alerts
- Overtime budgeting and forecasting
- Compliance reporting untuk audit

## Sources and Cross-References
- Official URL: https://jdih.kemnaker.go.id/asset/data_puu/peraturan_file_186.pdf
- Related: UU 13/2003 Pasal 78, PP 35/2021
