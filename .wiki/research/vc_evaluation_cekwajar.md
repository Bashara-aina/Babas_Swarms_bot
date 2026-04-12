# cekwajar.id — VC Partner Evaluation
**Role:** Senior VC evaluating seed investment in cekwajar.id
**Date:** April 2026
**Verdict:** Conditional — see Section F

---

## Strongest reason this company could fail

The salary benchmark product depends entirely on crowdsourced data that does not yet exist. Before critical mass (~5,000 verified submissions per province × job-group cell), the "verdicts" are statistically unreliable extrapolations from province-level BPS data that any government website already publishes for free. If the "contribute-to-unlock" flywheel stalls — which it does in 70%+ of similar platforms — the company has no proprietary data, no moat, and no product that a competitor cannot replicate in six weeks.

## Strongest reason this company could succeed

Wajar Slip is a legally defensible, technically complex, high-urgency product with no direct competitor in Indonesia. PPh21 + BPJS compliance calculation on an actual payslip is a task that 140 million formal employees need done, almost none of them can do themselves, and no existing platform delivers. The regulatory complexity (PMK 168/2023 TER method, progressive bracket reconciliation, 6 BPJS components) creates a real technical moat that compounds with every rule change. If the founder can make this tool accurate and trustworthy, it can anchor the entire platform's monetization and credibility — even before the salary database reaches statistical maturity.

---

## Section A: VC Scoring Table

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
| **Market size** | 8/10 | 140M+ formal workers + 80M+ potential property buyers in Indonesia. Realistic TAM for Wajar Gaji alone is IDR 8–15T/year in premium subscription value if 5% of formal workers pay IDR 49K/month. The property and abroad-comparison verticals add meaningful adjacency without requiring a new core infrastructure. Score is not 10/10 because Indonesian B2C SaaS willingness-to-pay at this price point is unvalidated. |
| **User pain** | 9/10 | Three documented cultural pain points with measurable intensity: (1) "Kabur aja dulu" sentiment around underpayment — viral TikTok category with 500M+ views on salary content; (2) widespread BPJS noncompliance estimated at 40%+ of formal employers; (3) opaque property pricing in secondary markets exploited by agents. The pain is real, frequent, and already driving organic search. Score is not 10/10 because willingness to act (register, upload payslip, pay) has not been tested against willingness to feel the pain. |
| **Data quality** | 4/10 | This is the most dangerous weak point in the current plan. BPS data is province × major occupation group only — not city, not job title, not seniority. The pre-build checklist confirms there is no bulk NJOP API. Crowdsourced data does not exist. Day-one salary verdicts for "Software Engineer, Jakarta, 3 years experience" will be interpolated from Jawa province × "ICT Occupation" BPS averages, which have nothing to do with Jakarta tech market salaries. The checklist itself concedes this. Until k-anonymity thresholds are reached (minimum 10 submissions per cell), no cell is statistically publishable. This is an existential gap for Wajar Gaji and Wajar Tanah on launch day. |
| **Legal safety** | 5/10 | UU PDP No.27/2022 is active. Payslip uploads classify as "data sensitif" under Pasal 4, requiring explicit consent architecture before first upload. Supabase us-east-1 creates a cross-border transfer obligation under Pasal 56 that requires a DPA and likely a data localization decision before commercial launch. Scraping property portals (99.co, Rumah123) violates their ToS and exposes the company to UU ITE Pasal 30 claim. NJOP automated scraping has no documented legal basis. The BPS terms of use are not explicit enough for commercial re-use without direct contact and written clearance. Payslip OCR at scale qualifies cekwajar.id as a data processor under UU PDP, which triggers the full regulatory stack. Score rises to 5/10 only because these risks are fixable with correct architecture — they are not inherently unresolvable. |
| **Technical feasibility** | 7/10 | Next.js + Supabase + Vercel is a sound, proven stack for this complexity level. Cloud OCR (Textract or Google Vision) for payslip parsing is architecturally sound and cost-effective at early volumes. The PPh21/BPJS calculation engine is fully implementable in deterministic Python. Edge Functions for verdict generation are appropriate and correct. Score is 7/10, not higher, because: (1) the OCR accuracy on real Indonesian payslips — which range from Excel-printed PDFs to mobile camera photos of paper slips — has not been empirically validated; (2) the property listing scraper requires continuous maintenance against anti-bot measures; (3) the Swarms multi-agent AI architecture adds operational complexity that a solo founder will struggle to maintain under real load. |
| **Monetization strength** | 5/10 | The model is theoretically coherent. Wajar Slip has the clearest willingness-to-pay — finding a hidden BPJS deduction worth IDR 500K/month justifies IDR 49K/month instantly. The 6.8x revenue uplift from hybrid subscription + pay-per-report is a directionally correct claim. However, the B2C conversion assumptions (2% free-to-paid) are benchmarked against international SaaS, not Indonesian app behavior. Indonesian freemium apps typically see 0.3–0.8% conversion in comparable fintech categories. If true conversion is 0.5%, break-even requires 3–4x more users than the Base Case, which is a fundamentally different fundraising and timeline story. The B2B licensing revenue is assumed but has zero validated pipeline. |
| **Defensibility** | 6/10 | Wajar Slip's PPh21 + BPJS engine is the strongest moat element — legally complex, annually updated, requires Indonesian labor law expertise, and creates audit-trail value that compounds. Wajar Gaji's moat is entirely dependent on crowdsourced data accumulation — without it, the moat is zero. Wajar Tanah's moat requires either an ATR/BPN partnership or a large proprietary transaction database — neither exists at MVP. The cross-tool "Wajar ecosystem" lock-in (a user with salary + property + abroad comparison data in one account) is a real but long-term (Year 2–3) moat. Score would be 8/10 if the company focused only on Wajar Slip for 12 months and built the compliance database moat first. |
| **Distribution potential** | 7/10 | TikTok-first is the right call for Gen Z Indonesian workers. The "kabur aja dulu" organic content category is real, validated, and still undercrowded with authoritative data tools. SEO around "gaji wajar", "slip gaji cek", "harga tanah" has verified search volume and low competition. The "contribute-to-unlock" viral loop — where every user who shares their salary creates a social signal — is a structurally sound distribution mechanism. Score is 7/10, not 9/10, because: (1) 30 TikTok scripts does not equal 30 viral TikToks — production quality and algorithm luck are exogenous; (2) distribution assumes high Day-7 retention, which is unvalidated for a tool-based app in this category. |
| **Execution realism** | 4/10 | Five tools, 17 AI agents, a full legal compliance stack, OCR pipeline, property scraper, crowdsource flywheel, TikTok content engine, and B2B sales — being built by one person. The checklist correctly identifies this as theoretically feasible, but the execution sequence is dangerously broad. The financial model already assumes the founder operates at near-zero cost, which means no professional legal review, no paid design, and no QA testing budget. A single PPh21 calculation error that goes viral — a non-trivial risk given the regulatory complexity of TER vs progressive reconciliation — can destroy credibility in a market where trust is the entire value proposition. The solo execution risk is the most underweighted variable in all previous analysis. |
| **Fundability** | 5/10 | Currently unfundable by institutional VCs at pre-seed above IDR 1B valuation without at least one of: (a) 500+ real payslip audits with documented user satisfaction, (b) 1,000+ unique salary submissions with 3+ province × job-group cells hitting k-anonymity, or (c) one signed B2B pilot (HR software, recruiter, or bank). Angel fundable today at IDR 300–500M for 10–15% equity if the founder can demonstrate working PPh21 engine + Wajar Slip MVP accuracy. The story is fundable. The evidence is not yet there. |

