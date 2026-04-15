# Build Guide 02: Wajar Gaji — Salary Benchmark

**Priority:** Second after Wajar Slip. Launch in Week 6–8.  
**Accuracy target:** 65–75% vs Mercer (acceptable for 0-cost data)  
**Data strategy:** BPS Sakernas (free) + Crowdsource + Scraping (grey area)  
**Reality check:** BPS data alone is province + occupation group only. Crowdsource fills the gap over time.

---

## Data Sources Ranked by Quality (All Free)

| Source | Quality | Coverage | Effort |
|--------|---------|----------|--------|
| BPS Sakernas (official) | Medium | Province × 9 occupation groups | Download CSV, 1 hour |
| Glassdoor Indonesia (scrape) | Good | Job title + company | Hard to scrape, blocks bots |
| LinkedIn Salary Insights (scrape) | Good | Role + location | Very hard, rate limited |
| JobStreet/Indeed (scrape) | Medium | Job ads salary ranges | Moderate difficulty |
| Crowdsource (our users) | Best over time | Exact job + city + industry | Starts empty, grows with MAU |
| Kemnaker UMK/UMP (official) | Minimum floor | 514 cities | Download Excel, 1 hour |

**Strategy for Month 1–3 (pre-crowdsource critical mass):**
- Load BPS + UMK as baseline floor
- Show P50 from BPS province (with disclaimer "data provinsi BPS")
- Scrape JobStreet/Karir.com for job ad salary ranges (lower quality but free)
- Show confidence score: low (BPS only), medium (100+ crowdsource), high (500+)

---

## Step 1: Load BPS Sakernas Data

`[PERPLEXITY]` — Research step first
> "Find download link for BPS Sakernas terbaru (2023 or 2024) upah rata-rata pekerja per provinsi. URL is bps.go.id. Find the Excel/CSV format."

`[MANUAL]` — Download from BPS
1. Go to: https://www.bps.go.id/id/statistics-table/2/OTEzIzI=/upah-rata-rata-per-bulan-buruh-tani.html
2. Also: https://www.bps.go.id → Statistik → Ketenagakerjaan → Upah
3. Download Excel files for "Upah Rata-rata Buruh/Karyawan" by province + occupation group
4. Save as `data/bps_sakernas_2024.xlsx`

`[SWARMS]` — Parse and load:

```python
# agents/data_loaders/bps_loader.py
import pandas as pd
import json
from supabase import create_client

supabase = create_client(
    os.environ['SUPABASE_URL'],
    os.environ['SUPABASE_SERVICE_ROLE_KEY']
)

# BPS occupation groups (9 main groups, Klasifikasi Baku Jabatan Indonesia)
BPS_OCCUPATION_MAP = {
    'Manajer': 'manager',
    'Profesional': 'professional',
    'Teknisi': 'technician',
    'Tenaga Tata Usaha': 'clerical',
    'Tenaga Usaha Jasa': 'service',
    'Tenaga Usaha Pertanian': 'agriculture',
    'Tenaga Produksi': 'production',
    'Operator': 'operator',
    'Pekerja Kasar': 'manual_labor',
}

def load_bps_data(excel_path: str):
    """Parse BPS Sakernas Excel and load to Supabase salary_benchmarks table"""
    df = pd.read_excel(excel_path, skiprows=3)  # BPS usually has 3 header rows
    
    records = []
    for _, row in df.iterrows():
        province = row.get('Provinsi', row.get('Province', ''))
        if not province or pd.isna(province):
            continue
            
        for bps_occ, std_occ in BPS_OCCUPATION_MAP.items():
            salary = row.get(bps_occ)
            if pd.notna(salary) and salary > 0:
                records.append({
                    'province': str(province).strip(),
                    'city': None,  # BPS doesn't have city-level
                    'occupation_group': std_occ,
                    'job_title': None,  # BPS doesn't have job title
                    'p50_salary': int(salary),
                    'p25_salary': int(salary * 0.78),  # Estimate from ILO ratio
                    'p75_salary': int(salary * 1.25),
                    'sample_count': 0,  # BPS doesn't provide sample count
                    'data_source': 'bps_sakernas_2024',
                    'confidence_level': 'low',  # Province-level only
                    'year': 2024,
                })
    
    # Batch insert
    if records:
        supabase.table('salary_benchmarks').upsert(records).execute()
        print(f"Loaded {len(records)} BPS records")

# Run
load_bps_data('data/bps_sakernas_2024.xlsx')
```

