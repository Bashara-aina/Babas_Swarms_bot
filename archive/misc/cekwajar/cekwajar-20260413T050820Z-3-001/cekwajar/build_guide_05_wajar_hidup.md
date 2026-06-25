# Build Guide 05: Wajar Hidup — Cost of Living Comparison

**Priority:** Fifth tool. Simplest. Launch Week 10–11 (parallel with Wajar Kabur).  
**Accuracy target:** 70–80% (BPS CPI is official but lagged; Numbeo is real-time but user-submitted)  
**Data strategy:** BPS CPI (free official) + Numbeo Indonesia cities (scrape) + Crowdsource basket  
**Complexity:** Lowest of all 5 tools. Mostly UI + data display.

---

## What Wajar Hidup Does

User inputs: current city + target city (or current salary + target city)  
System shows: how much more/less you need to earn to maintain same lifestyle  

**Core formula:**
```
Required Salary in Target City = Current Salary × (COL_Target / COL_Current)
Adjustment % = ((COL_Target / COL_Current) - 1) × 100
```

---

## Free Data Sources

| Source | What It Provides | Format | Access |
|--------|-----------------|--------|--------|
| BPS CPI (Indeks Harga Konsumen) | City-level inflation rates, price indices | Excel/CSV monthly | bps.go.id free download |
| Numbeo (Indonesia cities) | Cost of living index per Indonesian city | Scrape | Free/scrape |
| BPS Survei Biaya Hidup | Detailed household expenditure by city | Excel | bps.go.id free |
| Hargapangan.id | Fresh food prices by city | API | Free |
| Komunitas/forums | Anecdotal cost data | — | — |

---

## Step 1: BPS CPI Data

`[MANUAL]` — Download from BPS
1. Go to: https://www.bps.go.id/id/statistics-table/1/OTUxIzE=/indeks-harga-konsumen.html
2. Download "IHK Kota" (CPI by City) Excel file
3. Also download: Survei Biaya Hidup per kota (SBH) — done every 5 years, gives basket weights

`[SWARMS]` — Parse and load:

```python
# agents/data_loaders/bps_cpi_loader.py
import pandas as pd
from supabase import create_client
import os

supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])

# BPS tracks ~90 cities for CPI (most complete city coverage in official data)
def load_bps_cpi(excel_path: str, year: int, month: int):
    """
    Load BPS IHK (CPI) by city.
    BPS covers ~90 cities with monthly CPI data.
    This is OFFICIAL government data — 100% legal to use.
    """
    df = pd.read_excel(excel_path, skiprows=4)  # BPS has 4 header rows typically
    
    records = []
    for _, row in df.iterrows():
        city = row.get('Kota', row.get('City', ''))
        cpi = row.get('IHK', row.get('CPI', row.get('Indeks', None)))
        
        if city and pd.notna(cpi) and cpi > 0:
            records.append({
                'city': str(city).strip(),
                'cpi_index': float(cpi),
                'year': year,
                'month': month,
                'source': 'bps_ihk',
            })
    
    if records:
        supabase.table('city_cpi_data').upsert(records).execute()
        print(f"Loaded {len(records)} BPS CPI records")
    
    return records


def calculate_col_index_from_bps(records: list[dict]) -> list[dict]:
    """
    Normalize CPI to create a Cost of Living Index where Jakarta = 100.
    """
    jakarta_cpi = next(
        (r['cpi_index'] for r in records if 'jakarta' in r['city'].lower()),
        110  # Default if Jakarta not found
    )
    
    normalized = []
    for r in records:
        normalized.append({
            **r,
            'col_index': round((r['cpi_index'] / jakarta_cpi) * 100, 1),
        })
    
    return normalized
```

---

## Step 2: Supabase Schema

`[SUPABASE]`:

```sql
-- Monthly CPI by city (from BPS)
CREATE TABLE public.city_cpi_data (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  city TEXT NOT NULL,
  province TEXT,
  cpi_index NUMERIC(8,2),
  col_index NUMERIC(8,2),   -- Normalized: Jakarta = 100
  year INTEGER NOT NULL,
  month INTEGER,
  source TEXT DEFAULT 'bps_ihk',
  UNIQUE(city, year, month)
);

-- Cost of living basket by city (detailed breakdown)
CREATE TABLE public.col_basket (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  city TEXT NOT NULL,
  category TEXT NOT NULL,  -- food, housing, transport, entertainment, utilities
  item_name TEXT NOT NULL,
  average_price NUMERIC(15,2),
  unit TEXT,  -- 'per_month', 'per_kg', 'per_liter'
  currency TEXT DEFAULT 'IDR',
  year INTEGER,
  source TEXT,
  UNIQUE(city, item_name, year)
);

-- Pre-computed adjustment factors between city pairs
CREATE TABLE public.city_adjustment_factors (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  city_from TEXT NOT NULL,
  city_to TEXT NOT NULL,
  adjustment_factor NUMERIC(8,4),  -- Multiply salary by this
  adjustment_pct NUMERIC(6,2),     -- % difference
  last_calculated TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(city_from, city_to)
);

-- Seed data: Indonesian cities with COL indices (base from BPS + Numbeo)
INSERT INTO public.city_cpi_data (city, province, col_index, year, month, source) VALUES
-- These are ILLUSTRATIVE — replace with actual BPS data after download
('Jakarta Selatan', 'DKI Jakarta', 100.0, 2024, 1, 'bps_ihk'),
('Jakarta Pusat', 'DKI Jakarta', 102.0, 2024, 1, 'bps_ihk'),
('Surabaya', 'Jawa Timur', 84.0, 2024, 1, 'bps_ihk'),
('Bandung', 'Jawa Barat', 79.0, 2024, 1, 'bps_ihk'),
('Medan', 'Sumatera Utara', 72.0, 2024, 1, 'bps_ihk'),
('Semarang', 'Jawa Tengah', 73.0, 2024, 1, 'bps_ihk'),
('Yogyakarta', 'DI Yogyakarta', 68.0, 2024, 1, 'bps_ihk'),
('Makassar', 'Sulawesi Selatan', 74.0, 2024, 1, 'bps_ihk'),
('Palembang', 'Sumatera Selatan', 68.0, 2024, 1, 'bps_ihk'),
('Balikpapan', 'Kalimantan Timur', 82.0, 2024, 1, 'bps_ihk'),
('Bali (Denpasar)', 'Bali', 91.0, 2024, 1, 'bps_ihk'),
('Bogor', 'Jawa Barat', 76.0, 2024, 1, 'bps_ihk'),
('Bekasi', 'Jawa Barat', 88.0, 2024, 1, 'bps_ihk'),
('Tangerang', 'Banten', 90.0, 2024, 1, 'bps_ihk'),
('Depok', 'Jawa Barat', 85.0, 2024, 1, 'bps_ihk'),
('Malang', 'Jawa Timur', 70.0, 2024, 1, 'bps_ihk'),
('Pekanbaru', 'Riau', 75.0, 2024, 1, 'bps_ihk'),
('Manado', 'Sulawesi Utara', 71.0, 2024, 1, 'bps_ihk'),
('Padang', 'Sumatera Barat', 66.0, 2024, 1, 'bps_ihk'),
('Pontianak', 'Kalimantan Barat', 69.0, 2024, 1, 'bps_ihk');

-- All publicly readable
ALTER TABLE public.city_cpi_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.col_basket ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read COL" ON public.city_cpi_data FOR SELECT USING (true);
CREATE POLICY "Public read basket" ON public.col_basket FOR SELECT USING (true);
```

---

## Step 3: Calculation Engine

`[CURSOR]` — Create: `lib/calculations/cost-of-living.ts`

```typescript
// lib/calculations/cost-of-living.ts

export interface COLInput {
  currentCity: string;
  targetCity: string;
  currentMonthlySalary: number;
  lifestyle: 'hemat' | 'standar' | 'nyaman';  // Budget / Standard / Comfortable
}

export interface COLResult {
  currentCOLIndex: number;
  targetCOLIndex: number;
  adjustmentFactor: number;    // Multiply salary by this
  adjustmentPct: number;       // % more or less
  requiredSalary: number;      // Salary needed in target city for same lifestyle
  salaryDiff: number;          // Difference (can be negative)
  verdict: 'LEBIH_MURAH' | 'LEBIH_MAHAL' | 'HAMPIR_SAMA';
  verdictLabel: string;
  breakdown: CategoryBreakdown[];
  confidence: number;
  note: string;
}

interface CategoryBreakdown {
  category: string;
  currentCityMonthly: number;
  targetCityMonthly: number;
  diff: number;
  diffPct: number;
}

// Lifestyle multipliers: hemat=0.7, standar=1.0, nyaman=1.4
const LIFESTYLE_MULTIPLIER = {
  hemat: 0.70,
  standar: 1.00,
  nyaman: 1.40,
};

// Estimated monthly spending by category in Jakarta at IDR 10M salary (standard)
// Source: BPS Survei Biaya Hidup, adjusted
const JAKARTA_BASELINE_MONTHLY: Record<string, number> = {
  'Makanan & Minuman': 2_500_000,
  'Tempat Tinggal': 2_000_000,   // Kos/sewa, bukan cicilan KPR
  'Transportasi': 800_000,
  'Utilitas (listrik, air, internet)': 500_000,
  'Hiburan & Gaya Hidup': 600_000,
  'Pendidikan': 300_000,
  'Kesehatan': 200_000,
  'Tabungan/Investasi': 500_000,
};

export function calculateCOLAdjustment(
  currentCOLIndex: number,
  targetCOLIndex: number,
  currentSalary: number,
  lifestyle: 'hemat' | 'standar' | 'nyaman'
): COLResult {
  const adjustmentFactor = targetCOLIndex / currentCOLIndex;
  const adjustmentPct = (adjustmentFactor - 1) * 100;
  const requiredSalary = Math.round(currentSalary * adjustmentFactor * LIFESTYLE_MULTIPLIER[lifestyle]);
  const salaryDiff = requiredSalary - currentSalary;
  
  let verdict: COLResult['verdict'];
  let verdictLabel: string;
  
  if (adjustmentPct < -10) {
    verdict = 'LEBIH_MURAH';
    verdictLabel = `Biaya hidup lebih murah ${Math.abs(adjustmentPct).toFixed(0)}% dari kota asal 🟢`;
  } else if (adjustmentPct > 10) {
    verdict = 'LEBIH_MAHAL';
    verdictLabel = `Biaya hidup lebih mahal ${adjustmentPct.toFixed(0)}% dari kota asal 🔴`;
  } else {
    verdict = 'HAMPIR_SAMA';
    verdictLabel = `Biaya hidup hampir sama dengan kota asal 🔵`;
  }
  
  // Estimate category breakdown
  const breakdown: CategoryBreakdown[] = Object.entries(JAKARTA_BASELINE_MONTHLY).map(([cat, jakartaBase]) => {
    const currentBase = jakartaBase * (currentCOLIndex / 100);
    const targetBase = jakartaBase * (targetCOLIndex / 100);
    return {
      category: cat,
      currentCityMonthly: Math.round(currentBase),
      targetCityMonthly: Math.round(targetBase),
      diff: Math.round(targetBase - currentBase),
      diffPct: Math.round(((targetBase - currentBase) / currentBase) * 100),
    };
  });
  
  return {
    currentCOLIndex,
    targetCOLIndex,
    adjustmentFactor: Math.round(adjustmentFactor * 10000) / 10000,
    adjustmentPct: Math.round(adjustmentPct * 10) / 10,
    requiredSalary,
    salaryDiff,
    verdict,
    verdictLabel,
    breakdown,
    confidence: 65, // BPS data is reliable but lagged
    note: 'Data berdasarkan Indeks Harga Konsumen BPS. Biaya aktual bervariasi tergantung gaya hidup dan lokasi spesifik dalam kota.',
  };
}
```