**Overall: 6/10** — Conditional interest. Revisit at 8/10 when data quality, legal compliance, and solo execution risk are addressed.

---

## Section B: Red Flags

### Red Flag 1: Day-One Salary Data Is Not Trustworthy
**Why it matters:** The product's promise is "find out if your salary is fair." On Day 1, with zero crowdsourced submissions, the benchmark for "Software Engineer in Jakarta" will be derived from BPS Jawa province × "ICT Occupation" data, which is an average across all ICT workers in a province, including entry-level IT support, government IT staff, and senior engineers. Publishing a verdict — "Your salary is BELOW MARKET" — based on this data is both misleading and legally exposing.

**Severity:** Critical. This is not a launch-day polish issue. It is a product integrity issue that could generate a viral "cekwajar.id gave me wrong salary data" post within the first week.

**Evidence to resolve it:** Minimum 1,000 verified salary submissions across the top 3 job categories in Jakarta before any real-time verdict is surfaced. Until then, verdicts should be transparently labeled "Province-Level Estimate" with confidence intervals.

**Fallback plan:** Launch Wajar Slip first (deterministic, not crowdsource-dependent). Use the payslip user base as the initial salary data seed before launching Wajar Gaji publicly.

---

### Red Flag 2: OCR Accuracy on Real Payslips Is Untested
**Why it matters:** The payslip OCR pipeline is described in architectural terms only. Indonesian payslips are not standardized. They range from: (a) professionally formatted PDFs from large corporations, (b) Excel-generated slips from SMEs with no consistent field labeling, (c) handwritten entries in some informal formal-sector cases, (d) mobile camera photos of physical paper slips, often blurry and skewed. Cloud OCR handles (a) well. Its performance on (b), (c), and (d) is unknown without empirical testing on a real sample of at least 200 diverse Indonesian payslips.

**Severity:** High. If OCR fails to extract BPJS Ketenagakerjaan correctly on 30% of slips, the compliance verdict is wrong on 30% of users — the exact users most likely to be currently underpaid and most vulnerable to a wrong verdict.

