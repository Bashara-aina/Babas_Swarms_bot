# req_07 — Calculation Engine Specs: cekwajar.id
**Document Type:** Algorithm & Calculation Specification  
**Version:** 1.0  
**Scope:** Salary benchmark (Wajar Gaji), Property price benchmark (Wajar Tanah), CoL comparison (Wajar Hidup), Abroad comparison (Wajar Kabur)

> **Note:** PPh21 TER engine and BPJS calculation are specified in `block_03_pph21_bpjs_engine.md`. This document covers the 4 remaining calculation engines.

---

## 4.4 Salary Benchmark Algorithm (Wajar Gaji)

### Problem Statement

A user enters their job title, city, and years of experience. The system must return a statistically meaningful salary benchmark that:
1. Is always available (never returns "no data" if we have province-level data)
2. Correctly signals data quality (Low/Cukup/Terverifikasi confidence)
3. Blends sparse crowdsource submissions with stable BPS priors
4. Is immune to outlier manipulation

---

### Input Schema

```typescript
interface SalaryBenchmarkInput {
  jobTitle: string;          // raw user input, e.g. "software engineer"
  city: string;              // e.g. "Kota Bekasi"
  province: string;          // derived from city lookup
  experienceBucket: '0-2' | '3-5' | '6-10' | '10+';
  industry?: string;         // optional filter
}
```

### Step 1: Job Title Normalization

User enters free text. Must map to a canonical `job_category_id`.

**Algorithm:**
1. Lowercase + trim input
2. Check exact match in `job_categories.title` (fast path)
3. If no exact match: trigram similarity via pg_trgm
4. If trigram similarity < 0.3: pgvector embedding similarity
5. If best similarity < 0.15: return "Judul pekerjaan tidak ditemukan"

```sql
-- Step 1: Exact match
SELECT id, title FROM job_categories 
WHERE LOWER(title) = LOWER($1);

-- Step 2: Trigram fuzzy match
SELECT id, title, similarity(title, $1) AS sim
FROM job_categories
WHERE title % $1                    -- uses pg_trgm
ORDER BY sim DESC
LIMIT 5;

-- Step 3: Vector semantic match (if trigram fails)
SELECT id, title, 
       1 - (embedding <=> $1::vector) AS similarity
FROM job_categories
ORDER BY similarity DESC
LIMIT 5;
```

**Mapping thresholds:**
- sim ≥ 0.7: AUTO_MATCH (use directly)
- 0.3 ≤ sim < 0.7: SOFT_MATCH (show "Apakah maksud Anda: [title]?")
- sim < 0.3: NO_MATCH (show "Judul tidak dikenali, pilih dari daftar")

---

### Step 2: Geographic Data Availability Check

```typescript
async function checkDataAvailability(
  jobCategoryId: string,
  city: string,
  province: string
): Promise<DataTier> {
  // Check city-level n (crowdsource + scraped combined)
  const cityCount = await db.query(`
    SELECT sample_count FROM salary_benchmark_public
    WHERE job_category_id = $1 AND city = $2
  `, [jobCategoryId, city]);

  if (cityCount >= 30) return 'CITY_LEVEL';      // show city P25/P50/P75
  if (cityCount >= 10) return 'CITY_LEVEL_LIMITED'; // show city P50 only

  // Fall back to province
  const provCount = await db.query(`
    SELECT sample_count FROM salary_benchmark_province_public
    WHERE job_category_id = $1 AND province = $2
  `, [jobCategoryId, province]);

  if (provCount >= 5) return 'PROVINCE_LEVEL';   // show province P50

  // Fall back to BPS Sakernas prior
  const bpsData = await db.query(`
    SELECT p50_idr FROM bps_sakernas
    WHERE job_category_id = $1 AND province = $2
  `, [jobCategoryId, province]);

  if (bpsData) return 'BPS_PRIOR';               // BPS only, low confidence

  return 'NO_DATA';
}
```

---

### Step 3: Bayesian Blending Formula

**When to blend:** When city sample count n < 30. Pure sample when n ≥ 30.

**Formula:**

```
BlendedP50 = (n / (n + k)) × SampleP50 + (k / (n + k)) × PriorP50
```

Where:
- `n` = number of validated submissions in current cell (city + job_category + experience_bucket)
- `k` = 15 (shrinkage constant — tuned for Indonesian labor data sparseness)
- `SampleP50` = median from crowdsource + scraped submissions
- `PriorP50` = BPS Sakernas province-level median

**Worked example:**

```
User: "backend developer" + "Kota Bekasi" + "3-5 years"
- n = 8 (8 validated submissions in cell)
- k = 15
- SampleP50 = IDR 12,500,000 (from 8 submissions)
- PriorP50 = IDR 9,800,000 (BPS Sakernas Jawa Barat, IT workers)

BlendedP50 = (8/23) × 12,500,000 + (15/23) × 9,800,000
           = 0.348 × 12,500,000 + 0.652 × 9,800,000
           = 4,347,826 + 6,389,130
           = IDR 10,736,956

Weight toward prior: 65.2% — data is sparse, result is conservative
```

