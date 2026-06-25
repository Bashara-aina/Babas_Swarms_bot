# Build Guide 04: Wajar Kabur — Abroad Salary Comparison

**Priority:** Fourth tool. Launch Week 9–10 (1 week build after scaffold).  
**Accuracy target:** 75–85% vs Mercer global  
**Data strategy:** World Bank API (free) + Numbeo (scrape) + Expatistan (scrape) + Big Mac Index (free)  
**Complexity:** LOWEST of all 5 tools. Build in 1 week.

---

## What Wajar Kabur Does

User inputs: current Indonesian salary + job role  
System shows: equivalent purchasing power in target country + local market salary for same role  
Answer: "Should I go abroad for this job offer?"

**Key formula:**
```
PPP_Adjusted = IDR_salary × (Country_PPP_factor / Indonesia_PPP_factor)
Local_market = Numbeo/scraped salary for same role in target city
Verdict = Compare PPP-adjusted vs Local market
```

---

## Free Data Sources

| Source | Data | Access |
|--------|------|--------|
| World Bank API | PPP conversion factors, GDP per capita | 100% free REST API |
| Numbeo | Cost of living by city, salary data | Scrape or free tier |
| Big Mac Index (The Economist) | Purchasing power proxy | Free (scrape or download CSV) |
| OECD iLibrary | PPP data | Free download |
| Expatistan.com | Cost of living comparisons | Scrape |
| Glassdoor global | Salary by role + country | Hard to scrape (needs login) |
| levels.fyi | Tech salaries global | Scrape (public data, no login) |

---

## Step 1: World Bank API Integration

`[CURSOR]` — Create: `lib/data/world-bank.ts`