**Evidence to resolve it:** Run 200 real Indonesian payslips (sampled from different employer types: large corp, SME, startup, government) through Textract and measure field extraction accuracy for: Gaji Pokok, BPJS JHT, JP, Kesehatan, JKK, JKM, PPh21, and net take-home. Publish internal accuracy report before launch. Acceptable threshold: ≥ 92% field-level accuracy for numeric fields on PDF payslips; ≥ 80% on photo payslips with manual fallback triggered below 70%.

**Fallback plan:** If Textract accuracy is insufficient, limit Wajar Slip to PDF uploads only at launch, require guided manual-entry form for unclear fields, and delay photo payslip support to v2 after OCR fine-tuning.

---

### Red Flag 3: Property Data Has No Automated Legal Source
**Why it matters:** BHUMI ATR/BPN has no documented public bulk API. There is no programmatic access to NJOP data at scale. Wajar Tanah — as currently designed — depends on: (a) manual NJOP lookups, (b) scraped listing data from 99.co/Rumah123 (which violates their ToS), and (c) crowdsourced transaction data that does not yet exist. The entire Wajar Tanah verdict therefore rests on scraped data from sources that can send a cease-and-desist letter.

**Severity:** High. This is not a future risk — it exists from Day 1 if property listing scraping is live.

**Evidence to resolve it:** Either (a) execute a formal data partnership with one major property portal before launch, or (b) sign an MoU with ATR/BPN, or (c) launch Wajar Tanah as "user-reported only" with explicit disclaimer that all values are community-submitted and not derived from official government data.

**Fallback plan:** Drop Wajar Tanah from MVP v1 entirely. Redirect the development time to Wajar Slip OCR refinement. Reintroduce Wajar Tanah in v2 once a data partnership or crowdsource critical mass is in place. This is the conservative but correct call.

---

### Red Flag 4: PPh21 Calculation Error Carries Reputational Catastrophe Risk
**Why it matters:** The PPh21 engine is deterministic, which is good, but it is also extraordinarily complex. PMK 168/2023 (TER method) introduced a new default withholding regime with December true-up logic that even many certified tax consultants misapply. If a user shares a payslip verdict — "Your employer owes you IDR 2.3 juta in underpaid BPJS" — and the number is wrong, that single viral screenshot destroys the trust foundation of the entire platform permanently.

**Severity:** Critical. This is the highest-probability existential risk in the product, not the rarest.

**Evidence to resolve it:** Mandatory third-party audit of the PPh21/BPJS calculation engine by a licensed tax consultant (PKP / konsultan pajak terdaftar, PMK 111/2014) before launch. The audit must cover: all TER bracket categories, all PTKP combinations (TK/0 through K/I/3), non-December vs December true-up, all 6 BPJS components across all 5 job risk classes, and the "below-UMK" salary edge case. This is not optional. It is the minimum legal and reputational protection required.

**Fallback plan:** Include a mandatory disclaimer on every Wajar Slip verdict that explicitly states: "Hasil ini bukan merupakan konsultasi pajak atau hukum ketenagakerjaan. Untuk keputusan penting, konsultasikan dengan akuntan atau konsultan pajak terdaftar." Discoverability of this disclaimer in a UI audit by OJK or Kemnaker must be demonstrable — not buried in ToS.

---

### Red Flag 5: UU PDP Payslip Upload Exposes the Company on Day One
**Why it matters:** The moment a user uploads a payslip, cekwajar.id becomes a data processor under UU PDP No.27/2022 for "data pribadi yang bersifat sensitif" (salary amounts, tax ID, employer name, BPJS membership number). Pasal 20 requires consent before collection. Pasal 22 requires explicit consent for sensitive data. Pasal 46 imposes a maximum IDR 2% annual revenue fine for violations. Pasal 53 requires appointment of a Data Protection Officer for "high-risk" processing — payslip data almost certainly qualifies.

**Severity:** High. If a user files a complaint to Kominfo within the first month of operation — which is increasingly common in Indonesian digital rights activism — the company could face operational suspension before it reaches 1,000 users.

**Evidence to resolve it:** Before any payslip upload goes live: (a) complete UU PDP-compliant Privacy Policy and ToS in Bahasa Indonesia (not translated boilerplate), (b) implement explicit opt-in consent flow that names the specific data being collected, (c) choose ap-southeast-1 (Singapore) Supabase region or implement a DPA with cross-border transfer provisions, (d) establish and document data retention and deletion procedures (data subject rights under Pasal 22–27).

**Fallback plan:** If legal infrastructure is not complete before launch, launch Wajar Slip in "manual input only" mode — no file upload, user manually enters salary breakdown fields. Slower OCR adoption but zero UU PDP exposure at launch.

---

### Red Flag 6: "Contribute-to-Unlock" Flywheel Has a Cold-Start Problem That Could Be Permanent
**Why it matters:** The data acquisition strategy relies on users contributing salary data in exchange for seeing richer benchmarks. But until the benchmark is rich, there is no incentive to contribute. Glassdoor took 7 years to reach statistical validity in most US markets. Gajimu has been operating in Indonesia since ~2010 and still has thin data outside Jabodetabek × white-collar categories. The cold-start problem is not just a Month 1–3 issue — it may be permanent in secondary cities and non-white-collar job categories.