**P25/P75 estimation when n < 30:**

When sample size is insufficient for reliable percentile calculation:
```
BlendedP25 = BlendedP50 × 0.78   (empirical multiplier for Indonesian market)
BlendedP75 = BlendedP50 × 1.28
```

These multipliers derived from BPS Sakernas historical P25/P75 ratios across all provinces.

---

### Step 4: Confidence Badge Assignment

| Confidence | Label | Badge Color | Requirements |
|-----------|-------|-------------|-------------|
| HIGH | "Terverifikasi" | Green | city n ≥ 30, data fresh < 6 months |
| MEDIUM | "Cukup" | Yellow | city n ≥ 10 OR province n ≥ 5, data fresh < 12 months |
| LOW | "Estimasi" | Orange | BPS prior only, or stale data > 12 months |
| NONE | "Belum ada data" | Gray | No data at any level |

```typescript
function assignConfidenceBadge(
  tier: DataTier,
  sampleCount: number,
  dataAgeMonths: number
): ConfidenceBadge {
  if (tier === 'NO_DATA') return { level: 'NONE', label: 'Belum ada data' };
  
  if (tier === 'CITY_LEVEL' && sampleCount >= 30 && dataAgeMonths < 6) {
    return { level: 'HIGH', label: 'Terverifikasi', count: sampleCount };
  }
  
  if ((tier === 'CITY_LEVEL_LIMITED' && sampleCount >= 10) || 
      (tier === 'PROVINCE_LEVEL' && dataAgeMonths < 12)) {
    return { level: 'MEDIUM', label: 'Cukup', count: sampleCount };
  }
  
  return { level: 'LOW', label: 'Estimasi berdasarkan data BPS' };
}
```

---

### Step 5: UMK Floor Integration

Every benchmark result always shows the UMK for the entered city:

```typescript
async function getUMKForCity(city: string, year: number = 2026): Promise<number | null> {
  const result = await db.query(`
    SELECT monthly_minimum_idr 
    FROM umk_2026
    WHERE LOWER(city) = LOWER($1) AND EXTRACT(YEAR FROM effective_date) = $2
  `, [city, year]);
  
  return result[0]?.monthly_minimum_idr ?? null;
}

// Display rule:
// If user's salary < UMK → show red warning "Di bawah UMK kota ini"
// Always show UMK as reference regardless
```

---

### Step 6: Outlier Detection for Incoming Submissions

Before a new salary submission enters the database:

```python
def is_outlier_salary(salary_idr: int, city: str, job_category_id: str) -> bool:
    """
    Reject submissions that are statistically implausible.
    Uses 3× UMK lower bound and IQR upper bound.
    """
    # Get UMK for city
    umk = get_umk(city)
    
    # Lower bound: less than 0.5× UMK is almost certainly fake
    if salary_idr < umk * 0.5:
        return True  # outlier: too low
    
    # Upper bound: more than 30× UMK is almost certainly fake
    if salary_idr > umk * 30:
        return True  # outlier: too high (even for top execs)
    
    # IQR-based check against existing cell data
    existing = get_cell_salaries(city, job_category_id)
    if len(existing) >= 5:
        q1 = np.percentile(existing, 25)
        q3 = np.percentile(existing, 75)
        iqr = q3 - q1
        lower_fence = q1 - 3.0 * iqr  # 3× IQR = extreme outlier (Tukey)
        upper_fence = q3 + 3.0 * iqr
        
        if salary_idr < lower_fence or salary_idr > upper_fence:
            return True
    
    return False
```

**Why 3× IQR (not 1.5×):** Indonesian salary distributions are right-skewed. Standard 1.5× fence rejects too many legitimate high earners (e.g., FAANG-equivalent salaries at IDR 50M+). Use 3× to only reject extreme outliers.

---

### Full TypeScript Implementation

