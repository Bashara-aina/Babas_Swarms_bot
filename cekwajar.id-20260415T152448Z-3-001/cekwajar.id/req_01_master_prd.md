# req_01 — Master PRD: cekwajar.id
**Document Type:** Product Requirements Document  
**Version:** 1.0 | **Status:** Active  
**Owner:** Founder  
**Last Updated:** 2024-01

---

## 1. Problem Statement

Indonesian workers, property buyers, and lifestyle decision-makers lack access to reliable, free, and localized data benchmarks. Specifically:

1. **Payslip compliance:** >60% of Indonesian formal workers cannot independently verify whether PPh21 and BPJS deductions on their payslip are correct. Tax regulations (PMK 168/2023, TER method) changed in January 2024, but most employees still do not understand how their deductions are calculated. Underpayment or overpayment of PPh21 by employers is widespread in SME payroll environments.

2. **Salary benchmark:** There is no free, Indonesian-localized, city-level salary benchmark. Glassdoor is not Indonesia-localized. WageIndicator/Gajimu has thin coverage outside Jabodetabek. BPS Sakernas only provides province-level data for 9 occupation groups — not useful for "Is IDR 12M as a Backend Engineer in Bandung fair?"

3. **Property price:** 99.co and Rumah123 show raw listings, but no tool gives a clean "wajar atau tidak?" verdict for a specific price-per-m² in a specific kelurahan. NJOP values published by BPN are often 40–60% below market price, making them useless as a fairness benchmark.

4. **Abroad comparison:** Hundreds of thousands of Indonesian graduates consider working abroad annually. There is no free tool that converts their current IDR salary to a PPP-adjusted equivalent in Singapore, Australia, or Europe, or that tells them whether a specific foreign offer is actually better in real terms.

5. **Cost of living:** When relocating for work within Indonesia (Jakarta → Surabaya, Jakarta → Bali), workers have no quick tool to calculate how much salary adjustment they need to maintain the same lifestyle.

**Root cause:** All existing solutions are either paywalled (Mercer, WTW), not Indonesian-localized (Glassdoor), or use lagged government data without UX (BPS.go.id).

**cekwajar.id's answer:** 5 interconnected tools, free tier for all basic checks, premium for deep breakdown — powered by public data, crowdsource, and AI-assisted data collection.

---

## 2. Target Users (Summary — see req_03_personas.md for full detail)

| Persona | Name | Primary Tools | WTP |
|---------|------|---------------|-----|
| P1 — Karyawan Curiga | Rina, 28, HRD staff, Jakarta | Wajar Slip, Wajar Gaji | IDR 29K/mo |
| P2 — Gen Z Global | Dimas, 24, fresh grad, Surabaya | Wajar Kabur, Wajar Hidup | IDR 29K/mo (one-time) |
| P3 — Pembeli Properti Pertama | Sari, 32, supervisor, Bekasi | Wajar Tanah | IDR 29K (one search) |

---

## 3. Out of Scope (All Versions)

These items will never be built without explicit re-scoping:

- **Actual tax filing or form generation** (SPT 1770, 1721-A1) — cekwajar.id is NOT a tax software
- **Actual property listing platform** — we show benchmarks, not list properties
- **Investment advice, portfolio management, or OJK-regulated services**
- **B2B payroll processing or HRIS integration** (may revisit post-Month 12 with B2B licensing)
- **Insurance comparison or OJK-regulated financial product referral**
- **Real-time stock or crypto data**
- **Legal document generation** (employment contracts, property deeds)
- **Multi-language support** (English, Mandarin) before Month 9
- **Native iOS/Android app** before Month 12

---

## 4. PRD: Wajar Slip

### 4.1 Problem
Karyawan cannot verify if PPh21 and BPJS deductions are correct without a tax consultant. Standard Indonesian payslips do not show calculation methodology. Employees routinely overpay or are underpaid BPJS without knowing.

### 4.2 Target User
Primary: Karyawan with monthly salary IDR 5M–30M at SME or mid-size company. Secondary: HRD staff who want to verify their payroll output.

### 4.3 Feature List