**Severity:** High. If the data flywheel stalls at 500–1,000 submissions (plausible for a solo founder without a PR event), Wajar Gaji is permanently stuck in "province-level estimate" mode. This makes it indistinguishable from a free BPS table lookup.

**Evidence to resolve it:** Before scaling Wajar Gaji, run a closed beta with at least 100 invited participants in 3 job categories (software engineer, teacher, nurse) in Jakarta. Measure: (1) submit rate (target ≥ 30% of invited users), (2) data quality (target <10% extreme outliers), (3) unlock engagement (target ≥ 50% of submitters returning within 7 days to use premium features). If these thresholds are not met in the closed beta, the flywheel mechanism must be redesigned before public launch.

**Fallback plan:** Pre-seed the database by purchasing access to Indonesian salary survey data from: (a) Mercer Indonesia, (b) Korn Ferry, or (c) EY Hay Group — all run annual Indonesian remuneration surveys that can be licensed for IDR 50–150M and cover 20,000+ job-title-level data points. This immediately creates a minimum viable benchmark while crowdsourcing grows.

---

### Red Flag 7: Solo Founder Execution Across 5 Tools Is a Timeline Delusion
**Why it matters:** The current plan involves simultaneously building: (1) a statistically credible salary benchmark engine, (2) a legally defensible payslip OCR and tax compliance checker, (3) a property valuation model, (4) a PPP-adjusted cost of living comparison engine, (5) a multi-city cost basket calculator, plus the frontend, infrastructure, content engine, crowdsource incentive system, payment integration, legal compliance stack, and TikTok content strategy. A team of 5 engineers with 18 months would struggle with this scope. One person has no realistic chance of building all 5 tools to a quality that earns user trust within 12 months.

**Severity:** Critical. Not because the founder is incapable, but because the scope-to-resource ratio is irresponsible. Spreading across 5 tools means none of them is excellent. A mediocre Wajar Gaji + mediocre Wajar Slip + mediocre Wajar Tanah is a weaker business than an excellent Wajar Slip alone.

**Evidence to resolve it:** The founder must publicly commit to a single-tool MVP strategy. Proof of focus: only one tool is live and validated before the second is started. No exceptions.

**Fallback plan:** Build Wajar Slip only for 6 months. Use revenue and data from Wajar Slip to prove the business model, then expand to Wajar Gaji as second tool. The "5 tools" positioning is a product roadmap for investor decks, not an execution plan for a solo operator.

---

### Red Flag 8: B2B Revenue Is Completely Unvalidated
**Why it matters:** The financial model includes B2B licensing as a material revenue contributor by Year 2. Assumed buyers: HR software companies (Mekari, Gadjian, KaryaOne), recruiters, and banks. No signed LOI, no discovery call documented, no pricing validated, no B2B product design complete. B2B sales in Indonesia's HR software space requires: (a) a proven, trusted data product (not a 6-month-old startup), (b) procurement cycles of 3–9 months, (c) integration APIs that the buyer can connect to their existing HR stack, (d) a dedicated salesperson. None of these conditions exist at MVP.

**Severity:** Medium. B2B revenue before Month 18 is a heroic assumption, not a plan. If the financial model breaks without B2B, the business is more fragile than it appears.

**Evidence to resolve it:** Conduct 10 discovery interviews with HR managers, recruiters, or bank credit analysts before including B2B in any financial projection. Ask specifically: (1) Would you pay for access to real-time salary benchmarks at province × job-title level? (2) What format (API, spreadsheet export, dashboard)? (3) What is your current budget for HR benchmarking tools? Minimum standard to validate B2B: at least 3 of 10 respondents express purchase intent at IDR 500K–2M/month and have budget authority.

**Fallback plan:** Remove B2B revenue from Base Case financial model entirely. Treat it as upside scenario only. If B2B is not validated by Month 12, it is not happening in Year 2.

---

### Red Flag 9: The "Wajar Kabur" Tool Creates Regulatory and Reputational Risk
**Why it matters:** Wajar Kabur tells Indonesian workers whether they'd be better off financially moving abroad. This is a politically sensitive product in a country where the government has an explicit policy around managing overseas migrant worker (TKI) flows, including through BP2MI and Kemnaker. A tool that recommends "kabur ke Singapura" for a nurse or teacher will attract political attention quickly. Additionally, the tool requires accurate PPP-adjusted cost-of-living data for 20+ countries, which is methodologically complex and highly prone to oversimplification errors that users will call out.

**Severity:** Medium. This is unlikely to result in a regulatory shutdown but very likely to generate: (a) negative press from nationalist media, (b) political commentary, (c) technical criticism when the PPP calculation is wrong for a specific country.