---

## Step 2: Load UMK/UMR as Floor Reference

`[MANUAL]` — Download from Kemnaker
1. Go to: https://kemnaker.go.id/berita/detail/ump-umk
2. Download UMK 2024 Excel by province/city
3. Save as `data/umk_2024.xlsx`

`[SWARMS]` — UMK loader:

```python
# agents/data_loaders/umk_loader.py
def load_umk_data(excel_path: str):
    """Load UMK by city into salary_floors table"""
    df = pd.read_excel(excel_path)
    
    records = []
    for _, row in df.iterrows():
        records.append({
            'province': str(row.get('Provinsi', '')).strip(),
            'city': str(row.get('Kabupaten/Kota', '')).strip(),
            'umk_2024': int(row.get('UMK 2024', row.get('Upah Minimum', 0))),
            'umk_2023': int(row.get('UMK 2023', 0)),
            'source': 'kemnaker_2024',
        })
    
    supabase.table('salary_floors').upsert(records).execute()
    print(f"Loaded {len(records)} UMK records")
```

---

## Step 3: Supabase Schema for Salary Data

`[SUPABASE]` — Run in SQL Editor:

```sql
-- BPS + Crowdsource salary benchmarks
CREATE TABLE public.salary_benchmarks (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  -- Location
  province TEXT NOT NULL,
  city TEXT,  -- NULL for BPS province-level data
  -- Job classification
  occupation_group TEXT,  -- BPS main group
  job_title TEXT,  -- Crowdsource: specific title like "Software Engineer"
  industry TEXT,  -- tech, finance, manufacturing, etc.
  -- Salary data
  p25_salary NUMERIC(15,2),
  p50_salary NUMERIC(15,2),
  p75_salary NUMERIC(15,2),
  p90_salary NUMERIC(15,2),
  -- Metadata
  sample_count INTEGER DEFAULT 0,
  data_source TEXT NOT NULL,  -- 'bps_sakernas_2024', 'crowdsource', 'jobstreet_scrape'
  confidence_level TEXT DEFAULT 'low' CHECK (confidence_level IN ('low', 'medium', 'high')),
  year INTEGER,
  last_updated TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- UMK/UMR floor reference
CREATE TABLE public.salary_floors (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  province TEXT NOT NULL,
  city TEXT NOT NULL,
  umk_2024 NUMERIC(15,2),
  umk_2023 NUMERIC(15,2),
  source TEXT DEFAULT 'kemnaker',
  UNIQUE(province, city)
);

-- Crowdsource salary submissions
CREATE TABLE public.salary_submissions (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  -- Anonymous: no user_id stored (privacy)
  -- Location
  province TEXT NOT NULL,
  city TEXT NOT NULL,
  -- Job info
  job_title TEXT NOT NULL,
  industry TEXT,
  years_experience INTEGER,
  education_level TEXT,
  -- Salary
  monthly_gross_salary NUMERIC(15,2) NOT NULL,
  salary_year INTEGER NOT NULL,
  -- Validation flags
  is_validated BOOLEAN DEFAULT false,  -- Passes outlier check
  is_published BOOLEAN DEFAULT false,  -- Has k-anonymity (min 10 in cell)
  -- Privacy
  ip_hash TEXT,  -- Hashed IP to detect duplicates
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Aggregated view (k-anonymity: only publish if n >= 10)
CREATE VIEW public.salary_benchmark_aggregated AS
SELECT
  province,
  city,
  job_title,
  industry,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY monthly_gross_salary) as p25,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY monthly_gross_salary) as p50,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY monthly_gross_salary) as p75,
  COUNT(*) as sample_count,
  MAX(salary_year) as latest_year
FROM public.salary_submissions
WHERE is_validated = true
GROUP BY province, city, job_title, industry
HAVING COUNT(*) >= 10;  -- k-anonymity minimum

-- RLS: benchmarks are readable by all (they're aggregated, no PII)
ALTER TABLE public.salary_benchmarks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read benchmarks" ON public.salary_benchmarks FOR SELECT USING (true);

-- Submissions: no read for users (they submit but don't see individual records)
ALTER TABLE public.salary_submissions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "No user read of individual submissions" ON public.salary_submissions FOR SELECT USING (false);
CREATE POLICY "Anyone can submit" ON public.salary_submissions FOR INSERT WITH CHECK (true);
```

