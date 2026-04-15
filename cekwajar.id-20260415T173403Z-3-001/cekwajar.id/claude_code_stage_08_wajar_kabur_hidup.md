# Stage 8 — Wajar Kabur + Wajar Hidup
**cekwajar.id Vibe Coding Playbook**  
**Estimated time:** 3–4 hours  
**Prerequisites:** Stages 1–7 complete. ppp_reference seeded (from migration 017). col_indices seeded.  
**Goal:** Wajar Kabur (PPP abroad comparison) + Wajar Hidup (COL city comparison) both working end-to-end.

---

## ═══════════════════════════════════════════════
## MASTER PROMPT — SEND THIS TO CLAUDE CODE
## (Stage 8 — Wajar Kabur + Wajar Hidup)
## ═══════════════════════════════════════════════

```
===START===
cekwajar.id — Stage 8: Wajar Kabur + Wajar Hidup

Context: Stages 1-7 complete. ppp_reference has 15 countries. col_indices has 20 cities.
col_categories has 10 categories with lifestyle weights.

YOUR TASK FOR STAGE 8:
Build Wajar Kabur (abroad PPP comparison) and Wajar Hidup (COL city comparison).
Both tools with APIs, calculation engines, and full UI.

════════════════════════════════════════════════════
PART A: WORLD BANK PPP INTEGRATION
════════════════════════════════════════════════════

Create src/lib/external/worldbank.ts

World Bank PPP API — completely free, no key required.

interface WorldBankPPPData {
  countryCode: string
  countryName: string
  pppFactor: number      // local currency per international dollar
  year: number
  fetchedAt: string
}

export async function getWorldBankPPP(countryCode: string): Promise<WorldBankPPPData | null> {
  // Check Supabase cache first (30-day cache)
  const supabase = getServiceClient()
  const { data: cached } = await supabase
    .from('ppp_reference')
    .select('ppp_factor, ppp_year, fetched_at')
    .eq('country_code', countryCode)
    .single()
  
  // Use cache if fresh (< 30 days)
  if (cached && cached.ppp_factor) {
    const cacheAge = Date.now() - new Date(cached.fetched_at).getTime()
    if (cacheAge < 30 * 24 * 60 * 60 * 1000) {
      return { countryCode, countryName: '', pppFactor: cached.ppp_factor, year: cached.ppp_year, fetchedAt: cached.fetched_at }
    }
  }
  
  // Fetch from World Bank API
  const url = `https://api.worldbank.org/v2/country/${countryCode}/indicator/PA.NUS.PPP?format=json&mrv=1`
  
  try {
    const response = await fetch(url, { 
      next: { revalidate: 86400 },  // Next.js cache for 24h
    })
    
    if (!response.ok) throw new Error(`World Bank API error: ${response.status}`)
    
    const [meta, data] = await response.json()
    const latest = data?.find((d: any) => d.value !== null)
    
    if (!latest) return null
    
    const result = {
      countryCode,
      countryName: latest.country.value,
      pppFactor: latest.value,
      year: parseInt(latest.date),
      fetchedAt: new Date().toISOString(),
    }
    
    // Update cache in DB
    await supabase.from('ppp_reference')
      .update({ ppp_factor: result.pppFactor, ppp_year: result.year, fetched_at: result.fetchedAt })
      .eq('country_code', countryCode)
    
    return result
  } catch (error) {
    console.error('World Bank API failed:', error)
    // Return cached value even if stale (better than nothing)
    if (cached?.ppp_factor) {
      return { countryCode, countryName: '', pppFactor: cached.ppp_factor, year: cached.ppp_year, fetchedAt: cached.fetched_at }
    }
    return null
  }
}

Indonesia PPP factor is needed for comparison. Always fetch ID (Indonesia):
  const idPPP = await getWorldBankPPP('ID')
  // Indonesia PPP factor is ~4790 IDR per international dollar (2023)

════════════════════════════════════════════════════
PART B: EXCHANGE RATE INTEGRATION
════════════════════════════════════════════════════

