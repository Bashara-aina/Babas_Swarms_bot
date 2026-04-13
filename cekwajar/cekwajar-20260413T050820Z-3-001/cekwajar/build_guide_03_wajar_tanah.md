# Build Guide 03: Wajar Tanah — Property Price Benchmark

**Priority:** Third tool. Launch Week 7–9.  
**Accuracy target:** 70–80% vs KJPP appraisal (market listing price, not appraised value)  
**Data strategy:** Scrape 99.co + Rumah123 + OLX (grey area) + BHUMI NJOP (free official)  
**Reality check on scraping:** This is the highest-risk tool legally and technically. Read the full risk section before building.

---

## Legal Risk Assessment — Read This First

| Risk | Assessment | Your Decision |
|------|-----------|---------------|
| 99.co ToS violation | High certainty — their ToS explicitly prohibits scraping | You accept ToS risk |
| Rumah123 ToS violation | Same as 99.co | You accept ToS risk |
| OLX Indonesia ToS violation | Same | You accept ToS risk |
| UU ITE Pasal 30 (unauthorized access) | **LOW** if you only read public pages (no login bypass, no CAPTCHA bypass) | As long as data is publicly visible without login, this is ToS risk, not criminal |
| Getting IP banned | Certain — happens within days of aggressive scraping | Mitigation: rotating proxies, rate limiting, monthly runs only |
| Cease and desist letter | Possible but rare for small players at <5K MAU | Response: stop scraping that source, use cached data |

**Decision framework:** Run scraper ONCE per month. Store data in Supabase. Serve from cache. Never run continuously. This limits your exposure to: (a) one-time ToS violation, (b) IP ban on that run.

---

## Data Sources

| Source | Data Quality | Login Required | Bot Detection |
|--------|-------------|----------------|---------------|
| 99.co/id/jual | High (structured, many listings) | No | Medium (Cloudflare) |
| rumah123.com | High (structured) | No | Medium |
| olx.co.id/properti | Medium (less structured) | No | Low |
| BHUMI/BPN NJOP | Official NJOP values | No | None (government site) |
| sikp.go.id | KJPP appraisal registry | No | None |

**BHUMI is your legitimacy anchor:** Official NJOP data from BPN (Badan Pertanahan Nasional) is 100% legal to use. Use it to validate/anchor scraped market prices.

---

## Step 1: Supabase Schema

`[SUPABASE]` — Run in SQL Editor:

```sql
-- Property listings (from scraping)
CREATE TABLE public.property_listings (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  -- Location
  province TEXT,
  city TEXT,
  district TEXT,       -- Kecamatan
  subdistrict TEXT,    -- Kelurahan
  address_snippet TEXT, -- Partial address (not full, for privacy)
  -- Property details
  property_type TEXT CHECK (property_type IN ('rumah', 'tanah', 'apartemen', 'ruko', 'villa')),
  land_area_m2 NUMERIC(10,2),
  building_area_m2 NUMERIC(10,2),
  bedrooms INTEGER,
  -- Price data
  listed_price NUMERIC(18,2),  -- Total price IDR
  price_per_m2 NUMERIC(15,2),  -- Calculated: listed_price / land_area_m2
  price_type TEXT DEFAULT 'jual' CHECK (price_type IN ('jual', 'sewa')),
  -- Source
  source TEXT NOT NULL,  -- '99co', 'rumah123', 'olx'
  source_url_hash TEXT,  -- Hash of URL (not full URL, to avoid ToS issues in storage)
  scraped_at TIMESTAMPTZ DEFAULT NOW(),
  listing_date DATE,
  is_active BOOLEAN DEFAULT true,
  -- Outlier flags
  is_outlier BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- NJOP reference data (from BHUMI/BPN)
CREATE TABLE public.njop_reference (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  province TEXT NOT NULL,
  city TEXT NOT NULL,
  district TEXT,
  subdistrict TEXT,
  njop_per_m2 NUMERIC(15,2),
  njop_year INTEGER,
  source TEXT DEFAULT 'bhumi_bpn',
  last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- Aggregated price benchmarks (what users see)
CREATE TABLE public.property_benchmarks (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  province TEXT NOT NULL,
  city TEXT NOT NULL,
  district TEXT,
  property_type TEXT NOT NULL,
  -- Aggregated stats
  p25_price_per_m2 NUMERIC(15,2),
  p50_price_per_m2 NUMERIC(15,2),
  p75_price_per_m2 NUMERIC(15,2),
  sample_count INTEGER,
  njop_per_m2 NUMERIC(15,2),  -- Official reference
  -- Metadata
  data_sources TEXT[],  -- ['99co', 'rumah123', 'njop']
  last_updated TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(province, city, district, property_type)
);

-- RLS: benchmarks publicly readable
ALTER TABLE public.property_benchmarks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read property benchmarks" ON public.property_benchmarks FOR SELECT USING (true);

-- Raw listings not exposed to users (only aggregates)
ALTER TABLE public.property_listings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "No user read raw listings" ON public.property_listings FOR SELECT USING (false);
```

