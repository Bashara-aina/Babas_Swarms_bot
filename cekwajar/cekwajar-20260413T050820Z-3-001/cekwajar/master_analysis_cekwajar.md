# cekwajar.id — Master Analysis: Fintech Consultant Evaluation
**Consultant Role:** Senior Indonesian Fintech & Data Platform Consultant
**Date:** April 2026
**Launch Target:** Wajar Slip MVP — May 2026
**Basis:** Pre-Build Checklist + VC Evaluation + 10 Prompt-Block Deep Analyses + Strategic Blueprint

---

## 1. MVP SCOPE LOCK

### 1.1 Decision: What Exactly Is v1?

**Decision: Wajar Slip Only. No exceptions.**

The rationale is not opinion — it is arithmetic:
- Wajar Slip is the only tool with zero data cold-start problem (deterministic calculation, no crowdsource needed)
- It is the only tool where every audit creates a verified, k-anonymity-eligible salary data point for Wajar Gaji
- It is the only tool where the paywall is immediately and obviously justified ("I just found my employer owes me IDR 847K in underpaid JHT — of course I'll pay IDR 49K")
- Its technical moat (PPh21 TER + progressive + all 6 BPJS components) is the deepest and most defensible across the entire platform

A combined Slip + Gaji launch fails because it splits engineering time, legal review effort, and content strategy between two different trust architectures: one deterministic (Wajar Slip) and one data-quality-dependent (Wajar Gaji). A mediocre Wajar Slip that ships in 6 weeks is worse than an excellent one that ships in 12 weeks. Launch Wajar Gaji only when Wajar Slip has proven the monetization model.

### 1.2 v1 Feature Scope

| Feature | Include in v1 | Engineering Hours (Solo) | Legal Risk | Data Dependency | Priority |
|---------|:---:|---:|---:|---|:---:|
| PDF payslip upload (≤5MB) | ✅ | 8h | HIGH — triggers UU PDP sensitif flow | None | P0 |
| Google Vision / Textract OCR integration | ✅ | 16h | LOW | Cloud API | P0 |
| PPh21 TER method calculation engine | ✅ | 20h | CRITICAL — needs tax audit | Regulatory tables | P0 |
| PPh21 progressive annual true-up | ✅ | 12h | CRITICAL | PMK 168/2023 | P0 |
| BPJS 6-component engine (JHT/JP/JKK/JKM/Kes ER+EE) | ✅ | 16h | HIGH — needs tax audit | BPJS/PMK 66/2023 | P0 |
| Violation detection (7 categories, Bahasa ID messages) | ✅ | 10h | HIGH | Above | P0 |
| UU PDP consent flow (explicit, separate for sensitif) | ✅ | 6h | CRITICAL — pre-launch gate | None | P0 |
| Manual field override fallback form | ✅ | 8h | LOW | None | P0 |
| Freemium gate: pass/fail free, IDR amount paid | ✅ | 4h | LOW | None | P0 |
| Midtrans individual merchant (IDR 49K/month) | ✅ | 10h | LOW | KTP + NPWP | P0 |
| Share card generation (@vercel/og) | ✅ | 6h | LOW — verdict language must be reviewed | None | P1 |
| 30-day raw payslip auto-delete (Supabase cron) | ✅ | 4h | CRITICAL — UU PDP retention | None | P0 |
| Basic dashboard: verdicts, violations, history | ✅ | 12h | LOW | None | P1 |
| Verdict history (up to 3 payslips free) | ✅ | 4h | LOW | None | P1 |
| PSE registration (Kominfo) | ✅ | 0h code | MED — legal process, not code | None | P0 |
| **v1 Total Estimated Hours** | | **~136h** | | | |

**136 engineering hours = ~17 working days at 8h/day, or ~5–6 weeks for a solo founder working 4–5h/day.**

### 1.3 Everything Excluded from v1

| Tool/Feature | Excluded Until | Reason |
|---|---|---|
| Wajar Gaji (salary benchmark) | Month 6–8 | Zero real data on Day 1; BPS province-level data creates misleading city-level verdicts. Launch only when either: (a) licensed survey data acquired, or (b) 500+ verified submissions exist |
| Wajar Tanah (property) | Month 10–12 | No NJOP API, property listing scraping is a ToS violation, zero crowdsourced transactions |
| Wajar Kabur (abroad comparison) | Month 12–18 | Politically sensitive, methodologically complex, requires BPS + World Bank PPP data pipeline |
| Wajar Hidup (cost of living) | Month 6–9 | Feasible on BPS CPI + Susenas, but not blocking — build only after Wajar Slip is profitable |
| Photo payslip support (camera capture) | Month 4–6 | OCR accuracy on photos unvalidated; launch with PDF only, add photo after accuracy audit |
| 3-tier pricing (29K/49K/99K) | Month 3–4 | Launch single Pro tier IDR 49K. Add Lite and Premium after conversion data exists |
| Annual subscription plans | Month 4–6 | Pre-launch conversation with Midtrans needed for recurring annual product setup |
| B2B API / licensing | Month 12+ | No pipeline, no product, no sales capacity |
| 17-agent Swarms architecture | Month 9+ | Operationally premature. Use single Edge Functions + one well-prompted LLM call per task |
| Wajar Gaji 500 SEO pages | Month 7–8 | Build only when benchmark data is credible; thin-content SEO pages with wrong salary data is a liability not an asset |
| AI-generated payslip analysis narrative | Month 4–6 | Build after OCR accuracy is validated; hallucinated legal analysis is legally dangerous |
| Salary submission crowdsource flow | Month 4–6 | Launch when Wajar Slip user base provides the initial seed data via payslip-to-salary pipeline |

### 1.4 Release Gates — Tool Additions

**Gate to add Wajar Gaji:**
- [ ] 500+ payslip audits completed (verified salary data pool established)
- [ ] ≥50 paying Wajar Slip subscribers with ≥30-day retention
- [ ] Licensed salary survey (Mercer/Korn Ferry) contract signed OR 200+ direct salary submissions
- [ ] PPh21 engine has zero reported calculation errors after 500 audits

**Gate to add Wajar Hidup:**
- [ ] Wajar Slip is cash-flow positive (revenue ≥ server + legal + content costs)
- [ ] BPS Susenas CPI data pipeline automated and tested
- [ ] 1,000+ MAU on platform

**Gate to add Wajar Tanah:**
- [ ] Formal data partnership signed with ATR/BPN or one major property portal
- [ ] 5,000+ platform MAU (distribution credibility to negotiate with portals)
- [ ] Legal review of property valuation disclaimer language

**Gate to add Wajar Kabur:**
- [ ] 10,000+ MAU (platform is established)
- [ ] World Bank + OECD PPP data pipeline tested for 5 target countries minimum
- [ ] Political risk assessment + legal review of emigration-adjacent content

### 1.5 Solo Founder Capacity Assessment

At 4–6 productive hours/day, a solo technical founder can realistically maintain:
- Maximum 2 active tools simultaneously (one in maintenance, one in active development)
- 3–5 TikTok videos/week (batch-produced, 1 day/week)
- 1 customer support response cycle/day (AI-assisted, <30 min/day)
- Monthly legal/regulatory monitoring (2h/month with AI assistance)

**Conclusion:** v1 Wajar Slip only is achievable. The moment a second tool launches before Wajar Slip reaches the release gate metrics above, quality degrades across both tools and the business model breaks.

---

## 2. OPERATIONAL DATA ACCESS ROADMAP

### 2.1 Layer 1 — Government Data (Launch-Ready)

#### BPS Sakernas Wage Data

| Item | Detail |
|---|---|
| **Access URL** | https://www.bps.go.id/id/statistics-table/2/MTQ1OCMy/rata-rata-upah-gaji-bersih-sebulan-buruh-pekerja-menurut-provinsi-dan-jenis-pekerjaan-utama.html |
| **API** | https://webapi.bps.go.id/v1/api/ (requires free registration at BPS API portal) |
| **Granularity** | Province × 9 major occupation groups (ISCO-adapted: managers, professionals, technicians, clerical, sales, farming, craft, operators, elementary). NOT city. NOT job title. |
| **Refresh cadence** | Annual (August survey, published Q1 following year) |
| **Legal basis** | Public statistical tables, free for cited use. Commercial re-use: conservative practice = contact BPS webmaster (statistik@bps.go.id) for written clearance before commercial launch. No explicit prohibition found, but no explicit commercial license either. |
| **Attribution required** | "Sumber: Badan Pusat Statistik (BPS), Sakernas [year]" — mandatory on every benchmark page |
| **Commercial re-use risk** | LOW-MEDIUM — BPS explicitly allows data use in reports and research; gray area for automated commercial product. Resolves with written clearance. |
| **Fallback if API down** | Static JSON file in repository updated quarterly; Supabase cron pulls from API, falls back to cached file |
| **Cost** | IDR 0 (free tier API) |

**Critical limitation for Wajar Gaji:** Province × major occupation = ~306 cells for 34 provinces × 9 occupations. Cannot deliver "Software Engineer in Surabaya" — can only deliver "Professional/Technical worker in Jawa Timur." Label this explicitly in UI.