```typescript
// lib/data/world-bank.ts
// World Bank API: https://api.worldbank.org/v2/
// No API key needed. Free. 500 req/min.

export interface PPPData {
  countryCode: string;
  countryName: string;
  pppConversionFactor: number;  // Local currency per international dollar
  gdpPerCapitaUSD: number;
  year: number;
}

// PPP conversion factor indicator: PA.NUS.PPP
// GDP per capita PPP: NY.GDP.PCAP.PP.KD
const WB_BASE = 'https://api.worldbank.org/v2';

export async function getWorldBankPPP(countryCodes: string[], year: number = 2023): Promise<PPPData[]> {
  const codes = countryCodes.join(';');
  const url = `${WB_BASE}/country/${codes}/indicator/PA.NUS.PPP?format=json&date=${year}&per_page=100`;
  
  const response = await fetch(url);
  if (!response.ok) throw new Error(`World Bank API error: ${response.status}`);
  
  const [, data] = await response.json();
  
  return data
    .filter((item: any) => item.value !== null)
    .map((item: any) => ({
      countryCode: item.countryiso3code,
      countryName: item.country.value,
      pppConversionFactor: item.value,
      gdpPerCapitaUSD: 0, // Fetch separately if needed
      year: parseInt(item.date),
    }));
}

// Target countries for Wajar Kabur
export const TARGET_COUNTRIES = [
  { code: 'SGP', name: 'Singapura', currency: 'SGD', flag: '🇸🇬' },
  { code: 'MYS', name: 'Malaysia', currency: 'MYR', flag: '🇲🇾' },
  { code: 'AUS', name: 'Australia', currency: 'AUD', flag: '🇦🇺' },
  { code: 'USA', name: 'Amerika Serikat', currency: 'USD', flag: '🇺🇸' },
  { code: 'GBR', name: 'Inggris', currency: 'GBP', flag: '🇬🇧' },
  { code: 'CAN', name: 'Kanada', currency: 'CAD', flag: '🇨🇦' },
  { code: 'DEU', name: 'Jerman', currency: 'EUR', flag: '🇩🇪' },
  { code: 'NLD', name: 'Belanda', currency: 'EUR', flag: '🇳🇱' },
  { code: 'JPN', name: 'Jepang', currency: 'JPY', flag: '🇯🇵' },
  { code: 'KOR', name: 'Korea Selatan', currency: 'KRW', flag: '🇰🇷' },
  { code: 'ARE', name: 'Dubai/UAE', currency: 'AED', flag: '🇦🇪' },
  { code: 'QAT', name: 'Qatar', currency: 'QAR', flag: '🇶🇦' },
  { code: 'HKG', name: 'Hong Kong', currency: 'HKD', flag: '🇭🇰' },
  { code: 'TWN', name: 'Taiwan', currency: 'TWD', flag: '🇹🇼' },
  { code: 'NZL', name: 'Selandia Baru', currency: 'NZD', flag: '🇳🇿' },
];

export async function calculatePPPAdjusted(
  idrSalary: number,
  targetCountryCode: string
): Promise<{
  pppAdjustedMonthly: number;
  pppAdjustedAnnual: number;
  targetCurrency: string;
  exchangeRateReference: number;
  interpretation: string;
}> {
  // Fetch PPP data for both IDN and target country
  const [pppData] = await Promise.all([
    getWorldBankPPP(['IDN', targetCountryCode]),
  ]);
  
  const idnPPP = pppData.find(d => d.countryCode === 'IDN')?.pppConversionFactor || 4500;
  const targetPPP = pppData.find(d => d.countryCode === targetCountryCode)?.pppConversionFactor || 1;
  
  // Convert IDR to International Dollars first
  const internationalDollarsMonthly = idrSalary / idnPPP;
  
  // Convert International Dollars to target country local currency
  const pppAdjustedMonthly = internationalDollarsMonthly * targetPPP;
  
  // Get exchange rate for reference (from free API)
  const exchangeRate = await getExchangeRate('IDR', getCountryCurrency(targetCountryCode));
  const directConversionMonthly = idrSalary / exchangeRate;
  
  const pppPremium = ((pppAdjustedMonthly - directConversionMonthly) / directConversionMonthly) * 100;
  
  return {
    pppAdjustedMonthly: Math.round(pppAdjustedMonthly),
    pppAdjustedAnnual: Math.round(pppAdjustedMonthly * 12),
    targetCurrency: getCountryCurrency(targetCountryCode),
    exchangeRateReference: exchangeRate,
    interpretation: pppPremium > 0
      ? `Daya beli IDR ${idrSalary.toLocaleString('id-ID')}/bulan setara ${Math.abs(Math.round(pppPremium)).toFixed(0)}% lebih tinggi dari nilai tukar nominal — artinya penghasilan kamu relatif lebih besar jika dinilai dari daya beli.`
      : `Biaya hidup di negara tujuan lebih rendah ${Math.abs(Math.round(pppPremium)).toFixed(0)}% dari Indonesia, artinya gaji nominal lebih kecil tapi daya beli relatif sama.`,
  };
}

function getCountryCurrency(code: string): string {
  const map: Record<string, string> = {
    SGP: 'SGD', MYS: 'MYR', AUS: 'AUD', USA: 'USD', GBR: 'GBP',
    CAN: 'CAD', DEU: 'EUR', NLD: 'EUR', JPN: 'JPY', KOR: 'KRW',
    ARE: 'AED', QAT: 'QAR', HKG: 'HKD', TWN: 'TWD', NZL: 'NZD',
  };
  return map[code] || 'USD';
}

async function getExchangeRate(from: string, to: string): Promise<number> {
  // Free tier: exchangerate-api.com (1,500 req/month free)
  // Alternative: frankfurter.app (completely free, no limit)
  const response = await fetch(`https://api.frankfurter.app/latest?from=${from}&to=${to}`);
  if (!response.ok) return 15000; // Fallback IDR/USD
  const data = await response.json();
  return data.rates[to];
}
```

---

## Step 2: Numbeo Cost of Living Scraper

`[SWARMS]` — Python scraper

```python
# agents/scrapers/numbeo_scraper.py
# Numbeo has a free public API tier: https://www.numbeo.com/api/
# Free tier: 1,000 calls/month (with registration)
# Alternative: scrape public pages (grey area)

import asyncio
from playwright.async_api import async_playwright
import json
import re