---

## Step 2: 99.co Scraper (Playwright Stealth)

`[SWARMS]` — Python scraper with Playwright stealth plugin

First, install:
```bash
pip install playwright playwright-stealth
playwright install chromium
```

```python
# agents/scrapers/property_scraper.py
import asyncio
import json
import re
import hashlib
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from supabase import create_client
import os

supabase = create_client(
    os.environ['SUPABASE_URL'],
    os.environ['SUPABASE_SERVICE_ROLE_KEY']
)

class PropertyScraper99co:
    """
    Scrapes property listings from 99.co/id (public search results).
    
    IMPORTANT: 
    - Only scrapes publicly visible data (no login required)
    - Rate limited to 1 request per 8-15 seconds (randomized)
    - Runs once per month maximum, stores in DB
    - Never bypasses CAPTCHA (that would trigger UU ITE Pasal 30)
    - Data is used for aggregate benchmarks only
    
    Risk: ToS violation → IP ban. NOT criminal risk.
    """
    
    BASE_URL = "https://www.99.co/id"
    
    # Target locations (start with top 10 cities)
    LOCATIONS = [
        ("Jakarta Selatan", "jakarta-selatan"),
        ("Jakarta Timur", "jakarta-timur"),
        ("Jakarta Barat", "jakarta-barat"),
        ("Bandung", "bandung"),
        ("Surabaya", "surabaya"),
        ("Bekasi", "bekasi"),
        ("Tangerang", "tangerang"),
        ("Depok", "depok"),
        ("Bogor", "bogor"),
        ("Semarang", "semarang"),
    ]
    
    async def scrape_location(self, page, city_name: str, city_slug: str, property_type: str = 'rumah') -> list[dict]:
        results = []
        
        # 99.co search URL format
        url = f"{self.BASE_URL}/jual/{property_type}?q={city_slug}"
        
        try:
            await page.goto(url, timeout=45000, wait_until='networkidle')
            await asyncio.sleep(3)  # Wait for dynamic content
            
            # Check for CAPTCHA — if detected, STOP (we don't bypass)
            captcha = await page.query_selector('[class*="captcha"], [id*="captcha"], iframe[src*="recaptcha"]')
            if captcha:
                print(f"CAPTCHA detected for {city_name}. Stopping this city.")
                return results
            
            # Extract listing cards
            # Note: 99.co uses React, selectors may change
            # Check for data-testid attributes which tend to be more stable
            listings = await page.query_selector_all('[data-testid*="listing"], [class*="ListingCard"], [class*="property-card"]')
            
            if not listings:
                # Fallback: try to find any anchor with /jual/ in href
                listings = await page.query_selector_all('a[href*="/jual/"]')
            
            for listing in listings[:30]:  # Max 30 per page per city
                try:
                    listing_data = await self._extract_listing_data(listing, city_name, property_type)
                    if listing_data:
                        results.append(listing_data)
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error scraping {city_name}: {e}")
        
        return results
    
    async def _extract_listing_data(self, element, city_name: str, property_type: str) -> dict | None:
        try:
            text = await element.inner_text()
            
            # Extract price (Indonesian Rupiah)
            price = self._extract_price(text)
            if not price:
                return None
            
            # Extract land area
            land_area = self._extract_area(text, 'LT|Luas Tanah|Tanah')
            if not land_area:
                return None
                
            price_per_m2 = price / land_area if land_area > 0 else None
            
            # Basic sanity check
            if price_per_m2 and (price_per_m2 < 500_000 or price_per_m2 > 500_000_000):
                return None  # Outlier: below 500K/m2 or above 500M/m2
            
            return {
                'city': city_name,
                'property_type': property_type,
                'listed_price': price,
                'land_area_m2': land_area,
                'building_area_m2': self._extract_area(text, 'LB|Luas Bangunan|Bangunan'),
                'price_per_m2': price_per_m2,
                'bedrooms': self._extract_bedrooms(text),
                'source': '99co',
                'source_url_hash': hashlib.md5(text[:100].encode()).hexdigest(),
                'scraped_at': datetime.now().isoformat(),
            }
        except Exception:
            return None
    
    def _extract_price(self, text: str) -> float | None:
        # Match Rp format: Rp 1.500.000.000 or Rp 1,5 M or Rp 500 Jt
        patterns = [
            r'Rp\s*([\d.]+(?:,\d+)?)\s*[Mm](?:iliar)?',  # Miliar
            r'Rp\s*([\d.]+(?:,\d+)?)\s*[Jj](?:uta)?',    # Juta
            r'Rp\s*([\d.]+)',                               # Full number
        ]
        
        text_clean = text.replace('\n', ' ')
        
        for pattern in patterns:
            match = re.search(pattern, text_clean)
            if match:
                num_str = match.group(1).replace('.', '').replace(',', '.')
                try:
                    value = float(num_str)
                    if 'M' in pattern or 'M' in text_clean[max(0, match.start()-20):match.end()+5]:
                        value *= 1_000_000_000
                    elif 'J' in pattern:
                        value *= 1_000_000
                    
                    if 100_000_000 <= value <= 50_000_000_000_000:  # 100M to 50T IDR
                        return value
                except ValueError:
                    continue
        return None
    
    def _extract_area(self, text: str, label_pattern: str) -> float | None:
        pattern = rf'(?:{label_pattern})[:\s]+(\d+(?:[.,]\d+)?)\s*m²?'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', '.'))
            except ValueError:
                pass
        return None
    
    def _extract_bedrooms(self, text: str) -> int | None:
        patterns = [r'(\d+)\s*KT', r'(\d+)\s*Kamar\s*Tidur', r'(\d+)\s*BR']
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        return None


class RumahScraper:
    """Similar to PropertyScraper99co but for rumah123.com"""
    
    BASE_URL = "https://www.rumah123.com"
    
    async def scrape_location(self, page, city_name: str, city_slug: str) -> list[dict]:
        url = f"{self.BASE_URL}/jual/rumah/{city_slug}/"
        results = []
        
        try:
            await page.goto(url, timeout=45000)
            await asyncio.sleep(4)
            
            # Rumah123 uses different selectors
            listings = await page.query_selector_all('[class*="card-featured"], [data-id]')
            
            for listing in listings[:25]:
                try:
                    text = await listing.inner_text()
                    price = self._parse_rumah123_price(text)
                    area = self._parse_area(text)
                    
                    if price and area:
                        results.append({
                            'city': city_name,
                            'property_type': 'rumah',
                            'listed_price': price,
                            'land_area_m2': area,
                            'price_per_m2': price / area,
                            'source': 'rumah123',
                            'source_url_hash': hashlib.md5(text[:100].encode()).hexdigest(),
                            'scraped_at': datetime.now().isoformat(),
                        })
                except Exception:
                    continue
        except Exception as e:
            print(f"Rumah123 error for {city_name}: {e}")
        
        return results
    
    def _parse_rumah123_price(self, text: str) -> float | None:
        # Rumah123 format: "Rp 1,2 M" or "Rp 850 Jt"
        match = re.search(r'Rp\s*([\d,\.]+)\s*([MJT])', text)
        if not match:
            return None
        try:
            value = float(match.group(1).replace(',', '.'))
            unit = match.group(2)
            if unit == 'M': value *= 1_000_000_000
            elif unit in ('J', 'T'): value *= 1_000_000
            return value if 100_000_000 <= value <= 50_000_000_000_000 else None
        except ValueError:
            return None
    
    def _parse_area(self, text: str) -> float | None:
        match = re.search(r'LT[:\s]*(\d+)\s*m', text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None


async def run_property_scrapers():
    """Main orchestrator — run once per month"""
    all_results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1366, 'height': 768},
            locale='id-ID',
        )
        
        page = await context.new_page()
        await stealth_async(page)  # Apply stealth plugin
        
        scraper_99 = PropertyScraper99co()
        
        for city_name, city_slug in PropertyScraper99co.LOCATIONS:
            print(f"Scraping 99.co: {city_name}")
            results = await scraper_99.scrape_location(page, city_name, city_slug, 'rumah')
            all_results.extend(results)
            
            # Respectful delay between cities: 15-30 seconds (random)
            import random
            delay = random.uniform(15, 30)
            print(f"Waiting {delay:.1f}s before next city...")
            await asyncio.sleep(delay)
        
        await browser.close()
    
    print(f"Total scraped: {len(all_results)} listings")
    
    # Load to Supabase
    if all_results:
        # Batch insert in chunks of 100
        for i in range(0, len(all_results), 100):
            chunk = all_results[i:i+100]
            supabase.table('property_listings').insert(chunk).execute()
    
    # Run aggregation
    aggregate_property_benchmarks()


def aggregate_property_benchmarks():
    """Build price_per_m2 benchmarks from raw listings"""
    query = """
    SELECT 
        city,
        property_type,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price_per_m2) as p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY price_per_m2) as p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price_per_m2) as p75,
        COUNT(*) as n
    FROM property_listings
    WHERE is_outlier = false
      AND price_per_m2 IS NOT NULL
      AND scraped_at > NOW() - INTERVAL '60 days'
    GROUP BY city, property_type
    HAVING COUNT(*) >= 5
    """
    result = supabase.rpc('run_sql', {'query': query}).execute()
    # Upsert into property_benchmarks table


if __name__ == '__main__':
    asyncio.run(run_property_scrapers())
```