#### Kemnaker UMR/UMK Data

| Item | Detail |
|---|---|
| **Access URL** | https://kemnaker.go.id/informasi/berita (annual UMK announcements) + SIPP Online portal |
| **API** | No official API. Data published as PDF decrees (SK Gubernur) and summarized on Kemnaker site |
| **Granularity** | Kabupaten/kota — 514 cities/regencies. Updated November/December annually. |
| **Legal basis** | Public regulatory data. No restrictions on use as reference floor. |
| **Operational approach** | Manual annual update: parse each SK Gubernur from 34 provinces (34 documents × 1h processing = 34h/year). Automate with Python PDF parser + Supabase insert. |
| **Refresh cadence** | Annual (effective January each year) |
| **Fallback** | Previous year UMK + official inflation adjustment estimate |
| **Cost** | IDR 0 |

UMK is critical as the legal floor for all Wajar Gaji verdicts. A salary below UMK is "Tidak Wajar Hukum" regardless of market position.

#### BPJS Rates (JHT, JP, JKK, JKM, Kesehatan)

| Component | Rate | Legal Source | Last Changed |
|---|---|---|---|
| JHT Employee | 2% | PP 46/2015 | 2015 |
| JHT Employer | 3.7% | PP 46/2015 | 2015 |
| JP Employee | 1% | PP 45/2015 | 2015 |
| JP Employer | 2% | PP 45/2015 | 2015 |
| JP Salary Cap | IDR 9,559,600 | Annual Permen | Updated annually |
| JKK Employer | 0.24%–1.74% (5 classes) | PP 44/2015 | 2015 |
| JKM Employer | 0.30% | PP 44/2015 | 2015 |
| Kesehatan Employee | 1% | Perpres 82/2018 | 2018 |
| Kesehatan Employer | 4% | Perpres 82/2018 | 2018 |
| Kesehatan Salary Cap | IDR 12,000,000 | Perpres | Updated by regulation |

**Operational requirement:** Hard-code rates in a `bpjs_rates` table (not application logic) with effective_date field. Supabase cron checks Kemnaker/BPJS website for regulatory changes quarterly. Rate changes require manual validation before deployment — no automated rate updates.

#### PPh21 Tax Tables (PMK 168/2023 TER Method)

TER rates are statutory tables embedded in PMK 168/2023 Lampiran A (monthly TER by PTKP category). These must be stored in a `pph21_ter_rates` table with effective_date. Any PMK update requires re-audit of the calculation engine before deployment. **Do not auto-update tax rates from any external source.**

#### BHUMI ATR/BPN (Wajar Tanah only — delay to v3)

| Item | Detail |
|---|---|
| **Access URL** | https://bhumi.atrbpn.go.id/ |
| **API status** | No documented public bulk API. Interactive map only. |
| **Operational reality** | Manual NJOP lookup per parcel query is feasible for low-volume validation but cannot power automated mass benchmarks. |
| **Day 1 availability** | No. Exclude from v1 and v2. |
| **Path to integration** | Formal MoU with ATR/BPN required. Initiate by Month 6 if Wajar Tanah is on roadmap. |

### 2.2 Layer 2 — Licensed Proprietary Survey Data

**Recommendation: License one survey before Wajar Gaji launches. This is not optional.**

| Provider | Indonesian Coverage | Data Points | Cost Estimate | Lead Time | Priority |
|---|---|---|---|---|---|
| **Mercer Indonesia (PT Mercer)** | 500+ companies, 30,000+ positions, Jakarta + 5 major cities | Job grade × city × industry | IDR 80–150M/year | 4–8 weeks negotiation | **#1 — Most comprehensive** |
| **Korn Ferry Indonesia** | 400+ companies, 25,000+ positions | Similar to Mercer | IDR 60–120M/year | 3–6 weeks | **#2 — Competitive price** |
| **Willis Towers Watson (WTW)** | 300+ companies | HR + benefits data | IDR 70–130M/year | 4–8 weeks | #3 |
| **EY Hay Group** | 250+ companies | Job evaluation-linked | IDR 70–130M/year | 6–10 weeks | #4 |

**Can you launch Wajar Gaji without licensed data?** Technically yes — using BPS Sakernas + crowdsource seed. But the verdict quality for anything beyond "Operator di Jawa" will be unreliable for at least 12 months of crowdsource accumulation. The licensed survey costs IDR 60–80M and immediately unlocks credible verdicts for the top 200 job titles in 6 major cities. **At seed funding, this is the first IDR 80M check to write.**

**Negotiation approach:** Propose a co-marketing deal — cekwajar.id credits Mercer/KF as "data partner" on all benchmark pages, Mercer/KF gets marketing exposure to a platform targeting 140M formal workers. This may reduce licensing cost to IDR 30–60M in exchange for co-branding.

**Without licensed data at launch:** Model Wajar Gaji as "Province Benchmark Mode" — explicitly tell users: "Data berdasarkan rata-rata provinsi BPS. Untuk akurasi lebih tinggi berdasarkan kota dan jabatan spesifik, kontribusi data gaji Anda." This is honest and sets the right expectation.

### 2.3 Layer 3 — Crowdsourced Data (Flywheel Strategy)

**Cold-Start Problem and Solution**

The fundamental issue: users submit salary data in exchange for seeing better benchmarks, but better benchmarks require submitted data they don't yet have. The cold-start must be solved artificially.

**Phase 0 — Pre-launch seeding (Month -2 to 0, ~200 submissions):**
- Recruit 200 beta testers from: tech LinkedIn groups, r/indonesia Reddit, Telegram finance communities, founder's personal network
- Offer: 6 months free Pro access in exchange for verified salary submission
- Target: 50 submissions each across 4 job categories: Software Engineer (Jakarta), Teacher (3+ provinces), Nurse (3+ provinces), Marketing/Sales (Jakarta + Surabaya)
- Verify via payslip upload — this seeds both Wajar Gaji AND Wajar Slip simultaneously

**Phase 1 — Organic growth (Month 1–6):**
- Every Wajar Slip audit auto-prompts: "Tambahkan gaji pokok Anda ke database benchmark anonim? Ini membantu sesama karyawan." (one-click consent from existing payslip data)
- Expected conversion: 30–40% of payslip users opt into salary contribution
- At 500 Wajar Slip users by Month 6: expect 150–200 salary submissions organically

**Phase 2 — Incentivized crowdsource (Month 3–9):**
- "Contribute-to-unlock" gate on Wajar Gaji: submit your salary → unlock full percentile breakdown for your category
- Social proof counter: "47 orang di Jakarta dengan posisi yang sama sudah berkontribusi"
- Limited-time unlock: salary submission = 30 days Pro access free

**K-anonymity thresholds:**

| Cell Sample Size | Action | UI Display |
|---|---|---|
| 0–9 submissions | Do not show benchmark. Show BPS province estimate only. | "Belum cukup data lokal (n<10). Menampilkan rata-rata provinsi BPS." |
| 10–29 submissions | Show range with Bayesian blend toward BPS prior | "Estimasi awal — berdasarkan 15 laporan lokal + data provinsi BPS" |
| 30–99 submissions | Show P25/P50/P75 with confidence interval | "Berdasarkan 42 laporan terverifikasi di area Anda" |
| 100+ submissions | Show full percentile distribution | "Berdasarkan 134 laporan terverifikasi" |

**Outlier handling:** Any submission > 3× IQR from the cell median is flagged for manual review. Flagged submissions are excluded from live benchmarks until reviewed. A separate `salary_outlier_review` queue is checked weekly by the founder (takes 15–30 min/week at early volumes).

**Bias mitigation:** Track submission distribution by province, job category, and seniority level. Surface "We need more data from [category]" prompts in the app. Offer double unlock value for underrepresented cells (e.g., "Anda adalah orang ke-3 yang melaporkan gaji untuk posisi ini di Medan — Anda mendapatkan 60 hari akses gratis").

### 2.4 Layer 4 — Scraped/Real-Time Market Data

| Source | Data Available | Legal Risk | Operational Approach | Day 1? |
|---|---|---|---|:---:|
| 99.co property listings | Price/sqm by area | HIGH — ToS violation, UU ITE Pasal 30 risk | Do not scrape commercially. Seek formal partnership. | ❌ |
| Rumah123 property listings | Same | HIGH — same ToS risk | Same | ❌ |
| OLX Properti | Listing prices (less curated) | HIGH | Same | ❌ |
| LinkedIn Jobs | Salary ranges in job ads | MEDIUM — only public job post data | Extract only explicitly posted salary ranges (e.g., "Gaji: 8-12 juta") from public postings. Never profile data. Rate limit aggressively. | ⚠️ v2 only |
| Glassdoor Indonesia | Salary reports | HIGH — ToS explicit prohibition | Do not scrape | ❌ |
| Numbeo Indonesia | Cost of living indices | LOW — user-generated, permissive ToS | API available (USD 149/month for commercial use) — use for Wajar Hidup and Wajar Kabur | ✅ v3 |
| World Bank Open Data | PPP conversion factors | LOW — CC-BY 4.0 | Direct API access | ✅ v4 |
| Google Maps API | Business categories, neighborhood | LOW — standard API pricing | Use for city-level enrichment | ✅ within paid tier |