**Evidence to resolve it:** (1) Frame the tool entirely as financial literacy, not emigration advice — "Here's what your salary buys in Singapore vs Jakarta", not "You should leave." (2) Validate PPP methodology with an economist or reference OECD/World Bank PPP data sources explicitly. (3) Include prominent disclaimer on all Wajar Kabur outputs.

**Fallback plan:** Deprioritize Wajar Kabur to v3 or later. The reputational upside (viral content) is real, but the execution and reputational risk on a politically sensitive topic is too high for a pre-launch company with no legal buffer established yet.

---

### Red Flag 10: The Brand Name "Wajar" Creates a Legal Liability
**Why it matters:** The word "wajar" means "reasonable" or "fair" in Bahasa Indonesia. Every tool verdict — "Gaji Anda WAJAR", "Harga Tanah WAJAR", "Slip Anda TIDAK WAJAR" — carries an implicit legal assertion. In Indonesian contract and consumer protection law (UU Perlindungan Konsumen No.8/1999), issuing a misleading quality assertion about a product or service creates civil liability. If a user receives a "WAJAR" verdict on their salary, negotiates a raise rejection on those grounds, and the data later proves to be wrong, cekwajar.id has a documented liability trail. Similarly, if a property buyer pays a price cekwajar.id labeled "WAJAR" and the transaction later proves to have been significantly overpriced, the company is exposed.

**Severity:** Medium-High. The risk is not the brand name itself — it is the binary verdict language ("WAJAR" / "TIDAK WAJAR") that carries assertive authority the company cannot legally back.

**Evidence to resolve it:** Legal review of all user-facing verdict language with an Indonesian consumer law attorney before launch. Verdict language must be repositioned from assertions ("Your salary IS fair") to probabilistic statements ("Based on available data, your salary falls within the typical range for your job category and region. This is an estimate, not a legal determination.").

**Fallback plan:** Replace binary WAJAR/TIDAK WAJAR verdicts with range visualizations ("Your salary is in the 35th–55th percentile for similar roles in your province") that communicate the same information without legally assertive language. This is better UX anyway.

---

## Section C: Data Architecture Recommendation

### The Core Problem
The company needs data before it has users, but needs users before it has data. This is the classic cold-start problem for crowdsourced data businesses. The resolution requires a deliberate data seeding strategy before any crowdsourcing flywheel can work.

### Recommended Architecture: 4-Layer Data Stack

**Layer 1 — Government Anchor Data (launch-ready, free, citable)**

| Source | Data Type | Granularity | Legal Basis | Confidence |
|--------|-----------|-------------|-------------|------------|
| BPS Sakernas | Average net wages | Province × major occupation (ISCO groups 1-9) | Public statistical tables, cite clearly | Medium — representative but not job-title specific |
| Kemnaker | UMR/UMK by region | Kabupaten/kota level | Official government publication | High — legally binding floor |
| BPJS Ketenagakerjaan | Published rate schedules | National (5 components) | Official regulation (PMK 66/2023) | Deterministic — no estimation required |
| BPS CPI / Susenas | Cost of living baskets | Province level | Public statistical tables | Medium — use as deflator, not primary source |
| World Bank PPP | PPP conversion factors | Country level | World Bank Open Data License | High for macro, low for city-level comparisons |

**Layer 1 limitation:** This layer supports province × occupation salary verdicts and deterministic compliance checking (BPJS/PPh21). It cannot support city × job-title × seniority verdicts, which is what users actually want. Be transparent about this ceiling.

**Layer 2 — Licensed Proprietary Survey Data (required before Month 6)**

| Source | Cost (estimated) | Data Points | Acquisition Path |
|--------|-----------------|-------------|-----------------|
| Mercer Indonesia Annual Remuneration Survey | IDR 80–150M/year | 30,000+ job-title-level data points, 500+ companies | Direct licensing from Mercer Indonesia PT |
| Korn Ferry Indonesia Pay Survey | IDR 60–120M/year | 25,000+ positions across 400+ companies | Direct licensing from Korn Ferry Consulting |
| PricewaterhouseConsulting Salary Survey | IDR 70–130M/year | 20,000+ data points | Direct approach to PwC Indonesia |

**Verdict:** Licensing even one of these surveys before launch gives cekwajar.id immediate statistical credibility for at least the top 200 job titles in 5 major cities. This is not optional if the salary benchmark is the core product. Cost is IDR 60–150M — which is significantly cheaper than losing early user trust to inaccurate data.

**Layer 3 — Crowdsourced Data (flywheel; starts Month 1, matures Month 12–18)**

Architecture requirements for credible crowdsourced salary data:

- **k-anonymity gate:** Never publish a benchmark for a cell with fewer than 10 verified submissions. Display "Insufficient data" with invitation to contribute rather than extrapolating.
- **Verification signal:** Payslip upload for Wajar Slip users provides a self-verifying salary submission. These are 10x more credible than self-reported salary. Route Wajar Slip users into Wajar Gaji data pool with consent.
- **Bayesian smoothing:** For cells with 10–30 submissions, blend toward the Layer 1/2 prior (province × occupation estimate). Document the blend ratio. Be transparent with users.
- **Outlier handling:** Flag submissions above 3× standard deviation for manual review. Do not include in live benchmarks until reviewed.
- **Segmentation minimum for cell creation:** Do not segment beyond Province × Job Title × Seniority (3 dimensions) until a minimum 500 submissions exist for a given combination. Avoid the trap of creating 10,000 cells and having all of them below k-anonymity.

**Layer 4 — Scraped / Real-Time Market Data (secondary, legally constrained)**

| Source | Data | Risk Level | Strategy |
|--------|------|------------|----------|
| Property portals (99.co, Rumah123) | Listing prices | HIGH — ToS violation | Seek formal data partnership; do not scrape commercially |
| OLX Properti | Transaction-adjacent listings | HIGH | Same |
| LinkedIn Jobs | Salary ranges in job postings | MEDIUM — varies by ToS | Extract only publicly posted salary ranges, not profile data |
| Expatriate.com / Numbeo | Cost of living data | LOW — user-generated, permissive | Use with clear attribution and methodology disclosure |
| Google Places / Maps | Business category, address | LOW | Use Google Maps API within paid tier limits |

**Layer 4 constraint:** Do not build the business on scraped data that cannot be formalized. Any data source that requires scraping a site with a ToS restriction is infrastructure debt — it works until the day it doesn't, and the day it doesn't will be the day your most important feature breaks.

### Confidence Scoring System

Every verdict must carry an explicit confidence score surfaced in the UI:

| Confidence Level | Definition | Display |
|-----------------|------------|---------|
| Verified (85–100%) | Derived from licensed survey + ≥30 local crowdsource submissions | Green badge: "Berdasarkan data terverifikasi" |
| Estimated (60–84%) | Derived from province BPS data + Bayesian blend, ≥10 local submissions | Yellow badge: "Estimasi — data terbatas" |
| Indicative (30–59%) | Derived from province BPS data only, <10 local submissions | Orange badge: "Indikasi awal — belum cukup data lokal" |
| Unavailable (<30%) | Insufficient data for any reliable estimate | Grey: "Data belum tersedia untuk area dan posisi ini" |

Users must be able to see which confidence level applies to their verdict. This is both ethically correct and legally protective.

### Source Attribution Requirements
Every benchmark must display: (a) data source names, (b) sample size (e.g., "berdasarkan 47 laporan di provinsi ini"), (c) data recency (e.g., "diperbarui Maret 2026"), (d) methodology note (e.g., "menggunakan interpolasi dari data BPS + laporan pengguna terverifikasi"). This is non-negotiable before launch.

---

## Section D: MVP Scope

### What to Build First: Wajar Slip Only

The minimum credible MVP is Wajar Slip — the payslip compliance auditor — built as a standalone product.

**Why Wajar Slip first:**
- 100% deterministic (PPh21/BPJS calculation — no crowdsource dependency)
- Immediate, quantifiable value (user sees: "Employer owes you IDR 847,000 in underpaid JHT")
- No data cold-start problem
- Natural monetization hook (free: show violation/no violation; paid: show exact amount and itemized breakdown)
- Creates a verified salary database as a byproduct — every payslip audited seeds Wajar Gaji with k-anonymity-eligible data
- Highest legal defensibility against competition (requires deep regulatory knowledge)

**Wajar Slip MVP scope (build this, nothing else):**

| Feature | Include | Notes |
|---------|---------|-------|
| PDF payslip upload | Yes | Limit to PDF at launch; photo support in v2 after OCR validation |
| Textract / Vision OCR | Yes | With manual fallback for low-confidence fields |
| PPh21 calculation engine (all TER brackets + progressive true-up) | Yes | Audit by licensed tax consultant before launch |
| BPJS JHT, JP, Kesehatan, JKK, JKM calculation | Yes | Full 5-component engine with all employer/employee splits |
| Violation detection (7 categories) | Yes | With Bahasa Indonesia plain-language explanations |
| Free vs paid gating | Yes | Free: pass/fail; Paid: itemized breakdown + IDR amount |
| Share card generation | Yes | Vercel OG — high viral potential for TikTok |
| Midtrans individual merchant payment | Yes | IDR 29K/month Lite tier only at launch |
| UU PDP consent flow | Yes | Required before any upload |
| Data deletion (user-initiated) | Yes | Required by UU PDP Pasal 22 |

**What to delay:**

| Feature | Delay to | Reason |
|---------|----------|--------|
| Wajar Gaji (salary benchmark) | Month 7–9 | Requires licensed data seed + crowdsource flywheel |
| Wajar Tanah (property) | Month 10–12 | Requires data partnership or MoU |
| Wajar Kabur (abroad comparison) | Month 12–18 | High execution complexity + political sensitivity |
| Wajar Hidup (cost of living) | Month 6–8 | Can launch with BPS CPI data when infrastructure is ready |
| 17-agent AI architecture | Month 6+ | Operational overkill for MVP; use single well-prompted LLM call |
| B2B API / licensing | Month 12+ | No pipeline, no product design, no sales capacity yet |
| Advanced crowdsource mechanics | Month 4–6 | Launch simple salary submission form after Wajar Slip user base exists |