```typescript
export async function getSalaryBenchmark(
  input: SalaryBenchmarkInput
): Promise<SalaryBenchmarkResult> {
  
  // 1. Normalize job title
  const { jobCategoryId, matchType, matchedTitle } = await normalizeJobTitle(input.jobTitle);
  if (!jobCategoryId) {
    return { status: 'NO_MATCH', message: 'Judul pekerjaan tidak dikenali' };
  }

  // 2. Check data availability
  const tier = await checkDataAvailability(jobCategoryId, input.city, input.province);

  // 3. Get raw data
  const [cityData, provinceData, bpsData, umk] = await Promise.all([
    getCityLevelData(jobCategoryId, input.city, input.experienceBucket),
    getProvinceData(jobCategoryId, input.province),
    getBPSSakernasData(jobCategoryId, input.province),
    getUMKForCity(input.city)
  ]);

  // 4. Blend
  const blended = blendBayesian({
    sampleP50: cityData?.p50 ?? provinceData?.p50,
    priorP50: bpsData?.p50,
    n: cityData?.sampleCount ?? provinceData?.sampleCount ?? 0,
    k: 15
  });

  // 5. Confidence badge
  const badge = assignConfidenceBadge(
    tier,
    cityData?.sampleCount ?? 0,
    getDataAgeMonths(cityData?.latestSubmission ?? provinceData?.latestSubmission)
  );

  // 6. Freemium gate check
  const userTier = await getUserSubscriptionTier();
  const showDetailedBreakdown = userTier !== 'free';

  return {
    status: 'SUCCESS',
    jobTitle: matchedTitle,
    matchType,
    
    // Free tier: province P50 only
    provinceP50: blended.provinceP50,
    
    // Basic tier: city P25/P50/P75 + chart
    ...(showDetailedBreakdown && {
      cityP25: blended.p25,
      cityP50: blended.p50,
      cityP75: blended.p75,
    }),
    
    // Always show
    umk: umk,
    confidenceBadge: badge,
    sampleCount: cityData?.sampleCount ?? 0,
    dataFreshness: cityData?.latestSubmission,
    
    // Gate message for free users
    gateMessage: !showDetailedBreakdown 
      ? 'Upgrade ke Basic untuk melihat rentang P25–P75 kota ini'
      : undefined
  };
}
```

---

## 4.5 Property Price Benchmark Spec (Wajar Tanah)

### Cell Definition

A property benchmark cell is the most granular unit where we aggregate data.

```
Cell = (province × city × district × property_type × size_band)
```

**Property types (4):**
- `RUMAH` — landed house (includes any land)
- `TANAH` — land only (no building)
- `APARTEMEN` — apartment / condominium
- `RUKO` — shophouse (rumah toko)

**Size bands (4):**
- `KECIL` — ≤ 50m² land
- `SEDANG` — 51–100m²
- `BESAR` — 101–200m²
- `SANGAT_BESAR` — > 200m²

**Minimum sample n:** 5 per cell (lower than salary because property transactions are rare and area-specific)

---

### Data Sources and Weighting

| Source | Weight | Freshness Max | Notes |
|--------|--------|--------------|-------|
| 99.co scraped listings | 60% | 30 days | Primary, highest volume |
| Rumah123 scraped listings | 30% | 30 days | Secondary |
| Crowdsource user submissions | 10% | 90 days | Lowest weight (asking price bias) |

**Why crowdsource gets low weight:** User-submitted prices are often asking prices, not transaction prices. 99.co and Rumah123 are also asking prices but with more market-clearing effect.

---

### Verdict Algorithm

```typescript
type PropertyVerdict = 'MURAH' | 'WAJAR' | 'MAHAL' | 'SANGAT_MAHAL';

interface PropertyBenchmark {
  p25: number;  // 25th percentile price/m²
  p50: number;  // median price/m²
  p75: number;  // 75th percentile price/m²
}

function calculatePropertyVerdict(
  askingPricePerSqm: number,
  benchmark: PropertyBenchmark
): { verdict: PropertyVerdict; percentileEstimate: number; message: string } {
  
  const iqr = benchmark.p75 - benchmark.p25;
  
  // Verdict thresholds (calibrated against Indonesian market behavior)
  if (askingPricePerSqm < benchmark.p25 - 0.5 * iqr) {
    return {
      verdict: 'MURAH',
      percentileEstimate: estimatePercentile(askingPricePerSqm, benchmark),
      message: 'Harga ini di bawah rata-rata pasar. Pastikan kondisi properti baik.'
    };
  }
  
  if (askingPricePerSqm <= benchmark.p75) {
    return {
      verdict: 'WAJAR',
      percentileEstimate: estimatePercentile(askingPricePerSqm, benchmark),
      message: 'Harga sesuai dengan kisaran pasar area ini.'
    };
  }
  
  if (askingPricePerSqm <= benchmark.p75 + 1.5 * iqr) {
    return {
      verdict: 'MAHAL',
      percentileEstimate: estimatePercentile(askingPricePerSqm, benchmark),
      message: 'Harga di atas median pasar. Ada ruang untuk negosiasi.'
    };
  }
  
  return {
    verdict: 'SANGAT_MAHAL',
    percentileEstimate: estimatePercentile(askingPricePerSqm, benchmark),
    message: 'Harga jauh di atas pasar. Negosiasi agresif direkomendasikan.'
  };
}

function estimatePercentile(price: number, benchmark: PropertyBenchmark): number {
  // Linear interpolation between known percentiles
  if (price <= benchmark.p25) {
    return Math.max(0, 25 * (price / benchmark.p25));
  }
  if (price <= benchmark.p50) {
    const ratio = (price - benchmark.p25) / (benchmark.p50 - benchmark.p25);
    return 25 + ratio * 25;
  }
  if (price <= benchmark.p75) {
    const ratio = (price - benchmark.p50) / (benchmark.p75 - benchmark.p50);
    return 50 + ratio * 25;
  }
  // Above P75 — extrapolate
  const overage = (price - benchmark.p75) / (benchmark.p75 - benchmark.p25);
  return Math.min(99, 75 + overage * 20);
}
```