**Property listing scraping — final call:** Do not build a property scraper for v1, v2, or v3. The legal risk under UU ITE Pasal 30 and the maintenance burden (anti-bot systems on Rumah123/99.co are enterprise-grade) are not justified for a solo founder. The correct path is a formal data partnership negotiated after the platform reaches 5,000+ MAU and has credibility to bring to the table. Wajar Tanah launches on crowdsourced transaction data only until that partnership exists.

### 2.5 Data Source Summary Table

| Source | Day 1 Available | Refresh Cadence | Legal Risk | Fallback | Monthly Cost |
|---|:---:|---|---|---|---|
| BPS Sakernas (province × occupation) | ✅ | Annual | LOW-MED (cite clearly) | Static JSON cache | IDR 0 |
| Kemnaker UMK/UMR (all 514 cities) | ✅ | Annual (Dec–Jan) | NONE | Previous year + adjustment | IDR 0 |
| BPJS rate tables (6 components) | ✅ | Regulatory changes | NONE | Hardcoded with manual update | IDR 0 |
| PMK 168/2023 TER tables | ✅ | PMK amendments | NONE | Version-controlled in DB | IDR 0 |
| Mercer/Korn Ferry survey | ❌ (pre-Wajar Gaji) | Annual | LOW (licensed) | BPS province estimate | IDR 6–12.5M/mo |
| Crowdsourced salary | ❌ (starts Month 1) | Real-time | LOW (consented) | BPS + licensed | IDR 0 |
| Property listings (99.co) | ❌ | N/A | HIGH | N/A | Do not use |
| Numbeo (cost of living) | ❌ (v3) | Monthly | LOW | BPS CPI | USD ~149/mo |
| World Bank PPP | ❌ (v4) | Annual | NONE (CC-BY 4.0) | OECD PPP | IDR 0 |
| Google Cloud Vision OCR | ✅ | Real-time API | LOW | Amazon Textract | ~USD 1.5/1000 docs |
| Amazon Textract (fallback) | ✅ | Real-time API | LOW | Manual form | ~USD 1.5/1000 docs |

---

## 3. BENCHMARK METHODOLOGY

### 3.1 Salary Percentile Calculation (Wajar Gaji)

**When crowdsourced data exists (n ≥ 30 for cell):**

```
P25 = 25th percentile of verified salary submissions in cell
P50 = median of verified salary submissions in cell
P75 = 75th percentile of verified salary submissions in cell

Cell definition = Province × Job Category (L2) × Seniority Band (Junior/Mid/Senior)
```

**When crowdsourced data is thin (10 ≤ n < 30) — Bayesian smoothing:**

```
Blended_P50 = (n / (n + k)) × Sample_P50 + (k / (n + k)) × Prior_P50

where:
  n = number of local verified submissions
  k = smoothing weight = 15 (tuned to collapse toward prior at n < 15)
  Prior_P50 = BPS province × occupation group average wage (or licensed survey if available)
  
Confidence_Score = n / (n + k) × 100  → shown as percentage in UI
```

**When data is absent (n < 10):**
- Show BPS province estimate only
- Label clearly as "Rata-rata provinsi BPS — belum cukup data lokal"
- Do not show percentile bands
- Prompt contribution

**Outlier detection before inclusion in cell:**
```
Lower fence = Q1 - 1.5 × IQR
Upper fence = Q3 + 1.5 × IQR

Extreme outlier = Q1 - 3.0 × IQR OR Q3 + 3.0 × IQR → exclude, flag for review
Standard outlier = within 1.5–3.0 IQR → include in calculation but reduce weight to 0.5
```

For cells with n < 30, also apply MAD (Median Absolute Deviation) check:
```
MAD_threshold = median ± 2.5 × MAD
```

### 3.2 Confidence Score and UI Display

| n (local submissions) | Confidence Score | Badge | UI Verdict Format |
|---|---|---|---|
| ≥ 100 | 90–100% | 🟢 Terverifikasi | "Gaji Anda berada di persentil ke-[X] dari [n] laporan terverifikasi" |
| 30–99 | 70–89% | 🟡 Cukup Data | "Estimasi berdasarkan [n] laporan lokal + data BPS" |
| 10–29 | 40–69% | 🟠 Data Terbatas | "Estimasi awal — data lokal masih terbatas ([n] laporan)" |
| < 10 | < 40% | ⚪ Tidak Cukup | "Belum cukup data untuk area dan posisi ini. Tampil rata-rata provinsi BPS." |

### 3.3 Verdict Classification

| Position in Distribution | Verdict Label | Bahasa Indonesia | Action Triggered |
|---|---|---|---|
| Below P10 | Di Bawah Pasar Signifikan | "Gaji Anda jauh di bawah rata-rata pasar untuk posisi yang sama" | Strong upgrade prompt + negotiation script (paid) |
| P10–P25 | Di Bawah Pasar | "Gaji Anda di bawah rata-rata pasar" | Moderate upgrade prompt |
| P25–P75 | Dalam Rentang Pasar | "Gaji Anda berada dalam rentang wajar untuk posisi ini" | Neutral + retain message |
| P75–P90 | Di Atas Pasar | "Gaji Anda di atas rata-rata pasar" | Positive reinforcement |
| Above P90 | Di Atas Pasar Signifikan | "Gaji Anda termasuk yang tertinggi untuk posisi ini" | Premium brand signal |
| Below UMK | Tidak Wajar (Hukum) | "Gaji Anda di bawah UMK [kota]. Ini melanggar hukum ketenagakerjaan Indonesia." | Urgent action prompt + Wajar Slip upgrade |

**Important — legal language constraint (from vc_evaluation_cekwajar.md Red Flag 10):** Never use binary "WAJAR/TIDAK WAJAR" as a standalone label. Always follow with a probabilistic framing: "berdasarkan data yang tersedia" and include confidence score. The below-UMK verdict is the only truly binary determination (it is a legal fact, not an estimate).

### 3.4 Geographic Segmentation Rules

| Query Type | Minimum Cell Size Required | Fallback Granularity |
|---|---|---|
| City × Job Title × Seniority | 30 submissions | Province × Occupation Group |
| Province × Job Title × Seniority | 20 submissions | Province × Occupation Group (BPS) |
| Province × Occupation Group | BPS data (no minimum) | National average |
| National × Occupation Group | BPS data | — |

Do not create city-level cells until 30+ submissions exist for that cell. Over-segmentation with low n is worse than using a higher-level aggregate — it creates false precision.

---

## 4. WAJAR SLIP ACCURACY SYSTEM

### 4.1 OCR Pipeline Specification

**Test corpus requirement (pre-launch gate):**

Before any public launch of Wajar Slip, test OCR on a minimum 200 real Indonesian payslips across these categories:

| Category | Sample Required | Description | Expected Accuracy |
|---|---|---|---|
| Large corp PDF (digital-native) | 60 samples | Auto-generated PDF from SAP/Oracle HR systems, consistent layout | ≥ 97% field accuracy |
| SME Excel-to-PDF | 50 samples | Excel-designed payslip converted to PDF, variable layout | ≥ 92% field accuracy |
| Startup HTML payslip | 30 samples | Mekari/Gadjian-generated digital payslips | ≥ 95% field accuracy |
| Government payslip (ASN) | 20 samples | Fixed format, often printed and scanned | ≥ 88% field accuracy |
| Mobile photo of paper payslip | 40 samples | Camera capture, variable lighting, rotation, blur | ≥ 75% field accuracy |

**Critical fields to validate accuracy on (all must be extracted correctly):**

1. Gaji Pokok (base salary) — P0
2. Total tunjangan (allowances, can be multi-line) — P0
3. BPJS Ketenagakerjaan JHT (employee portion) — P0
4. BPJS Ketenagakerjaan JP (employee portion) — P0
5. BPJS Kesehatan (employee portion) — P0
6. PPh21 amount (actual deducted) — P0
7. Gaji bersih / take-home pay — P0
8. Period (month/year) — P1
9. Company name — P2

**Accuracy thresholds:**
- P0 fields on digital PDFs: ≥ 92% per-field accuracy required. Below 90% = delay launch, fix extraction logic.
- P0 fields on photos: ≥ 75% accuracy. Below 70% = disable photo upload at launch, PDF-only.
- If any P0 field is below threshold: trigger manual entry fallback, never show a verdict based on unconfirmed OCR.

**OCR engine selection decision tree:**

1. First attempt: Google Cloud Vision Document AI (superior on tables and forms)
2. If confidence < 80% on any P0 field: re-run with Amazon Textract AnalyzeDocument (forms mode)
3. If Textract confidence also < 80%: trigger guided manual entry form
4. Manual entry form: pre-populate detected fields, allow user to correct each one individually

**Confidence threshold implementation:**