**P0 (Must have at launch):**
- Manual input form: gross salary, PTKP status, month/year, NPWP (Y/N), reported deductions (PPh21, JHT, JP, JKK, JKM, BPJS Kesehatan, net salary), city for UMK lookup
- PPh21 TER calculation engine (PMK 168/2023 Lampiran A, B, C)
- PPh21 progressive annual engine (UU HPP No.7/2021)
- December true-up detection and calculation
- BPJS 6-component calculation (JHT, JP, JKK, JKM, Kesehatan employee + employer)
- Salary vs UMK comparison (Kemnaker data, 514 cities)
- Violation detection V01–V07
- Free result: shows violation codes found (V01, V03, etc.) without IDR amounts
- Freemium gate at IDR shortfall amount
- Disclaimer: "Bukan nasihat pajak"

**P1 (Week 2–4):**
- OCR upload: Google Vision API primary, Tesseract.js fallback
- Confidence threshold routing: AUTO_ACCEPT=0.92 / SOFT_CHECK=0.80 / MANUAL_REQUIRED=0.70
- Payslip file storage (Supabase Storage, 30-day auto-delete)
- Audit history (3 months, Basic tier)

**P2 (Month 2):**
- PDF export of audit report
- Share card (OG image with result)
- December true-up simulation (Pro tier)
- THR/bonus month PPh21 recalculation
- Employer contribution breakdown (JKK, JKM, employer JHT, employer JP)

**Excluded:**
- SPT 1770/1721-A1 form generation
- Multi-year tax history
- API access for third-party HR systems (B2B: Month 9+)

### 4.4 Freemium Gate Definition

| Feature | Free (anon) | Free (logged in) | Basic IDR 29K | Pro IDR 79K |
|---------|-------------|------------------|----------------|--------------|
| PPh21 calculation | ✅ | ✅ | ✅ | ✅ |
| BPJS calculation | ✅ | ✅ | ✅ | ✅ |
| Violation codes (V01–V07 names) | Shows first 1 | All codes | All codes | All codes |
| IDR shortfall amounts | ❌ | ❌ | ✅ | ✅ |
| OCR upload | 1/lifetime | 1/month | 10/month | Unlimited |
| Audit history | None | 1 entry | 3 months | Unlimited |
| PDF report | ❌ | ❌ | ✅ | ✅ |
| December true-up sim | ❌ | ❌ | ❌ | ✅ |

### 4.5 Success Metrics

| Metric | Week 4 | Month 3 | Month 6 | Kill if |
|--------|--------|---------|---------|---------|
| Tool completions (audits/day) | 20 | 150 | 500 | <5/day at Month 2 |
| Conversion to paid | — | 2% | 5% | <0.5% at Month 3 |
| OCR success rate (AUTO_ACCEPT) | 70% | 80% | 85% | <50% at launch |
| Confirmed calc errors (user reports) | 0 | 0 | 0 | Any confirmed error = P0 bug |
| NPS post-verdict | — | ≥30 | ≥40 | <15 at Month 3 |

### 4.6 Kill Criteria
- 2 or more confirmed PPh21/BPJS calculation errors reported by users in 30 days: **pull tool, fix, re-test with all 20 TC before relaunch**
- OCR AUTO_ACCEPT rate < 50% at launch: **disable OCR path, manual form only**
- Zero paying users after 60 days of public access: **pivot pricing or tool framing**

---

## 5. PRD: Wajar Gaji

### 5.1 Problem
Karyawan have no free, city-level, job-title-level salary benchmark in Indonesia. BPS Sakernas is province-level only. Glassdoor is not localized. LinkedIn Salary is behind login. Result: employees negotiate from zero information.

### 5.2 Target User
Primary: Karyawan negotiating salary for a new job, or verifying their current salary. Secondary: Fresh graduates benchmarking first offer.

### 5.3 Feature List

**P0:**
- Input form: job title (text with autocomplete), city, industry, years of experience
- Province-level BPS Sakernas P50 (with disclaimer "data provinsi BPS, bukan kota")
- UMK floor display for entered city
- Crowdsource submission form (anonymous, no login required)
- K-anonymity threshold: show result only if n ≥ 10 for city+title+industry cell
- Bayesian blend formula: `BlendedP50 = (n/(n+k)) × CrowdP50 + (k/(n+k)) × BPS_prior` where k=15
- Confidence badge: Low (BPS only) / Cukup (n<30) / Terverifikasi (n≥30)
- Free: province P50 only