---

### NJOP Display Logic

NJOP (Nilai Jual Objek Pajak) is shown as a reference alongside market price. Data from BPN/BJUMI loader.

```typescript
interface NJOPData {
  njop_per_sqm: number;
  njop_year: number;
  source: 'BPN' | 'BJUMI' | 'PBB_ESTIMATE';
}

function getNJOPContext(njop: NJOPData, marketP50: number): string {
  const ratio = marketP50 / njop.njop_per_sqm;
  
  if (ratio < 1.5) {
    return `NJOP ${formatIDR(njop.njop_per_sqm)}/m² (${njop.njop_year}). Harga pasar hanya ${ratio.toFixed(1)}× NJOP — area ini relatif terjangkau.`;
  }
  if (ratio < 3.0) {
    return `NJOP ${formatIDR(njop.njop_per_sqm)}/m² (${njop.njop_year}). Harga pasar ${ratio.toFixed(1)}× NJOP — tipikal untuk area urban.`;
  }
  return `NJOP ${formatIDR(njop.njop_per_sqm)}/m² (${njop.njop_year}). Harga pasar ${ratio.toFixed(1)}× NJOP — area premium.`;
}
```

---

### KJPP Disclaimer Language

**Indonesian (mandatory display):**

> ⚠️ **Perhatian:** Data ini bersumber dari listing properti publik dan bukan merupakan penilaian resmi dari Kantor Jasa Penilai Publik (KJPP). Untuk transaksi properti di atas IDR 500 juta, kami menyarankan untuk menggunakan jasa KJPP bersertifikat. cekwajar.id tidak bertanggung jawab atas kerugian yang timbul dari keputusan properti berdasarkan data ini.

Display: Always. Below verdict card. Small text. Cannot be dismissed.

---

### Outlier Detection for Property Data

```python
def flag_property_outlier(price_per_sqm: int, district: str, property_type: str) -> bool:
    """
    IQR 1.5× fence for property price outliers.
    More aggressive than salary (1.5× vs 3×) because property data has
    more data entry errors (e.g., price in millions vs billions).
    """
    existing = get_district_prices(district, property_type)
    
    if len(existing) < 3:
        # Too few to compute IQR — use absolute sanity check
        if price_per_sqm < 500_000:      # IDR 500K/m² absolute min (rural land)
            return True
        if price_per_sqm > 200_000_000:  # IDR 200M/m² (SCBD prime office)
            return True
        return False
    
    q1, q3 = np.percentile(existing, [25, 75])
    iqr = q3 - q1
    
    # 1.5× IQR Tukey fence
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    
    return price_per_sqm < lower or price_per_sqm > upper
```

**Outlier handling:**
- Flagged listings: `is_outlier = TRUE`, included in raw table but excluded from aggregation view
- Inspector review: Python agent logs outlier count per scrape run
- Manual review: If outlier% > 20% of a district's data, flag for human review

---

## 4.6 CoL Comparison Spec (Wajar Hidup)

### Problem Statement

User moving from City A → City B. How much salary adjustment is needed to maintain the same lifestyle?

---

### The 10 Expense Categories

| # | Category | Bahasa Label | Hemat Weight | Standar Weight | Nyaman Weight | BPS Source |
|---|---------|-------------|-------------|---------------|--------------|------------|
| 1 | Housing (rent/mortgage) | Biaya Tempat Tinggal | 30% | 28% | 25% | BPS Susenas |
| 2 | Food & dining | Makanan & Makan Luar | 35% | 28% | 22% | BPS Susenas |
| 3 | Transportation | Transportasi | 12% | 12% | 10% | BPS Susenas |
| 4 | Utilities (electricity, water, gas) | Listrik, Air, Gas | 6% | 5% | 4% | PLN tariff + PDAM |
| 5 | Healthcare | Kesehatan | 4% | 4% | 4% | BPS Susenas |
| 6 | Education | Pendidikan | 3% | 5% | 6% | BPS Susenas |
| 7 | Entertainment & leisure | Hiburan & Rekreasi | 2% | 6% | 10% | Estimated |
| 8 | Clothing | Pakaian | 3% | 4% | 5% | BPS Susenas |
| 9 | Personal care | Perawatan Diri | 3% | 4% | 6% | Estimated |
| 10 | Savings & emergency | Tabungan & Darurat | 2% | 4% | 8% | Financial best practice |
| **Total** | | | **100%** | **100%** | **100%** | |