```typescript
const OCR_CONFIDENCE_THRESHOLDS = {
  AUTO_ACCEPT: 0.92,    // Accept without review
  SOFT_CHECK: 0.80,     // Show extracted value, ask user to confirm
  MANUAL_REQUIRED: 0.70 // Block verdict, require manual entry
};
```

### 4.2 PPh21/BPJS Edge Cases — Complete Test Matrix

This matrix must be validated by a licensed tax consultant (PKP) before launch:

| Test Case | PTKP | Salary (IDR) | Expected PPh21 | Expected BPJS JHT | Notes |
|---|---|---|---|---|---|
| TC-01: TK/0, mid-level salary | TK/0 (IDR 54M/year) | 8,000,000 | TER: ~IDR 0 (under threshold) | IDR 160,000 | Below taxable threshold test |
| TC-02: K/0, typical worker | K/0 (IDR 58.5M/year) | 10,000,000 | TER: ~IDR 112,500/month | IDR 200,000 | Most common case |
| TC-03: K/1, higher salary | K/1 (IDR 63M/year) | 15,000,000 | TER: ~IDR 325,000/month | IDR 300,000 | Reference case from block_03 |
| TC-04: K/3, high salary | K/3 (IDR 72M/year) | 25,000,000 | Progressive calc | IDR 500,000 | JP cap may apply |
| TC-05: Above JP cap | TK/0 | 10,000,000 | Standard | IDR 95,600 (capped at IDR 9,559,600 base) | JP employer/employee cap test |
| TC-06: Above Kesehatan cap | K/1 | 20,000,000 | Standard | Kes: IDR 200,000 (capped at IDR 12M base) | BPJS Kesehatan cap test |
| TC-07: Below UMK | TK/0 | 2,500,000 | IDR 0 | IDR 50,000 | UMK violation flag test |
| TC-08: December true-up | K/0 | 10,000,000 | ~IDR 1,350,000 (accumulated catch-up) | Normal | TER vs progressive reconciliation — highest error risk |
| TC-09: Annual bonus month | TK/0 | 30,000,000 (inc THR) | Higher bracket | Normal | THR/bonus annualization test |
| TC-10: JKK class mismatch | K/0, office | 10,000,000 | Standard | JKK: 0.24% (class I office) | Employer JKK by risk class |
| TC-11: Missing BPJS entirely | TK/0 | 8,000,000 | Standard | IDR 0 detected | Violation detection: no BPJS |
| TC-12: BPJS underpaid | K/0 | 10,000,000 | Standard | IDR 100,000 instead of 200,000 | Violation: partial BPJS |
| TC-13: PPh21 missing | K/1 | 15,000,000 | IDR 0 on slip instead of IDR 325K | Normal BPJS | Violation: no tax withheld |
| TC-14: Freelance/contract | TK/0, contract | 12,000,000 | PPh21 Pasal 21 different rate | No BPJS employer contribution | Employment type edge case |
| TC-15: Part-time | TK/0, 3 days/week | 4,500,000 | Prorated | Prorated BPJS | Prorated calculation test |

**Audit process:** These 15 test cases (plus 5 additional edge cases identified by the auditing tax consultant) must produce zero errors before any public user submits a payslip. Estimated audit cost: IDR 15,000,000–25,000,000 (one-time). Annual re-audit recommended if PMK changes: IDR 8,000,000–15,000,000.

### 4.3 Violation Detection — 7 Categories

| Code | Violation | Detection Logic | Message (Bahasa Indonesia) | Severity |
|---|---|---|---|---|
| V01 | BPJS JHT tidak dipotong | Extracted JHT = 0 AND gaji > 0 | "BPJS JHT tidak ditemukan pada slip Anda. Potongan 2% dari gaji pokok wajib dilakukan oleh perusahaan." | CRITICAL |
| V02 | BPJS underpaid | Extracted JHT < (0.02 × gaji_pokok × 0.95) | "BPJS JHT yang dipotong (IDR X) lebih rendah dari yang seharusnya (IDR Y). Selisih: IDR Z/bulan." | HIGH |
| V03 | PPh21 tidak dipotong | Extracted PPh21 = 0 AND expected PPh21 > 50,000 | "PPh21 tidak ditemukan pada slip Anda, padahal seharusnya dipotong IDR X berdasarkan PTKP dan gaji Anda." | HIGH |
| V04 | PPh21 kurang dipotong | abs(extracted_PPh21 - expected_PPh21) > 50,000 | "PPh21 yang dipotong berbeda IDR X dari perhitungan kami. Ini bisa menyebabkan kekurangan bayar pajak di akhir tahun." | MED |
| V05 | BPJS Kesehatan tidak ada | Extracted Kes = 0 AND gaji > 0 | "BPJS Kesehatan tidak ditemukan. Potongan 1% dari gaji (maks. IDR 120,000) wajib dilakukan." | HIGH |
| V06 | Gaji di bawah UMK | Gaji pokok < UMK kota | "Gaji pokok Anda (IDR X) di bawah UMK [kota] (IDR Y). Ini tidak sesuai dengan Peraturan Menteri Ketenagakerjaan." | CRITICAL |
| V07 | BPJS JP tidak ada | Extracted JP = 0 AND gaji > 0 AND age < 56 | "BPJS JP tidak ditemukan. Potongan 1% dari gaji (maks. IDR 95,596) seharusnya ada pada slip Anda." | MED |

**Freemium gate on violations:**
- FREE: Show violation codes found (e.g., "Ditemukan 2 pelanggaran") — no amounts
- PAID (IDR 49K/month): Show exact violation amounts, month-by-month calculation, and employer's estimated liability

### 4.4 Viral Error Response Playbook

The highest-probability existential event is a viral social media post claiming cekwajar.id calculated their PPh21 incorrectly. This is not a hypothetical — it will happen. Prepare before launch.

**Tier 1 — Reported error (1–10 users, no viral):**
- Response time: within 4 hours during business hours
- Owner: Founder personally
- Action: (1) reproduce the calculation independently, (2) if error confirmed — immediately pull the relevant calculation from production, fix, re-audit test case, re-deploy; (3) issue personal apology via DM and email; (4) extend 3 months free Pro access to affected users
- Public statement: none unless it goes Tier 2

**Tier 2 — Viral post (> 1,000 views on any platform):**
- Response time: within 2 hours, any time
- Action: (1) post transparent "we are investigating" reply on the exact platform; (2) if error confirmed — pull feature from production same day; (3) publish postmortem within 48 hours explaining the calculation error, the fix, and the controls that will prevent recurrence; (4) offer free audits for all users who used the affected calculation window
- DO NOT: delete any comments, go silent, dispute the calculation publicly before it's verified

**Tier 3 — Media pickup (KompasTekno, DailySocial, etc.):**
- Engage media proactively with factual correction before the story publishes
- Statement must be drafted by the founder and reviewed by the tax consultant who performed the original audit
- Message: "Kami menemukan [specific error]. Kami telah memperbaiki dan memvalidasi ulang seluruh mesin perhitungan. Pengguna yang terdampak mendapatkan kompensasi [X]."

**Prevention — the only reliable protection:**
- Tax consultant audit before launch (non-negotiable)
- Internal "calculation smoke test" runs nightly via Supabase pg_cron against 15 test vectors (TC-01 through TC-15 above)
- Any test failure triggers automated PagerDuty/uptime alert and blocks verdict generation until resolved

---

## 5. LEGAL & COMPLIANCE OPERATIONS

### 5.1 Pre-Launch Legal Requirements

| Requirement | Status (Pre-Build) | Owner | Timeline | Cost (IDR) | Risk if Delayed |
|---|---|---|---|---|---|
| PPh21/BPJS engine tax audit by licensed PKP | ❌ Not done | Founder + contracted tax consultant | Weeks 3–6 before launch | 15M–25M | Existential if wrong calc goes viral |
| UU PDP consent flow (sensitif data: payslip, PTKP status) | ❌ Not implemented | Founder (frontend) | Week 4–6 | 0 (code only) | Kominfo enforcement action, IDR 2% revenue fine |
| Supabase region: us-east-1 → ap-southeast-1 | ❌ Not changed | Founder (1h migration) | Week 1 | 0 | Cross-border transfer violation Pasal 56 |
| Privacy Policy (Bahasa Indonesia, UU PDP-compliant) | ❌ Not drafted | Founder + lawyer | Week 4–6 | 5M–15M (lawyer review) | Pasal 29 violation |
| ToS (Bahasa Indonesia, UU PerlKons disclaimer) | ❌ Not drafted | Founder + lawyer | Week 4–6 | 3M–8M (lawyer review) | Consumer protection exposure |
| Verdict language review (not "WAJAR" as binary assertion) | ❌ Not reviewed | Indonesian consumer law attorney | Week 5–7 | 3M–5M (1-session review) | UU PerlKons No.8/1999 liability |
| PSE (Penyelenggara Sistem Elektronik) registration — Kominfo | ❌ Not filed | Founder | Weeks 2–8 (government processing) | ~IDR 0 (admin only) | Kominfo blocking order |
| Midtrans individual merchant account | ❌ Not set up | Founder (KTP + NPWP needed) | Week 1–2 | 0 (account setup) | Cannot accept payments |
| Data Retention Policy: 30-day payslip deletion schedule | ❌ Not implemented | Founder (Supabase cron) | Week 6 | 0 (code only) | UU PDP Pasal 28 violation |
| Data Subject Rights flow (deletion request, access request) | ❌ Not implemented | Founder | Week 7–8 | 0 (code only) | UU PDP Pasal 22–27 violation |