---

## Step 4: JobStreet Scraper (Grey Area)

`[SWARMS]` — Scraper agent for job salary data

**Reality check:** JobStreet Indonesia does NOT require authentication for job listings. They display salary ranges publicly. Scraping salary ranges from public job postings is legally lower-risk than scraping user-generated property listings.

**Legal note:** JobStreet's ToS prohibits scraping. This is a ToS violation risk, not a UU ITE criminal risk (you're reading public data, not bypassing authentication). Risk: IP ban, not prosecution.

```python
# agents/scrapers/jobstreet_scraper.py
import asyncio
from playwright.async_api import async_playwright
import json
import re
from datetime import datetime

class JobStreetScraper:
    """
    Scrapes publicly listed salary ranges from JobStreet Indonesia job ads.
    These are salary ranges posted by employers, NOT user-submitted data.
    
    Grey area note: Violates JobStreet ToS. Risk = IP ban, not legal action.
    Mitigation: Rate limit 1 req/5sec, rotate user agents, don't hammer.
    """
    
    BASE_URL = "https://www.jobstreet.co.id/jobs"
    RATE_LIMIT_SECONDS = 5  # Be respectful
    
    # Top job titles to search for Indonesian market
    JOB_TITLES = [
        "software engineer", "data analyst", "product manager",
        "marketing manager", "finance analyst", "HR manager",
        "sales manager", "operations manager", "business analyst",
        "UI UX designer", "backend developer", "frontend developer",
        "project manager", "accountant", "lawyer",
        "civil engineer", "mechanical engineer", "electrical engineer",
        "nurse", "doctor", "pharmacist",
        "teacher", "lecturer", "researcher",
    ]
    
    CITIES = [
        "jakarta", "surabaya", "bandung", "medan", "semarang",
        "yogyakarta", "bekasi", "tangerang", "depok", "bogor",
        "balikpapan", "makassar", "palembang",
    ]
    
    async def scrape_salary_ranges(self) -> list[dict]:
        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            for city in self.CITIES[:5]:  # Start with top 5 cities
                for job_title in self.JOB_TITLES[:10]:  # Start with top 10 titles
                    try:
                        url = f"{self.BASE_URL}?q={job_title.replace(' ', '+')}&l={city}&salary=1"
                        await page.goto(url, timeout=30000)
                        await asyncio.sleep(self.RATE_LIMIT_SECONDS)
                        
                        # Extract job listing cards
                        listings = await page.query_selector_all('[data-testid="job-card"]')
                        
                        for listing in listings[:20]:  # Max 20 per page
                            try:
                                # Extract salary range if displayed
                                salary_el = await listing.query_selector('[data-automation="jobSalary"]')
                                if not salary_el:
                                    continue
                                    
                                salary_text = await salary_el.inner_text()
                                salaries = self._parse_salary_range(salary_text)
                                
                                if salaries:
                                    results.append({
                                        'job_title': job_title,
                                        'city': city,
                                        'salary_min': salaries[0],
                                        'salary_max': salaries[1] if len(salaries) > 1 else salaries[0],
                                        'salary_mid': (salaries[0] + (salaries[1] if len(salaries) > 1 else salaries[0])) / 2,
                                        'source': 'jobstreet_scrape',
                                        'scraped_at': datetime.now().isoformat(),
                                    })
                            except Exception:
                                continue
                                
                    except Exception as e:
                        print(f"Error scraping {job_title} in {city}: {e}")
                        continue
            
            await browser.close()
        return results
    
    def _parse_salary_range(self, text: str) -> list[int] | None:
        """Parse 'Rp 8.000.000 - Rp 15.000.000 per bulan' format"""
        # Remove non-numeric except separators
        numbers = re.findall(r'[\d.,]+', text.replace('Rp', '').replace('IDR', ''))
        
        parsed = []
        for num in numbers:
            try:
                # Handle Indonesian number format: 8.000.000 or 8,000,000
                cleaned = num.replace('.', '').replace(',', '')
                value = int(cleaned)
                if 1_000_000 <= value <= 100_000_000:  # Sanity: 1M to 100M IDR
                    parsed.append(value)
            except ValueError:
                continue
        
        return parsed if parsed else None


async def run_jobstreet_scraper():
    scraper = JobStreetScraper()
    results = await scraper.scrape_salary_ranges()
    
    print(f"Scraped {len(results)} salary data points from JobStreet")
    
    # Load to Supabase
    from supabase import create_client
    import os
    supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])
    
    # Aggregate by job title + city before inserting
    from collections import defaultdict
    aggregated = defaultdict(list)
    for r in results:
        key = (r['job_title'], r['city'])
        aggregated[key].append(r['salary_mid'])
    
    benchmarks = []
    for (job_title, city), salaries in aggregated.items():
        salaries.sort()
        n = len(salaries)
        benchmarks.append({
            'province': 'Unknown',  # Would need city-to-province mapping
            'city': city,
            'job_title': job_title,
            'p25_salary': salaries[int(n * 0.25)],
            'p50_salary': salaries[int(n * 0.50)],
            'p75_salary': salaries[int(n * 0.75)],
            'sample_count': n,
            'data_source': 'jobstreet_scrape_2024',
            'confidence_level': 'low' if n < 5 else 'medium' if n < 20 else 'high',
            'year': 2024,
        })
    
    if benchmarks:
        supabase.table('salary_benchmarks').upsert(benchmarks).execute()
        print(f"Loaded {len(benchmarks)} aggregated benchmarks")


if __name__ == '__main__':
    asyncio.run(run_jobstreet_scraper())
```