**Weight interpretation:**
- `Hemat` (frugal): rent-heavy, almost no entertainment, minimal savings
- `Standar` (standard): balanced, some dining out, moderate savings
- `Nyaman` (comfortable): more dining out, entertainment, higher savings target

---

### BPS CPI Data Mapping

BPS publishes CPI (Indeks Harga Konsumen) by city and by expenditure group. Mapping:

| BPS Group | Maps To Our Category |
|-----------|---------------------|
| Makanan, Minuman, dan Tembakau | Food & dining |
| Perumahan, Air, Listrik, dan Bahan Bakar | Housing + Utilities |
| Perlengkapan, Peralatan, dan Pemeliharaan Rutin RT | Partially housing |
| Kesehatan | Healthcare |
| Transportasi | Transportation |
| Informasi, Komunikasi, dan Jasa Keuangan | Utilities (partial) |
| Rekreasi, Olahraga, dan Budaya | Entertainment |
| Pendidikan | Education |
| Penyediaan Makanan dan Minuman / Restoran | Food & dining (dining out portion) |
| Perawatan Pribadi dan Jasa Lainnya | Personal care + Clothing |

**CPI to COL Index conversion:**

```python
def bps_cpi_to_col_index(city_cpis: dict, jakarta_cpis: dict) -> float:
    """
    Convert BPS CPI data to COL index (Jakarta = 100).
    Uses weighted average across our 10 categories.
    """
    WEIGHTS = {
        'food': 0.28,
        'housing_utilities': 0.33,  # housing + utilities combined
        'transport': 0.12,
        'healthcare': 0.04,
        'education': 0.05,
        'entertainment': 0.06,
        'clothing': 0.04,
        'personal_care': 0.04,
        'savings': 0.04,  # savings not in CPI — use 1.0 ratio
    }
    
    weighted_ratio = 0.0
    for category, weight in WEIGHTS.items():
        city_cpi = city_cpis.get(category, jakarta_cpis.get(category, 100))
        jakarta_cpi = jakarta_cpis.get(category, 100)
        category_ratio = city_cpi / jakarta_cpi
        weighted_ratio += category_ratio * weight
    
    return weighted_ratio * 100  # express as index (Jakarta = 100)
```

---

### COL Adjustment Calculation

```typescript
interface COLInput {
  fromCity: string;
  toCity: string;
  currentSalary: number;     // IDR monthly gross
  lifestyleTier: 'HEMAT' | 'STANDAR' | 'NYAMAN';
}

interface COLResult {
  fromCOLIndex: number;      // e.g., 100 (Jakarta)
  toCOLIndex: number;        // e.g., 78.5 (Surabaya)
  adjustmentRatio: number;   // toCOL / fromCOL = 0.785
  requiredSalary: number;    // currentSalary × adjustmentRatio
  salaryDifference: number;  // requiredSalary - currentSalary (negative = cheaper)
  verdict: 'LEBIH_MURAH' | 'SAMA' | 'LEBIH_MAHAL';
  categoryBreakdown: CategoryBreakdown[];
}

export function calculateCOLAdjustment(input: COLInput): COLResult {
  const fromIndex = getCOLIndex(input.fromCity);  // lookup from DB
  const toIndex = getCOLIndex(input.toCity);
  
  if (!fromIndex || !toIndex) {
    throw new Error('COL data not available for one or both cities');
  }
  
  // Lifestyle multiplier adjusts for spending pattern
  const lifestyleMultiplier = {
    HEMAT: 0.70,      // frugal lifestyle — less sensitive to expensive cities
    STANDAR: 1.00,    // baseline
    NYAMAN: 1.30,     // comfortable — more spending, more sensitive to price differences
  }[input.lifestyleTier];
  
  // Base ratio: what fraction of Jakarta cost is the destination?
  const baseRatio = toIndex / fromIndex;
  
  // Adjusted ratio applies lifestyle sensitivity
  // Luxury spending has higher price elasticity geographically
  const adjustedRatio = 1 + (baseRatio - 1) * lifestyleMultiplier;
  
  const requiredSalary = Math.round(input.currentSalary * adjustedRatio);
  const difference = requiredSalary - input.currentSalary;
  
  const verdict = 
    difference < -100_000 ? 'LEBIH_MURAH' :
    difference > 100_000  ? 'LEBIH_MAHAL' : 'SAMA';
  
  // Category breakdown for Basic tier
  const breakdown = calculateCategoryBreakdown(
    input.currentSalary,
    input.lifestyleTier,
    fromIndex,
    toIndex
  );
  
  return {
    fromCOLIndex: fromIndex,
    toCOLIndex: toIndex,
    adjustmentRatio: adjustedRatio,
    requiredSalary,
    salaryDifference: difference,
    verdict,
    categoryBreakdown: breakdown
  };
}

function calculateCategoryBreakdown(
  salary: number,
  tier: string,
  fromIndex: number,
  toIndex: number
): CategoryBreakdown[] {
  const weights = getCategoryWeights(tier);  // from lifestyle_tiers table
  const ratio = toIndex / fromIndex;
  
  return weights.map(({ category, label, weight, categoryRatio }) => {
    const fromAmount = Math.round(salary * weight);
    const toAmount = Math.round(fromAmount * (categoryRatio ?? ratio));
    return {
      category,
      label,
      fromAmount,
      toAmount,
      difference: toAmount - fromAmount,
      percentageChange: ((toAmount - fromAmount) / fromAmount * 100).toFixed(1)
    };
  });
}
```