**What to delete:**

| Feature | Delete | Reason |
|---------|--------|--------|
| Post T-Studio Workbook content | Delete | No clear product equivalent at this stage |
| Wajar Kabur PPP engine for 20+ countries | Delete from v1 | 2–3 countries (Singapore, Malaysia, Australia) is sufficient if this tool is built at all |
| Property listing scraper | Delete from v1 | Legal risk not justified without data partnership |
| Swarms 17-agent orchestration | Delete from v1 | Build individual deterministic functions first; agents add complexity, not value, at <10K users |
| Multiple subscription tiers at launch | Simplify | Launch with 1 tier (Pro, IDR 49K/month). Add Lite and Premium in v2 after conversion data exists |

**What not to overbuild:**
- The frontend does not need animation, multiple themes, or a mobile-optimized progressive web app at launch. A clean, functional Tailwind + Next.js 15 App Router interface is sufficient.
- The AI content generation system does not need to run daily. Batch TikTok script generation once per week is sufficient.
- The database does not need 19 tables on Day 1. Start with 5 (users, payslip_uploads, payslip_verdicts, salary_submissions, payments).

**Proof required before building more:**
Before adding any second tool, the following must be true:
1. ≥ 500 payslip audits completed
2. ≥ 50 paid subscribers (not trial, not free — paying)
3. Average verdict satisfaction score ≥ 4.0/5.0 (measured by post-verdict 1-question survey)
4. Zero reported PPh21 calculation errors verified by a tax professional

---

## Section E: Go / No-Go Criteria

### Pre-Launch Gate (before any public user can access the product)

| Requirement | Threshold | Status |
|-------------|-----------|--------|
| PPh21 engine audited by licensed tax consultant | Pass/fail | Must pass |
| UU PDP consent flow implemented and reviewed | Pass/fail | Must pass |
| Supabase region set to ap-southeast-1 OR DPA executed | Pass/fail | Must pass |
| OCR accuracy test on 100+ real payslips | ≥ 90% field accuracy on PDF | Must pass |
| Midtrans individual merchant account active | Active account | Must pass |
| Verdict language reviewed by Indonesian consumer law attorney | Pass/fail | Must pass |

### Launch (soft, invite-only beta → public)

- 100 invite-only beta users with ≥ 70% completing a full payslip audit
- Average audit completion rate ≥ 60% (user starts upload → receives verdict)
- Zero critical bugs in PPh21/BPJS calculation detected by beta users
- NPS or single satisfaction question ≥ 30 (measured post-verdict)

### Raise Pre-Seed (IDR 300–700M, individual angel or family office)

- ≥ 500 payslip audits completed (organic, not incentivized)
- ≥ 50 paying subscribers (at any tier)
- ≥ 1,000 unique users who completed at least one tool interaction
- Demonstrable retention: ≥ 30% Day-30 retention for paying users
- Zero significant calculation errors in live environment
- Clean data processing agreement with legal counsel signed

### Raise Seed (IDR 2–5B, institutional pre-seed fund)

- ≥ 5,000 payslip audits completed
- ≥ 500 paying subscribers (Month 6+ cohort)
- Free-to-paid conversion ≥ 1.0% (not 2%; adjust for Indonesian market reality)
- Wajar Gaji live with ≥ 1,000 verified salary submissions, at least 3 cells hitting k-anonymity
- At least 1 B2B discovery call converted to pilot (even at IDR 0, just proof of enterprise interest)
- Licensed salary survey data from at least 1 provider (Mercer/Korn Ferry)

### Pivot Trigger

Any two of the following, measured at Month 6:
- Payslip audit completion rate < 40%
- Free-to-paid conversion < 0.3% despite A/B testing
- Average payslip OCR field accuracy < 85% (too many fallback to manual)
- No salary submissions flywheel traction (< 200 submissions in 6 months)
- PPh21 calculation credibility issue going viral (any public post with > 10K views disputing results)

If pivot: narrow to a single B2B product — provide the PPh21/BPJS engine as an embeddable API for payroll software companies (Gadjian, Mekari). Charge IDR 500–2,000 per audit at B2B volume. This avoids the consumer trust problem while leveraging the technical moat.

### Shut-Down Criteria

Any one of the following:
- Verified PPh21 calculation error results in documented user financial harm and legal action
- Kominfo issues formal notice of UU PDP violation and enforcement is threatened
- Founder is unable to maintain minimum 10 hours/week on product due to day-job obligations
- Month 12 revenue is below IDR 5M/month AND no credible path to 3x within 6 months

---

## Section F: Investor Memo

**To:** Investment Committee
**Re:** cekwajar.id Seed Evaluation — Decision Recommendation