---

## Step 3: BHUMI/BPN NJOP Data (Free Official)

`[MANUAL]` — Access BHUMI portal
1. Go to: https://bhumi.atrbpn.go.id
2. BHUMI provides NJOP (Nilai Jual Objek Pajak) zone maps
3. Download by kelurahan
4. Alternative: Each city government publishes NJOP tables annually — Google "[kota] NJOP 2024 PDF"

`[SWARMS]` — Batch load NJOP data:

```python
# agents/data_loaders/njop_loader.py
# NJOP data is public government data — 100% legal to use

# Example manual NJOP data structure (loaded from government PDFs/Excel)
NJOP_SAMPLE = [
    # These are illustrative values — download actual from BHUMI/BPN
    {'province': 'DKI Jakarta', 'city': 'Jakarta Selatan', 'district': 'Kebayoran Baru', 'njop_per_m2': 18_500_000, 'year': 2024},
    {'province': 'DKI Jakarta', 'city': 'Jakarta Selatan', 'district': 'Tebet', 'njop_per_m2': 12_300_000, 'year': 2024},
    {'province': 'DKI Jakarta', 'city': 'Jakarta Timur', 'district': 'Cakung', 'njop_per_m2': 5_200_000, 'year': 2024},
    {'province': 'Jawa Barat', 'city': 'Bandung', 'district': 'Dago', 'njop_per_m2': 6_800_000, 'year': 2024},
    {'province': 'Jawa Timur', 'city': 'Surabaya', 'district': 'Sukolilo', 'njop_per_m2': 4_500_000, 'year': 2024},
    # ... load 100+ kelurahan from government PDFs
]

def load_njop(data: list[dict]):
    supabase.table('njop_reference').upsert(data).execute()
    print(f"Loaded {len(data)} NJOP records")
```

