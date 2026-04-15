# Stage 7 — Wajar Tanah: Property Price + Python Scraper
**cekwajar.id Vibe Coding Playbook**  
**Estimated time:** 4–5 hours  
**Prerequisites:** Stages 1–6 complete. Python scraper environment ready.  
**Goal:** Property verdict tool with 99.co + Rumah123 scrapers, IQR-based outlier detection, MURAH/WAJAR/MAHAL/SANGAT_MAHAL verdict.

---

## ═══════════════════════════════════════════════
## MASTER PROMPT — SEND THIS TO CLAUDE CODE
## (Stage 7 — Wajar Tanah)
## ═══════════════════════════════════════════════

```
===START===
cekwajar.id — Stage 7: Wajar Tanah (Property Price Benchmark)

Context: Stages 1-6 complete. Database has property_benchmarks, property_submissions tables.
Python agent environment ready with playwright, playwright-stealth, supabase installed.

YOUR TASK FOR STAGE 7:
Build Wajar Tanah tool: property price verdict UI, API route, 
99.co + Rumah123 Python scraper agents.

════════════════════════════════════════════════════
PART A: PROPERTY BENCHMARK API ROUTE
════════════════════════════════════════════════════

Create src/app/api/property/benchmark/route.ts

GET params: province, city, district, propertyType, landAreaSqm, askingPriceTotal

Zod validation:
  province: z.string().min(1)
  city: z.string().min(1)
  district: z.string().min(1)        // kecamatan
  propertyType: z.enum(['RUMAH','TANAH','APARTEMEN','RUKO'])
  landAreaSqm: z.number().int().min(1).max(100000)
  askingPriceTotal: z.number().int().min(1)

Processing:
  1. Calculate askingPricePerSqm = askingPriceTotal / landAreaSqm
  
  2. Determine size band:
    ≤50: 'KECIL', 51-100: 'SEDANG', 101-200: 'BESAR', >200: 'SANGAT_BESAR'
  
  3. Query property_benchmarks for matching cell:
    WHERE province=$1 AND city=$2 AND district=$3 
    AND property_type=$4 AND is_outlier=false
    SELECT COUNT(*), 
      PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price_per_sqm) as p25,
      PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY price_per_sqm) as p50,
      PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price_per_sqm) as p75,
      MAX(scraped_at) as freshness
    -- Filter by size band using CASE WHEN
  
  4. If count < 5: try city-level fallback (no district filter)
  5. If still < 5: return hasData=false
  
  6. Calculate verdict using IQR formula:
    iqr = p75 - p25
    
    if askingPerSqm < p25 - 0.5*iqr → 'MURAH'
    if askingPerSqm <= p75 → 'WAJAR'
    if askingPerSqm <= p75 + 1.5*iqr → 'MAHAL'
    else → 'SANGAT_MAHAL'
  
  7. Estimate percentile (linear interpolation between known percentiles)
  
  8. Return response:
    Free: verdict + p50 + sampleCount + freshness + kjppDisclaimer
    Basic+: p25 + p75 + njopPerSqm (if available)

TypeScript verdict calculation function:
  export function calculatePropertyVerdict(
    askingPricePerSqm: number,
    p25: number, p50: number, p75: number
  ): { verdict: PropertyVerdict; percentileEstimate: number; message: string } {
    const iqr = p75 - p25
    
    if (askingPricePerSqm < p25 - 0.5 * iqr) {
      return { verdict: 'MURAH', percentileEstimate: estimatePercentile(askingPricePerSqm, p25, p50, p75), message: 'Harga di bawah rata-rata pasar. Pastikan kondisi properti baik.' }
    }
    if (askingPricePerSqm <= p75) {
      return { verdict: 'WAJAR', percentileEstimate: estimatePercentile(askingPricePerSqm, p25, p50, p75), message: 'Harga sesuai dengan kisaran pasar area ini.' }
    }
    if (askingPricePerSqm <= p75 + 1.5 * iqr) {
      return { verdict: 'MAHAL', percentileEstimate: estimatePercentile(askingPricePerSqm, p25, p50, p75), message: 'Harga di atas median pasar. Ada ruang untuk negosiasi.' }
    }
    return { verdict: 'SANGAT_MAHAL', percentileEstimate: Math.min(99, 90), message: 'Harga jauh di atas pasar. Negosiasi agresif direkomendasikan.' }
  }

KJPP disclaimer constant:
  export const KJPP_DISCLAIMER = 'Data ini bersumber dari listing properti publik dan bukan merupakan penilaian resmi dari Kantor Jasa Penilai Publik (KJPP). Untuk transaksi di atas Rp 500 juta, kami sarankan menggunakan jasa KJPP bersertifikat. cekwajar.id tidak bertanggung jawab atas kerugian dari keputusan properti berdasarkan data ini.'

Create src/app/api/property/districts/route.ts:
  GET?province=X&city=Y → return list of districts from property_benchmarks (unique)
  Used for location drill-down dropdowns

════════════════════════════════════════════════════
PART B: WAJAR TANAH UI
════════════════════════════════════════════════════

Replace stub at src/app/wajar-tanah/page.tsx

CLIENT COMPONENT.

FORM (cascading dropdowns):
  Step 1: Province dropdown (all provinces from Indonesia)
    When province changes → load cities for that province
  
  Step 2: City dropdown (auto-loads when province selected)
    When city changes → load districts
  
  Step 3: District dropdown (kecamatan, auto-loads when city selected)
    GET /api/property/districts?province=X&city=Y
  
  Step 4: Property type (radio cards with icons):
    🏠 Rumah | 🌿 Tanah | 🏢 Apartemen | 🏪 Ruko
  
  Step 5: Two inputs side by side:
    Luas Tanah (m²): number input
    Harga Ditawarkan (IDR): formatted number input
    
  Auto-calculate: show "Rp [X]/m²" as user types both values

  [Cek Harga →] button

VERDICT DISPLAY:
  Show large verdict badge with color coding:
    MURAH: green with ↓ arrow
    WAJAR: blue with ✓ check
    MAHAL: orange with ↑ arrow
    SANGAT_MAHAL: red with ⚠️

  Always shown (free + paid):
    - Verdict badge
    - "Harga/m² kamu: Rp X"
    - "Median pasar (P50): Rp Y"  
    - "Posisi estimasi: P[N]" (percentile)
    - Sample count: "Berdasarkan [n] listing · [X hari] lalu"
    - Verdict message

  PremiumGate for P25/P75 range (Basic+):
    requiredTier='basic'
    featureLabel='Rentang harga P25-P75 di area ini'
    Show blurred bar chart of price distribution

  KJPP Disclaimer (always, below verdict):
    Small collapsible text

NO DATA state:
  Show friendly message with location adjustment suggestion:
    "Belum ada data yang cukup untuk kecamatan ini."
    "Coba kecamatan terdekat atau gunakan data tingkat kota."
    Show button to search without district filter

Create src/components/wajar-tanah/VerdictBadge.tsx:
  Props: { verdict: PropertyVerdict }
  Large colored badge with label

Create src/components/wajar-tanah/PropertyPriceBar.tsx:
  Horizontal bar showing P25-P50-P75 range with user's price marked
  Only shown for paid users

════════════════════════════════════════════════════
PART C: PYTHON PROPERTY SCRAPERS
════════════════════════════════════════════════════

Create agents/scrapers/property_99co.py

Legal header:
# Scrapes 99.co/id public property listing pages.
# No authentication bypassed. No CAPTCHA bypassed.
# Rate limited: 1 req/5s. Monthly runs only.
# Risk: IP ban (ToS violation). Not criminal per UU ITE Pasal 30.

import asyncio
import re
import random
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

class PropertyScraper99co:
    BASE_URL = "https://www.99.co/id"
    MIN_DELAY = 4.0
    MAX_DELAY = 8.0
    
    # Target locations for initial data seeding
    TARGET_LOCATIONS = [
        ('DKI Jakarta', 'Jakarta Selatan', 'Kebayoran Baru'),
        ('DKI Jakarta', 'Jakarta Barat', 'Kebon Jeruk'),
        ('DKI Jakarta', 'Jakarta Timur', 'Duren Sawit'),
        ('Jawa Barat', 'Kota Bekasi', 'Bekasi Selatan'),
        ('Jawa Barat', 'Kota Bekasi', 'Bekasi Utara'),
        ('Jawa Barat', 'Kota Bandung', 'Coblong'),
        ('Jawa Barat', 'Kota Depok', 'Cimanggis'),
        ('Banten', 'Kota Tangerang', 'Ciledug'),
        ('Jawa Timur', 'Kota Surabaya', 'Rungkut'),
    ]
    
    def parse_price_idr(self, text: str) -> int | None:
        if not text:
            return None
        # Handle "Rp 1.5 M" (millions) and "Rp 1.500.000.000" formats
        text = text.replace('\n', ' ').strip()
        
        # Match billion format
        m = re.search(r'Rp\s*([\d.]+)\s*M(?:iliar)?', text, re.IGNORECASE)
        if m:
            return int(float(m.group(1).replace('.', '')) * 1_000_000_000)
        
        # Match million format
        m = re.search(r'Rp\s*([\d.]+)\s*Jt', text, re.IGNORECASE)
        if m:
            return int(float(m.group(1).replace('.', '')) * 1_000_000)
        
        # Match full number
        m = re.search(r'Rp\s*([\d.]+)', text)
        if m:
            return int(m.group(1).replace('.', ''))
        
        return None
    
    async def scrape_listing_page(self, page, province: str, city: str, district: str, property_type: str = 'rumah') -> list[dict]:
        results = []
        
        # Build 99.co search URL
        location_slug = f"{city.lower().replace(' ', '-')}"
        url = f"{self.BASE_URL}/id/jual/{property_type}/{location_slug}/"
        
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(random.uniform(2, 4))
        
        # Check for CAPTCHA — NEVER bypass
        if await page.query_selector('[class*="captcha"]'):
            print(f"CAPTCHA detected. Stopping scrape for {city}.")
            return []
        
        # Extract listing cards
        cards = await page.query_selector_all('[class*="ListingCard"]')
        
        for card in cards[:30]:
            try:
                price_el = await card.query_selector('[class*="price"]')
                area_el = await card.query_selector('[class*="land-area"]') or \
                          await card.query_selector('[class*="area"]')
                
                price_text = await price_el.inner_text() if price_el else None
                area_text = await area_el.inner_text() if area_el else None
                
                if not price_text:
                    continue
                
                total_price = self.parse_price_idr(price_text)
                if not total_price:
                    continue
                
                # Parse area
                land_area = None
                if area_text:
                    area_match = re.search(r'(\d+)\s*m²?', area_text)
                    if area_match:
                        land_area = int(area_match.group(1))
                
                if not land_area or land_area < 1:
                    continue
                
                price_per_sqm = total_price // land_area
                
                # Basic sanity check
                if price_per_sqm < 100_000 or price_per_sqm > 200_000_000:
                    continue  # likely parsing error
                
                results.append({
                    'province': province,
                    'city': city,
                    'district': district,
                    'property_type': property_type.upper(),
                    'price_per_sqm': price_per_sqm,
                    'land_area_sqm': land_area,
                    'source': '99co',
                    'is_outlier': False,
                    'scraped_at': datetime.utcnow().isoformat(),
                })
                
            except Exception as e:
                pass
        
        return results
    
    async def run_monthly_scrape(self, supabase_client):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            await stealth_async(page)
            
            all_results = []
            property_types = ['rumah', 'tanah']
            
            for province, city, district in self.TARGET_LOCATIONS:
                for prop_type in property_types:
                    try:
                        results = await self.scrape_listing_page(page, province, city, district, prop_type)
                        all_results.extend(results)
                        print(f"{city} {prop_type}: {len(results)} listings")
                        await asyncio.sleep(random.uniform(self.MIN_DELAY, self.MAX_DELAY))
                    except Exception as e:
                        print(f"Error: {city} {prop_type}: {e}")
                        await asyncio.sleep(15)
            
            await browser.close()
        
        # Run outlier detection before loading
        all_results = self.flag_outliers(all_results)
        
        # Load to Supabase
        if all_results:
            supabase_client.table('property_benchmarks').upsert(all_results).execute()
            print(f"Loaded {len(all_results)} property records")
    
    def flag_outliers(self, results: list[dict]) -> list[dict]:
        import numpy as np
        from collections import defaultdict
        
        # Group by district + property_type
        groups = defaultdict(list)
        for r in results:
            key = (r['district'], r['property_type'])
            groups[key].append(r['price_per_sqm'])
        
        for r in results:
            key = (r['district'], r['property_type'])
            prices = groups[key]
            
            if len(prices) < 3:
                continue
            
            q1 = np.percentile(prices, 25)
            q3 = np.percentile(prices, 75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            
            if r['price_per_sqm'] < lower or r['price_per_sqm'] > upper:
                r['is_outlier'] = True
        
        return results

if __name__ == '__main__':
    from supabase import create_client
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])
    scraper = PropertyScraper99co()
    asyncio.run(scraper.run_monthly_scrape(client))

Also create agents/scrapers/property_rumah123.py with similar structure:
  - Same pattern but for rumah123.com
  - URL pattern: https://www.rumah123.com/jual/[type]/[location]/
  - Parse their listing card HTML (different selectors)
  - Same rate limiting and CAPTCHA detection

════════════════════════════════════════════════════
VERIFICATION:
════════════════════════════════════════════════════

STEP 1: Run property scraper (may take 5-10 minutes):
  cd agents && python scrapers/property_99co.py
  # Check output: should show "X listings" for each location
  # Check DB: SELECT COUNT(*) FROM property_benchmarks;

STEP 2: Test benchmark API:
  curl "localhost:3000/api/property/benchmark?province=DKI+Jakarta&city=Jakarta+Selatan&district=Kebayoran+Baru&propertyType=RUMAH&landAreaSqm=100&askingPriceTotal=2000000000"
  # Expected: verdict + p50

STEP 3: Test UI:
  Visit localhost:3000/wajar-tanah
  Select Jakarta → Jakarta Selatan → Kebayoran Baru → Rumah
  Enter 100m² land, Rp 2B asking price
  Should show MAHAL or SANGAT_MAHAL for that area

STEP 4: Test no-data state:
  Enter a district with no data
  Should show friendly "Belum ada data" message

pnpm tsc --noEmit → zero errors
===END===
```

**Next:** Stage 8 — Wajar Kabur + Wajar Hidup