Create src/lib/external/exchangerates.ts

Use Frankfurter.app — completely free, no API key.
Source: European Central Bank daily rates.

export async function getExchangeRate(
  fromCurrency: string,
  toCurrency: string
): Promise<number | null> {
  // Cache for 24 hours (rates update daily)
  const cacheKey = `rate_${fromCurrency}_${toCurrency}`
  
  // Simple in-memory cache for Edge (replace with KV in production)
  if (rateCache.has(cacheKey) && rateCache.get(cacheKey).expiresAt > Date.now()) {
    return rateCache.get(cacheKey).rate
  }
  
  try {
    const url = `https://api.frankfurter.app/latest?from=${fromCurrency}&to=${toCurrency}`
    const response = await fetch(url, { next: { revalidate: 3600 } })
    
    if (!response.ok) throw new Error(`Exchange rate API error: ${response.status}`)
    
    const data = await response.json()
    const rate = data.rates[toCurrency]
    
    // Cache for 24 hours
    rateCache.set(cacheKey, { rate, expiresAt: Date.now() + 86400000 })
    
    return rate
  } catch (error) {
    return null
  }
}

const rateCache = new Map<string, { rate: number; expiresAt: number }>()

════════════════════════════════════════════════════
PART C: WAJAR KABUR API ROUTE
════════════════════════════════════════════════════

Create src/app/api/abroad/compare/route.ts

GET params: currentIDRSalary, targetCountry, jobRole (optional)

PPP comparison calculation:
  1. Get Indonesia PPP factor
  2. Get target country PPP factor  
  3. Calculate user's real purchasing power in international dollars
  4. Get nominal exchange rate
  5. Return comparison

function calculatePPPComparison(
  idSalary: number,
  idPPPFactor: number,
  foreignSalary: number,    // optional — if user enters target salary
  foreignPPPFactor: number,
  exchangeRate: number,     // IDR per 1 unit of foreign currency
): PPPComparisonResult {
  
  // User's purchasing power in international dollars
  const userPowerIntlUSD = idSalary / idPPPFactor
  
  // Nominal equivalent: how much is IDR salary worth in foreign currency?
  const nominalEquivalent = idSalary / exchangeRate
  
  let result: PPPComparisonResult = {
    idSalary,
    nominalEquivalent,
    nominalCurrency: '', // filled by caller
    userPowerIntlUSD,
    idPPPFactor,
    foreignPPPFactor,
    exchangeRate,
  }
  
  if (foreignSalary) {
    const offerPowerIntlUSD = foreignSalary / foreignPPPFactor
    result.offerPowerIntlUSD = offerPowerIntlUSD
    result.realRatio = offerPowerIntlUSD / userPowerIntlUSD
    result.isPPPBetter = offerPowerIntlUSD > userPowerIntlUSD
  }
  
  return result
}

Response structure:
  Free (top 5 countries):
    nominalEquivalent, nominalCurrency, realPurchasingPowerIntlUSD, pppFactor, pppYear, exchangeRate
  
  Gated (non-top-5 for free users):
    isGated = true, countryName, requiresUpgrade = true
  
  Basic+:
    + colBreakdown (Numbeo data if available, else static estimates)
    + marketSalaryInTarget

Check free tier:
  const country = await supabase.from('ppp_reference').select('is_free_tier').eq('country_code', targetCountry).single()
  const isGated = !country.data?.is_free_tier && tier === 'free'

════════════════════════════════════════════════════
PART D: WAJAR KABUR UI
════════════════════════════════════════════════════

Replace stub at src/app/wajar-kabur/page.tsx

CLIENT COMPONENT.

FORM:
  Gaji Saat Ini (IDR, number input)
  Peran Pekerjaan (text, optional — helps with market salary lookup later)
  
  Country selector grid:
    Mobile: vertical list with flag + name + arrow
    Desktop: 3-column grid with flag + name
    
    Free tier (top 5 countries): clickable immediately
    Locked countries: show 🔒 overlay, clicking shows gate modal
    
    Countries display: 15 total from ppp_reference table
    Fetch with: GET /api/abroad/countries → return all with is_free_tier flag
    
  [Bandingkan →] button