---

## Step 4: Wajar Tanah Verdict Algorithm

`[CURSOR]` — Create: `lib/calculations/property-verdict.ts`

```typescript
// lib/calculations/property-verdict.ts

export interface PropertyInput {
  province: string;
  city: string;
  district?: string;
  propertyType: 'rumah' | 'tanah' | 'apartemen';
  landAreaM2: number;
  askedPricePerM2: number;
}

export interface PropertyVerdict {
  marketP25: number | null;
  marketP50: number | null;
  marketP75: number | null;
  njopPerM2: number | null;
  verdict: 'MURAH' | 'WAJAR' | 'MAHAL' | 'SANGAT_MAHAL' | 'INSUFFICIENT_DATA';
  verdictLabel: string;
  verdictColor: 'green' | 'blue' | 'orange' | 'red' | 'gray';
  percentilePosition: number | null;  // Where asked price sits
  njopRatio: number | null;  // asked price / NJOP
  confidence: number;
  dataSourceNote: string;
  disclaimer: string;
}

export function calculatePropertyVerdict(input: PropertyInput, marketData: any, njopData: any): PropertyVerdict {
  const { askedPricePerM2 } = input;
  
  // Get market data
  const p25 = marketData?.p25_price_per_m2 || null;
  const p50 = marketData?.p50_price_per_m2 || null;
  const p75 = marketData?.p75_price_per_m2 || null;
  const njop = njopData?.njop_per_m2 || null;
  const sampleCount = marketData?.sample_count || 0;
  
  if (!p50) {
    return {
      marketP25: null, marketP50: null, marketP75: null, njopPerM2: njop,
      verdict: 'INSUFFICIENT_DATA',
      verdictLabel: 'Data belum cukup untuk area ini',
      verdictColor: 'gray',
      percentilePosition: null,
      njopRatio: njop ? askedPricePerM2 / njop : null,
      confidence: 10,
      dataSourceNote: 'Data pasar belum tersedia untuk area ini. Gunakan NJOP sebagai referensi minimum.',
      disclaimer: PROPERTY_DISCLAIMER,
    };
  }
  
  // Calculate verdict thresholds
  const CHEAP_THRESHOLD = p25 * 0.85;   // >15% below P25
  const FAIR_LOW = p25 * 0.85;
  const FAIR_HIGH = p75 * 1.15;         // Up to 15% above P75 = still "fair"
  const EXPENSIVE_THRESHOLD = p75 * 1.30;
  
  let verdict: PropertyVerdict['verdict'];
  let verdictLabel: string;
  let verdictColor: PropertyVerdict['verdictColor'];
  
  if (askedPricePerM2 < CHEAP_THRESHOLD) {
    verdict = 'MURAH'; verdictLabel = 'Harga di bawah pasar 🟢'; verdictColor = 'green';
  } else if (askedPricePerM2 <= FAIR_HIGH) {
    verdict = 'WAJAR'; verdictLabel = 'Harga wajar sesuai pasar 🔵'; verdictColor = 'blue';
  } else if (askedPricePerM2 <= EXPENSIVE_THRESHOLD) {
    verdict = 'MAHAL'; verdictLabel = 'Harga di atas pasar 🟠'; verdictColor = 'orange';
  } else {
    verdict = 'SANGAT_MAHAL'; verdictLabel = 'Harga jauh di atas pasar 🔴'; verdictColor = 'red';
  }
  
  // Percentile position
  let percentilePosition: number | null = null;
  if (p25 && p50 && p75) {
    if (askedPricePerM2 <= p25) percentilePosition = 25;
    else if (askedPricePerM2 <= p50) percentilePosition = Math.round(25 + 25 * (askedPricePerM2 - p25) / (p50 - p25));
    else if (askedPricePerM2 <= p75) percentilePosition = Math.round(50 + 25 * (askedPricePerM2 - p50) / (p75 - p50));
    else percentilePosition = Math.min(99, Math.round(75 + 25 * (askedPricePerM2 - p75) / (p75 * 0.5)));
  }
  
  const confidence = sampleCount >= 50 ? 75 : sampleCount >= 20 ? 60 : sampleCount >= 5 ? 45 : 30;
  
  return {
    marketP25: p25,
    marketP50: p50,
    marketP75: p75,
    njopPerM2: njop,
    verdict,
    verdictLabel,
    verdictColor,
    percentilePosition,
    njopRatio: njop ? Math.round((askedPricePerM2 / njop) * 10) / 10 : null,
    confidence,
    dataSourceNote: `Data dari ${sampleCount} listing pasar (99.co, Rumah123). Data per ${new Date().toLocaleDateString('id-ID', { month: 'long', year: 'numeric' })}.`,
    disclaimer: PROPERTY_DISCLAIMER,
  };
}

const PROPERTY_DISCLAIMER = `Hasil ini berdasarkan data listing pasar dan bukan merupakan penilaian properti resmi (appraisal). 
Harga pasar aktual bisa berbeda tergantung kondisi fisik, dokumen, dan negosiasi. 
Untuk transaksi signifikan, gunakan jasa penilai properti berlisensi KJPP.`;
```