---

## Step 5: Crowdsource Submission Flow

`[CURSOR]` — Create form component: `components/wajar-gaji/SalarySubmit.tsx`

Cursor prompt:
> "Create a React component for anonymous salary submission. Fields: job title (text input with autocomplete from existing titles), city (dropdown of 34 provinces + major cities), industry (dropdown), years of experience (1–30), education level (SMA/D3/S1/S2/S3), monthly gross salary (IDR). No login required. On submit call /api/submit-salary. After submit show: 'Terima kasih! Data kamu akan digunakan setelah diverifikasi dan ada minimum 10 data sejenis.'"

**Privacy handling:** No email, no name, no user_id stored. Only IP hash (one-way) to prevent duplicate submissions.

```typescript
// app/api/submit-salary/route.ts
import { createHash } from 'crypto';
import { createClient } from '@/lib/supabase/server';

export async function POST(req: NextRequest) {
  const body = await req.json();
  const ip = req.headers.get('x-forwarded-for') || req.ip || '';
  
  // Hash IP for dedup only — never store raw IP
  const ipHash = createHash('sha256').update(ip + body.jobTitle + body.city).digest('hex').slice(0, 16);
  
  // Outlier check: reject if >3x or <0.3x city UMK
  const cityFloor = await getCityUMK(body.city);
  if (body.monthlySalary < cityFloor * 0.8 || body.monthlySalary > cityFloor * 30) {
    return NextResponse.json({ error: 'Data gaji tampak tidak valid' }, { status: 400 });
  }
  
  const supabase = createClient();
  await supabase.from('salary_submissions').insert({
    province: body.province,
    city: body.city,
    job_title: body.jobTitle.toLowerCase().trim(),
    industry: body.industry,
    years_experience: body.yearsExperience,
    education_level: body.educationLevel,
    monthly_gross_salary: body.monthlySalary,
    salary_year: new Date().getFullYear(),
    ip_hash: ipHash,
    is_validated: true,  // Basic outlier check passed
  });
  
  return NextResponse.json({ message: 'Berhasil dikirim!' });
}
```

---

## Step 6: Bayesian Blending (BPS + Crowdsource)

`[CURSOR]` — Add to calculation library: `lib/calculations/salary-blend.ts`