### 5.2 UU PDP Compliance Architecture

**Data classification applied to Wajar Slip:**

| Data Collected | Classification | Consent Type | Retention |
|---|---|---|---|
| Payslip file (PDF/image) | SENSITIF | Explicit, separate checkbox, cannot be bundled | Delete 30 days after upload (automated) |
| PTKP status (K/0, TK/0, etc.) | SENSITIF | Explicit, separate checkbox | Delete 90 days after last use |
| Salary amount (gaji pokok) | UMUM | Standard consent | Anonymize after 90 days, retain in benchmark pool indefinitely |
| Company name | UMUM | Standard consent | Anonymize after 90 days |
| Email / account data | UMUM | Standard consent | Retain for account life, delete on account deletion |
| Violation verdict history | UMUM | Legitimate interest | Anonymize after 24 months |
| Device ID / IP | UMUM | Legitimate interest (fraud detection) | Delete after 90 days |

**Exact consent flow for Wajar Slip:**

Step 1 — Account registration: Standard consent banner (email, analytics, usage data)

Step 2 — Before first payslip upload: Full-screen modal with TWO separate checkboxes:
```
☐ Saya menyetujui pemrosesan data gaji dan informasi pekerjaan saya (data umum) 
   untuk keperluan benchmark anonim. [Lihat kebijakan privasi]

☐ Saya memberikan persetujuan EKSPLISIT untuk pemrosesan slip gaji saya 
   (data sensitif) sesuai Pasal 20 ayat 2(a) UU No. 27/2022 tentang 
   Perlindungan Data Pribadi. Slip gaji saya akan diproses secara otomatis 
   dan dihapus permanen dalam 30 hari. [Lihat detail pemrosesan]
```

Both checkboxes must be individually clicked — no "agree to all." Neither can be pre-checked.

### 5.3 Cross-Border Transfer (Supabase Region)

**Current risk:** Supabase default region us-east-1 (Virginia, USA) creates a cross-border data transfer under UU PDP Pasal 56, requiring either: (a) an adequacy determination (US does not have one with Indonesia), or (b) a binding Data Processing Agreement (DPA) with Supabase Inc., or (c) migration to ap-southeast-1 (Singapore).

**Recommended action:** Migrate to ap-southeast-1 before any user data is collected. This takes approximately 1 hour (new project creation + schema migration + DNS update). Singapore is not in Indonesia's adequacy list either, but is the pragmatic choice — Supabase Singapore is closer to Indonesian users (latency improvement) and Singapore's PDPA is broadly considered compatible with Indonesian PDP law's principles.

**If DPA is preferred instead:** Supabase publishes a standard DPA at supabase.com/dpa. Download, complete, have reviewed by your privacy lawyer. This costs IDR 3–5M in legal review time. Still migrate to ap-southeast-1 for performance reasons.

### 5.4 OJK Boundary — Financial Advice Analysis

**Question:** Does providing PPh21 / salary benchmark / property price verdict require any OJK license?

**Analysis:**
- POJK 21/2023 (financial services regulation) covers financial advisors, investment managers, insurance advisors
- PPh21 calculation is a tax compliance check (Ministry of Finance / DGT jurisdiction — not OJK)
- BPJS compliance check is a labor compliance check (Kemnaker / BPJS jurisdiction — not OJK)
- Salary benchmarking is informational market data — not financial advice
- Property price reference is informational — not KJPP appraisal (regulated under PMK 101/2014 for formal appraisal)

**Conclusion:** No OJK license required for current tool scope as long as: (a) no investment recommendations are made, (b) no insurance recommendations are made, (c) property tool is explicitly labeled as a "referensi harga pasar" not an appraisal (penilai publik). Add this disclaimer to Wajar Tanah when it launches.

**Verdict language must include:** "Hasil ini bukan merupakan konsultasi pajak, konsultasi hukum, atau penilaian resmi. Untuk keputusan finansial penting, konsultasikan dengan konsultan pajak atau KJPP terdaftar."

### 5.5 PSE (Penyelenggara Sistem Elektronik) Registration

Under Permenkominfo 5/2020 (amended by PP 71/2019), platforms that process electronic data must register as PSE with Kominfo before operating commercially.

**Process:**
1. Complete registration form at oss.go.id (PSE section)
2. Submit: entity identity, system description, technical specification, security policy
3. Processing time: 14–30 working days
4. Cost: IDR 0 (administrative only)
5. Deadline: Before commercial launch (before first paying user)

Risk if not registered: Kominfo blocking order (as applied to Steam/Epic/PayPal in 2022). This is a real, documented enforcement mechanism.

---

## 6. SECURITY & PRIVACY OPERATIONS

### 6.1 Payslip Data Flow — Security Architecture

```
User → HTTPS Upload → Supabase Storage (encrypted at rest, ap-southeast-1)
                    ↓
              Edge Function: validate_file (type, size, malware check)
                    ↓
              Cloud OCR API call (Vision/Textract) — no raw image sent with PII context
                    ↓
              Structured field extraction → payslip_structured_data table
                    ↓
              PPh21/BPJS calculation engine (Edge Function)
                    ↓
              Verdict stored in payslip_verdicts table (no raw image reference)
                    ↓
              pg_cron: DELETE FROM payslip_uploads WHERE created_at < NOW() - INTERVAL '30 days'
```

**What is NEVER stored permanently:**
- Raw payslip image/PDF after 30 days
- Full employer name in linkable form (anonymized to industry + company size category after 90 days)
- NIK if it appears on the payslip (redact before storing structured data)

**What IS stored permanently (anonymized):**
- Extracted salary amount + BPJS + PPh21 amounts (as benchmark contribution)
- Violation codes detected (aggregate statistics)
- Province + job category (not job title, not company name)

### 6.2 RLS Policies — Critical Rules

Every table with user data must have Row Level Security enabled. The three most critical policies:

```sql
-- Users can only read their own payslip verdicts
CREATE POLICY "users_own_verdicts" ON payslip_verdicts
  FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own submissions
CREATE POLICY "users_own_submissions" ON salary_submissions
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Service role only for admin operations (never expose service key in frontend)
CREATE POLICY "admin_only_aggregate" ON benchmark_salary
  FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
```

**Critical security rule:** The Supabase `service_role` key must NEVER appear in any frontend code, environment variable exposed to the browser, or git commit. Use `anon` key only in frontend; `service_role` only in Edge Functions and server-side code.

### 6.3 Rate Limiting — 3 Layers

| Layer | Implementation | Limit | Protects |
|---|---|---|---|
| Vercel Edge Middleware | IP-based, per endpoint | 10 req/min for /api/ routes | Bot scraping, DDoS |
| Supabase RLS + custom function | Auth user per tool | 5 verdict queries/month (free), 50/month (paid) | Free tier abuse |
| OCR API rate limit | Per API key, tracked in Redis/KV | 100 OCR calls/hour (initial limit) | OCR cost runaway |

### 6.4 Breach Response Playbook

Even one leaked payslip is an existential event. Pre-build response protocol:

**Detection:** Daily automated check that no payslip files older than 30 days exist in Supabase Storage (pg_cron alert). Supabase Vault audit logs monitored weekly.

**If breach detected:**
1. Within 1 hour: Isolate affected storage bucket (revoke all access tokens for that bucket)
2. Within 2 hours: Assess scope — how many payslips, what data exposed, which users
3. Within 24 hours: Notify affected users individually via email (UU PDP Pasal 46 requires notification "tanpa penundaan yang tidak wajar")
4. Within 3 days: File incident report with Kominfo BSSN (Pasal 46 requirement for high-risk personal data breaches)
5. Public disclosure: Proactive, factual statement within 48 hours

**Prevention first:**
- OCR API calls use temporary signed URLs, not permanent storage paths
- Raw payslip files stored in a private Supabase Storage bucket with no public access policy
- 30-day deletion is automated AND manually verified weekly by founder

### 6.5 Pen Test Scope (Pre-Launch)

Engage an Indonesian security firm (e.g., CyberTeam, Elsam, or Telkom Sigma CERT) for a pre-launch pen test covering:
- SQL injection on all form inputs
- RLS bypass attempts on payslip_verdicts and salary_submissions tables
- Authentication bypass (Supabase auth token manipulation)
- File upload malware injection
- OCR API key exposure scan
- Midtrans webhook spoofing test
- CORS misconfiguration check

Estimated cost: IDR 15M–30M. Timeline: 1 week. This is recommended but not blocking for soft launch — complete before scaling past 500 users.

---

## 7. PAYMENT & REVENUE OPERATIONS