---

### Verdict Display Mapping

| Verdict | Badge | Color | Main Message |
|---------|-------|-------|-------------|
| `LEBIH_MURAH` | "Lebih Murah" | Green | "Gaya hidup yang sama membutuhkan {X}% lebih sedikit di {toCity}" |
| `SAMA` | "Setara" | Gray | "Biaya hidup kedua kota relatif sama" |
| `LEBIH_MAHAL` | "Lebih Mahal" | Red | "Kamu butuh {X}% lebih banyak untuk gaya hidup yang sama di {toCity}" |

---

### Jakarta COL Indices Reference (20-City Seed)

| City | COL Index | Notes |
|------|-----------|-------|
| Jakarta | 100.0 | Baseline |
| Bekasi | 85.2 | Satellite city, Jakarta prices bleed in |
| Tangerang | 87.1 | Same |
| Depok | 84.3 | Same |
| Bogor | 73.6 | Some commuters, own economy |
| Bandung | 72.3 | Major city, own market |
| Surabaya | 78.5 | 2nd largest city |
| Medan | 65.4 | Lower COL, higher transport |
| Semarang | 70.1 | Central Java hub |
| Yogyakarta | 66.2 | Student city, low housing |
| Malang | 64.8 | Student + military |
| Solo | 62.4 | Very low housing |
| Makassar | 68.2 | Eastern Indonesia hub |
| Batam | 79.6 | High cost, proximity to Singapore |
| Denpasar | 83.4 | Tourism premium |
| Balikpapan | 76.3 | Oil/mining city |
| Pekanbaru | 67.3 | Sumatera commercial |
| Pontianak | 63.7 | Kalimantan |
| Manado | 71.2 | North Sulawesi |
| Palembang | 61.8 | Lowest in list |

---

## 4.7 Abroad Comparison Spec (Wajar Kabur)

### Problem Statement

User wants to know if a foreign salary offer is better than their current IDR salary in real terms — accounting for Purchasing Power Parity, not just exchange rate.

---

### PPP Formula

**PPP-adjusted purchasing power:**

```
PPP_Equivalent = ForeignSalary × (IDR_PPP / Foreign_PPP)
```

Where:
- `IDR_PPP` = World Bank PPP conversion factor for Indonesia (IDR per international dollar, latest year)
- `Foreign_PPP` = World Bank PPP conversion factor for target country (local currency per international dollar)
- `ForeignSalary` = the offer amount in local currency

**More precisely (using international dollars as common unit):**

```
UserPurchasingPower_intlUSD = CurrentIDRSalary / IDR_PPP_factor
OfferPurchasingPower_intlUSD = ForeignSalary / Foreign_PPP_factor
RealRatio = OfferPurchasingPower_intlUSD / UserPurchasingPower_intlUSD
```

**Example (Singapore):**

```
Indonesian: IDR 8,500,000/month
PPP factor Indonesia: 4,790 IDR per international dollar
User's purchasing power: 8,500,000 / 4,790 = 1,775 international dollars/month

Singapore offer: SGD 4,500/month
PPP factor Singapore: 0.88 SGD per international dollar
Offer purchasing power: 4,500 / 0.88 = 5,114 international dollars/month

Real ratio: 5,114 / 1,775 = 2.88×

Conclusion: The offer is 2.88× better in real purchasing power
```

---

### Data Sources

**World Bank PPP API:**

```
Endpoint: https://api.worldbank.org/v2/country/{country_code}/indicator/PA.NUS.PPP?format=json&mrv=1
Free: Yes, no API key required
Rate limit: 50 req/second (very generous)
Update frequency: Annual
```