---

## Step 4: Hargapangan.id Integration (Food Prices)

`[CURSOR]` — Bonus free data source for food basket

```typescript
// lib/data/hargapangan.ts
// hargapangan.id is a government-linked platform for food prices by city/market
// Maintained by Badan Pangan Nasional — free to use

export async function getFoodPricesByCity(city: string): Promise<Record<string, number>> {
  // hargapangan.id API endpoint (check current endpoint at hargapangan.id)
  const url = `https://www.bi.go.id/hargapangan/Tabel/PasarTradisional?idprov=${getProvId(city)}`;
  
  try {
    const response = await fetch(url);
    if (!response.ok) return {};
    
    const data = await response.json();
    // Parse response for key food items
    const prices: Record<string, number> = {};
    // Structure depends on their API format — check at runtime
    return prices;
  } catch {
    return {};
  }
}

// Alternative: Bank Indonesia monitors food prices
// https://www.bi.go.id/hargapangan — public access
```

---

## Step 5: Frontend

`[CURSOR]` — Prompt:
> "Create Wajar Hidup page for Indonesian city cost of living comparison. Two inputs: current city dropdown (20 major cities), target city dropdown (same list). Optional: current salary input. Lifestyle selector: Hemat/Standar/Nyaman with IDR 3M/7M/15M examples. Results: large adjustment percentage badge (green if cheaper, red if expensive), required salary in target city, and category breakdown table (food/housing/transport etc). Chart showing visual comparison. Premium: full category breakdown. Free: total % only."

---

## Freemium Gates for Wajar Hidup

| Feature | Free | Basic (IDR 29K) | Pro (IDR 79K) |
|---------|------|-----------------|---------------|
| City vs City % comparison | ✅ | ✅ | ✅ |
| Required salary in target city | ✅ | ✅ | ✅ |
| Category breakdown (food/housing/etc) | ❌ (summary only) | ✅ | ✅ |
| Historical trend (price changes YoY) | ❌ | ❌ | ✅ |
| Multi-city comparison (3+ cities) | ❌ | ❌ | ✅ |
| Export PDF | ❌ | ✅ | ✅ |

---

## Reality Check for Wajar Hidup

| Issue | Reality |
|-------|---------|
| BPS CPI covers only ~90 cities | True — smaller cities are not covered. Show "data tidak tersedia" honestly |
| COL indices are estimates, not measured | True — actual costs vary 20-30% based on lifestyle choices |
| Housing costs vary hugely within a city | Yes — Kos IDR 500K vs apartment IDR 5M in same city | Show "estimasi kos/kontrakan" explicitly |
| Food prices change with inflation | BPS updates monthly — schedule monthly data refresh via SWARMS |
| Numbeo Indonesia data is thin | Jakarta, Bandung, Bali OK. Others sparse | Cross-reference with BPS and note data source |

**Build time reality:** This tool is the easiest to build. Core logic is just a formula + two city lookups. Frontend effort is 2–3 days. Data loading is 1 day. Total: 4–5 days for a working v1.

**Crowdsource opportunity:** Add "Bagaimana biaya hidupmu di [city]?" submission form. Users submit monthly spend by category. Over time this becomes your most accurate source.