### 7.1 Midtrans Setup Timeline

| Step | Action | Timeline | Cost |
|---|---|---|---|
| Account registration | Create merchant account at merchant.midtrans.com | Day 1–2 | IDR 0 |
| Passport verification — Individual | Upload KTP + NPWP personal | Day 3–7 (review time) | IDR 0 |
| Sandbox testing | Test webhook flows for subscription creation, payment success, failure, expiry | Days 7–14 | IDR 0 |
| Production go-live | Switch to production keys, test live IDR 1,000 transaction | Week 3 | IDR 0 |
| PT incorporation (later) | Begin process once metrics justify B2B deals | Month 4–6 | IDR 3M–8M |

**Subscription webhook events to handle:**
```typescript
// Critical webhook events
'payment.success'       → activate subscription, update users.subscription_status
'payment.failed'        → retry notification (Day 1, 3, 7), then downgrade to free
'payment.expired'       → downgrade to free, send win-back email
'subscription.cancel'   → log cancellation reason (required for churn analysis)
```

**Dunning sequence (payment recovery):**
- Day 0 of failure: In-app notification + email "Pembayaran gagal — coba lagi"
- Day 3: Second attempt + email with payment link
- Day 7: Final attempt + "Akun Pro Anda akan dinonaktifkan dalam 3 hari" warning
- Day 10: Downgrade to free, send win-back offer (30% off 3 months)

### 7.2 Pricing Test Matrix

**Single-tier launch (v1 recommendation): IDR 49K/month Pro only**

Rationale: Testing conversion with one price point generates cleaner signal. After 200+ paid subscribers, A/B test adding IDR 29K Lite tier to see if it expands the base (good) or just downgrades existing users (bad).

**Month 4+ pricing evolution test:**

| Test | Hypothesis | Success Metric |
|---|---|---|
| Add IDR 29K Lite tier | Increases total conversion by 50%+ | New paid users from Lite > downgrade of existing Pro |
| Add IDR 99K Premium tier | 15% of Pro users upgrade | Revenue per user +10% minimum |
| Annual plan (IDR 499K = 2 months free) | Reduces monthly churn by 30% | Annual plan take rate ≥ 20% |
| Pay-per-report: IDR 15K/audit | Higher revenue per user than subscription? | Revenue/user > IDR 49K at any usage level |

**Pay-per-report vs subscription economics:**
- Power users (3+ audits/month): subscription wins
- Casual users (1 audit/quarter): pay-per-report wins
- Best strategy: offer both, let users self-select. Supabase handles this — no credit/token system needed, just two separate product_id variants in Midtrans.

### 7.3 Conversion Funnel Targets

| Stage | Free | Paid | Notes |
|---|---|---|---|
| Landing page → Sign up | 15–25% | N/A | Target with strong CTA ("Cek payslip Anda gratis sekarang") |
| Sign up → First audit | 50–65% | N/A | Reduce friction: no credit card, no email verification required first |
| First audit → Gate hit | 75–85% | N/A | Most users will hit the paid gate (violation amounts are hidden) |
| Gate hit → Payment page | 8–15% | N/A | Lower for generic prompt, higher for "you specifically have IDR X missing" |
| Payment page → Paid | 35–55% | ~2–5% overall | Strong at this stage because intent is high |
| Month 1 → Month 3 retention | — | 70–80% | Churn starts if no new payslip to check |
| Month 3 → Month 6 retention | — | 55–65% | Multi-tool users retain better — Wajar Gaji integration helps |

**Realistic Month 12 targets (base case):**
- MAU: 8,000–12,000 (not 50,000 — see Section 12)
- Paying subscribers: 160–360 (2% of 8K–12K MAU at low-end; 3% at high-end)
- MRR: IDR 7.8M–17.6M (160–360 × IDR 49K)
- B2B: IDR 0–3M (discovery calls only, no closed deals expected)

### 7.4 Tier Economics Table

| Scenario | MAU | Conversion | Subscribers | ARPU | MRR | CAC | LTV (10mo) | LTV:CAC |
|---|---|---|---|---|---|---|---|---|
| Pessimistic | 5,000 | 1.0% | 50 | IDR 49K | IDR 2.45M | IDR 120K | IDR 490K | 4.1x |
| Base Case | 10,000 | 2.0% | 200 | IDR 49K | IDR 9.8M | IDR 85K | IDR 490K | 5.8x |
| Optimistic | 20,000 | 3.0% | 600 | IDR 65K (mixed tiers) | IDR 39M | IDR 65K | IDR 650K | 10x |

**Indonesian reality adjustment:** The financial model in block_09 uses 2% conversion rate benchmarked against international SaaS. Indonesian B2C freemium data tools historically convert at 0.5–1.5%. The Base Case above uses 2.0% because Wajar Slip's gate moment ("you have IDR X missing from your BPJS") is unusually high-intent. If conversion is running at <1.0% by Month 3, it indicates the gate message is not compelling enough — A/B test the paywall copy before adjusting the underlying business model.

---

## 8. GTM CHANNEL MODEL

### 8.1 TikTok Dependency Risk Assessment

**Current plan reliance on TikTok: ~60% of all projected MAU acquisition**