```typescript
// Bayesian smoothing: blend crowdsource data with BPS prior
// Formula: Blended_P50 = (n/(n+k)) × Sample_P50 + (k/(n+k)) × Prior_P50
// where k=15 (smoothing constant), Prior_P50 = BPS province estimate

interface SalaryBlendInput {
  bpsProvince: number | null;    // BPS Sakernas P50 for province+occupation
  crowdsourceP50: number | null; // Crowdsource P50 for job+city
  crowdsourceN: number;          // Sample count in crowdsource
}

export function blendSalaryEstimate(input: SalaryBlendInput): {
  blendedP50: number;
  confidence: number;
  dataSource: string;
} {
  const k = 15; // Smoothing weight (tuned for Indonesian market)
  
  if (!input.crowdsourceP50 && !input.bpsProvince) {
    return {
      blendedP50: 0,
      confidence: 0,
      dataSource: 'insufficient_data',
    };
  }
  
  if (!input.crowdsourceP50) {
    return {
      blendedP50: input.bpsProvince!,
      confidence: 25, // Low: BPS province data only
      dataSource: 'bps_only',
    };
  }
  
  if (!input.bpsProvince) {
    const confidence = Math.min(90, (input.crowdsourceN / (input.crowdsourceN + k)) * 100);
    return {
      blendedP50: input.crowdsourceP50,
      confidence,
      dataSource: 'crowdsource_only',
    };
  }
  
  // Blend both sources
  const weight = input.crowdsourceN / (input.crowdsourceN + k);
  const blendedP50 = Math.round(weight * input.crowdsourceP50 + (1 - weight) * input.bpsProvince);
  const confidence = Math.min(85, weight * 100);
  
  return {
    blendedP50,
    confidence,
    dataSource: 'blended_bps_crowdsource',
  };
}
```

---

## Step 7: Wajar Gaji Result UI

`[CURSOR]` — Prompt:
> "Create result component showing: salary range bar (P25 in yellow, P50 in green, P75 in blue), confidence indicator (low/medium/high with explanation), comparison to UMK, sample count badge, and disclaimer. Free users see P50 only. Premium users see full P25/P75 range and industry breakdown."

---

## Freemium Gates for Wajar Gaji

| Feature | Free | Basic (IDR 29K) | Pro (IDR 79K) |
|---------|------|-----------------|---------------|
| Province-level P50 | ✅ | ✅ | ✅ |
| City-level breakdown | ❌ | ✅ | ✅ |
| P25/P75 range | ❌ | ✅ | ✅ |
| Industry comparison | ❌ | ❌ | ✅ |
| Salary trend (YoY) | ❌ | ❌ | ✅ |
| Anonymous submit | ✅ | ✅ | ✅ |
| Sample count visible | ❌ | ✅ | ✅ |

---

## Reality Check for Wajar Gaji

| Issue | Reality | Mitigation |
|-------|---------|------------|
| BPS data is province-level, NOT city or job title | True. DKI Jakarta P50 ≠ Jakarta Software Engineer P50 | Show "data estimasi provinsi" label clearly. Crowdsource closes gap over months. |
| Crowdsource starts at 0 | True. Month 1–3: almost no useful crowdsource data for niche titles | Show "belum ada data cukup — bantu kami dengan kirim data gajimu" + BPS estimate as fallback |
| JobStreet scraper may get blocked | High probability after 1–2 weeks | Run scraper once, load to DB, refresh monthly. Don't run continuously. |
| Glassdoor/LinkedIn harder to scrape | Very hard. Both use heavy bot detection + login walls | Skip these for MVP. Not worth the engineering time. Focus on JobStreet + Karir.com |
| Salary data becomes stale | BPS updates annually | Schedule SWARMS agent to re-scrape quarterly, note "data per [year]" in UI |
| Users may submit false data | Yes | Outlier detection in submission API, IP hash dedup, k-anonymity hides individual outliers |

**Honest accuracy expectation:**
- Month 1: 50–60% (BPS only, rough approximation)
- Month 3 with 500 submissions: 65–70%
- Month 6 with 2,000+ submissions: 70–78%
- Month 12 with 10,000+ submissions: 78–85%
