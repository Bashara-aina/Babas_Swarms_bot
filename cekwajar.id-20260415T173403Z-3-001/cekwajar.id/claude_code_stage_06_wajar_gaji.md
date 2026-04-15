# Stage 6 — Wajar Gaji: Salary Benchmark + Python Scraper Agent
**cekwajar.id Vibe Coding Playbook**  
**Estimated time:** 4–5 hours (2h frontend + 2h Python agent)  
**Prerequisites:** Stages 1–5 complete. Python agent environment set up from Stage 1.  
**Goal:** Full salary benchmark tool with BPS prior data, crowdsource form, Bayesian blending, Python scraper agent for JobStreet.

---

## New Dependencies This Stage

```bash
# Next.js side — no new packages

# Python agents side (in agents/ directory)
cd agents && source venv/bin/activate
pip install swarms playwright playwright-stealth supabase python-dotenv openpyxl pandas numpy httpx

# Playwright browsers (if not done in Stage 1)
playwright install chromium
```

---

## ═══════════════════════════════════════════════
## MASTER PROMPT — SEND THIS TO CLAUDE CODE
## (Stage 6 — Wajar Gaji)
## ═══════════════════════════════════════════════

```
===START===
cekwajar.id — Stage 6: Wajar Gaji (Salary Benchmark)

Context: Stages 1-5 complete. Database has job_categories, salary_submissions, 
salary_benchmarks, umk_2026, col_categories tables. Python agent environment ready 
in agents/ directory with swarms, playwright, supabase installed.

YOUR TASK FOR STAGE 6:
Build the complete Wajar Gaji tool — API route with Bayesian blending algorithm,
full UI, crowdsource form, and Python scraper agent for BPS data loading + JobStreet.

════════════════════════════════════════════════════
PART A: JOB CATEGORIES SEED DATA
════════════════════════════════════════════════════

Create a seeding script at scripts/seed-job-categories.ts

Seed these 50 common Indonesian job categories into job_categories table:
(Use these exact titles — these are the most common Indonesian LinkedIn job titles)

[
  'Software Engineer', 'Backend Developer', 'Frontend Developer', 'Full Stack Developer',
  'Data Analyst', 'Data Scientist', 'Product Manager', 'Project Manager',
  'UI/UX Designer', 'Graphic Designer',
  'HRD Officer', 'HR Manager', 'Recruitment Specialist',
  'Finance Staff', 'Accounting Staff', 'Tax Consultant', 'Financial Analyst',
  'Marketing Staff', 'Digital Marketing', 'Content Creator', 'SEO Specialist',
  'Sales Executive', 'Business Development', 'Account Manager',
  'Customer Service', 'Customer Success',
  'Operations Manager', 'Supply Chain Staff', 'Logistics Coordinator',
  'Legal Officer', 'Compliance Officer',
  'Teacher', 'Lecturer', 'Education Staff',
  'Nurse', 'Pharmacist', 'Medical Staff',
  'Civil Engineer', 'Mechanical Engineer', 'Electrical Engineer',
  'Architect', 'Interior Designer',
  'Journalist', 'Content Writer', 'Copywriter',
  'Procurement Staff', 'Purchasing Staff',
  'IT Support', 'Network Engineer', 'System Administrator',
  'General Affairs', 'Office Manager',
]

Each entry: { title: jobTitle, title_normalized: jobTitle.toLowerCase().trim(), industry: derived_from_title, is_active: true }

Script to run: npx ts-node scripts/seed-job-categories.ts

════════════════════════════════════════════════════
PART B: SALARY BENCHMARK API ROUTE
════════════════════════════════════════════════════

Create src/app/api/salary/benchmark/route.ts

GET /api/salary/benchmark?jobTitle=X&city=Y&province=Z&experienceBucket=W

Zod validation for query params.

Implementation:
  1. Normalize job title → match to job_categories
  2. Check city-level data availability
  3. Apply Bayesian blending if n < 30
  4. Return with confidence badge

STEP 1: Job title normalization
  Function: async function normalizeJobTitle(input: string, supabase): Promise<MatchResult>
  
  // Exact match first (fastest)
  const exactMatch = await supabase
    .from('job_categories')
    .select('id, title')
    .ilike('title', input.trim())
    .single()
  
  if (exactMatch.data) return { id: exactMatch.data.id, title: exactMatch.data.title, matchType: 'EXACT' }
  
  // Trigram fuzzy match using PostgreSQL pg_trgm
  const fuzzyMatch = await supabase
    .rpc('search_job_categories_fuzzy', { search_term: input, threshold: 0.3 })
    .limit(5)
  
  // Create the RPC function in a new migration:
  // CREATE FUNCTION search_job_categories_fuzzy(search_term TEXT, threshold FLOAT)
  // RETURNS TABLE (id UUID, title TEXT, similarity FLOAT) AS $$
  //   SELECT id, title, similarity(title, search_term) as sim
  //   FROM job_categories
  //   WHERE similarity(title, search_term) > threshold
  //   ORDER BY sim DESC
  //   LIMIT 5;
  // $$ LANGUAGE SQL;
  
  if (fuzzyMatch.data?.length > 0) {
    const best = fuzzyMatch.data[0]
    if (best.similarity >= 0.7) {
      return { id: best.id, title: best.title, matchType: 'FUZZY', confidence: best.similarity }
    }
    // Return candidates for user to pick
    return { matchType: 'CANDIDATES', candidates: fuzzyMatch.data }
  }
  
  return { matchType: 'NO_MATCH' }

STEP 2: Geographic data availability
  type DataTier = 'CITY_LEVEL' | 'CITY_LEVEL_LIMITED' | 'PROVINCE_LEVEL' | 'BPS_PRIOR' | 'NO_DATA'
  
  Query salary_benchmarks for best available granularity.

STEP 3: Bayesian blending formula
  function blendBayesian(sampleP50: number | null, priorP50: number | null, n: number, k: number = 15): number | null {
    if (!priorP50 && !sampleP50) return null
    if (!sampleP50) return priorP50
    if (!priorP50 || n >= 30) return sampleP50
    
    const weight = n / (n + k)
    return Math.round(weight * sampleP50 + (1 - weight) * priorP50)
  }
  
  // P25/P75 estimation from P50 when sample too small
  const estimatedP25 = Math.round(blendedP50 * 0.78)
  const estimatedP75 = Math.round(blendedP50 * 1.28)

STEP 4: Build response
  Free tier: provinceP50 only + UMK + confidence badge
  Basic+: cityP25, cityP50, cityP75 + detailed chart data

Create RPC function for fuzzy search.
Create new migration: supabase/migrations/020_job_search_rpc.sql
  CREATE OR REPLACE FUNCTION search_job_categories_fuzzy(search_term TEXT, threshold FLOAT DEFAULT 0.3)
  RETURNS TABLE(id UUID, title TEXT, similarity_score FLOAT) AS $$
  SELECT id, title, similarity(title, search_term) as similarity_score
  FROM job_categories
  WHERE similarity(title, search_term) > threshold
  ORDER BY similarity_score DESC
  LIMIT 10;
  $$ LANGUAGE SQL SECURITY DEFINER;

════════════════════════════════════════════════════
PART C: CROWDSOURCE SUBMISSION API
════════════════════════════════════════════════════

Create src/app/api/salary/submit/route.ts

POST with body:
  { jobTitle, city, province, grossSalary, experienceBucket, industry? }

Processing:
  1. Validate with Zod
  2. Normalize job title → category (same as benchmark route)
  3. Create submission fingerprint: SHA-256 of IP+title+city+(salary rounded to nearest million)
  4. Check duplicate (fingerprint in salary_submissions within 24h)
  5. Outlier check: salary < 0.5× UMK OR > 30× UMK → reject
  6. Insert with is_validated=false (Python agent validates nightly)
  7. Return { accepted, isDuplicate, violatesOutlierRule, message }

Fingerprint creation:
  import { createHash } from 'crypto'
  const ip = request.headers.get('x-forwarded-for')?.split(',')[0] ?? 'unknown'
  const salaryBucket = Math.round(body.grossSalary / 1_000_000)
  const fingerprint = createHash('sha256')
    .update(`${ip}:${body.jobTitle.toLowerCase()}:${body.city.toLowerCase()}:${salaryBucket}`)
    .digest('hex')
    .slice(0, 16)

════════════════════════════════════════════════════
PART D: WAJAR GAJI UI
════════════════════════════════════════════════════

Replace stub at src/app/wajar-gaji/page.tsx

CLIENT COMPONENT.

State machine:
  IDLE → SEARCHING → RESULT_FREE | RESULT_PAID | NO_DATA | ERROR | CROWDSOURCE_OPEN

FORM:
  Job Title (autocomplete input — debounced 300ms)
  City (Select from umk_2026)
  Experience (Select: 0-2, 3-5, 6-10, 10+ tahun)
  "Gaji Saya Saat Ini" (optional, number input — for comparison positioning)
  [Cek Benchmark →] button

JOB TITLE AUTOCOMPLETE:
  As user types:
  - After 300ms: call GET /api/salary/benchmark-search?q=X to search categories
  - Show dropdown with matches
  - If CANDIDATES returned: show "Apakah maksud kamu: [options]?" confirmation UI
  - If NO_MATCH: show red border + "Judul tidak dikenali. Pilih dari daftar."

Create src/app/api/salary/benchmark-search/route.ts:
  GET?q=X → search job_categories by trigram → return top 10 matches

RESULT — FREE TIER:
  Job title card with match badge (✓ exact / ≈ fuzzy)
  
  Province P50 (always shown):
    "Median Provinsi [Jawa Barat]: Rp 7.200.000"
  
  UMK reference:
    "UMK [Kota Bekasi] 2026: Rp 5.331.680"
  
  If user entered their salary:
    Horizontal bar showing where they sit relative to P50
    "Gaji kamu [████░░░░░░] di bawah median provinsi" or "di atas median"
  
  Confidence badge: color coded + "Terverifikasi (n=14)" / "Estimasi (BPS)"
  
  PremiumGate wrapping P25/P75 city data:
    requiredTier='basic'
    featureLabel='Rentang gaji P25-P75 di kota kamu'
    currentTier=userTier

RESULT — BASIC+ TIER:
  City P25/P50/P75 display:
    Visual range bar: P25 ——[████P50████]—— P75
    If user entered salary: show marker on bar
  
  Data freshness: "Berdasarkan [n] laporan · [X bulan] lalu"
  
  Explanation of Bayesian blending if data is blended:
    "Data digabung dengan prior BPS (bobot [X]%) karena sampel kota terbatas"

CROWDSOURCE FORM:
  Show below result (or standalone button "Tambah laporan gaji anonim")
  Fields: job title (pre-filled), city (pre-filled), salary (required), experience (pre-filled), industry (optional)
  Disclaimer: "Data dikirim anonim. Tidak ada nama/email disimpan. Hanya IP hash untuk deduplikasi."
  Submit → show success message

════════════════════════════════════════════════════
PART E: PYTHON AGENTS — BPS SAKERNAS LOADER
════════════════════════════════════════════════════

Create agents/loaders/bps_loader.py

This script loads BPS Sakernas data (Indonesian labor statistics) as the prior for Bayesian blending.
BPS provides labor market data by province and occupation.

Since BPS Excel format changes, provide a static seed approach for launch:

BPS Sakernas P50 salary estimates by province (2024 data):
This is the "prior" — province-level median salary by broad job category.
Use these hardcoded estimates based on published BPS data.

class BPSSakernasLoader:
    """
    Loads BPS Sakernas provincial salary priors.
    
    Data source: BPS Sakernas (Survei Angkatan Kerja Nasional)
    Available at: bps.go.id/id/statistics-table (search: sakernas)
    Format: Excel (.xlsx) with provincial breakdown
    
    For launch: use static estimates. Update annually.
    """
    
    # Province-level P50 salary estimates for key job categories (IDR/month)
    # Based on BPS Sakernas 2024 data + industry knowledge
    STATIC_PRIORS = {
        'DKI Jakarta': {
            'Software Engineer': 12000000,
            'Backend Developer': 12500000,
            'Data Analyst': 9500000,
            'HRD Officer': 7500000,
            'Finance Staff': 6500000,
            'Marketing Staff': 6000000,
            'Customer Service': 5000000,
            'General Affairs': 5500000,
        },
        'Jawa Barat': {
            'Software Engineer': 9000000,
            'Backend Developer': 9500000,
            'Data Analyst': 7500000,
            'HRD Officer': 6000000,
            'Finance Staff': 5500000,
            'Marketing Staff': 5000000,
            'Customer Service': 4500000,
        },
        'Jawa Timur': {
            'Software Engineer': 8000000,
            'Backend Developer': 8500000,
            'Data Analyst': 6500000,
            'HRD Officer': 5500000,
            'Finance Staff': 5000000,
        },
        # Add all provinces...
    }
    
    async def load_to_supabase(self, supabase_client):
        """Load all static priors into salary_benchmarks table."""
        records = []
        
        for province, categories in self.STATIC_PRIORS.items():
            for job_title, p50 in categories.items():
                # Get job_category_id
                result = supabase_client.table('job_categories') \
                    .select('id') \
                    .eq('title', job_title) \
                    .execute()
                
                if not result.data:
                    continue
                
                job_category_id = result.data[0]['id']
                
                records.append({
                    'job_category_id': job_category_id,
                    'city': None,
                    'province': province,
                    'experience_bucket': None,
                    'data_source': 'bps_sakernas',
                    'sample_count': 0,  # prior doesn't have real count
                    'p25': int(p50 * 0.78),
                    'p50': p50,
                    'p75': int(p50 * 1.28),
                })
        
        # Upsert all records
        supabase_client.table('salary_benchmarks').upsert(records).execute()
        print(f"Loaded {len(records)} BPS Sakernas prior records")

if __name__ == '__main__':
    import asyncio
    from supabase import create_client
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])
    loader = BPSSakernasLoader()
    asyncio.run(loader.load_to_supabase(client))

════════════════════════════════════════════════════
PART F: PYTHON AGENTS — JOBSTREET SCRAPER (Swarms)
════════════════════════════════════════════════════

Create agents/scrapers/jobstreet_scraper.py

This scraper uses Playwright + playwright-stealth to extract salary data from JobStreet Indonesia.
Rate limited: 1 request per 5 seconds. Monthly runs only (not continuous).

Legal note in file header:
# Legal notice: This scraper reads publicly available job listing pages.
# It does NOT bypass authentication, captchas, or access control.
# Rate limited to 1 req/5s to avoid server load.
# ToS risk: JobStreet ToS may prohibit scraping.
# Accepted risk: IP ban (not criminal liability per UU ITE Pasal 30).

import asyncio
import time
import re
import random
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

class JobStreetScraper:
    """
    Scrapes JobStreet Indonesia for salary data to supplement crowdsource data.
    Only runs once per month via manual trigger or scheduled task.
    """
    
    BASE_URL = "https://id.jobstreet.com"
    MIN_DELAY = 4.0   # seconds between requests
    MAX_DELAY = 8.0   # random delay upper bound
    
    # Target job categories to scrape
    SEARCH_QUERIES = [
        ('software engineer', 'Jakarta'),
        ('backend developer', 'Jakarta'),
        ('data analyst', 'Jakarta'),
        ('hrd officer', 'Jakarta'),
        ('finance staff', 'Jakarta'),
        ('software engineer', 'Surabaya'),
        ('software engineer', 'Bandung'),
        # Add more as needed
    ]
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.scraped_count = 0
        self.error_count = 0
    
    def parse_salary_range(self, salary_text: str) -> tuple[int | None, int | None]:
        """Parse 'Rp 8.000.000 - Rp 12.000.000' to (8000000, 12000000)."""
        if not salary_text:
            return None, None
        
        # Match IDR amounts
        amounts = re.findall(r'[\d.]+(?:\.[\d]{3})*', salary_text.replace(',', '.'))
        parsed = []
        for amount in amounts:
            clean = amount.replace('.', '')
            if len(clean) >= 6:  # at least 6 digits = at least 100K IDR
                parsed.append(int(clean))
        
        if len(parsed) >= 2:
            return min(parsed), max(parsed)
        if len(parsed) == 1:
            return parsed[0], parsed[0]
        return None, None
    
    async def scrape_search_results(self, page, query: str, city: str) -> list[dict]:
        """Scrape one page of search results."""
        results = []
        
        url = f"{self.BASE_URL}/jobs/{query.replace(' ', '-')}-jobs"
        params = f"?where={city}&salaryType=monthly"
        
        await page.goto(url + params, wait_until='networkidle')
        await asyncio.sleep(random.uniform(2, 4))  # let JS render
        
        # Check for CAPTCHA
        captcha_detected = await page.query_selector('[data-automation="captcha"]')
        if captcha_detected:
            print(f"CAPTCHA detected for query '{query}' in {city}. Stopping.")
            return []  # NEVER bypass CAPTCHA
        
        # Extract job listings
        job_cards = await page.query_selector_all('[data-automation="job-card-search-result"]')
        
        for card in job_cards[:20]:  # max 20 per search
            try:
                title_el = await card.query_selector('[data-automation="job-title"]')
                salary_el = await card.query_selector('[data-automation="job-card-salary"]')
                
                if not title_el:
                    continue
                
                title = await title_el.inner_text()
                salary_text = await salary_el.inner_text() if salary_el else None
                
                if not salary_text or not salary_text.strip():
                    continue  # Skip listings without salary info
                
                min_salary, max_salary = self.parse_salary_range(salary_text)
                if not min_salary:
                    continue
                
                results.append({
                    'job_title': title.strip(),
                    'city': city,
                    'salary_min': min_salary,
                    'salary_max': max_salary,
                    'salary_mid': (min_salary + max_salary) // 2,
                    'source': 'jobstreet',
                    'scraped_at': datetime.utcnow().isoformat(),
                })
            except Exception as e:
                self.error_count += 1
        
        return results
    
    async def run_monthly_scrape(self):
        """Main scraping run. Call this once per month."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            await stealth_async(page)  # evade basic bot detection
            
            all_results = []
            
            for query, city in self.SEARCH_QUERIES:
                try:
                    print(f"Scraping: {query} in {city}...")
                    results = await self.scrape_search_results(page, query, city)
                    all_results.extend(results)
                    self.scraped_count += len(results)
                    
                    # Rate limit: random delay between searches
                    delay = random.uniform(self.MIN_DELAY, self.MAX_DELAY)
                    print(f"  Got {len(results)} results. Waiting {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    print(f"Error scraping {query} in {city}: {e}")
                    self.error_count += 1
                    await asyncio.sleep(10)  # longer wait after error
            
            await browser.close()
        
        # Load results into salary_submissions
        await self.load_to_supabase(all_results)
        print(f"Scraping complete. {self.scraped_count} salaries scraped, {self.error_count} errors.")
    
    async def load_to_supabase(self, results: list[dict]):
        """Load scraped salary data into DB."""
        job_categories = self.supabase.table('job_categories').select('id, title').execute().data
        title_to_id = {cat['title'].lower(): cat['id'] for cat in job_categories}
        
        records = []
        for r in results:
            # Find matching category (fuzzy match)
            job_title_lower = r['job_title'].lower()
            category_id = None
            
            # Exact match
            for title, cat_id in title_to_id.items():
                if title in job_title_lower or job_title_lower in title:
                    category_id = cat_id
                    break
            
            if not category_id:
                continue  # Skip unmatched titles
            
            records.append({
                'job_category_id': category_id,
                'job_title_raw': r['job_title'],
                'city': r['city'],
                'province': self.get_province(r['city']),
                'gross_salary': r['salary_mid'],
                'experience_bucket': '3-5',  # default for scraped data
                'submission_fingerprint': f"scraped_{r['scraped_at'][:10]}_{r['job_title'][:20]}",
                'is_validated': True,  # scraped data pre-validated
                'is_outlier': False,
            })
        
        if records:
            self.supabase.table('salary_submissions').upsert(records).execute()
            print(f"Loaded {len(records)} salary records to DB")
    
    def get_province(self, city: str) -> str:
        city_to_province = {
            'Jakarta': 'DKI Jakarta', 'Surabaya': 'Jawa Timur',
            'Bandung': 'Jawa Barat', 'Semarang': 'Jawa Tengah',
            'Bekasi': 'Jawa Barat', 'Tangerang': 'Banten',
        }
        return city_to_province.get(city, 'Indonesia')

if __name__ == '__main__':
    client = create_client(
        os.environ['SUPABASE_URL'],
        os.environ['SUPABASE_SERVICE_ROLE_KEY']
    )
    scraper = JobStreetScraper(client)
    asyncio.run(scraper.run_monthly_scrape())

════════════════════════════════════════════════════
VERIFICATION:
════════════════════════════════════════════════════

STEP 1: Seed job categories
  cd project-root
  npx ts-node scripts/seed-job-categories.ts
  # Expected: 50 categories in job_categories table

STEP 2: Run BPS loader
  cd agents && python loaders/bps_loader.py
  # Expected: ~200 prior records in salary_benchmarks

STEP 3: Test benchmark API
  curl "localhost:3000/api/salary/benchmark?jobTitle=Software+Engineer&city=Jakarta&province=DKI+Jakarta&experienceBucket=3-5"
  # Expected: { data: { matchedTitle: 'Software Engineer', matchType: 'EXACT', provinceP50: 12000000 } }

STEP 4: Test fuzzy match
  curl "localhost:3000/api/salary/benchmark?jobTitle=software+eng&city=Jakarta&province=DKI+Jakarta&experienceBucket=3-5"
  # Expected: { data: { matchType: 'FUZZY', ... } }

STEP 5: Test crowdsource submission
  curl -X POST localhost:3000/api/salary/submit \
    -H "Content-Type: application/json" \
    -d '{"jobTitle":"Software Engineer","city":"Jakarta","province":"DKI Jakarta","grossSalary":12000000,"experienceBucket":"3-5"}'
  # Expected: { data: { accepted: true } }

STEP 6: Test UI
  Visit localhost:3000/wajar-gaji
  Search "software engineer" → should show benchmark result
  Submit crowdsource form → verify row in salary_submissions

pnpm tsc --noEmit → zero errors
===END===
```

**Next:** Stage 7 — Wajar Tanah (Property Price)