```typescript
interface WorldBankPPPResponse {
  countryCode: string;
  countryName: string;
  pppFactor: number;      // local currency per international dollar
  year: number;
}

async function getWorldBankPPP(countryCode: string): Promise<WorldBankPPPResponse> {
  const cached = await getCachedPPP(countryCode);
  if (cached && isLessThanDaysOld(cached.fetchedAt, 30)) return cached;
  
  const url = `https://api.worldbank.org/v2/country/${countryCode}/indicator/PA.NUS.PPP?format=json&mrv=1`;
  const response = await fetch(url);
  const [meta, data] = await response.json();
  
  const latestEntry = data.find((d: any) => d.value !== null);
  const result = {
    countryCode,
    countryName: latestEntry.country.value,
    pppFactor: latestEntry.value,
    year: latestEntry.date
  };
  
  await cachePPP(result);
  return result;
}
```

**Exchange Rate (Frankfurter.app):**

```typescript
async function getExchangeRate(fromCurrency: string, toCurrency: string): Promise<number> {
  // Truly free, no API key, no limit stated
  const url = `https://api.frankfurter.app/latest?from=${fromCurrency}&to=${toCurrency}`;
  const response = await fetch(url);
  const { rates } = await response.json();
  return rates[toCurrency];
}
```

---

### 15 Target Countries

| # | Country | Currency | ISO Code | World Bank ID | Free Tier (top 5) |
|---|---------|----------|----------|--------------|-------------------|
| 1 | Singapore | SGD | SGP | SG | ✅ |
| 2 | Malaysia | MYR | MYS | MY | ✅ |
| 3 | Australia | AUD | AUS | AU | ✅ |
| 4 | United States | USD | USA | US | ✅ |
| 5 | United Kingdom | GBP | GBR | GB | ✅ |
| 6 | Japan | JPY | JPN | JP | 🔒 Basic |
| 7 | South Korea | KRW | KOR | KR | 🔒 Basic |
| 8 | United Arab Emirates | AED | ARE | AE | 🔒 Basic |
| 9 | Netherlands | EUR | NLD | NL | 🔒 Basic |
| 10 | Germany | EUR | DEU | DE | 🔒 Basic |
| 11 | Canada | CAD | CAN | CA | 🔒 Basic |
| 12 | New Zealand | NZD | NZL | NZ | 🔒 Basic |
| 13 | Hong Kong | HKD | HKG | HK | 🔒 Basic |
| 14 | South Africa | ZAR | ZAF | ZA | 🔒 Basic |
| 15 | Thailand | THB | THA | TH | 🔒 Basic |

---

### Net Salary Calculation (After Tax, Pro Tier)

For Pro users: show estimated after-tax salary in destination country.

```typescript
interface TaxEstimate {
  country: string;
  grossSalary: number;
  currency: string;
  estimatedIncomeTax: number;
  socialContributions: number;
  estimatedNetSalary: number;
  effectiveTaxRate: number;
  disclaimer: string;
}

// Simplified tax brackets (not legal advice — show disclaimer)
const TAX_BRACKETS: Record<string, TaxBracket[]> = {
  'SG': [
    { min: 0, max: 20000, rate: 0.00 },
    { min: 20001, max: 30000, rate: 0.02 },
    { min: 30001, max: 40000, rate: 0.035 },
    { min: 40001, max: 80000, rate: 0.07 },
    { min: 80001, max: 120000, rate: 0.115 },
    { min: 120001, max: 160000, rate: 0.15 },
    { min: 160001, max: 200000, rate: 0.18 },
    { min: 200001, max: 240000, rate: 0.19 },
    { min: 240001, max: 280000, rate: 0.195 },
    { min: 280001, max: 320000, rate: 0.20 },
    { min: 320001, max: Infinity, rate: 0.22 },
  ],
  // AUS, USA, GBR, etc.
};