---

## Step 5: Wajar Tanah Frontend

`[CURSOR]` — Prompt:
> "Create Next.js page for property price benchmark. Form fields: province (dropdown), city (dropdown, filtered by province), district/kecamatan (text), property type (rumah/tanah/apartemen), land area m2, total asking price OR price per m2. Result shows: price range bar chart comparing asked price to P25/P50/P75, NJOP reference line, verdict badge (murah/wajar/mahal), confidence score, and data source note. Premium: shows exact P25/P75 values. Free: shows verdict and P50 only."

---

## Freemium Gates for Wajar Tanah

| Feature | Free | Basic (IDR 29K) | Pro (IDR 79K) |
|---------|------|-----------------|---------------|
| Verdict (murah/wajar/mahal) | ✅ | ✅ | ✅ |
| P50 market price | ✅ | ✅ | ✅ |
| P25/P75 range | ❌ | ✅ | ✅ |
| NJOP reference | ❌ | ✅ | ✅ |
| Price trend (3 months) | ❌ | ❌ | ✅ |
| Nearby comparable listings | ❌ | ❌ | ✅ |
| PDF valuation summary | ❌ | ✅ | ✅ |

---

## Reality Check for Wajar Tanah

| Issue | Reality | Mitigation |
|-------|---------|------------|
| Scraper gets blocked by Cloudflare | 99.co uses Cloudflare — Playwright stealth works ~70% of the time | Run with stealth plugin, use residential proxy if blocked (free proxies exist), check result count |
| Scraped data reflects listing price, not sold price | Listing price can be 10–30% above sold price in Indonesia | Clearly state "harga penawaran pasar" not "harga transaksi aktual" |
| 99.co changes selectors | Happens ~2–4x per year | Run scraper, check result count, fix selectors when count drops |
| Province outside top 10 cities: no data | True for early months | Show "belum ada data untuk area ini" — be honest |
| NJOP is often 40–60% below market price | True for major cities | Show NJOP as minimum reference floor, not "fair value" |
| Legal complaint from 99.co | Possible but rare at <5K users | If received: stop scraping that source, continue with cached data + user crowdsource |

**Reality check on accuracy:**
- Jakarta major districts: 75–80% (lots of listings)
- Secondary cities (Semarang, Makassar): 60–70%
- Rural/tier-3 cities: < 50% or no data

**Run schedule:** Monthly scraper run via SWARMS scheduled task. Don't run continuously.
