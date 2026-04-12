---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/labor-law/016-umsp-umsk.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:01.551335"
}
---

---
source_id: 016
title: "UMSP UMSK Upah Minimum Sektoral Provinsi Kabupaten Kota"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://peraturan.bpk.go.id/Download/370470"
last_verified: "2026-04-11"
tags: [umsp,umsk,upah-minimum-sektoral,labor-law,pengupahan]
cekwajar_impact: HIGH
legion_can_act: YES
---

# UMSP UMSK Upah Minimum Sektoral Provinsi Kabupaten Kota

## Why This Matters for cekwajar.id
UMSP dan UMSK adalahupah minimum yang lebih tinggi dari UMK/UMP untuk sektor tertentu. Perusahaan di industri tertentu (konfeksi, perhotelan, dll) mungkin harus membayar sesuai UMSK, bukan UMK standard.

## Core Knowledge

### Jenis Upah Minimum di Indonesia

```
UPah Minimum
├── UMK (Upah Minimum Kabupaten/Kota)
│   ├── UMK Standard
│   └── UMSK (Upah Minimum Sektoral Kabupaten/Kota) ← LEBIH TINGGI
├── UMP (Upah Minimum Provinsi)
│   ├── UMP Standard
│   └── UMSP (Upah Minimum Sektoral Provinsi) ← LEBIH TINGGI
```

### Ketentuan UMSP dan UMSK

1. **UMSP** = Upah Minimum Sektoral Provinsi
2. **UMSK** = Upah Minimum Sektoral Kabupaten/Kota
3. **Nilai harus lebih tinggi dari UMK/UMP** standard
4. **Ditetapkan oleh Gubernur** berdasarkan rekomendasi dewan pengupahan
5. **Berlaku untuk sektor tertentu** seperti:
   - Industri tekstil dan garment
   - Industri perhotelan
   - Industri perbankan
   - Pariwisata

### Dasar Hukum
- PP 36/2021 Pasal 23-25
- PP 51/2023 (perubahan)
- Permenaker 16/2024

### Contoh Nilai UMSP 2025

| Sektor | Provinsi | UMSP 2025 (Rp) |
|--------|----------|-----------------|
| Industri Textil/Garment | Jawa Tengah | 2.420.000 |
| Industri Perhotelan (Bintang 4-5) | Bali | 3.500.000 |
| Industri Perbankan | DKI Jakarta | 6.000.000 |

```typescript
interface UMSData {
  kodeWilayah: string;
  namaWilayah: string;
  jenis: 'provinsi' | 'kabupaten-kota';
  sektor: string;
  umum: number;  // UMP or UMK standard
  sektoral: number;  // UMSP or UMSK
  tanggalBerlaku: Date;
}

function getApplicableMinimumWage(
  employeeSector: string,
  locationCode: string,
  umsData: UMSData[]
): number {
  const data = umsData.find(
    d => d.kodeWilayah === locationCode && 
         d.sektor.toLowerCase() === employeeSector.toLowerCase()
  );
  
  if (data && data.sektoral > data.umum) {
    return data.sektoral;
  }
  
  // Fallback to standard UMK/UMP
  const standard = umsData.find(d => d.kodeWilayah === locationCode && d.sektor === 'standard');
  return standard ? standard.umum : 0;
}

function validateWageCompliance(
  totalCompensation: number,
  employeeSector: string,
  locationCode: string,
  umsData: UMSData[]
): { compliant: boolean; requiredWage: number; shortfall: number } {
  const requiredWage = getApplicableMinimumWage(employeeSector, locationCode, umsData);
  
  return {
    compliant: totalCompensation >= requiredWage,
    requiredWage,
    shortfall: Math.max(0, requiredWage - totalCompensation)
  };
}
```

## Exact Formulas / Numbers (if applicable)

### TypeScript Implementation
```typescript
interface EmployeeSector {
  employeeId: string;
  sectorCode: string;
  sectorName: string;
  locationCode: string;
}

interface UMSComparison {
  employeeId: string;
  umrStandard: number;
  umrSektoral: number;
  applicableWage: number;
  currentWage: number;
  isCompliant: boolean;
  shortfall: number;
}

function compareAndValidateSectorWages(
  employees: EmployeeSector[],
  currentWages: Map<string, number>,
  umsData: UMSData[]
): UMSComparison[] {
  return employees.map(emp => {
    const umrStandard = getUMK(emp.locationCode, umsData);
    const umrSektoral = getUMSK(emp.sectorName, emp.locationCode, umsData);
    const applicableWage = Math.max(umrStandard, umrSektoral);
    const wage = currentWages.get(emp.employeeId) || 0;
    
    return {
      employeeId: emp.employeeId,
      umrStandard,
      umrSektoral,
      applicableWage,
      currentWage: wage,
      isCompliant: wage >= applicableWage,
      shortfall: Math.max(0, applicableWage - wage)
    };
  });
}

function getUMSK(
  sector: string,
  locationCode: string,
  umsData: UMSData[]
): number {
  const umsk = umsData.find(
    d => d.kodeWilayah === locationCode && 
         d.jenis === 'kabupaten-kota' &&
         d.sektor.toLowerCase() === sector.toLowerCase()
  );
  return umsk ? umsk.sektoral : 0;
}
```

## Edge Cases and Common Mistakes

1. **Perusahaan baru tidak tahu sektor mereka**: should confirm dengan disnaker
2. **UMSK lebih rendah dari UMK standard**: Tidak boleh, should lebih tinggi
3. **Sector misclassification**: textile vs garment bisa beda UMSK
4. **Belum ada UMSK di daerah**: maka menggunakan UMK standard

## cekwajar.id Implementation Notes

- **File to update**: `src/data/sectoral-minimum-wages.json` (or Supabase)
- **Function to modify/create**: `getApplicableSectorWage()`, `validateSectorCompliance()`
- **Data source to query**: Supabase `sectoral_minimum_wages` table
- **Update frequency**: Annual
- **Legion action**: YES - can auto-match employee sector to applicable wage

## Monetization Angle
- Multi-sector wage compliance engine
- Sector benchmarking analytics
- Cost projection by industry sector

## Sources and Cross-References
- PP 36/2021 Pasal 23-25
- PP 51/2023
- Permenaker 16/2024
- Related: UMP, UMK