---

**Would I fund this now?**

No. Not at institutional pre-seed terms. Conditional angel interest at IDR 300–500M for 10–15% equity, contingent on three specific items being resolved within 60 days.

This is not a negative judgment on the idea — the problem is real, large, and underserved. Wajar Slip in particular addresses a genuine, urgent, high-frequency pain for 140 million formal workers who routinely have BPJS contributions miscalculated by their employers. The technical architecture is sound. The founding thesis is correct. The product, if accurate, earns trust in a market that has almost no trusted reference point for salary and compliance data.

The problem is execution risk compounded by scope delusion.

---

**What is missing?**

Three things, in order of severity:

**1. Data credibility proof.** The salary benchmark on Day 1 will not be trustworthy for the specific queries users actually have. "Is my salary as a data analyst in Surabaya fair?" cannot be answered with BPS province × occupation data. Before launch, the founder must either license one professional salary survey (Mercer or Korn Ferry) or limit Wajar Gaji to explicit province-level data with a transparent confidence rating system. A product that misleads users on its headline promise destroys brand credibility in Week 1, and brand credibility is the entire business model for a platform named after the word "fair."

**2. Wajar Slip legal clearance.** The PPh21/BPJS calculation engine must be audited by a licensed tax consultant (PKP, per PMK 111/2014) before any payslip is processed for a real user. One viral wrong verdict — "cekwajar bilang gaji saya kena potong PPh21 IDR 2 juta lebih, ternyata salah hitung" — ends the company's trustworthiness permanently. This audit costs IDR 15–30M and should be the first check written after incorporation.

**3. Scope commitment.** The investor memo cannot say "we are building 5 tools" and be taken seriously at a seed check. Every experienced SEA investor has seen 5-tool visions fail because none of the 5 tools is excellent. The fundable version of this company is: "We are building the most accurate, legally defensible payslip compliance auditor in Indonesia. That is the product. Here are 500 users who have already used it and here is their NPS." The other 4 tools are the roadmap for after Series A.

---

**What needs to be proven first?**

In 90 days, the following is achievable by a competent solo founder:

1. Wajar Slip MVP live (PDF upload → PPh21/BPJS verdict) with tax consultant audit complete — 60 days
2. 100 beta payslip audits completed, audit accuracy validated by 3 independent test users who compare verdict against their own accountant's assessment — 75 days
3. 30 paying subscribers at IDR 49K/month — 90 days
4. UU PDP consent architecture and Privacy Policy reviewed by Indonesian data law attorney — 90 days

If these four conditions are met at Day 90, this company crosses from "interesting idea with unclear execution" to "demonstrably working product with paying users and legal clarity." That version of the company can raise IDR 500M–1B from a single informed angel or a micro-fund.

---

**What is the fastest path to a fundable company?**

1. Month 1–2: Build and internally test Wajar Slip only. Do the tax audit. Set up Midtrans individual merchant. Implement UU PDP consent flow. Deploy to ap-southeast-1 Supabase.
2. Month 2–3: Invite 100 beta users via WhatsApp groups and fintech Telegram communities. Measure OCR accuracy. Fix calculation edge cases. Do not post publicly until accuracy is validated.
3. Month 3–4: Go public on TikTok and Instagram with Wajar Slip content. First 10 paying subscribers are the proof point.
4. Month 4–5: Conduct 10 B2B discovery interviews with HR managers. License one salary survey dataset. Begin soft-launch of Wajar Gaji with province-level data + explicit confidence ratings.
5. Month 5–6: 50 paying subscribers → pitch angels with real data. Not projections. Actual paying users. Actual NPS. Actual retention rate.

This company should not be raising money on a deck. It should be raising money on a working product with 50 people who already paid for it.

---

**Final judgment:**

cekwajar.id is a fundable idea with a solvable set of pre-launch problems. The founding thesis — that Indonesia's 140 million formal workers are being systematically underinformed about their compensation rights and market position — is correct and underserved. The technical execution is more sophisticated than most consumer fintech ideas at this stage. The regulatory intelligence embedded in the compliance engine is a genuine barrier that cannot be easily replicated.

But the company is not yet a company. It is a well-researched plan with five tools that do not yet exist and a data problem that has not yet been solved. The gap between "the checklist says this is theoretically feasible" and "500 users trust this enough to pay for it" is the entire execution challenge that remains.

Fund this company when it has solved the execution problem. Not before.

**Decision: Pass at current stage. Revisit at Month 3 if Wajar Slip beta achieves ≥ 30 paying subscribers with documented zero calculation errors.**

---

*Analysis prepared based on: Pre-Build Checklist for cekwajar.id (April 2026), cekwajar.id Strategic Blueprint, Financial Model, AI Blueprint (Swarms architecture), and 10 deep-analysis prompt blocks covering verdict algorithm, database schema, PPh21/BPJS engine, legal compliance, monetization, GTM, technical architecture, competitive intelligence, financial model, and pre-mortem analysis.*