RESULT CARD:
  
  PPP Comparison display:
    Box 1 (left):
      "Gaji Kamu di Indonesia"
      IDR [amount]
      "= [X] international dollar per bulan (PPP)"
    
    Box 2 (right):
      "[flag] [Country]"
      "Setara secara nominal: [currency] [amount]"
      "Setara secara daya beli: [currency] [ppp_amount]"
      
    Big comparison banner:
      If offer entered AND better: 🟢 "Penawaran [X]× lebih besar secara daya beli"
      If offer entered AND worse: 🔴 "Penawaran hanya [X]× daya beli"
      If no offer: "Masukkan penawaran gaji untuk membandingkan"
    
    PPP source note: "PPP sumber: World Bank [year]"
  
  CoL Breakdown (Basic+ gate):
    PremiumGate wrapping cost breakdown
    requiredTier='basic'
    featureLabel='Detail biaya hidup di negara tujuan'
  
  Political/accuracy disclaimer (always shown):
    Small collapsible: "Catatan: PPP adalah ukuran ekonometrik. Data biaya hidup dari Numbeo bersifat estimasi komunitas..."

Create src/app/api/abroad/countries/route.ts:
  GET → return all countries from ppp_reference ordered by display_order
  Include: country_code, country_name, currency_code, flag_emoji, is_free_tier

════════════════════════════════════════════════════
PART E: WAJAR HIDUP API ROUTE
════════════════════════════════════════════════════

Create src/app/api/col/compare/route.ts

GET params: fromCity, toCity, currentSalary, lifestyleTier

Validation:
  fromCity, toCity: must exist in col_indices
  currentSalary: number min 500000
  lifestyleTier: 'HEMAT' | 'STANDAR' | 'NYAMAN'
  fromCity !== toCity (else return SAME_CITY_ERROR)

Calculation:
  1. Get COL indices for both cities
  2. Get category weights for lifestyle tier
  3. Apply adjustment formula

function calculateCOLAdjustment(
  currentSalary: number,
  fromIndex: number,
  toIndex: number,
  lifestyleTier: string,
): COLResult {
  
  const LIFESTYLE_MULTIPLIER: Record<string, number> = {
    HEMAT: 0.70,    // frugal — less sensitive
    STANDAR: 1.00,  // baseline
    NYAMAN: 1.30,   // comfortable — more sensitive
  }
  
  const baseRatio = toIndex / fromIndex
  const mult = LIFESTYLE_MULTIPLIER[lifestyleTier]
  
  // Adjusted ratio: 1 + (distance from 1) × multiplier
  // Example: if destination is 20% cheaper (ratio=0.8), and multiplier=1.3:
  // adjustedRatio = 1 + (0.8-1) × 1.3 = 1 + (-0.26) = 0.74 (26% cheaper)
  const adjustedRatio = 1 + (baseRatio - 1) * mult
  
  const requiredSalary = Math.round(currentSalary * adjustedRatio)
  const difference = requiredSalary - currentSalary
  const percentChange = ((adjustedRatio - 1) * 100)
  
  const verdict: 'LEBIH_MURAH' | 'SAMA' | 'LEBIH_MAHAL' =
    difference < -100_000 ? 'LEBIH_MURAH' :
    difference > 100_000 ? 'LEBIH_MAHAL' : 'SAMA'
  
  return {
    fromCOLIndex: fromIndex,
    toCOLIndex: toIndex,
    adjustmentRatio: adjustedRatio,
    requiredSalary,
    salaryDifference: difference,
    percentChange,
    verdict,
    verdictMessage: buildVerdictMessage(verdict, percentChange, toCity),
  }
}