**P1:**
- JobStreet scraped salary ranges per job title (loaded monthly, not real-time)
- City-level P50 when n≥30 crowdsource
- P25/P75 range (Basic tier)

**P2:**
- Industry comparison within same city (Pro tier)
- Year-over-year trend (Pro tier)
- Job title fuzzy matching via pgvector

**Excluded:**
- Company-specific salary data (legal risk: company trade secrets)
- Real-time job ad matching
- Recruiter mode / B2B access (Month 9+)

### 5.4 Freemium Gate Definition

| Feature | Free | Basic IDR 29K | Pro IDR 79K |
|---------|------|---------------|--------------|
| Province P50 (BPS) | ✅ | ✅ | ✅ |
| City P50 (if n≥30) | ❌ | ✅ | ✅ |
| P25/P75 range | ❌ | ✅ | ✅ |
| Industry comparison | ❌ | ❌ | ✅ |
| Salary trend (YoY) | ❌ | ❌ | ✅ |
| Anonymous submit | ✅ | ✅ | ✅ |

### 5.5 Success Metrics

| Metric | Month 3 | Month 6 | Kill if |
|--------|---------|---------|---------|
| Crowdsource submissions | 200 | 2,000 | <50 at Month 3 |
| Cells with n≥10 | 20 | 200 | <5 at Month 3 |
| Audit completions/day | 50 | 300 | <10 at Month 2 |
| User-reported inaccuracies | <5 | <10 | >30/month = data quality crisis |

### 5.6 Kill Criteria
- Crowdsource submissions <50 at Month 3: **pivot to scraped data only, stop promoting Wajar Gaji**
- User complaints about wildly inaccurate benchmarks >30/month: **add larger disclaimer, reduce confidence badge**

---

## 6. PRD: Wajar Tanah

### 6.1 Problem
First-time property buyers in Indonesia cannot independently verify whether the price they are being asked to pay per m² is fair for a specific kelurahan. NJOP is 40–60% below market. Real estate agents have information asymmetry advantage.

### 6.2 Target User
Primary: First-time property buyer researching a specific property. Secondary: Seller wanting to price competitively.

### 6.3 Feature List

**P0:**
- Input form: province, city, kecamatan/kelurahan, property type (rumah/tanah/apartemen/ruko), land area m², total asking price OR price/m²
- Market P50 per m² from scraped listing data (99.co + Rumah123, cached monthly)
- NJOP reference from BPN/BHUMI (official government data)
- Verdict: MURAH / WAJAR / MAHAL / SANGAT_MAHAL
- Free: Verdict + P50 only
- Disclaimer: "Bukan penilaian KJPP berlisensi"

**P1:**
- P25/P75 price range (Basic tier)
- NJOP/market ratio display
- Sample count badge

**P2:**
- Price trend (3 months if scraper runs monthly) — Pro tier
- Nearby comparable listings summary
- PDF "mini valuation summary" (Basic+)

**Excluded:**
- Actual property listings or marketplace features
- KJPP-certified appraisal
- Mortgage calculator (may add as simple companion)

### 6.4 Freemium Gate Definition

| Feature | Free | Basic IDR 29K | Pro IDR 79K |
|---------|------|---------------|--------------|
| Verdict (Murah/Wajar/Mahal) | ✅ | ✅ | ✅ |
| P50 market price/m² | ✅ | ✅ | ✅ |
| P25/P75 range | ❌ | ✅ | ✅ |
| NJOP reference | ❌ | ✅ | ✅ |
| Price trend | ❌ | ❌ | ✅ |
| PDF report | ❌ | ✅ | ✅ |

### 6.5 Success Metrics

| Metric | Month 3 | Month 6 | Kill if |
|--------|---------|---------|---------|
| Lookups/day | 30 | 200 | <5 at Month 2 |
| Cities with n≥5 listings | 10 | 30 | <5 = no useful data |
| Scraper success rate | 80% | 90% | <50% = blocked, rebuild scraper |

### 6.6 Kill Criteria
- Property scraper permanently blocked by all 3 sources (99.co, Rumah123, OLX) and no fallback data: **disable tool, show "segera hadir" with crowdsource submission option**
- Cease and desist received from 99.co or Rumah123: **immediately stop scraping that source**