function estimateNetSalary(
  annualGross: number,
  currency: string,
  countryCode: string
): TaxEstimate {
  const brackets = TAX_BRACKETS[countryCode];
  let tax = 0;
  let remaining = annualGross;
  
  for (const bracket of brackets) {
    if (remaining <= 0) break;
    const taxableInBracket = Math.min(remaining, bracket.max - bracket.min);
    tax += taxableInBracket * bracket.rate;
    remaining -= taxableInBracket;
  }
  
  // Social contributions (CPF for SG, Super for AU, etc.) — simplified
  const socialRate = SOCIAL_RATES[countryCode] ?? 0.05;
  const socialContributions = annualGross * socialRate;
  
  return {
    country: countryCode,
    grossSalary: annualGross,
    currency,
    estimatedIncomeTax: Math.round(tax),
    socialContributions: Math.round(socialContributions),
    estimatedNetSalary: Math.round(annualGross - tax - socialContributions),
    effectiveTaxRate: (tax / annualGross),
    disclaimer: 'Estimasi pajak ini bersifat indikatif dan belum memperhitungkan deduction, allowance, atau status perpajakan individual. Konsultasikan dengan tax advisor setempat.'
  };
}
```

---

### Political/Accuracy Disclaimer Language

**Indonesian (mandatory, always displayed):**

> ⚠️ **Catatan Penting:** Data Purchasing Power Parity (PPP) bersumber dari World Bank dan diperbarui tahunan. PPP adalah ukuran ekonometrik — bukan cerminan sempurna dari pengalaman hidup seseorang di negara tersebut. Faktor non-ekonomi seperti kualitas hidup, budaya, peluang karir, dan regulasi visa tidak tercakup dalam kalkulasi ini. Data biaya hidup dari Numbeo bersifat estimasi komunitas. cekwajar.id tidak memberikan nasihat imigrasi atau karir.

**Where displayed:** Below result card, collapsible "Pelajari lebih lanjut" section.

---

### CoL Basket for Target Cities (Numbeo Integration)

For Basic tier: show cost of living breakdown in destination city.

```python
class NumbeoScraper:
    BASE_URL = "https://www.numbeo.com"
    
    CITY_SLUGS = {
        'SG': 'Singapore',
        'MY-KL': 'Kuala-Lumpur',
        'AU-SYD': 'Sydney',
        'AU-MEL': 'Melbourne',
        'US-NY': 'New-York',
        'US-SF': 'San-Francisco',
        'GB-LON': 'London',
        'JP-TKY': 'Tokyo',
    }
    
    # Key expense items to extract (Numbeo cost of living page)
    EXPENSE_MAPPING = {
        'meal_cheap': 'Makan di warung/food court',
        'meal_restaurant': 'Makan di restoran menengah',
        'monthly_transport': 'Transportasi publik bulanan',
        'apartment_1br_center': 'Sewa apartemen 1BR pusat kota',
        'apartment_1br_outside': 'Sewa apartemen 1BR luar pusat kota',
        'utilities_basic': 'Listrik, air, gas (1BR)',
    }
    
    async def scrape_col_basket(self, city_slug: str) -> dict:
        url = f"{self.BASE_URL}/cost-of-living/in/{city_slug}"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (compatible; research/1.0)'
            })
            
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(2000)  # let JS render
            
            # Extract table data
            items = {}
            rows = await page.query_selector_all('table.data_wide_table tr')
            
            for row in rows:
                cells = await row.query_selector_all('td')
                if len(cells) >= 2:
                    label = await cells[0].inner_text()
                    price_text = await cells[1].inner_text()
                    price = self.parse_price(price_text)
                    if price:
                        items[label.strip()] = price
            
            await browser.close()
            return items
    
    def parse_price(self, text: str) -> float | None:
        import re
        # Extract median or single price from "X.XX $" or "X.XX-Y.YY $"
        # Take lower value of range if range is given
        numbers = re.findall(r'[\d,]+\.?\d*', text.replace(',', ''))
        if not numbers:
            return None
        return float(numbers[0])
```

---

### Full Abroad Comparison TypeScript Function

```typescript
export async function getAbroadComparison(input: {
  currentIDRSalary: number;
  jobRole: string;
  targetCountry: string;   // ISO code e.g. 'SG'
  userTier: 'free' | 'basic' | 'pro';
}): Promise<AbroadComparisonResult> {
  
  const [idPPP, foreignPPP, exchangeRate, colData] = await Promise.all([
    getWorldBankPPP('ID'),
    getWorldBankPPP(input.targetCountry),
    getExchangeRate('IDR', getCurrencyForCountry(input.targetCountry)),
    input.userTier !== 'free' ? getNumbeoCoLData(input.targetCountry) : null
  ]);
  
  // Core PPP calculation
  const userPowerIntlUSD = input.currentIDRSalary / idPPP.pppFactor;
  
  // Nominal exchange
  const nominalEquivalent = input.currentIDRSalary / exchangeRate;
  
  // For display: "your IDR salary equals X in foreign currency (nominal)"
  // "in real purchasing power, it equals Y international dollars"
  
  // Market salary for role in target country (scraped or estimated)
  const marketSalary = await getMarketSalaryAbroad(input.jobRole, input.targetCountry);
  
  const result: AbroadComparisonResult = {
    // Always shown (free)
    currentIDRSalary: input.currentIDRSalary,
    nominalEquivalent: nominalEquivalent,
    nominalCurrency: getCurrencyForCountry(input.targetCountry),
    realPurchasingPowerIntlUSD: userPowerIntlUSD,
    pppSourceYear: idPPP.year,
    
    // Top 5 countries free, rest gated
    isGated: !isCountryInFreeTier(input.targetCountry) && input.userTier === 'free',
    
    // Basic+
    ...(input.userTier !== 'free' && {
      colBreakdown: colData,
      marketSalaryInTarget: marketSalary,
    }),
    
    // Pro only
    ...(input.userTier === 'pro' && {
      netSalaryEstimate: estimateNetSalary(
        (marketSalary?.median ?? nominalEquivalent) * 12,
        getCurrencyForCountry(input.targetCountry),
        input.targetCountry
      )
    }),
    
    disclaimer: POLITICAL_DISCLAIMER_ID
  };
  
  return result;
}
```