Category breakdown (Basic+ only):
  For each of 10 categories in col_categories:
    fromAmount = currentSalary × category.weight
    toAmount = fromAmount × (toIndex / fromIndex)
    Adjusted by category-specific ratio if we have it (use overall ratio otherwise)

Create src/app/api/col/cities/route.ts:
  GET → all cities from col_indices: { cityCode, cityName, province, colIndex }
  Used for dropdowns in Wajar Hidup form

════════════════════════════════════════════════════
PART F: WAJAR HIDUP UI
════════════════════════════════════════════════════

Replace stub at src/app/wajar-hidup/page.tsx

CLIENT COMPONENT.

FORM:
  Two city dropdowns side by side:
    Dari Kota: [Select from 20 cities] 
    Ke Kota: [Select from 20 cities]
    
  Gaji Sekarang: IDR number input
  
  Gaya Hidup (3 radio cards):
    🪙 Hemat — "Prioritas tabungan, makan masak sendiri, transportasi umum"
    🏠 Standar — "Sesekali makan di luar, kendaraan pribadi, tabungan moderat"  
    ✨ Nyaman — "Makan di restoran, hiburan rutin, tabungan lebih banyak"
  
  [Hitung →] button

RESULT:

Large verdict card:
  If LEBIH_MURAH:
    🟢 "Lebih Murah di [toCity]!"
    "Dengan gaya hidup yang sama, kamu butuh [X]% lebih sedikit"
    "Gaji setara: Rp [requiredSalary]/bulan (hemat Rp [difference]/bulan)"
  
  If LEBIH_MAHAL:
    🔴 "Lebih Mahal di [toCity]!"
    "Kamu butuh [X]% lebih banyak untuk gaya hidup yang sama"
    "Gaji setara: Rp [requiredSalary]/bulan"
  
  If SAMA:
    🔵 "Biaya Hidup Setara"
    "Kedua kota memiliki biaya hidup yang kurang lebih sama"
  
  COL index display:
    [fromCity]: [fromIndex] | [toCity]: [toIndex]
    "Jakarta = 100 sebagai baseline"
  
  Category breakdown table (PremiumGate — Basic+):
    requiredTier='basic'
    featureLabel='Breakdown per kategori pengeluaran'
    
    Table when unlocked:
      | Kategori | [fromCity] | [toCity] | Selisih |
      | Tempat Tinggal | Rp X | Rp Y | ±Rp Z |
      | Makanan | ... | ... | ... |
      | ... 10 rows |

════════════════════════════════════════════════════
VERIFICATION:
════════════════════════════════════════════════════

Test Wajar Kabur:
  curl "localhost:3000/api/abroad/compare?currentIDRSalary=8500000&targetCountry=SG"
  Expected response includes:
    nominalEquivalent ≈ 730 (SGD)
    userPowerIntlUSD ≈ 1775 (IDR 8.5M / 4790 PPP factor)
    pppFactor for ID and SG both present

Test Wajar Hidup:
  curl "localhost:3000/api/col/compare?fromCity=JKT&toCity=SBY&currentSalary=12000000&lifestyleTier=STANDAR"
  Expected:
    fromCOLIndex: 100.0
    toCOLIndex: 78.5
    adjustedRatio: 0.785
    requiredSalary: ~9420000
    verdict: LEBIH_MURAH

Test same city:
  curl "localhost:3000/api/col/compare?fromCity=JKT&toCity=JKT&currentSalary=10000000&lifestyleTier=STANDAR"
  Expected: 400 error with SAME_CITY_ERROR code

Test gated country (free user):
  curl "localhost:3000/api/abroad/compare?currentIDRSalary=8500000&targetCountry=JP"
  Expected: { isGated: true, requiresUpgrade: true } (for free tier)

Visit localhost:3000/wajar-kabur → select Singapore → enter IDR 8.5M
Visit localhost:3000/wajar-hidup → select Jakarta → Surabaya → IDR 12M

pnpm tsc --noEmit → zero errors
===END===
```

**Next:** Stage 9 — Monetization (Midtrans + Full Freemium Gates)