class NumbeoScraper:
    """
    Option A: Use Numbeo API free tier (preferred — register at numbeo.com/api)
    Option B: Scrape public cost of living pages
    
    Using API is cleaner legally. Register at: https://www.numbeo.com/api/
    Free tier gives you 1,000 API calls/month — enough for monthly updates.
    """
    
    # Option A: API method (register for free key at numbeo.com/api)
    NUMBEO_API_BASE = "https://www.numbeo.com/api"
    
    async def get_city_cost_of_living_api(self, city: str, api_key: str) -> dict:
        """Use Numbeo free API (preferred method)"""
        import httpx
        async with httpx.AsyncClient() as client:
            # Cost of living indices
            response = await client.get(
                f"{self.NUMBEO_API_BASE}/city_prices",
                params={'api_key': api_key, 'query': city}
            )
            if response.status_code == 200:
                return response.json()
        return {}
    
    # Option B: Scrape method (fallback if no API key)
    NUMBEO_BASE = "https://www.numbeo.com/cost-of-living/in"
    
    TARGET_CITIES_ABROAD = {
        'Singapore': 'Singapore', 'Kuala Lumpur': 'Kuala_Lumpur',
        'Sydney': 'Sydney', 'Melbourne': 'Melbourne',
        'New York': 'New_York', 'San Francisco': 'San_Francisco',
        'London': 'London', 'Amsterdam': 'Amsterdam',
        'Tokyo': 'Tokyo', 'Seoul': 'Seoul',
        'Dubai': 'Dubai', 'Doha': 'Doha',
        'Hong Kong': 'Hong_Kong', 'Taipei': 'Taipei',
        'Toronto': 'Toronto', 'Vancouver': 'Vancouver',
        'Auckland': 'Auckland', 'Wellington': 'Wellington',
    }
    
    # Indonesian cities for comparison baseline
    TARGET_CITIES_ID = {
        'Jakarta': 'Jakarta', 'Surabaya': 'Surabaya', 'Bandung': 'Bandung',
        'Bali': 'Bali', 'Yogyakarta': 'Yogyakarta', 'Semarang': 'Semarang',
    }
    
    BASKET_ITEMS = [
        # Category: Food
        'Meal, Inexpensive Restaurant',
        'Meal for 2 People, Mid-range Restaurant',
        'McMeal at McDonalds',
        'Domestic Beer (0.5 liter draught)',
        'Milk (regular), (1 liter)',
        'Loaf of Fresh White Bread (500g)',
        'Eggs (regular) (12)',
        'Chicken Fillets (1kg)',
        # Category: Housing
        'Apartment (1 bedroom) in City Centre',
        'Apartment (1 bedroom) Outside of Centre',
        # Category: Transport
        'Monthly Pass (Regular Price)',
        'Taxi 1km (Normal Tariff)',
        # Category: Utilities
        'Basic (Electricity, Heating, Cooling, Water, Garbage) for 85m2 Apartment',
        'Internet (60 Mbps or More, Unlimited Data, Cable/ADSL)',
    ]
    
    async def scrape_city_prices(self, page, city_slug: str) -> dict:
        url = f"{self.NUMBEO_BASE}/{city_slug}/"
        prices = {}
        
        try:
            await page.goto(url, timeout=30000)
            await asyncio.sleep(2)
            
            # Find price table rows
            rows = await page.query_selector_all('table.data_wide_table tr')
            
            for row in rows:
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 2:
                        item_el = await cells[0].inner_text()
                        price_el = await cells[1].inner_text()
                        
                        item = item_el.strip()
                        price = self._parse_price(price_el)
                        
                        if item and price:
                            prices[item] = price
                except Exception:
                    continue
        except Exception as e:
            print(f"Numbeo scrape error for {city_slug}: {e}")
        
        return prices
    
    def _parse_price(self, text: str) -> float | None:
        # Numbeo format: "3,500.00" (USD/local currency)
        match = re.search(r'([\d,]+\.?\d*)', text.replace(',', ''))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None


async def run_numbeo_scraper():
    all_city_data = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        scraper = NumbeoScraper()
        
        all_cities = {**NumbeoScraper.TARGET_CITIES_ABROAD, **NumbeoScraper.TARGET_CITIES_ID}
        
        for city_name, city_slug in all_cities.items():
            print(f"Scraping Numbeo: {city_name}")
            prices = await scraper.scrape_city_prices(page, city_slug)
            if prices:
                all_city_data[city_name] = prices
            await asyncio.sleep(5)  # Respectful delay
        
        await browser.close()
    
    # Save to Supabase
    from supabase import create_client
    import os
    supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])
    
    for city_name, prices in all_city_data.items():
        supabase.table('cost_of_living_cities').upsert({
            'city_name': city_name,
            'prices_json': json.dumps(prices),
            'scraped_at': datetime.now().isoformat(),
        }).execute()
    
    print(f"Loaded data for {len(all_city_data)} cities")