This is dangerous. TikTok is a distribution channel over which the founder has zero control. Documented risks:
- Algorithm changes can reduce organic reach by 50–70% overnight (documented in creator communities Q3 2024)
- Indonesian government has previously considered TikTok restrictions (2023 TikTok Shop ban as precursor)
- Individual creator accounts can be shadowbanned for financial content (TikTok's "money content" category is filtered)
- The "kabur aja dulu" content category may attract platform moderation if the government flags emigration-adjacent content

**If TikTok reach drops 50%: what happens?**
- Base Case MAU acquisition drops from 10,000 to ~6,000 by Month 12
- CAC increases from IDR 85K to IDR 130K+ (organic is replaced by paid)
- Break-even pushed from Month 18–20 to Month 22–26

### 8.2 Multi-Channel Matrix

| Channel | CAC (realistic) | Conversion (free→paid) | Retention D30 | Month 6 MAU Target | Notes |
|---|---|---|---|---|---|
| TikTok organic | IDR 60–120K | 2.0–3.0% (high-intent content) | 25–35% | 2,000–4,000 | Primary launch channel. 3–5 videos/week |
| Google SEO | IDR 30–80K | 1.5–2.5% (search intent = high) | 35–45% | 500–1,500 | Compounds from Month 4. Long-term highest ROI |
| WhatsApp / Telegram communities | IDR 10–30K | 3.0–5.0% (peer referral) | 40–55% | 200–600 | Finance communities: @uangteman, @investasi_cuan, etc. |
| Instagram Reels | IDR 80–150K | 1.0–1.5% (lower intent) | 20–30% | 300–800 | Repurpose TikTok content. Not primary. |
| YouTube Shorts | IDR 50–100K | 1.5–2.5% (search crossover) | 30–40% | 200–500 | Repurpose TikTok content + SEO value |
| Reddit r/indonesia | IDR 5–20K | 4.0–7.0% (very high intent) | 45–60% | 100–300 | "Gaji gue wajar nggak sih?" posts perform very well |
| Paid Instagram/Google Ads | IDR 150–350K | 0.8–1.5% | 20–25% | Only after Month 6 | Not economical until conversion rate is established |
| Word of mouth / referral | IDR 0 | 3.0–5.0% | 55–70% | 100–500 | Share cards are the primary WoM driver |

**TikTok fallback plan:** If TikTok reach drops >50% in any 4-week period, activate:
1. Double SEO content production (1 landing page per keyword cluster instead of 1 per month)
2. Intensify WhatsApp/Telegram seeding (target 10 relevant communities per week)
3. Introduce referral program: "Ajak teman, dapat 1 bulan gratis" — activates WoM channel mechanically

### 8.3 Content Cadence (Solo Founder Sustainable)

| Format | Frequency | Time Investment | Batch Strategy |
|---|---|---|---|
| TikTok (talking head + screen recording) | 3–4 per week | 2–3 hours/video amortized | Film 8–10 videos in one day per week |
| Instagram Reels (repurposed TikTok) | 3–4 per week | 30 min repurposing | Automated via repurpose.io or similar |
| YouTube Shorts (repurposed TikTok) | 2–3 per week | 15 min upload | Same batch day |
| SEO blog posts (Bahasa Indonesia) | 1–2 per week | 1–2 hours with AI assistance | ContentFactoryAgent generates draft, founder edits |
| WhatsApp / Telegram community posts | 3–5 per week | 15 min/post | Repurpose content angles |
| Email newsletter | 2x/month | 2 hours/issue | Curated from week's content |

**Total content time commitment: 12–15 hours/week.** This is the maximum sustainable for a solo technical founder who is also building the product. If content time exceeds 15 hours/week, cut product development time and delay tool launches. Distribution is more valuable than features during Month 1–6.

### 8.4 Trust vs Viral Content Balance

**Viral formats** (high reach, lower conversion, builds top of funnel):
- "Gaji lo wajar nggak?" salary reveal content
- "Boss gue nggak bayar BPJS — ini buktinya" compliance gotcha content
- "Kabur ke Singapura: worth it nggak secara finansial?" comparison content

**Trust formats** (lower reach, higher conversion, builds paying users):
- Step-by-step "cara cek slip gajimu" walkthrough
- "Gue nemuin kesalahan IDR 2 juta di payslip gue — ini caranya" real-user proof
- Explainer: "Apa itu BPJS JP dan kenapa penting?" educational content

**Optimal mix:** 60% viral + 40% trust in Month 1–3. Shift to 40% viral + 60% trust in Month 4–6 as the audience is established and conversion optimization becomes the priority.

---

## 9. B2B VALIDATION

### 9.1 Discovery Interview Script (10 Minimum Required)

**Target respondents:**
- HR Managers at companies with 50–500 employees (the buyer decision-maker)
- Recruiters at mid-size recruiting agencies (use salary data daily)
- Credit analysts at BCA Digital, Bank Jago, Akulaku (salary data for credit underwriting)
- Payroll platform product managers at Mekari, Gadjian, KaryaOne (API integration potential)

**Interview script (45 minutes):**

Part 1 — Current workflow (15 min):
1. "Seberapa sering Anda perlu data benchmark gaji untuk pekerjaan Anda sehari-hari?"
2. "Saat ini, sumber data apa yang Anda gunakan untuk menetapkan atau memvalidasi range gaji?"
3. "Seberapa puas Anda dengan akurasi dan granularitas data tersebut? Apa yang kurang?"
4. "Berapa jam per minggu yang Anda habiskan untuk salary benchmarking?"

Part 2 — Pain points (15 min):
5. "Ceritakan satu situasi di mana Anda kehilangan kandidat bagus karena masalah gaji. Apa yang terjadi?"
6. "Apakah perusahaan Anda pernah menghadapi masalah kepatuhan BPJS atau PPh21? Seberapa sering?"
7. "Jika Anda bisa punya satu data point yang sekarang tidak ada, apa itu?"

Part 3 — Product fit (15 min):
8. Show Wajar Gaji prototype: "Apakah data seperti ini berguna untuk pekerjaan Anda? Untuk apa?"
9. "Format apa yang paling berguna — API, spreadsheet export, atau dashboard?"
10. "Jika produk ini tersedia, apakah Anda punya budget untuk membelinya? Berapa range-nya?"
11. "Siapa di perusahaan Anda yang perlu approve pembelian software seperti ini?"

**Validation threshold:** 3 of 10 respondents must express purchase intent with a specific budget range AND have budget authority. If not met: B2B is not validated for Year 1. Remove from financial projections.

### 9.2 B2B API Format Requirements (Based on Expected Discovery Findings)

Based on comparable Indonesian HR tech buyer interviews (Mekari, KaryaOne public case studies), expected format requirements:

| Buyer Type | Preferred Format | Data Need | Price Sensitivity |
|---|---|---|---|
| HR Manager (SME) | Spreadsheet export / CSV | Monthly salary range by role | Medium — IDR 500K–2M/month |
| Payroll Platform (Mekari) | REST API JSON | Real-time salary lookup by job title + city | Low — willing to pay for verified data |
| Recruiter | Web dashboard | Candidate salary expectation benchmark | High — IDR 200–500K/month |
| Bank Credit Analyst | API / batch CSV | Salary verification for specific job titles | Low — willing to pay for compliance value |

**B2B API minimum design (before any B2B sale):**
```
GET /api/v1/benchmark/salary
  ?job_title=software_engineer
  &city=jakarta
  &experience_years=3
  &industry=technology

Response:
{
  "p25": 12500000,
  "p50": 16000000,
  "p75": 22000000,
  "sample_size": 47,
  "confidence": "medium",
  "data_freshness": "2026-02",
  "source": "cekwajar.id verified submissions + licensed survey data"
}
```

### 9.3 Realistic B2B Sales Cycle

| Stage | Timeline | Action Required |
|---|---|---|
| Discovery call | Month 6–8 | After 500+ Wajar Slip audits, platform credibility established |
| Pilot agreement | Month 8–11 | 3-month free pilot with 1 company, measure their usage |
| Paid contract | Month 11–15 | After pilot metrics validated |
| Reference accounts | Month 15–18 | Use first client for case study to close next 5 |

**B2B revenue should not appear in financial model until Month 12. Any projection before Month 12 is aspirational, not operational.**

---

## 10. MEASUREMENT DASHBOARD

### 10.1 Daily Metrics

| Metric | Target (Month 3) | Target (Month 6) | Target (Month 12) | Alert Threshold |
|---|---|---|---|---|
| DAU | 200 | 800 | 3,000 | <50% of target = escalate content strategy |
| MAU | 1,500 | 5,000 | 10,000 | <50% = pivot review |
| Payslip audits completed/day | 15 | 60 | 200 | <5/day after Month 2 = product friction issue |
| Audit completion rate (start → verdict) | ≥ 55% | ≥ 65% | ≥ 70% | <40% = OCR failure or UX blocking |
| Gate hit → CTA click | ≥ 20% | ≥ 25% | ≥ 30% | <10% = gate message ineffective |
| New paid subscribers/day | 1 | 3 | 8 | 0 for 7 consecutive days = alarm |
| Calculation error reports | 0 | 0 | 0 | ANY = immediate investigation |

### 10.2 Weekly Cohort Metrics

| Metric | Definition | Target |
|---|---|---|
| D1 retention | % of new users who return next day | ≥ 30% |
| D7 retention | % of new users who return in Week 1 | ≥ 20% |
| D30 retention | % of new users active in first month | ≥ 15% |
| Paid D30 retention | % of paying users still paying at Day 30 | ≥ 85% |
| Paid D90 retention | % of paying users still paying at Day 90 | ≥ 65% |
| Monthly churn (paid) | % of subscribers canceling each month | ≤ 10% (target ≤ 7%) |
| Audit-to-submission rate | % of audit users who also submit salary data | ≥ 15% |

### 10.3 Monthly KPIs

| KPI | Month 3 | Month 6 | Month 12 | Note |
|---|---|---|---|---|
| MRR | IDR 1–2M | IDR 4–8M | IDR 10–18M | Below IDR 2M at Month 6 = pivot review |
| LTV:CAC | ≥ 3:1 | ≥ 4:1 | ≥ 5:1 | Below 2:1 = unsustainable |
| Free → Paid conversion | ≥ 1.5% | ≥ 2.0% | ≥ 2.5% | Below 0.8% at Month 3 = gate redesign |
| NPS (post-verdict survey) | ≥ 30 | ≥ 40 | ≥ 50 | Below 20 at Month 3 = accuracy problem |
| Salary submissions (cumulative) | 200 | 800 | 3,000 | Below 100 at Month 3 = flywheel not working |
| OCR field accuracy (PDF) | ≥ 92% | ≥ 94% | ≥ 96% | Below 90% at any time = immediate fix |
| Tax calculation error reports | 0 | 0 | 0 | Any confirmed error = immediate hotfix + audit |

### 10.4 Kill Criteria Table (from block_10 + vc_evaluation)

| Kill Criteria | Metric | Threshold | Timeline | Decision |
|---|---|---|---|---|
| Data flywheel failure | Cumulative salary submissions | < 1,000 by Month 6 | Month 6 | Pivot: license Mercer data or narrow to payslip-only |
| PPh21 error goes viral | Confirmed wrong calculation with >10K views | 1 event | Any time | Immediate: pull feature, audit, relaunch |
| UU PDP enforcement | Kominfo formal notice | 1 notice | Any time | Pause, consult lawyer, remediate |
| Conversion flatline | Free → paid conversion | < 0.5% at Month 6 despite A/B testing | Month 6 | Pivot to B2B API model |
| Retention collapse | Paid D30 retention | < 50% by Month 4 | Month 4 | Fix product before acquiring more users |
| Revenue stall | MRR | < IDR 5M at Month 12 | Month 12 | Stop product investment, consider sale or wind-down |
| Founder burnout | Product development velocity | Zero commits for 3+ weeks | Any time | Hire or stop — do not zombie-operate |
| Payslip data breach | Any confirmed leak of payslip data | 1 incident | Any time | Suspend payslip feature, full security review |

---

## 11. 30-DAY LAUNCH PLAN

### Week 1 — Legal, Infrastructure, Payment (Days 1–7)

| Day | Action | Output | Owner |
|---|---|---|---|
| 1 | Migrate Supabase project to ap-southeast-1 | New project URL, all schemas migrated | Founder |
| 1–2 | Register Midtrans individual merchant account | Merchant ID (sandbox) | Founder |
| 2–3 | File PSE registration at oss.go.id | Application submitted (processing: 14–30 days) | Founder |
| 2–4 | Contact licensed tax consultant (PKP) — schedule audit | Audit appointment confirmed | Founder |
| 3–5 | Draft Privacy Policy + ToS in Bahasa Indonesia | Draft documents (before lawyer review) | Founder |
| 5–7 | Set up Google Cloud Vision API + Amazon Textract sandbox keys | OCR pipeline functional in dev | Founder |

### Week 2 — Build Core Engine (Days 8–14)

| Day | Action | Output |
|---|---|---|
| 8–10 | Build PPh21 TER calculation engine (all PTKP categories) | Calculator class passing TC-01 through TC-08 |
| 10–12 | Build BPJS 6-component engine | BPJS calculator passing all component tests |
| 12–13 | Build violation detection (7 categories) | Violation engine with Bahasa ID messages |
| 13–14 | Build manual entry fallback form | UI functional for manual field entry |

### Week 3 — OCR + Consent + Payments (Days 15–21)

| Day | Action | Output |
|---|---|---|
| 15–17 | Build OCR pipeline (Vision → Textract fallback → manual) | End-to-end PDF upload → extracted fields |
| 17–18 | Build UU PDP consent flow (dual-checkbox sensitif modal) | Consent recorded in DB before any upload |
| 18–19 | Implement 30-day auto-delete cron (Supabase pg_cron) | Verified: old payslips deleted automatically |
| 19–20 | Midtrans webhook integration (payment success/fail/expire) | Subscription status updates correctly |
| 20–21 | Build freemium gate (pass/fail free, IDR amounts paid) | Gate functional on verdict page |

### Week 4 — Tax Audit, Beta, Soft Launch (Days 22–30)

| Day | Action | Output |
|---|---|---|
| 22–24 | Tax consultant audit session (TC-01 through TC-15) | Audit report: pass/fail per test case |
| 24–25 | Fix any issues found in audit | Zero failed test cases |
| 25–27 | Recruit 100 closed beta users (Telegram/WhatsApp/personal network) | 100 completed payslip audits |
| 27–28 | Analyze beta results: OCR accuracy, calculation accuracy, gate hit rate, satisfaction survey | Beta report with issues prioritized |
| 28–29 | Fix P0 issues from beta (not P1/P2 — ship P1/P2 in v1.1) | P0 issues resolved |
| 29–30 | Soft launch: remove invite gate, post first TikTok, announce on r/indonesia | First public users |

**Pre-launch checklist before Day 29 (hard gates — do not launch if any fails):**
- [ ] Tax consultant audit: all 15 test cases passing
- [ ] UU PDP consent flow: working, both checkboxes required before upload
- [ ] 30-day deletion: verified working on test data
- [ ] Midtrans: live payment of IDR 49K successfully processed
- [ ] RLS policies: service_role key not exposed in any frontend code
- [ ] Privacy Policy + ToS: published at cekwajar.id/privasi and /syarat
- [ ] OCR accuracy: ≥ 90% on 50 PDF test payslips
- [ ] Verdict language: reviewed, no binary "WAJAR/TIDAK WAJAR" as legal assertion

---

## 12. 6-MONTH SURVIVAL MODEL

### 12.1 Revenue Scenarios (Indonesian-Adjusted)

**Adjustment from block_09 model:** The 50K MAU Month 12 target is not achievable for a solo founder without paid distribution. Realistic organic-only growth for a new Indonesian fintech tool with TikTok-first strategy: 5K–15K MAU by Month 12 based on:
- Gajimu Indonesia: 5 years to reach ~100K MAU with a team
- Cermati.com: 18 months to reach 20K MAU with IDR 20B seed funding
- Benchmark: solo creator financial tools in Indonesia reach 3K–8K MAU in Year 1 organically

| Scenario | Month 3 MAU | Month 6 MAU | Month 12 MAU | Month 6 MRR | Month 12 MRR | Breakeven |
|---|---|---|---|---|---|---|
| Pessimistic | 800 | 2,500 | 5,000 | IDR 1.25M (25 subs) | IDR 2.5M (50 subs) | Never without B2B |
| Realistic | 2,000 | 6,000 | 12,000 | IDR 4.9M (100 subs) | IDR 12.25M (250 subs) | Month 20–22 |
| Optimistic | 4,000 | 12,000 | 25,000 | IDR 12.25M (250 subs) | IDR 36.75M (750 subs) | Month 12–14 |

**Monthly burn rate (solo founder, no staff):**

| Cost Item | Monthly (IDR) | Notes |
|---|---|---|
| Supabase Pro (ap-southeast-1) | 700,000 | ~USD 25/month pro plan |
| Vercel Pro | 560,000 | ~USD 20/month |
| Google Cloud Vision OCR | 280,000–2,800,000 | Variable: 200–2,000 audits/mo at USD 1.5/1000 |
| Amazon Textract (fallback) | 140,000–1,400,000 | ~30% of Vision volume |
| Midtrans fees | 2,200–4,000/transaction | 2.5–4% per payment |
| Domain + SSL | 40,000 | Annual, prorated |
| Content tools (repurpose.io etc.) | 400,000 | ~USD 15/month |
| Legal retainer (advisory) | 1,000,000–2,500,000 | Monthly lawyer on-call for regulatory questions |
| Tax consultant (annual audit) | 1,000,000–2,000,000 | Prorated monthly |
| **Total fixed + semi-variable** | **IDR 4.3M–10.5M/month** | |

**Break-even at Realistic scenario:** Month 20–22. Below IDR 10M/month burn is sustainable if founder has IDR 120M–200M personal runway or part-time consulting income. This is feasible.

### 12.2 Pivot Triggers (Concrete)

| Trigger | Metric | Threshold | When | Pivot To |
|---|---|---|---|---|
| Conversion too low | Free → Paid % | < 0.8% despite 3+ gate copy tests | Month 3 measurement | B2B API: sell data to HR companies directly |
| Flywheel stalls | Salary submissions | < 200 by Month 3 | Month 3 measurement | License Mercer data; rebuild Wajar Gaji on licensed foundation |
| OCR reliability | PDF field accuracy | < 88% after fix attempts | Month 2 | Manual-entry-only mode until OCR improved |
| Calculation error | PPh21/BPJS accuracy | Any confirmed error in production | Any time | Pull Wajar Slip, re-audit, relaunch (don't keep running wrong calculations) |
| Platform dependency | TikTok reach drop | > 50% for 4+ weeks | Any time | Double SEO + paid acquisition |

### 12.3 Hiring Timeline

| Milestone | First Hire | Role | Cost | Trigger |
|---|---|---|---|---|
| Month 4–6 | Part-time contractor | OCR fine-tuning + ML support | IDR 5–10M/month | OCR accuracy <90%, founder can't fix solo |
| Month 6–9 | Part-time content creator | TikTok/Instagram production | IDR 3–6M/month | Content becomes bottleneck to growth |
| Month 8–12 | Full-time engineer | Second tool development (Wajar Gaji) | IDR 12–18M/month | Wajar Slip release gates met, need velocity |
| Month 12–18 | B2B sales / BD | Enterprise pipeline | IDR 10–15M/month + commission | First B2B discovery calls converted, need dedicated sales |

**Fundraising timeline:**
- Month 3: Pitch angels if 50+ paying subscribers achieved. Target: IDR 300–700M at IDR 3–5B valuation (10–15% equity). Use of funds: Mercer/KF data license + legal + first content contractor.
- Month 9–12: Seed round if 500+ subscribers + 1 B2B LOI. Target: IDR 2–5B. Use: team + B2B sales + Wajar Gaji full launch.
- No round: If Month 12 MRR is ≥ IDR 15M, bootstrap to profitability is viable without external capital.

---

## The Single Most Important Decision Before Building Is:

**Whether to launch with a licensed salary survey dataset for Wajar Gaji, or to acknowledge that Wajar Slip alone is the entire v1 product and the salary benchmark will not launch until it can be trusted.**

This decision determines the scope of everything — legal exposure, data infrastructure, investor story, and whether users trust the platform on Day 1 or feel misled by provincial-average data presented as job-title benchmarks. The correct answer is Wajar Slip alone, built to an accuracy standard that can be externally audited and publicly defended, because one trusted tool with 50 paying users is worth more than five mediocre tools with zero.

---

*Sources: vc_evaluation_cekwajar.md (Section B red flags 1,2,3,4,5,7,10; Section D MVP scope; Section E criteria), block_01_verdict_algorithm.md (Bayesian smoothing, percentile formulas, confidence scoring), block_02_database_schema.md (RLS policies, k-anonymity function), block_03_pph21_bpjs_engine.md (TER vs progressive logic, BPJS component rates, test cases), block_04_legal_compliance.md (UU PDP data classification, consent text, Supabase region risk), block_05_monetization_pricing.md (tier pricing, IDR 69K mid-tier recommendation, conversion benchmarks), block_06_gtm_execution.md (30 TikTok scripts, 30-day launch timeline), block_07_technical_architecture.md (Next.js stack, Edge Functions, security architecture), block_08_competitive_intelligence.md (competitor analysis, moat assessment), block_09_financial_model.md (unit economics, CAC/LTV, 3-scenario model), block_10_premortem_kill_criteria.md (10 failure modes, kill thresholds), Pre-Build Checklist (BPS/Sakernas granularity limitation, BHUMI API status, Midtrans onboarding requirements, OCR accuracy benchmarks, crowdsource flywheel theory)*