---

## 7. PRD: Wajar Kabur

### 7.1 Problem
Indonesian graduates considering working abroad have no free tool to determine whether a foreign salary offer is actually better in real purchasing power terms than staying in Indonesia. IDR/SGD nominal comparison is misleading without PPP adjustment.

### 7.2 Target User
Primary: Gen Z / Millennial professional (25–35) with an offer from Singapore, Australia, or Europe. Secondary: Someone researching "is it worth going abroad?"

### 7.3 Feature List

**P0:**
- Input form: current monthly salary (IDR), job role, target country (15 country dropdown)
- World Bank PPP conversion (free REST API, updated annually)
- PPP-adjusted equivalent in target country currency
- Exchange rate reference (frankfurter.app free API, daily)
- Free: Top 5 countries, PPP result only

**P1:**
- Numbeo cost of living basket for target city
- Market salary for same role in target country (scraped or Numbeo)
- All 15 countries (Basic tier)

**P2:**
- Estimated income tax in target country (simplified effective rate)
- Side-by-side multi-country comparison (Pro tier)
- Savings potential simulation

**Excluded:**
- Visa or immigration advice
- Specific job listings abroad
- Tax treaty analysis

### 7.4 Freemium Gate Definition

| Feature | Free | Basic IDR 29K | Pro IDR 79K |
|---------|------|---------------|--------------|
| PPP comparison (top 5 countries) | ✅ | ✅ | ✅ |
| All 15 countries | ❌ | ✅ | ✅ |
| CoL basket breakdown | ❌ | ✅ | ✅ |
| Market salary abroad | ❌ | ✅ | ✅ |
| After-tax estimate | ❌ | ❌ | ✅ |
| Multi-country side-by-side | ❌ | ❌ | ✅ |

### 7.5 Success Metrics

| Metric | Month 3 | Month 6 | Kill if |
|--------|---------|---------|---------|
| Comparisons/day | 30 | 150 | <5 at Month 2 |
| Avg session time | >90s | >120s | <30s = low engagement |
| World Bank API uptime | 99% | 99% | API down >2 days = cache |

---

## 8. PRD: Wajar Hidup

### 8.1 Problem
Workers relocating within Indonesia (e.g., Jakarta → Surabaya for a new job) need to know how much salary adjustment is required to maintain the same lifestyle. No simple free calculator exists for this in Indonesian context.

### 8.2 Target User
Primary: Professional relocating for work. Secondary: Person comparing cities before accepting a job offer.

### 8.3 Feature List

**P0:**
- Input: current city, target city, current monthly salary (IDR), lifestyle level (Hemat/Standar/Nyaman)
- COL index per city from BPS CPI + Numbeo data
- Required salary in target city for same lifestyle
- % adjustment needed
- Free: Total % comparison only

**P1:**
- Category breakdown (food/housing/transport/utilities/entertainment) — Basic tier
- BPS CPI trend for both cities

**P2:**
- Historical city COL trend (Pro tier)
- Multi-city comparison table (Pro tier)

### 8.4 Freemium Gate Definition

| Feature | Free | Basic IDR 29K | Pro IDR 79K |
|---------|------|---------------|--------------|
| % adjustment (total) | ✅ | ✅ | ✅ |
| Required salary in target city | ✅ | ✅ | ✅ |
| Category breakdown | ❌ | ✅ | ✅ |
| Historical trend | ❌ | ❌ | ✅ |
| Multi-city table | ❌ | ❌ | ✅ |

### 8.5 Success Metrics

| Metric | Month 3 | Month 6 | Kill if |
|--------|---------|---------|---------|
| Comparisons/day | 20 | 100 | <5 at Month 2 |
| Cities covered | 20 | 50 | <10 = data too thin |

---

## 9. Global Kill Criteria (Platform Level)

These trigger a full platform pause:
- Any government (DJP, Kemnaker, OJK) sends formal cease-and-desist
- Security breach exposing user payslip data (any volume)
- Confirmed systematic PPh21 calculation errors affecting >100 users
- Monthly active users drop below 100 for 3 consecutive months after Month 6