```

---

## Step 3: Supabase Schema

`[SUPABASE]`:

```sql
-- Cost of living data per city
CREATE TABLE public.cost_of_living_cities (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  city_name TEXT NOT NULL UNIQUE,
  country_code TEXT,
  country_name TEXT,
  currency TEXT,
  prices_json JSONB,
  col_index NUMERIC(8,2),  -- Numbeo cost of living index
  scraped_at TIMESTAMPTZ DEFAULT NOW()
);

-- Abroad salary benchmarks by role + country
CREATE TABLE public.abroad_salary_benchmarks (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  job_title TEXT NOT NULL,
  country_code TEXT NOT NULL,
  city TEXT,
  p50_salary_local NUMERIC(15,2),  -- In local currency
  p50_salary_usd NUMERIC(15,2),    -- Normalized to USD
  currency TEXT NOT NULL,
  source TEXT,
  year INTEGER,
  UNIQUE(job_title, country_code)
);

-- PPP reference data (loaded from World Bank API)
CREATE TABLE public.ppp_reference (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  country_code TEXT NOT NULL,
  country_name TEXT,
  currency TEXT,
  ppp_factor NUMERIC(12,4),   -- Local currency per international $
  gdp_per_capita_usd NUMERIC(12,2),
  year INTEGER NOT NULL,
  UNIQUE(country_code, year)
);

-- All tables publicly readable (no PII)
ALTER TABLE public.cost_of_living_cities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ppp_reference ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read" ON public.cost_of_living_cities FOR SELECT USING (true);
CREATE POLICY "Public read PPP" ON public.ppp_reference FOR SELECT USING (true);
```

---

## Step 4: Levels.fyi Scraper (Tech Salaries Abroad)

`[SWARMS]` — For tech job seekers (high value segment)

```python
# agents/scrapers/levelsfyi_scraper.py
# levels.fyi shows tech salaries. Public data, no login required for most countries.
# Rate limit generously.

class LevelsFYIScraper:
    BASE_URL = "https://www.levels.fyi"
    
    # Target: Indonesian tech workers considering abroad
    TARGET_ROLES = ['Software Engineer', 'Data Engineer', 'Product Manager', 'Data Scientist']
    TARGET_COUNTRIES = ['Singapore', 'United States', 'United Kingdom', 'Australia', 'Germany', 'Netherlands']
    
    async def scrape_country_salaries(self, page, role: str, country: str) -> list[dict]:
        # levels.fyi uses query params
        url = f"{self.BASE_URL}/js/salaries/salary-data.json?country={country}&title={role.replace(' ', '%20')}"
        
        try:
            await page.goto(url, timeout=20000)
            content = await page.content()
            # Parse JSON response if available
            # levels.fyi has changed their data format — verify selector before running
            return []
        except Exception:
            return []
```

---

## Step 5: Wajar Kabur UI

`[CURSOR]` — Prompt:
> "Create Wajar Kabur page for Indonesian abroad salary comparison. Inputs: current Indonesian gross salary (IDR/month), job role (text with dropdown suggestions), current city, target country (dropdown with 15 countries + flags). Result shows: 3 cards side by side: (1) Current Indonesia - salary + cost of living breakdown, (2) Target country - PPP-adjusted equivalent + market salary for same role, (3) Net comparison - how much more/less in real terms. Add 'Estimasi Pajak Abroad' section showing typical income tax rate for target country. Use Tailwind CSS."

---

## Freemium Gates for Wajar Kabur

| Feature | Free | Basic (IDR 29K) | Pro (IDR 79K) |
|---------|------|-----------------|---------------|
| PPP-adjusted comparison (1 country) | ✅ | ✅ | ✅ |
| All 15 countries | ❌ (top 5 only) | ✅ | ✅ |
| Cost of living basket breakdown | ❌ | ✅ | ✅ |
| Market salary for role in target country | ❌ | ✅ | ✅ |
| Estimated abroad income tax | ❌ | ❌ | ✅ |
| Side-by-side multi-country compare | ❌ | ❌ | ✅ |

---

## Reality Check

| Issue | Reality |
|-------|---------|
| World Bank PPP data is 1–2 years old | Yes. PPP is updated annually, not real-time. Use with caveat. |
| Numbeo salary data is user-submitted | Not verified, can be noisy. Use with confidence score. |
| levels.fyi structure changes | Re-run scraper if data stops loading. |
| Exchange rates fluctuate daily | Use frankfurter.app for real-time rates (free, no limit) |
| Tax calculation for abroad is complex | Show typical effective rate only. Never claim exact calculation. |
