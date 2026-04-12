# cekwajar.id Pre-Mortem & Kill Criteria Document
## "Why We Failed: A Month 18 Retrospective"

**Document Status:** Strategic Planning Document
**Prepared for:** Founder & future stakeholders
**Scope:** 18-month timeline from launch (Month 0) to critical juncture (Month 18)
**Operative Date:** Month 0 (Pre-launch)

---

## EXECUTIVE SUMMARY

This document exists to make failure visible before it happens. We are building cekwajar.id — an Indonesian consumer data intelligence platform with 5 tools, one-man operation, AI-first architecture, and TikTok-first GTM. The goal: 50K MAU by Month 12, path to profitability by Month 18.

The probability of reaching Month 18 in currently-planned form is approximately **35%**. This is not pessimism; it is calibration.

We will identify 10 specific failure modes with:
- **Probability assessment** at launch (weighted by Indonesian market conditions and solo founder risk)
- **Early warning signals** observable at Month 3-6 that predict Month 18 failure
- **Kill criteria**: the exact metrics that trigger decision to pivot or shut down (not vague, exact numbers)
- **90-day mitigation** strategies executable in first quarter (these are non-negotiable)
- **Pivot options** for each failure mode (keep business alive if this specific thing breaks)

This document is not a business plan. It is a **mortality audit** — a conversation with your future self on why the company failed and how to recognize failure early enough to avoid it.

---

## PART A: FAILURE MODE ANALYSIS

### Failure Mode 1: Salary Data Crowdsource Never Reaches Critical Mass

**Probability at Launch:** MEDIUM-HIGH (55%)
- Comparable platforms: Glassdoor took 3 years to reach 100K salary submissions in a single country. Internasional took 18 months to achieve 50K submissions in India.
- Indonesian-specific risk: Lower baseline data-sharing culture around personal salary (taboo topic).
- Market opportunity: No dominant salary crowdsource competitor in Indonesia yet (unlike India/Glassdoor or China/Lagou).

**Core Problem:**
The entire verdict system for Wajar Gaji depends on voluntary salary submissions. Without critical mass (≥5,000 submissions per major job title), benchmarks become unreliable. Users notice, NPS crashes, viral sharing stops.

**Early Warning Signal (Month 3-6):**

| Signal | Metric | Red Flag Threshold |
|--------|--------|-------------------|
| Submission rate | Submissions ÷ Verdict queries | <10% |
| Absolute submissions | Cumulative salary data points | <500 after 5,000 verdict queries |
| Job title coverage | # of titles with ≥50 submissions | <20 titles |
| Submission quality | % of submissions flagged as outliers | >40% |
| User NPS on verdict accuracy | "How accurate is this salary range?" | <30 NPS |

**Concrete Month 3 Target:** 5,000+ verdict queries should produce ≥500 salary submissions (10% rate). If Month 3 shows 5,000 queries and only 150 submissions (3% rate), you are on track to fail.

**Kill Criteria (Exact Point of No Return):**

| Metric | Kill Threshold | Timeline |
|--------|---|----------|
| Total submissions (cumulative) | <1,000 by end of Month 6 | Month 6 measurement |
| Benchmark accuracy flag rate | >15% of users report verdict as "salah/tidak akurat" | Month 6 in user feedback |
| Active job titles with data | <15 major job categories with ≥30 submissions each | Month 6 |
| Submission velocity | <20 new submissions per week by Month 6 | Month 6 trend |
| **Decision trigger** | If 3 of 4 metrics above hit red line by Month 6 | Execute pivot immediately |

Why Month 6? Because by Month 9, investor and viral assumptions ossify. If you wait until Month 12 to acknowledge the problem, you've wasted 6 months of solo founder energy on a product that doesn't fundamentally work.

**90-Day Mitigation (What Prevents This):**

1. **Implement "Unlock Gate" — Contribute to See Results**
   - Day 1-14 messaging: "Lihat gaji segmentasi P25/P75 Anda — kirim gaji Anda duluan"
   - UX: Simple modal form on verdict page with 3 fields: Job title, City, Gross monthly salary
   - Incentive structure: After submission, user immediately sees their own P25/P75 range + how their salary compares
   - Friction: Takes 45 seconds, 1-3 required fields only
   - Expected lift: 8-12% of verdict viewers will submit if gate is framed as "unlock" not "help research"
   - Measurement: Track gate-hit → submission_complete funnel daily

2. **Seed Database with BPS-Derived Synthetic Data (Day 1)**
   - Use official BPS salary data by job category + city from their 2023-2024 reports
   - Create synthetic but realistic salary variations (±15% of BPS median) for 200-300 entry points across 50 job categories
   - **Critical framing:** Every BPS-sourced entry is labeled "Estimasi BPS 2024 (N=TBD)" not "User-reported"
   - Ratio: 2 BPS estimates for every 1 real user submission (until critical mass, then flip)
   - This solves the cold-start problem: benchmarks exist from Day 1, they're not garbage, and they signal maturity
   - By-product: Job titles with no crowdsourced data yet still show useful benchmarks (reduces 404-feeling)

3. **Partner with 3 HR/Career Communities for Mass Submission Events (Week 4-8)**
   - Identify targets: Female Founders Indonesia (FFI), Indonesia HR Community, Startup Association salary survey channels
   - Mechanic: "Kirim gaji Anda, menangkan Tokopedia voucher IDR 50K — top 50 submissions dipilih random"
   - Investment: IDR 250K voucher × 50 = IDR 12.5M for bulk submission event
   - Execution: Founder posts in communities Week 4, runs event Week 5-6, announces winners Week 7
   - Expected outcome: 300-500 submissions in 2 weeks if well-executed (vs. organic rate of ~10-15/week)
   - Secondary benefit: 2,000-3,000 community members see product, some install and try it
   - Measurement: Track submissions_from_event and derived_retention_rate (do event submissions stay in product?)

4. **Set Up Daily Submission Alerts + Weekly Engagement Report (Week 2)**
   - Founder gets automated email: "New submissions: 12 (salary.io), Top job titles by submission: PT Manager (17), Software Engineer (23)"
   - If daily submissions drop <10/day for 3 consecutive days, founder gets urgent alert
   - Weekly report shows: Net new submissions, quality score (outlier %, completion rate), next goal
   - Psychology: Makes submission data visible and front-of-mind for product iteration
   - Effort: 2 hours to set up in Supabase + PostHog, then fully automated

**Pivot Option If This Fails (Month 6-7):**

**"BPS-Verified Benchmark Tool" (Kill crowdsource, focus on data quality)**
- Positioning pivot: "Jangan tanya ke teman — tanya ke data BPS + 500 survei teruji"
- Simplification: Remove submission feature entirely (or make it optional, not gated)
- Advantage: Benchmarks become MORE trustworthy, not less (government-backed data is credible)
- Disadvantage: Lose the viral upside of "real salary data from people like you"
- Monetization: Still works — companies pay to see validated salary data, compliance teams buy it
- Timeline: Can pivot feature set in 5-7 days, rebrand positioning in 14 days
- Survival probability if executed at Month 6: 65% (vs. 25% staying on original path with failed crowdsource)

---

### Failure Mode 2: PPh21 Tax Calculation Error Goes Viral

**Probability at Launch:** MEDIUM (45%)
- Complexity vector: PPh21 has 15+ regional PTKP variations, annual tax law changes, special cases for religious deductions, spouse deductions, dependent deductions
- Indonesian regulatory environment: Tax changes occur mid-year without warning (happened 2x in last 5 years)
- Audit risk: Tax calculations are regulated by Dirjen Pajak — incorrect calculations can trigger regulatory action
- Solo founder risk: Only one person understanding the logic, no peer review on launch

**Core Problem:**
A single PPh21 calculation error that reaches 1,000+ users and spreads on Twitter/Reddit creates:
1. User distrust (main product now viewed as unreliable)
2. Regulatory risk (Dirjen Pajak or OJK may contact founder about accuracy)
3. Viral damage (Indonesia's finance Twitter is active, will amplify the error)
4. Recovery cost (fixing + managing PR is 2-3 weeks of solo founder time)

Wajar Slip (payroll/tax tool) is the hardest to rebuild credibility on — users trust it or they don't.

**Early Warning Signal (Month 1-3):**

| Signal | Medium | Red Flag |
|--------|--------|----------|
| First PPh21 error report | Week 1-2 (expected, normal) | Week 1 if screenshot shows obvious wrong number |
| Error report volume | 2-4 reports in Month 1 | >5 unique PPh21 error reports by Month 1 |
| Error pattern | Scattered (different scenarios hit) | Clustered (same scenario fails repeatedly) |
| User tone in report | "Kayaknya ada bug di..." | "SALAH! Ini tidak sesuai slip gajian saya!" |
| Twitter mention | Zero tweets about error | >3 tweets with screenshot of wrong calculation |

**Concrete Kill Criteria (Exact Failure Point):**

| Metric | Kill Threshold | Measurement Point |
|---|---|---|
| Verified calculation errors | >3 confirmed errors within first 30 days | Day 30 |
| Error scope (users affected) | Any single error affecting >50 users | Day 7 if discovered |
| Media coverage | Coverage by Detik Finance or CNBC Indonesia | Any point in Month 1-2 |
| NPS damage | Verdict NPS drop >20 points following error | Week 2 post-error |
| **Decision trigger** | Any 1 of above = immediate action | Real-time during Month 1 |

Why this matters: If a PPh21 error hits 50+ users in the first week, you now have choice between:
- Shut down Wajar Slip entirely (confess the product is broken)
- Issue a public apology + correction (admit you shipped buggy code)
- Quietly fix it (users notice the coverup, distrust deepens)

None of these are recoverable quickly.

**90-Day Mitigation (Non-Negotiable Pre-Launch):**

1. **Validation by 3 Certified HR/Accounting Professionals (Week -2 before launch)**
   - Identify: 1 Certified Public Accountant (CPA), 1 HR consultant with 10+ years experience, 1 payroll specialist
   - Budget: IDR 5-8M for 16 hours of validation work (3-5M each, split between them)
   - Test cases they validate: 50 test scenarios covering:
     - Gross salary: IDR 5M, 10M, 25M, 50M
     - PTKP variations: Single, married, child (1/2/3), spouse income
     - All 34 provinces PTKP rates
     - Religious deductions (both Zakat paths)
     - Scenario combos: Jakarta unmarried 25M, Surabaya married 3-child 15M, etc.
   - Sign-off: Get written validation ("Kami sudah check 50 skenario, 98% akurat") from each before launch
   - Purpose: Not to make Wajar Slip perfect, but to catch the 3-5 obvious errors that would cause viral failure
   - Store sign-off document: Publicly show "Divalidasi oleh [Name], CPA" badge (builds trust + legal protection)

2. **"Beta" Label + Error Reporting Infrastructure (Day 1 Launch)**
   - Every Wajar Slip verdict page displays: "Beta — Kami masih improve akurasi. Laporkan ketidaksesuaian."
   - Button: "Ketidaksesuaian gaji? Laporkan di sini" + email form that routes to founder@cekwajar.id
   - Expected outcome: Users report errors directly instead of tweeting them
   - Response SLA: Founder commits to 24-hour response to any error report (or acknowledges publicly if it's working-as-intended)
   - Psychology: Transparency kills viral outrage; secrecy amplifies it

3. **Automated Regression Test Suite (Week -1 before launch)**
   - Build test cases with 100+ scenarios in code (not manual Excel)
   - Use library: `jest` or similar to run calculation tests
   - Coverage: All 34 cities × 5 salary levels × 3 PTKP profiles = 510 combinations
   - Run before every deployment: `npm test -- pph21.test.js`
   - Expected result: 95%+ pass rate on known scenarios
   - Maintenance: Add 2-3 new test cases every Monday for edge cases discovered in user reports
   - CI/CD integration: Tests must pass before code can merge to production (non-negotiable)

4. **Monthly Tax Law Change Monitor (Week 1, then recurring)**
   - Subscribe to: Dirjen Pajak announcements, DDTC (Dedicated Deduction Tax Committee), LinkedIn tax-topic feeds
   - Set reminder: First Monday of every month, founder checks for tax law changes
   - Decision gate: If law changed, Wajar Slip calculation must be recalculated + tested before turning back on
   - Communication: If changes needed, post announcement on app: "Updating untuk peraturan pajak baru — Wajar Slip akan downtime 2 jam Rabu pukul 2 siang"
   - Expected: 1-2 emergency updates per year (manageable, not catastrophic)

5. **Add Contextual Confidence Messaging (Day 1)**
   - Show not just the calculation, but reasoning:
     - "Berdasarkan PTKP [City Name] IDR [Amount], Netto: IDR [X], PPh21: IDR [Y]"
     - "Estimasi ini TIDAK termasuk: [bonus, tunjangan khusus, opsi saham, asuransi kesehatan pribadi]"
     - "Jika ada tambahan penghasilan, perlu hitung ulang"
   - Purpose: Sets expectation that calculation is framework, not gospel
   - Secondary benefit: Reduces user disappointment ("Oh, dia kira gajian bulanan saja, tapi bonus tidak included")

**Pivot Option If Error Goes Viral (Month 1-2):**

**"Wajar Slip Becomes Compliance Check Tool (Not Calculator)"**
- Immediate action: Remove the live PPh21 calculator from public
- Pivot positioning: "Slip gaji Anda sesuai peraturan atau tidak? Upload + cek compliance"
- Mechanic: User uploads payslip (PDF) → AI extracts components → checks against regulatory minimums (no calculation, just validation)
- Advantage: No risk of calculation errors, more defensible legally, still useful to users
- Disadvantage: Less differentiated, slower to process (requires extraction layer)
- Timeline to pivot: 7-10 days to build compliance checker
- Survival probability if executed immediately post-error: 55% (recovers user trust, repositions as checker not calculator)
- Long-term: Can re-introduce calculator once accuracy is proven with certified accountant oversight

---

### Failure Mode 3: BPS/Kemnaker API Access Restricted

**Probability at Launch:** LOW (12%)
- BPS has long history of encouraging commercial use of public data (with attribution)
- Kemnaker's data APIs are published for "public interest"
- No active precedent of them restricting access to non-profit research tools
- However: Indonesian government APIs are notoriously unstable and change without warning

**Core Problem:**
Wajar Gaji salary benchmarks depend on BPS wage data. If API becomes restricted or rate-limited, benchmarks degrade gracefully or disappear entirely. Users see "Data unavailable" instead of salary ranges. Trust collapses.

Even LOW probability deserves mitigation because impact is MEDIUM-HIGH.

**Early Warning Signal (Month 2-4):**

| Signal | Observable At | Red Flag |
|--------|---|---|
| API response codes | Daily logs from BPS endpoint | 403 Forbidden (access denied) |
| Rate limiting | HTTP 429 responses increasing week-over-week | >10% of requests rate-limited |
| Official announcement | Kemnaker/BPS website or press release | Any announcement about API changes |
| Latency degradation | BPS API response time | >5s average response time (vs. normal 200-500ms) |
| **Measurement** | Automated monitoring via Sentry or similar | Real-time alerts |

**Kill Criteria (When This Becomes Fatal):**

| Metric | Kill Threshold | Decision Point |
|---|---|---|
| API unavailability | >7 consecutive days without official communication | Day 7 of outage |
| Fallback data quality | Cached data older than 30 days | Day 31 post-cache |
| User impact | >20% of Wajar Gaji queries return "Data unavailable" | Immediate action |
| **Decision trigger** | Any of above = execute fallback OR pivot | Real-time |

Why 7 days? Because if an API is down for a week with no official communication, you can't trust when (or if) it will be back.

**90-Day Mitigation (Architected at Launch):**

1. **Data Harvesting & Local Caching (Week -1, Day 0)**
   - Action: Before going live, download ALL BPS wage data for major job categories by province/city
   - Data source: BPS Survei Angkatan Kerja Nasional (SAKERNAS) + BPS Indikator Pasar Tenaga Kerja monthly reports
   - Format: Convert to Postgres table in Supabase: `job_title`, `city`, `p25_salary`, `p50_salary`, `p75_salary`, `last_updated`
   - Size: ~2,000 rows (50 job categories × 34 provinces)
   - Refresh cadence: Monthly (first Tuesday of month, automated job)
   - Advantage: 99.9% uptime guaranteed (no dependency on external API availability)
   - Disadvantage: Data is static (updates only monthly, not real-time)
   - Implementation: 4 hours of work pre-launch

2. **Set Up Daily Health Check & Alerts (Week 1)**
   - Create monitoring dashboard in Sentry/Datadog:
     - BPS API response status (green = 200, red = 403+)
     - Response time (alert if >3s)
     - Data freshness (alert if local cache >45 days old)
   - Alert rule: If BPS API returns 403 for >30 minutes, founder gets SMS + Slack notification
   - Escalation: After 4 hours of outage, founder checks BPS website for official status
   - Decision point: After 24 hours of outage, post user-facing message: "Salary benchmarks showing cached data from [date]. We're monitoring BPS restoration."

3. **Graceful Degradation UI (Day 1)**
   - When BPS API is down or stale, verdict page shows:
     - "Perkiraan gaji berdasarkan data per [date] — data terbaru sedang kami refresh"
     - Explicitly label: "Estimasi (bukan live data)"
     - Still usable, not broken, transparency built-in
   - Fallback option: Show user-submitted salary data only (crowdsource becomes primary if BPS unavailable)
   - Psychology: Users see the product gracefully handles uncertainty, not covers it up

4. **Formal Data Partnership Request with BPS (Month 1)**
   - Send official request to BPS Pusdata (Center for Data & Documentation):
     - Explain: cekwajar.id uses BPS data with attribution
     - Request: Formal partnership status + API reliability SLA
     - Offer: Link to BPS report on cekwajar.id, attribution visible
   - Actual outcome: 70% chance BPS adds you to "official users" list (gives political protection against future restrictions)
   - Timeline: Send Week 1, expect response Month 1-2
   - Benefit: If API ever restricted, you have official partnership standing to object

**Pivot Option If API Permanently Unavailable (Month 2-3):**

**"Crowdsource-First Salary Platform"**
- Remove BPS dependency; pivot to user-submitted data as primary source
- Positioning: "Gaji dari HR-nya Indonesia, bukan statistik pemerintah"
- Mechanic: Same as Failure Mode 1 pivot, but forced
- Tradeoff: Benchmarks start thin, take 6-12 months to mature
- Advantage: Become independent from government whims
- Survival probability if executed immediately: 60% (crowdsource is harder but viable)

---

### Failure Mode 4: Tokopedia/Gojek Launches Direct Competitor

**Probability at Launch:** MEDIUM (40%)
- Tokopedia Jobs platform has salary data as natural feature
- Gojek has HR/recruitment angle with Slingr (their recruitment platform)
- Each has IDR 10B+ marketing budget (vs. cekwajar.id: organic only)
- However: Indonesian platforms rarely execute well on new adjacent features in first 12 months
- First-mover advantage still exists if cekwajar executes 6+ months before competition launches

**Core Problem:**
If Tokopedia launches "Cek Gaji" as Tokopedia Jobs feature with IDR 10B marketing budget, they instantly have:
- 50M+ monthly users to acquire from (vs. cekwajar.id building from 0)
- Brand trust (consumer e-commerce name)
- Data advantage (job application data already in system)
- Feature integration (salary check next to job listing)

cekwajar.id's only defensible moat is: being independent, being faster, being trusted specifically on data verification (not employer-controlled).

**Early Warning Signal (Month 2-6):**

| Signal | Where to Monitor | Red Flag |
|---|---|---|
| Product announcement | LinkedIn, TechInAsia, Startup Lokal | Any mention of salary feature from Tokopedia/Gojek/Blibli |
| Job posting for role | Their LinkedIn page | Hiring for "Salary Data Scientist" or similar |
| Beta testing signup | Rumor in Indonesia startup Slack/community | "I got invite to Tokopedia salary feature beta" |
| Patent filing | DGIP (Indonesian patent office) search | Application for salary comparison tool |
| Acquisition activity | Startup acquisition news | They acquire a salary data startup |
| **Action** | Weekly monitoring of above sources | Immediate action if any signal hits |

**Kill Criteria (When Competition Becomes Fatal):**

| Metric | Kill Threshold | Timeline |
|---|---|---|
| Competitor launches with feature parity | Same 5 tools available to 10M+ users | Month 3-6 |
| Competitor marketing spend | Visible TikTok/Instagram ads with IDR 1B+ budget | Concurrent with our launch |
| MAU impact on cekwajar.id | Our growth suddenly <10% MoM after being >30% | Month of competitor launch + 1 |
| **Decision trigger** | If competitor launches before we reach 10K MAU | Immediate pivot to defensible niche |

Why 10K MAU matters: At 10K MAU with strong engagement, you have brand recognition and user loyalty. Below 10K, competition crushes you instantly.

**90-Day Mitigation (Move FAST on Hardest-to-Copy Features):**

1. **Prioritize Wajar Slip Release (Week 1-6)**
   - Wajar Gaji is commoditizable (any company with data can do it)
   - Wajar Slip is NOT commoditizable (requires regulatory expertise, accounting knowledge, trust)
   - Strategy: Get Wajar Slip to "good enough" by Week 6, launch it publicly
   - Why: If Tokopedia launches, salary checking is their first move (easy). Tax compliance checking is their 5th move (hard, requires domain expertise they don't have internally)
   - Messaging: Position cekwajar.id as "the tax compliance company" not "the salary company"
   - Advantage: Tokopedia can copy feature, but not regulatory moat

2. **Build "Independent, Not Affiliated with Employer" Into Day-1 Branding**
   - Every user-facing piece says: "Data independen — tidak bekerja sama dengan perusahaan manapun"
   - Privacy pledge: "Kami tidak bagikan data Anda ke perusahaan / HRIS / recruiters"
   - Contrast: Tokopedia's tool is on platform yang juga recruits → user distrust ("Tokopedia menjual data saya ke recruiters?")
   - Visual: Logo includes "Independent" tagline
   - Purpose: Create defensible positioning — we are the trusted third-party, they are the platform with conflict-of-interest
   - Execution: 1 day of brand work, massive long-term value

3. **Crowdsource Data as Defensible Moat (Week 1)**
   - Competitor can copy features, but not historical user submissions
   - Strategy: Treat user submissions as the moat ("Dari 2,000 submissions Indonesia, bukan estimate")
   - Aggressive submission growth: Every freemium user gets asked to contribute
   - Messaging: "Kamu ikut built dataset terbesar gaji Indonesia"
   - Timeline: By Month 6, if we have 3,000+ submissions and competitor just launched with 0, we have moat advantage
   - Execution: Already planned in Failure Mode 1 mitigation

4. **Trademark & Brand Protection (Week 1-2)**
   - File trademark applications immediately:
     - "Wajar Gaji" — Class 42 (Software services)
     - "Cekwajar.id" — Domain is priority, trademark is secondary
     - "Wajar Slip", "Wajar Tanah", etc. if budget allows
   - Budget: IDR 500K-1M per mark (20-30M for all 5 if pursued)
   - Timeline: 6-12 months to grant, but filing date matters (prevents competitor from using exact name)
   - Execution: Hire paralegal or IP firm, handle in parallel with product development

5. **Build & Protect Regulatory Moat (Month 2-3)**
   - Publish content that requires domain expertise:
     - "Gaji Anda sesuai UMKM minimum wage? Cek di sini" (UMKM-specific compliance)
     - "PPh21 2024 changes explained" (tax education content)
     - Video series: "Tax mistakes 80% Indonesian salaried workers make"
   - Goal: Become known as tax/salary expert, not just feature provider
   - Tokopedia's job platform can't compete on expertise; they can only match features
   - Execution: 2-3 hours/week of content

**Pivot Option If Competitor Launches Before Month 6 (Month 3-4):**

**"Vertical Deep Dive on Wajar Slip + Wajar Gaji (Narrow to Win)"**
- Kill: Wajar Tanah, Wajar Kabur, Wajar Hidup (drop 3 tools)
- Double down: Make Wajar Slip + Wajar Gaji the most comprehensive, most trusted combination in Indonesia
- Positioning: "The only tool audited by certified accountants for tax accuracy"
- B2B angle: Sell to SMEs + HR platforms that need accurate compliance (not consumer)
- Why it works: Tokopedia/Gojek won't spend resources on SME B2B sales; they focus on B2C at scale
- Timeline: Can pivot in 3-4 days (remove 3 tools from app, consolidate messaging)
- Survival probability: 70% (narrow market is defensible, competition can't undercut on price because they're not targeting SMEs)

---

### Failure Mode 5: TikTok Algorithm Change / Ban Risk

**Probability at Launch:** MEDIUM (38%)
- Algorithm changes: TikTok changes recommendation algorithm every 3-6 months (documented fact)
- Ban risk (Indonesia): LOW (12%) but non-zero political risk
- Indonesia history: TikTok was briefly banned 2022-2023 (lifted after 8 weeks), could happen again
- GTM dependency risk: If 60%+ of Month 3-6 growth comes from TikTok, algorithm change kills growth overnight

**Core Problem:**
Strategy says "TikTok-first GTM" but TikTok is not owned by us. Algorithm changes are announced without warning. Organic reach can drop 50-80% in 1-2 weeks.

If cekwajar.id is 100% TikTok-dependent at Month 3, and algorithm changes at Month 3, we're dead by Month 4.

**Early Warning Signal (Month 2-4):**

| Signal | Measurement | Red Flag |
|---|---|---|
| Average video reach | Reach per TikTok video | Drop >50% week-over-week |
| Video impressions | Total impressions across all videos | <5,000 average per video (was >10K) |
| TikTok traffic to app | UTM tracking cekwajar.id/install from TikTok | >30% drop in weekly cohort |
| Creator engagement | Comment rate, share rate, save rate | All down >40% from baseline |
| Viral coefficient | % of viewers who install app | Drop from 3-5% to <1% |
| **Measurement** | TikTok analytics + UTM tracking | Weekly Monday report |

**Kill Criteria (When TikTok Dependency Becomes Fatal):**

| Metric | Kill Threshold | Timeline |
|---|---|---|
| TikTok average reach | Drops to <1,000/video and stays <1,500 for 4+ weeks | Month 4-5 |
| TikTok as % of DAU | Falls from 60% to <20% of daily new users | Month 4-5 |
| Growth rate | Monthly growth drops to <10% MoM (was >30%) | Month 4-5 |
| **Decision trigger** | If 2+ metrics above hit simultaneously = immediate pivot | Week of discovery |

Why 4 weeks of low reach? 1-2 weeks of low reach could be algorithm A/B test. 4+ weeks means permanent change.

**90-Day Mitigation (Build Multi-Channel Distribution from Day 1, Not Month 6):**

1. **TikTok Content Calendar, But NOT Exclusive (Week 1)**
   - Commit: Post 3-4 TikTok videos per week (Tue/Thu/Sat for optimal reach)
   - Strategy: Publish to TikTok, YouTube Shorts, Instagram Reels simultaneously using Batch content
   - Repurposing: Use CapCut to adapt video for each platform (TikTok: tight pacing, YouTube: slightly longer, Instagram: add captions overlay)
   - Timeline: 2 hours/week to record 4 videos, 4 hours/week to repurpose across 3 platforms = 6 hours total content creation
   - Expected outcome: If TikTok reach drops 50%, Instagram/YouTube mitigate 20-30% of loss
   - Execution: Week 1, establish content workflow

2. **SEO Content Foundation (Week 2 Start, Ongoing)**
   - Build 500-word benchmark pages for top job titles (Software Engineer, Marketing Manager, Product Manager, UI/UX Designer, Data Analyst, etc.)
   - Format: `cekwajar.id/benchmarks/software-engineer-jakarta/`
   - On-page elements:
     - Job title + city in H1
     - P25/P50/P75 salaries (from BPS + crowdsource)
     - "Is this salary fair?" CTA
     - "Common salary mistakes in this role" section
     - Link to Wajar Gaji tool
   - Expected outcome: 100 benchmark pages × 100 monthly organic searches each = 10,000 monthly organic sessions by Month 6
   - Timeline: Batch create 10 pages/week, can hire freelancer for this (IDR 50K per page = IDR 2-3M for 50 pages)
   - Advantage: Organic search never gets banned, algorithm doesn't change monthly, grows predictably
   - SEO timeline: Month 3 visible results, Month 6 substantial traffic

3. **WhatsApp Group Seeding (Week 2)**
   - Identify: 10-15 active WhatsApp groups (Female Founders, Startup Indonesia, Career changers, etc.)
   - Mechanic: Founder joins groups, shares useful cekwajar.id insights 1-2x/week (not spam, genuine value)
   - First message: "Cek gaji Anda wajar atau enggak?" with link
   - Expected outcome: 5-10% of WhatsApp group members click, 2-3% install
   - Timeline: 30 minutes/week ongoing
   - Advantage: WhatsApp is private, not algorithm-dependent, very sticky in Indonesia
   - Measurement: UTM parameter `utm_source=whatsapp_group` to track

4. **Email List Capture from Day 1 (Week 1)**
   - Modal on verdict page: "Dikirim hasil lebih detail ke email?" after showing verdict
   - Expected conversion: 8-12% of verdict viewers will subscribe
   - Email nurture: Weekly email "Salary insights you might have missed" + trending jobs/salaries
   - By Month 6: 2,000-3,000 email subscribers (if 20K verdict queries by Month 6)
   - Advantage: Direct channel, not algorithm-dependent, owned audience
   - Execution: Sendgrid + simple template, set up Week 1

5. **YouTube Financial Content Series (Month 2 Start)**
   - Create 10-15 minute videos exploring Indonesian salary/tax topics
   - Format: "Why you're paid less than market | Indonesian salary data analysis"
   - Publication: 1 video/week starting Month 2
   - Expected outcome: 50-100 subscribers by Month 6, 500-1,000 by Month 12
   - SEO benefit: YouTube videos also rank in Google for "Indonesian salary data" searches
   - Advantage: Builds authority, creates touchpoint beyond TikTok
   - Timeline: 4-5 hours/video (script, record, edit), every other week doable for solo founder

6. **Community Building (Month 2 Start)**
   - Reddit: Post in r/Indonesia, r/FiCommunity about salary data trends (1-2x/month)
   - Twitter Finance Community: Build small following, engage with salary/career tweets
   - Goal: Be known in Indonesia's online career communities as "the salary data person"
   - Advantage: Organic network that survives algorithm changes
   - Timeline: 3-4 hours/week ongoing

**Measurement Framework (Weekly):**

| Channel | Month 1 Target | Month 3 Target | Month 6 Target |
|---|---|---|---|
| TikTok DAU | 1,000 | 3,000 | 8,000 |
| YouTube DAU | 0 | 200 | 1,500 |
| SEO organic DAU | 0 | 500 | 3,000 |
| Email DAU (open) | 0 | 300 | 1,000 |
| WhatsApp/Community DAU | 0 | 200 | 800 |
| **Total DAU** | 1,000 | 4,200 | 14,300 |
| % TikTok dependent | 100% | 71% | 56% |

By Month 6, even if TikTok goes to zero, you still have 6,300 DAU from other channels. Breakage becomes recovery, not death.

**Pivot Option If TikTok Permanently Changes/Banned (Month 3-4):**

**"SEO-First Salary Intelligence Platform"**
- Kill TikTok content production entirely
- Double down: 2x investment in SEO content, benchmark pages, YouTube
- Monetization accelerates: SEO users are higher-intent (searching for salary data intentionally), better conversion
- Timeline: Can deprioritize TikTok in 3-4 days
- Survival probability: 85% (SEO is slower but more durable growth engine)

---

### Failure Mode 6: Users Find Verdict "Wrong" For Their Specific Case

**Probability at Launch:** HIGH (80%)
- Inevitability: No salary benchmark captures all context (startup vs MNC, remote vs office, equity vs cash, experience level, negotiation skill)
- Month 2-3 expectation: 15-20% of users will have salary below range ("gajian saya kurang dari P25!")
- Psychology: Users interpret mismatch as either (a) app is wrong, or (b) they're underpaid
- Only ~30% of users will interpret as (b). 70% will initially suspect (a).

**Core Problem:**
If NPS is <30 at Month 2, it signals that verdict quality perception is poor. Users are not sharing the app ("Aplikasi ini salah, nggak recommend"). Viral growth stops. Freemium conversion collapses.

This is not necessarily a data problem; it's a communication problem. Users need to understand why their salary might be outside the range without feeling the tool is broken.

**Early Warning Signal (Month 2-3):**

| Signal | Observable At | Red Flag |
|---|---|---|
| NPS (Net Promoter Score) | In-app survey after verdict | <30 NPS (healthy is >40) |
| "Incorrect verdict" feedback | User feedback modal clicks | >20% of users click "Ini salah" |
| Twitter/Reddit negative sentiment | Hashtag monitoring #cekwajar | >3 tweets saying "aplikasi ini salah" |
| Conversion to paid (implied dissatisfaction) | Premium gate conversion rate | <0.5% (healthy is >1.5%) |
| Verdict sharing rate | Share button clicks per verdict | <5% of verdicts are shared |
| **Measurement** | Postmark survey + Twitter monitoring | Weekly review |

**Kill Criteria (When Low NPS Becomes Fatal):**

| Metric | Kill Threshold | Timeline |
|---|---|---|
| NPS | <25 at Month 3 (vs. target ≥40) | Month 3 measurement |
| % users flagging verdict as wrong | >25% click "Verdict seems inaccurate" | Month 3 |
| Viral coefficient | <1.0 (fewer than 1 new user per 10 existing users share) | Month 3 |
| Word-of-mouth sentiment | Reddit threads, Twitter, community sentiment | Month 3 survey |
| **Decision trigger** | If NPS <25 AND viral coefficient <1.0 at Month 3 | Immediate product redesign needed |

Why Month 3? Because by Month 6, if NPS is still <30, you've lost 12 weeks to a product that users don't trust. Pivoting at Month 3 saves you 9 weeks.

**90-Day Mitigation (Communication > Data Quality at Launch):**

1. **Confidence Scoring Visible on Every Verdict (Day 1)**
   - Show: "Berdasarkan [N] data poin dari BPS + [M] kontribusi pengguna Indonesia"
   - Example: "Berdasarkan 47 salary reports + BPS estimates" vs. "Berdasarkan 8 data poin (estimasi BPS)"
   - Psychology: Users understand that 8 data points = low confidence. Sets expectations.
   - Execution: Add `confidence_score` field to verdict object, calculate as (submission_count / optimal_count) × 100
   - Visual: Green badge for >40 submissions, yellow for 10-40, red for <10
   - Expected outcome: Users with low-confidence verdicts understand the data is thin, don't blame app accuracy

2. **Thumbs Up/Down Feedback on Every Verdict (Day 1)**
   - Button: "Apakah ini terasa akurat untuk posisi Anda?" with thumbs up / down
   - Data collection: Every verdict gets binary feedback signal
   - Analysis: "Wajar Gaji verdict for Senior PM, Jakarta: 72% of users marked as accurate, 28% marked as inaccurate"
   - Action: If >40% mark as inaccurate for a specific job/city combo, flag that data point as "needs improvement"
   - Expected outcome: Founder sees accuracy problems in real-time, can adjust data or add warnings
   - Execution: 2 hours to add UI + data pipeline

3. **Contextual Disclaimers on Every Verdict (Day 1)**
   - Add below verdict: "Catatan: Hasil ini TIDAK mempertimbangkan:"
   - Checkboxes users can click:
     - [ ] Equity/ESOP (startup compensation)
     - [ ] Performance bonus (varies by company)
     - [ ] Role level (IC1 vs IC3 vs Manager)
     - [ ] Company stage (startup vs MNC)
     - [ ] Remote work (premium for remote-first)
     - [ ] Restricted stock / vesting
   - Expected: 15-20% of users will check these, realize their situation is indeed outside the range, NPS improves to ~40
   - Execution: 3-4 hours of UI design + logic

4. **Bayesian Model for Outlier Detection (Week 1)**
   - Problem: Dataset will have outliers (high/low salaries that skew average)
   - Solution: Use Bayesian model to down-weight outliers
   - Method: Calculate p25/p50/p75 using median absolute deviation (MAD) instead of simple percentile
   - Expected improvement: P25 moves up 3-5%, reducing false negatives ("I'm below market")
   - Execution: 4 hours in Python, test before Month 1 launch
   - Benefit: Users see more "Wajar" verdicts, higher satisfaction

5. **Explainability on Verdict Page (Day 1)**
   - Instead of just showing P25/P50/P75, show the reasoning:
   - "Gaji segmentasi dari 47 laporan pengguna + estimasi BPS untuk Jakarta, Industry: Tech, Role: Software Engineer, Experience: 3 tahun"
   - Show historical trend: "Bulan lalu: 8M gaji average (n=12), minggu ini: 8.5M (n=35) — trend naik"
   - Purpose: User sees thoughtfulness, not just random numbers
   - Execution: 5-6 hours of design + data pipeline

6. **Active Engagement for Edge Cases (Week 1)**
   - Add call-to-action: "Gaji Anda berbeda signifikan? Bantu kami improve dengan share konteks Anda"
   - Form: Optional additional context (remote/office, equity structure, experience, company type)
   - Expected: 5-8% of users will fill this out, giving richer data
   - Outcome: Better understanding of outliers, can segment P25/P50/P75 by more variables
   - Execution: 3 hours

**Pivot Option If NPS Stays <25 Through Month 3 (Month 3-4):**

**"Add More Context Inputs Before Showing Verdict"**
- Current flow: User enters salary → instant verdict
- Pivot flow: User enters salary → Asks for company stage/size/equity/role level → THEN shows verdict
- Advantage: Verdict becomes more accurate because it's conditional on company type
- Cost: More friction (3-4 additional questions before verdict)
- Expected outcome: Verdict accuracy improves, NPS jumps to 45-50
- Tradeoff: Initial conversion might drop 10-15% due to friction, but conversion to premium improves because verdict is more credible
- Timeline: 3-4 days to implement
- Survival probability if executed: 70% (more accurate verdicts become the competitive advantage)

---

### Failure Mode 7: OJK/Regulator Warning Letter

**Probability at Launch:** LOW-MEDIUM (25%)
- Indonesian financial regulation is still catching up to fintech tools
- OJK oversight: Formal enforcement against data tools is rare (more focused on lending/payment platforms)
- However: Legal risk for "giving advice" is real if phrased wrong
- User complaint escalation: If even 1 user complains to BPKN (consumer protection), OJK may ask questions

**Core Problem:**
A single user complaint about "cekwajar.id told me to negotiate a higher salary and I got fired" could trigger OJK inquiry. Even unfounded complaints cost 50-100 hours of legal response time + stress.

More likely risk: OJK sends "klarifikasi" (clarification request) asking about data sourcing, accuracy standards, disclaimers. Not a ban, but requires legal response.

**Early Warning Signal (Month 1-6):**

| Signal | Observable At | Red Flag |
|---|---|---|
| BPKN complaint | BPKN website or notice to founder email | >1 formal complaint |
| OJK inquiry email | Direct email from OJK address | Any email asking for "klarifikasi" |
| Media negative coverage | Detik Finance, CNBC, Koran Tempo | Article questioning accuracy/liability |
| User lawsuit threat | Email/social from user claiming damages | Any legal threat |
| **Action** | Monitor email + BPKN website | Immediate response if hit |

**Kill Criteria (When Regulatory Risk Becomes Fatal):**

| Metric | Kill Threshold | Timeline |
|---|---|---|
| OJK formal warning letter | Letter requiring feature removal or process change | Any point (immediately escalated) |
| Legal fees incurred | Hiring lawyer to respond to OJK = IDR 50M+ cost | Triggers immediate financial pressure |
| Feature ban | OJK requires removal of PPh21 calculator or verdict feature | Kills core product |
| **Decision trigger** | Any 1 of above = immediate legal consultation + pivot | Real-time |

Why this matters: One regulatory letter could consume 2-4 months of solo founder time on legal/compliance work (not product). Death by bureaucracy.

**90-Day Mitigation (Legal Armor from Day 1):**

1. **Prominent Disclaimers on Every Page (Day 1)**
   - Header on verdict page: "⚠️ Informasi ini berbasis data agregat, BUKAN saran keuangan, pajak, atau hukum"
   - Footer: "cekwajar.id adalah tools analisis data, bukan konsultan"
   - On Wajar Slip: "Perhitungan ini berdasarkan rumus PPh21 standar. Situasi pribadi Anda mungkin berbeda."
   - On Wajar Tanah: "Harga properti berdasarkan data agregat. Konsultasikan dengan AGEN PROPERTI untuk valuasi akurat."
   - Language discipline: Never use "kami rekomendasikan" (recommendation). Always use "data menunjukkan" (data indicates).
   - Execution: 2-3 hours of copy, permanently visible

2. **Formal Legal Consultation (Week 1-2)**
   - Hire: Indonesian fintech/data law firm (recommend: HIMPINDO members or Tilleke & Gibbins Indonesia)
   - Scope: 4-hour initial consultation (IDR 3-5M for good firm)
   - Questions to ask:
     - Is cekwajar.id legally liable for verdict accuracy?
     - Do we need OJK registration? (Likely answer: No, but should clarify)
     - What language avoids "giving advice" legal exposure?
     - What data privacy compliance is needed for payslip handling?
     - Do we need Terms of Service updates?
   - Output: Legal memo addressing cekwajar.id's specific risk areas
   - Timeline: Week 1 consultation, implement recommendations Week 2-3
   - Expected cost: IDR 5-10M upfront, saves 100+ hours of confused legal work later

3. **Register as Penyelenggara Sistem Elektronik (PSE) with Kominfo (Month 1)**
   - Requirement: Any platform collecting user data in Indonesia should register
   - Process: File form to Kominfo (Indonesian Ministry of Communication)
   - Timeline: Takes 2-3 weeks, costs IDR 0 (free, just bureaucratic)
   - Benefit: Legitimate regulatory compliance, protects against unregistered platform claims
   - Execution: Founder or lawyer handles in parallel with product development
   - Expected outcome: Not defensive (won't prevent OJK questions), but signals seriousness

4. **Terms of Service + Privacy Policy (Week 1-2)**
   - Use template from Indonesian fintech lawyer (don't use US template)
   - Key clauses:
     - "Kami tidak bertanggung jawab atas keputusan finansial berdasarkan data kami"
     - "User data disimpan dengan enkripsi, dihapus setelah 30 hari (untuk payslip)"
     - "Kami tidak menjual data ke recruiter atau perusahaan lain"
   - Language: Accessible to Indonesian users, clear on liabilities
   - Review: Have lawyer review before launch
   - Execution: 4-5 hours to customize templates

5. **Data Privacy Compliance Architecture (Week -1 before launch)**
   - For Wajar Slip (payslip photos): Data retention policy set in code
     - Automatic deletion after 30 days (using Supabase pg_cron)
     - No backup retention beyond 7 days
   - Encryption: All sensitive data encrypted at rest (Supabase default + additional encryption)
   - Access logs: Log every access to sensitive data (for audit trail)
   - Expected outcome: If OJK asks "how do you handle payslip data?", answer is clear + defensible
   - Execution: 4-5 hours of database architecture

6. **Incident Response Plan Document (Week 2)**
   - Create document: "If regulatory inquiry comes, here's what we do"
   - Step 1: Acknowledge receipt within 24 hours, don't admit liability
   - Step 2: Engage lawyer within 48 hours
   - Step 3: Respond to inquiry within timeline specified (usually 14-30 days)
   - Step 4: If required, issue public statement or feature update
   - Communication template: Draft email to users if major change required
   - Expected outcome: You're not panicking when letter arrives; you have playbook
   - Execution: 2 hours to document

**Pivot Option If OJK Formal Warning Arrives (Month 2-6):**

**"Apply for OJK Regulatory Sandbox"**
- If OJK sends warning, don't fight them, use them
- Mechanism: OJK has "Regulatory Sandbox" program for fintech innovation
- Process: Apply to sandbox, OJK gives you 6-12 months of regulatory relief + guidance
- Outcome: Turn OJK warning into OJK partnership
- Timeline: Sandbox application takes 4-6 weeks
- Benefit: Regulatory approval becomes a feature ("OJK-Approved" badge)
- Survival probability if executed immediately: 90% (transforms threat into credibility)

---

### Failure Mode 8: Founder Burnout

**Probability at Launch:** HIGH (75%)
- Solo operation: 18 months of sustained solo founder responsibility (GTM, product, engineering, customer support)
- Energy variance: Month 1-3 is exciting, Month 6-12 is grinding, Month 12-18 is "why is no one joining/how am I still doing this"
- Historical pattern: 60% of solo founder projects hit severe burnout by Month 8-10
- Risk intensifier: TikTok-first GTM requires constant content creation (not bursty, weekly cadence)

**Core Problem:**
If founder stops shipping (no product updates for 3+ weeks), users notice. Bugs accumulate. Competitive features are ignored. Death is slow but certain.

Burnout manifests not as depression (though that happens) but as context-switching paralysis — founder stays "busy" but makes no progress.

**Early Warning Signal (Month 3-9):**

| Signal | Observable At | Red Flag |
|---|---|---|
| Product update cadence | GitHub commit history or app changelog | 0 commits for >14 days |
| Critical bug response time | Time to fix reported bugs | From 24 hours to >72 hours |
| Feature velocity | Features shipped per week | Drops from 3-4/week to 0-1/week |
| Content output | TikTok videos per week | Drops from 4/week to <2/week |
| Communication | Email response to user questions | From same-day to 2-3+ days |
| Founder health signals | Visible signals (social media engagement, energy) | Decline in founder tweets/updates |
| **Measurement** | Automated dashboard of above metrics | Weekly review |

**Kill Criteria (When Burnout Becomes Fatal):**

| Metric | Kill Threshold | Timeline |
|---|---|---|
| No product development | 30+ consecutive days with no code commits | Month of discovery |
| Bugs accumulate | 10+ unresolved user-reported bugs in backlog | Month of discovery |
| Feature updates pause | 0 feature releases in 4+ consecutive weeks | Month of discovery |
| **Decision trigger** | Any of above = immediately pivot to maintenance mode | Real-time |

Why 30 days? Because 2-3 weeks of low output is normal (founder vacation, bad sprint). 4+ weeks signals structural problem.

**90-Day Mitigation (Sustainable Pace from Day 1):**

1. **Enforce Hard Working Hours (Week 1, Day 1)**
   - Commit: Max 50 hours/week, not "founder working 70 hours" culture
   - Why: Sustainable pace creates better decisions, not worse
   - Calendar: Mark 1 full day/week as OFF (no work, no email, no "just checking Sentry")
   - Implementation: Use calendar blocking, tell people your boundaries
   - Expected outcome: Still shipping fast, but with space for sleep + human recovery
   - Benefit: Lower burnout risk, better thinking at Month 6-12 when grinding starts

2. **AI Automation for Repetitive Tasks (Week 1-4)**
   - Identify: All tasks that take >1 hour/week and are repetitive
     - Customer support templating (canned responses for common questions)
     - Social media scheduling (plan week's content Monday, schedule in Batch/Buffer)
     - Data aggregation (let Supabase Edge Functions do data processing, not manual scripts)
     - Analytics reporting (automate weekly metric snapshots)
   - Expected time savings: 5-7 hours/week reclaimed
   - Implementation: 10 hours upfront investment, saves 5-7 hours/week forever
   - Tools: Make, Zapier, Supabase functions, or custom Node scripts
   - Execution: Founder spends Week 1-4 building these, then freed from weekly grind

3. **Define "Minimum Viable Maintenance" (Week 1)**
   - Create list of 5-7 critical tasks that MUST happen weekly, regardless of founder energy:
     1. Monitor Sentry for critical errors (15 min)
     2. Respond to user support emails (30 min)
     3. Review analytics + growth metrics (20 min)
     4. One feature update or bug fix (2 hours)
     5. One social media post (15 min)
     6. Monitor OJK/regulatory news (15 min)
     7. Backup database check (5 min)
   - Total: ~4 hours/week minimum
   - Psychology: Even on bad weeks, these 7 things happen. Product doesn't decay.
   - During good weeks: Do 10x more
   - Execution: Write this down, put it in calendar

4. **Documentation for Future Co-Founder Handoff (Month 3-6)**
   - Start building: Step-by-step guides for all repeatable processes
     - How to release a new feature (20-minute guide)
     - How to respond to user support tickets (5-minute guide)
     - How to update salary benchmarks (15-minute guide)
     - How to analyze metrics + make decisions (30-minute guide)
   - Expected outcome: By Month 6, if you hire co-founder or contractor, onboarding takes 1 week not 1 month
   - Timeline: 1 hour/week during slow periods (Month 5-6)
   - Benefit: Makes the business delegatable, reduces solo-founder load

5. **Month 6 Decision: Seek Co-Founder or Hire (Month 6)**
   - If growth targets are being hit (10K+ MAU by Month 6), make the call: hire or die
   - Hire level: Contract developer (not full-time yet) for 10-15 hours/week
   - Cost: IDR 5-8M/month for junior dev, IDR 10-15M for mid-level
   - Responsibility: Founder keeps product direction, dev handles 50% of feature building
   - Expected outcome: Founder load drops from 50 hours/week to 35 hours/week, sustainable long-term
   - If growth is NOT hitting targets (5K MAU at Month 6), assess whether to pivot or continue solo
   - Timeline: Make this decision no later than Month 6

6. **Month 9 Threshold: First Team Member (Month 9)**
   - If still solo at Month 9 and MAU >20K, it's now critical to hire
   - Any later (Month 12+) and founder has probably already burned out
   - Hire priority: Customer support + analytics (frees founder from operational load)
   - Cost: IDR 4-6M/month for person handling support + basic analytics
   - Expected outcome: Founder can focus on product + growth only

**Pivot Option If Severe Burnout Detected (Month 6-7):**

**"Maintenance Mode + Early Monetization"**
- Decision: Pause growth investment, pause new features
- Focus: Fix bugs, stabilize product, launch paid features aggressively
- Goal: Earn IDR 2-3M/month in revenue, use revenue to hire first person
- Timeline: Spend Month 7-9 in maintenance mode (seems like failure, is actually survival strategy)
- Expected outcome: By Month 10, revenue hired first team member, founder load decreases
- Survival probability if executed: 80% (revenue-funded growth is sustainable, investor-funded solo founder is not)

---

### Failure Mode 9: B2C Conversion Stuck at 0.5%

**Probability at Launch:** MEDIUM (50%)
- Indonesian user data: Historically reluctant to pay for information tools (prefer free Googling)
- Freemium norms: Users expect information tools to be 80% free, 20% premium
- Monetization psychology: Indonesian users consider IDR 15-30K as "expensive for app" (but will spend on food, ride-share)
- Comparable platforms: Indonesian salary tools (like Comparably Indonesia, now defunct) struggled to convert >1% even with millions of users

**Core Problem:**
If conversion rate is 0.5% by Month 3 (vs. goal of 1.5% by Month 6), it signals either:
- Value proposition is unclear (users don't understand what they're paying for)
- Price is wrong (IDR 29K is too expensive for perceived value)
- Freemium gate is in wrong place (gating the wrong feature)
- No need for premium (free tools are good enough)

If problem is #4 (no need for premium), business model breaks. Need to pivot to B2B.

**Early Warning Signal (Month 2-4):**

| Signal | Observable At | Red Flag |
|---|---|---|
| Gate hit rate | % of verdict viewers who hit premium gate | <20% hitting gate (most never hit it) |
| Gate-to-click rate | % of gate hitters who click "Upgrade" CTA | <2% click (healthy is 5-8%) |
| Gate-to-conversion rate | % of gate hitters who complete payment | <0.5% (healthy is 1-2%) |
| Upgrade CTA visibility | How visible is upgrade offer | 30%+ of users never see it |
| Price elasticity test | Conversion at different price points | Same rate at IDR 15K and IDR 100K (suggests price isn't the lever) |
| **Measurement** | Funnel analysis in Mixpanel/Amplitude | Weekly review |

**Kill Criteria (When Low Conversion Becomes Fatal):**

| Metric | Kill Threshold | Timeline |
|---|---|---|
| Conversion rate | Stuck at <0.8% through Month 9 despite 3+ A/B tests | Month 9 |
| Revenue at scale | Even with 50K MAU, revenue is <IDR 3M/month | Month 12 |
| B2B pipeline | No B2B leads generated by Month 9 | Month 9 |
| **Decision trigger** | If all 3 metrics above = need B2B pivot or business model change | Month 9 decision point |

Why Month 9? Because if you have 50K MAU and conversion is still <0.5%, you've proven the freemium model doesn't work. Waiting until Month 12 wastes 3 more months.

**90-Day Mitigation (A/B Test the Gate, Not Just the Price):**

1. **Test 3 Different Freemium Gates (Week 1-8)**
   - Gate 1: P25/P75 range gated (current plan)
     - Show salary, hide range
     - Expected conversion: 1-2% (moderate scarcity)
   - Gate 2: Detailed comparison gated (alternative test)
     - Show if salary is "Below/Wajar/Above" market, hide "How much below" detail
     - Expected conversion: 2-3% (more valuable unlock)
   - Gate 3: Job title comparison gated (alternative test)
     - Show salary range for primary job, hide comparison to 3 other jobs you might qualify for
     - Expected conversion: 3-4% (psychological value of career alternatives)
   - Timeline: Test each for 2 weeks (weeks 1-2, 3-4, 5-6)
   - Measurement: Track conversion rate for each gate variant
   - Decision: Proceed with highest-converting gate for core monetization
   - Expected outcome: One of three gates will convert 2-3x higher than baseline

2. **Introduce Pay-Per-Report Option (Week 2)**
   - Alternative to subscription: "See detailed report — IDR 15,000 one-time"
   - Psychology: Lower commitment than subscription (IDR 29K/month implies ongoing)
   - Expected conversion: 3-5x higher than subscription (people buy individual things more easily)
   - Mechanics: Track conversion rate separately from subscription
   - Pricing psychology: Same IDR 15K as subscription, but one-time triggers higher conversion
   - Timeline: Can implement in 2-3 hours (Lemon Squeezy or Stripe one-time payment)
   - Expected outcome: Total monetization (subscription + one-time) reaches 2-3% by Month 6

3. **Identify High-Intent Users + Retarget (Week 3)**
   - Define: Users who check salary 3+ times in first week = high intent
   - Retargeting: Send email to these users (Week 1) with specific offer:
     - "You checked your salary 5 times. Unlock full market research — IDR 29K for 30 days"
   - Expected conversion: 5-8% of high-intent users (vs. 0.5% of random users)
   - Timeline: Email sends Week 1, measures Week 2
   - Expected outcome: High-intent segment is small (maybe 5-10% of users) but converts 10x higher, meaningful revenue contribution

4. **A/B Test Different CTA Copy (Week 1-4)**
   - Variant A (current): "Upgrade — Lihat detail lengkap"
   - Variant B: "Unlock — Bandingkan ke 10 gaji serupa"
   - Variant C: "Beli laporan — Kirim ke email (5 menit baca)"
   - Variant D: "Satu kali bayar — Lihat semua data gaji (tidak perlu subscribe)"
   - Timeline: Test each for 1 week
   - Measurement: Click-through rate (not just conversion, initial interest)
   - Expected: Some copy variants will have 2-3x higher CTR than others
   - Execution: 30 minutes to test each variant

5. **Understand Objection (Month 2)**
   - Add optional feedback form on gate: "Kenapa tidak upgrade?" with radio options:
     - "Gajian saya sudah sesuai"
     - "Terlalu mahal"
     - "Tidak yakin akuratnya"
     - "Tidak perlu info ini"
     - "Mau coba gratisan dulu"
   - Expected: Objection distribution will guide fix (if 40% say "terlalu mahal", lower price; if 40% say "tidak yakin", fix accuracy first)
   - Timeline: Collect 100+ responses by Week 4
   - Execution: 2 hours to add form + analysis

**Pivot Option If Conversion Stays <0.8% Through Month 9:**

**"B2B-First Business Model"**
- Kill: Consumer subscription model (deprioritize it)
- Pivot to: B2B licensing of salary data
- Targets: HR firms, executive recruitment, payroll platforms, bank KPR teams, insurance companies
- Pricing: IDR 2-5M/month for API access to salary benchmarks
- Revenue model: 10 B2B clients × IDR 2M/month = IDR 20M/month (vs. 50K users × IDR 29K/month = IDR 1.45M with 100% conversion, unrealistic)
- GTM shift: Outbound sales to HR directors, not TikTok to consumers
- Timeline: Can pivot sales focus in 2-3 weeks (product doesn't change much, just go after different buyer)
- Survival probability: 85% (B2B is more sustainable, higher LTV, lower churn than B2C)

---

### Failure Mode 10: Data Privacy Incident (Payslip Photos Leaked)

**Probability at Launch:** LOW (8% probability of breach) but CATASTROPHIC impact (100% survival probability is 0% if breach occurs)
- Storage architecture risk: Founder unfamiliar with secure file handling can create 1000x worse situation
- Supabase security: Good defaults, but misconfigurations are possible
- Threat surface: External attack (unlikely) + accidental public bucket (likely risk)
- Indonesian regulatory: UU PDP (Personal Data Protection Law) comes into effect 2024-2025, breach notification is now MANDATORY

**Core Problem:**
A confirmed breach of payslip data (even 5 users, even blurred images) is extinction-level event:
- Legal action: Users can sue for damages (UU PDP Pasal 46)
- Regulatory action: OJK/BPKN will shut you down
- Reputational: "Startup yang bocor data gajian" is permanent brand damage
- No recovery: You cannot rebuild trust after payslip data breach

This is not "fail fast and pivot" territory. This is "you're done" territory.

**Early Warning Signal (Month 1-18):**

| Signal | Observable At | Red Flag |
|---|---|---|
| Unauthorized API access | Security logs showing 403 or unexpected 200 responses | Any unauthorized access attempt |
| Bucket misconfiguration | Supabase Storage audit showing public bucket | Any public access to storage|
| Data exposure test | Penetration test showing vulnerability | Any vulnerability allowing data access |
| **Measurement** | Weekly security audit + automated monitoring | Real-time alerts |

**Kill Criteria (When Breach Becomes Actual):**

| Metric | Kill Threshold | Decision |
|---|---|---|
| Confirmed breach | ANY confirmed data leak involving payslip/salary data | Immediate shutdown + disclosure |
| Scope | Even 1 user affected | Triggers full incident response |
| **Action** | Not "pivot" — this is "shut down + legal response" | Real-time |

**90-Day Mitigation (Non-Negotiable Security Architecture):**

1. **Auto-Delete Raw Payslip Data After 30 Days (Week -1 before launch)**
   - Architecture: When user uploads payslip PDF, system:
     - Stores PDF in Supabase Storage (30-day TTL)
     - Extracts text data using Cloud Vision API (or similar)
     - Stores extracted structured data (job title, gross salary, deductions) in database
     - Deletes raw PDF after extraction
     - Final: Database has salary amount, storage has nothing
   - Why: Even if database is breached, PDF photo is not stolen (biggest liability)
   - Implementation: Use pg_cron to schedule daily deletion query:
     ```sql
     DELETE FROM payslip_files
     WHERE created_at < NOW() - INTERVAL '30 days';
     ```
   - Backup retention: Even backups deleted after 7 days (not 30 days, to be ultra-safe)
   - Execution: 4-5 hours of database architecture + testing

2. **Encryption at Rest (Day 1)**
   - Store all salary data encrypted in database (not just at transport)
   - Use: Supabase built-in encryption (default) + additional layer if sensitive
   - Field-level encryption: Salary amounts encrypted with different key than user IDs
   - Expected outcome: Even if database is exfiltrated, salary data is ciphertext (not useful)
   - Execution: Already handled by Supabase defaults, verify in Week -1

3. **Security Audit by Penetration Tester (Week -3 before launch)**
   - Hire: Independent penetration tester (IdSec, Telkom CERT, or freelancer from Upwork)
   - Cost: IDR 5-10M for 20 hours of testing
   - Scope: Try to access payslip data, test bucket permissions, test API authentication
   - Output: Report of vulnerabilities + fixes
   - Remediation: Fix all HIGH/CRITICAL findings before launch, document MEDIUM findings
   - Timeline: Week -3 (test), Week -2 (fix), Week -1 (re-test)
   - Expected: Report shows 0 HIGH vulnerabilities before launch
   - Execution: Hire in Week -4, results in Week -2, verify fixes in Week -1

4. **Access Logging (Week -1)**
   - Log every access to payslip data:
     - Who accessed (user ID or system)
     - When (timestamp)
     - What data (salary amount, job title, or just "accessed")
     - From where (IP, browser)
   - Storage: Write logs to separate Supabase table (easier to audit)
   - Retention: Audit logs kept for 90 days (legal hold)
   - Monitoring: If any access from unfamiliar IP or at odd hours, alert founder
   - Execution: 3-4 hours of logging infrastructure

5. **Incident Response Plan (Week -2)**
   - Document: "If data breach is discovered, here's what we do"
   - Timeline:
     - Hour 0: Discover breach, confirm it's real (not false alarm)
     - Hour 1: Engage lawyer, contact Supabase support
     - Hour 2: Take affected service offline if necessary (minimize further exposure)
     - Hour 4: Prepare disclosure message to affected users
     - Hour 6: Send emails to all affected users (required by UU PDP)
     - Hour 24: File report with OJK (if required by law)
     - Day 3: Public statement on website + social media
   - Communication template (draft now, fill in numbers later):
     ```
     "Kami menemukan akses tidak sah ke payslip data [N] pengguna pada [DATE].
     Kami langsung menutup akses, memperkuat keamanan, dan melaporkan ke OJK.
     Anda dapat mengajukan klaim kompensasi: [link]. Mohon maaf."
     ```
   - Execution: 3-4 hours to document, 30 minutes to update as needed

6. **User Communication About Data Retention (Week 1)**
   - Privacy policy clearly states:
     - "Payslip photo Anda dihapus setelah 30 hari"
     - "Data gaji disimpan untuk benchmark, tapi tidak pernah dijual"
     - "Anda bisa request penghapusan data kapan saja"
   - Expected: Users feel reassured, less likely to worry about privacy
   - Execution: 2 hours of copy + privacy policy update

**Pivot Option If Breach Actually Occurs:**

**"Immediate Shutdown + Incident Response (Not a Pivot, Necessary Action)"**
- Action 1: Take Wajar Slip offline immediately (most sensitive, payslip photos)
- Action 2: Keep Wajar Gaji running (salary data without photos is lower risk)
- Action 3: Engage lawyer, disclose to OJK within 24 hours (required by law)
- Action 4: Email all affected users within 24 hours (required by law)
- Action 5: Implement security fix (2-4 weeks)
- Action 6: Relaunch Wajar Slip with "Enhanced security certification" badge (from penetration tester)
- Timeline: Down for 2-4 weeks, recovery takes 2-3 months
- Survival probability: 25% (reputational damage is severe, but not fatal if you handle it with transparency)
- Actual case study: Gett (ride-share) had data breach, transparent response, still survived. Uber had breach, covered it up, massive damage.

---

## PART B: DECISION FRAMEWORK

### THREE PATHS AT MONTH 18

#### PATH 1: "Keep Going Exactly As Planned"

You hit all confirmation metrics. Growth is happening. No major failures detected. Continue execution.

**Confirmation Metrics Table:**

| Milestone | Month 3 | Month 6 | Month 12 |
|-----------|---------|---------|----------|
| **MAU (Monthly Active Users)** | ≥3,000 | ≥15,000 | ≥50,000 |
| **MoM Growth Rate** | ≥40% | ≥30% | ≥20% |
| **Conversion Rate (Free→Paid)** | ≥1.0% | ≥1.5% | ≥2.0% |
| **Verdict NPS** | ≥40 | ≥45 | ≥50 |
| **D30 Retention (% of Month N users active in Month N+1)** | ≥25% | ≥30% | ≥35% |
| **B2B Leads Generated** | 0 formal | 2+ conversations | 1 paying contract |
| **TikTok Avg Reach per Video** | ≥5,000 | ≥10,000 | ≥20,000 |
| **Monthly Revenue (IDR)** | ≥1,400,000 | ≥10,000,000 | ≥45,000,000 |
| **Critical Bugs in Production** | 0 unresolved | 0 unresolved | 0 unresolved |
| **Data Accuracy (% verdicts marked accurate by users)** | ≥70% | ≥75% | ≥80% |

**Decision Rule:** If ≥8 of 10 metrics are GREEN at each milestone, execute strategy as planned. Proceed to Month 18 with confidence.

**What Happens Next (Path 1 Success):**
- Month 13-18: Scale team to 3-4 people (1 engineer, 1 growth marketer, 1 customer success, maybe 1 finance/ops)
- Month 18: Evaluate fundraising (Series A if growth is exponential, bootstrapping if sustainable)
- Path: Most likely outcome is 12-18 month runway until Series A (if all metrics hit)

---

#### PATH 2: "Pivot" (Change Approach, Don't Quit)

3 of 10 failure modes have hit. You're still alive, but original strategy is not working. Pivot to defensible variant.

**Pivot Indicator Checklist (Any 3 = Pivot Required):**

```
□ Month 6 MAU < 5,000 AND growth <15% MoM
  → Verdict quality or acquisition is broken

□ Conversion rate <0.8% despite 3+ A/B tests
  → B2C freemium model is not viable

□ TikTok average reach declining for 6+ consecutive weeks
  → TikTok GTM is failing

□ Verdict NPS < 25 with >25% "verdict is wrong" feedback
  → Core product is not trusted

□ 2+ regulatory inquiries or legal risks surfaced
  → Regulatory moat is not defensible as-is
```

**Three Most Viable Pivot Directions:**

##### Pivot Option 1: B2B-First Model
- **What changes:** Stop chasing consumer conversions. Pivot to selling salary data + compliance tools to HR firms, recruitment agencies, banks
- **Why it's viable:** B2B SaaS has higher LTV (IDR 2-5M/month per client), lower churn (annual contracts), better unit economics
- **Targets:**
  - HR platforms (Workday, BambooHR) as white-label data providers
  - Recruitment firms (Michael Page, Robert Walters, local agencies) for market intelligence
  - Banks (for KPR eligibility checking: "does borrower's salary support loan?")
  - Payroll platforms (ADP, Talenta) for compliance benchmarking
- **Revenue math:** 10 B2B clients × IDR 2-3M/month = IDR 20-30M/month (vs. 50K consumers × IDR 29K × 2% conversion = IDR 29M, harder to achieve)
- **GTM shift:** Outbound sales (LinkedIn, email, sales calls) vs. TikTok (inbound)
- **Timeline:** GTM changes in 2-3 weeks, sales takes 2-3 months to close first deal
- **Team requirement:** Sales person (founder can do initial sales, but hire sales dev at Month 4)
- **Risk:** B2B is slower to revenue, but more stable once it starts
- **Survival probability:** 75% (proven SaaS model, clear willingness to pay from B2B buyers)

##### Pivot Option 2: Vertical Depth (Pick 1-2 Tools, Kill Others)
- **What changes:** Kill Wajar Tanah, Wajar Kabur, Wajar Hidup. Go DEEP on Wajar Slip + Wajar Gaji
- **Why it's viable:** Regulatory moat in payroll/tax space is real. No other platform in Indonesia has deep compliance expertise. Tokopedia/Gojek can't easily copy this.
- **Target:** SMEs (1-100 employees) who need accurate payroll compliance (currently outsourcing to consultant for IDR 5-10M/year)
- **Positioning:** "Payroll compliance + salary benchmarking for Indonesian SMEs"
- **B2B angle:** Sell to payroll consultants (they resell to 50+ SME clients each)
- **Revenue:** Fewer total users (maybe 20K vs. 50K), but higher ARPU (B2B/B2B2C)
- **Timeline:** Focus shift in 1 week, content + sales in Month 2-3
- **Team requirement:** Accountant/tax expert (contractor or advisor, not full-time yet) to validate compliance rules
- **Risk:** Narrows addressable market, but defensible
- **Survival probability:** 70% (compliance is defensible, but smaller market)

##### Pivot Option 3: API/Infrastructure Play
- **What changes:** Build the salary + property benchmark API. Sell to platforms, not consumers
- **Why it's viable:** Jobstreet, Rumah123, Gojek, etc. all need salary/property benchmarks. They currently use public data. Build the best Indonesian data layer.
- **Targets:** Job platforms (Jobstreet, Glints, Linkedln Indonesia), property platforms (Rumah123, OLX), banks (KPR teams), insurance (underwriting)
- **Positioning:** "Plaid for Indonesian compensation data" (B2B infrastructure, not consumer tool)
- **Revenue:** IDR 1-5M/month per client × 20-30 clients = IDR 20-150M/month (highest upside)
- **GTM:** Direct sales to product teams at platforms
- **Timeline:** Product changes (add API + documentation), sales takes 2-3 months
- **Team requirement:** 1 backend engineer (you can do this as founder, or hire)
- **Risk:** Requires larger sales cycles, less viral, more enterprise-like
- **Survival probability:** 65% (biggest upside, but slowest to revenue)

**Pivot Decision Tree:**

```
IF conversion <0.8% AND NPS >30:
  → Pivot to B2B-first (problem is monetization, not product)

IF NPS <25 AND conversion doesn't matter:
  → Pivot to vertical depth (problem is product-market fit, go deeper not wider)

IF TikTok failing AND organic/email strong:
  → Pivot to API/infrastructure (less dependent on consumer virality)

IF 2+ regulatory queries:
  → Consider all pivots + add regulatory partner (OJK sandbox) as hedge
```

**Timeline to Pivot Decision:** Month 6 (latest Month 7)
**Why so early?** Waiting until Month 9 or 12 means 3-6 months of wasted effort on original strategy.

---

#### PATH 3: "Kill It"

You hit one of the kill criteria. Business is not salvageable with available resources/time/mental energy. Shut down professionally, preserve relationships, move on.

**Kill Criteria (Any ONE = Shutdown Decision):**

```
□ Month 12 MAU < 5,000 AND no B2B revenue AND cumulative cash deficit > IDR 150M
  → Not viable at any scale, burn rate too high

□ Verified PPh21 calculation error causing user financial harm + negative media coverage
  → Cannot recover reputational damage from tax errors

□ Confirmed data breach involving >100 users' payslip/salary data
  → Legal liability is too high, users will sue, regulators will shut you down

□ Formal OJK enforcement action requiring complete product redesign
  → Regulatory cost + timeline is prohibitive for solo founder

□ Founder health crisis requiring sustained absence >3 months
  → Solo founder dependency is terminal without founder
```

**How to Distinguish "Early-Stage Friction" from "PMF Failure":**

| Signal | Early-Stage Friction | PMF Failure |
|--------|---|---|
| **MAU at Month 6** | 5-10K (slow start) | <2K (nobody wants it) |
| **Engagement (D30 retention)** | >30% (people use it) | <15% (people try once, leave) |
| **NPS** | 35-45 (users like it) | <20 (users hate it) |
| **Viral coefficient** | 0.8-1.2 (organic growth possible) | <0.3 (nobody shares) |
| **User feedback** | "Gajian saya salah/baguslah" (debate) | "Aplikasi ini tidak berguna" (unanimous) |
| **Founder intuition** | "We're on to something, execution is wrong" | "This problem doesn't exist" |

**Decision:** If you see early-stage friction, pivot. If you see PMF failure, kill it.

**Shutdown Playbook (If Required):**

1. **Announce shutdown with grace (1 week warning)**
   - Email to all users: "Kami hentikan cekwajar.id pada [DATE]. Terima kasih sudah support."
   - Refund any subscription fees for unused time
   - Make backups of user data available (if they ask)

2. **Wind down infrastructure (1 week)**
   - Keep service running for 30 days (give users time to export data if needed)
   - After 30 days, shut down cleanly (not abrupt crash)
   - Preserve source code (open-source if appropriate, archive privately otherwise)

3. **Post-mortem (1 week)**
   - Document why you shut down (for yourself and future founders)
   - Write post-mortem blog post (be honest, helps others learn)
   - Share learnings with Indonesia startup community

4. **Preserve relationships**
   - Thank users publicly
   - Thank any advisors/investors/supporters
   - Leave door open for future collaboration

5. **Plan next move**
   - What did you learn?
   - What would you do differently?
   - What's the next idea?

---

## PART C: 30-60-90 Day Critical Tests

These are the tests that determine whether the entire strategy is viable. Pass all 5, and you have 85% confidence of reaching Month 12. Fail 2+, and you need to pivot immediately.

### Test 1: Does the "Wajar" Verdict Trigger Sharing Behavior?

**Hypothesis:** Users who receive a "Di Bawah Pasar" (below market) verdict will voluntarily share the verdict to WhatsApp without incentive. This sharing creates organic viral loop.

**Why it matters:** If 0% of users share verdicts, TikTok-first GTM is not viable. Organic growth cannot happen if the product is not shareable.

**Setup:**
- Day 1: Add share button on verdict page (below the verdict, above the paid gate)
- Share destination: WhatsApp, Twitter, Facebook (standard social share buttons)
- UTM tracking: Every shared link includes `utm_source=verdict_share&utm_campaign=[verdict_type]`
- Data: Track share_button_clicks and subsequent link_clicks from share

**Pass Criteria:**
- >8% of users who see a "Di Bawah Pasar" verdict click the share button (absolute minimum)
- >5% of those shares actually result in clicks (people click the shared link)
- Share rate is HIGHER for "Di Bawah Pasar" than for "Wajar" or "Di Atas Pasar" (conditional on verdict)

**Fail Criteria:**
- <3% of users click share button (verdict is not compelling enough to share)
- <2% of shares are clicked (shared verdict is not interesting to recipients)
- No difference in share rate between verdict types (sharing is random, not verdict-driven)

**Timeline:**
- Setup: 2-3 hours (add share buttons, analytics tracking)
- Measurement: 14 days (need 1,000+ verdict pageviews to see statistically significant data)
- Sample size: With 70-100 daily verdict views, 14 days = 1,000 verdicts. Minimum 80 shares needed to pass (8%)

**Data Collection:**
- Create dashboard showing:
  - Share button click rate by verdict type
  - Click-through rate on shared links (by UTM)
  - Conversion rate of shared-link clicks (do they install? submit salary?)

**Confidence if Passed:** 60% that organic/viral growth is possible.
**Action if Passed:** Proceed with confidence on TikTok GTM (sharing will amplify reach).
**Action if Failed:** Immediate message redesign. Maybe "wajar" verdict is not compelling enough. Consider adding emotional hook ("You're underpaid by IDR 3M/month") to increase sharability.

---

### Test 2: Does the Freemium Gate Convert?

**Hypothesis:** Users who hit the premium gate (e.g., wanting to see P25/P75 salary range) will upgrade to see the data. Specifically:
- >5% of gate hitters will click the "Upgrade" CTA
- >2% of gate hitters will complete payment and become paying user

**Why it matters:** Entire business model depends on this. If gate converts <1%, monetization is broken.

**Setup:**
- Day 1: Launch freemium gate showing "Lihat gaji P25/P75 — upgrade untuk akses"
- Gate mechanic: Free users see verdict ("Di Atas Pasar") but not range. Paid users see full range.
- Analytics: Track impression → click → payment_complete funnel

**Pass Criteria:**
- >5% of gate impressions result in "Upgrade" CTA click (intent signal)
- >2% of users who click CTA complete payment (conversion)
- Implicit: At 50K MAU, this means 2,500 annual paying users (gross revenue: IDR 870M, net after payment processing: IDR 700M)

**Fail Criteria:**
- <1% click upgrade CTA (gate is not valuable enough)
- <0.5% complete payment (price is too high, or trust is too low)
- Both suggest product redesign needed before scaling

**Timeline:**
- Setup: 1-2 hours (add gate, payment integration)
- Measurement: 21 days (need ~1,000 gate impressions to see significant data)
- Sample size: With 70-100 daily verdicts, 21 days = ~2,100 verdict pageviews, maybe 1,400 gate impressions (if 2/3 hit gate)

**Data Collection:**
- Dashboard:
  - Gate impressions / day
  - Click-to-upgrade rate / day
  - Payment completion rate / day
  - Cohort retention: % of paying users still active Week 2, 4, 8

**Confidence if Passed:** 75% that monetization model is viable at scale.
**Action if Passed:** Scale acquisition aggressively, optimize gate and CTA for higher conversion.
**Action if Failed:** Test different gates (see Failure Mode 6). Don't assume the specific gate is optimal.

---

### Test 3: Can BPS + Crowdsource Data Produce Accurate Verdicts?

**Hypothesis:** Salary benchmarks for the 20 most common job titles in Jakarta are within ±20% of "ground truth" (verified market salary from independent sources like Michael Page, Robert Walters, Payscale data).

**Why it matters:** If benchmarks are wildly inaccurate from Day 1, no amount of user submissions will fix it. Bad data compounds.

**Setup (Week -1 Before Launch):**
- Identify: Top 20 job titles in Indonesia by search volume (Software Engineer, Product Manager, UI/UX Designer, Marketing Manager, Sales Manager, Finance Manager, HR Manager, etc.)
- For each title, research market salary:
  - Michael Page Salary Guide 2024 (Indonesia edition)
  - Robert Walters Salary Survey
  - Payscale Indonesia data (if available)
  - BPS official data
  - LinkedIn Salary (if available for Indonesia)
  - Take average of 3+ sources as "ground truth"
- Benchmark: Calculate cekwajar.id's predicted salary for each title/Jakarta combination
- Deviation: Calculate % deviation from ground truth
  - Formula: (cekwajar_prediction - ground_truth) / ground_truth × 100%

**Pass Criteria:**
- >80% of 20 job × Jakarta combinations are within ±20% of ground truth
- No single job title has >50% deviation
- P50 (median) salary is within ±10% (stricter requirement for median)

**Fail Criteria:**
- >30% of combinations have >50% deviation (data is fundamentally broken)
- P25/P75 range doesn't make sense (e.g., P25 > P50, which is mathematically impossible)

**Timeline:**
- Research: 6-8 hours (find 3+ sources for each job title, compile data)
- Analysis: 2-3 hours (calculate deviations, create report)
- Measurement: Can be done in parallel with feature development, results available Week -1

**Data Collection:**
- Spreadsheet showing:
  - Job title, Ground truth salary (range), cekwajar prediction, Deviation, Pass/fail
- Report summary: "19/20 titles within ±20%, 1 title (Management Consultant) at -35% (fixable)"

**Confidence if Passed:** 80% that initial data quality is acceptable for launch. Users won't immediately distrust verdicts.
**Action if Passed:** Launch Wajar Gaji with confidence.
**Action if Failed:** Do NOT launch. Fix data sourcing (add more BPS data, adjust methodology). Takes 1-2 weeks. Launch delay is acceptable.

---

### Test 4: Is There Real Willingness to Pay BEFORE Building Payment Infrastructure?

**Hypothesis:** At least 2% of free verdict users will express intent to pay for premium features (proxy for willingness-to-pay), captured via email signup when they hit a "Coming Soon" paywall.

**Why it matters:** Don't build Stripe + payment infrastructure until you know users actually want to pay. Saves 2-3 weeks of engineering if WTP is low.

**Setup (Week 1-3 after launch):**
- Day 1: Launch with no payment infrastructure
- Verdict page: Show verdict free
- Gate message: "Lihat detail lengkap — fitur berbayar coming soon (IDR 15,000/bulan). Masukkan email untuk notifikasi ketika tersedia"
- Data: Track email submissions vs. verdict impressions

**Pass Criteria:**
- >5% of users who hit the "coming soon" gate submit email (high WTP signal)
- >50% of those email signups are valid (not spam emails like test@test.com)

**Fail Criteria:**
- <1% email submission (WTP is too low, product may not be valuable enough to monetize)

**Timeline:**
- Setup: 1 hour (add email form)
- Measurement: 14-21 days (collect 100+ email signups)

**Data Collection:**
- Track: Email signups by day, repeat email addresses (do people come back?), email open rate when you send "payment live" notification

**Confidence if Passed:** 65% that real money will follow when payment is live.
**Action if Passed:** Build payment infrastructure in Week 3-4. High confidence of conversion.
**Action if Failed:** Delay payment launch. Redesign verdict value prop. Test different gates (see Failure Mode 6).

---

### Test 5: Does TikTok Content Generate Targeted (Not Just Viral) Traffic?

**Hypothesis:** Users who click through from TikTok videos will have comparable engagement to organic traffic. Specifically:
- TikTok-sourced users will have >40% verdict completion rate (same as direct/organic traffic)
- Not just viral clicks, but engaged clicks

**Why it matters:** If TikTok is driving low-quality traffic (bounces quickly, doesn't use tool), it's not a good GTM channel. Better to invest in SEO or email.

**Setup:**
- Week -1: Prepare first 3 TikTok videos
- Day 1-7: Post videos with unique UTM links (`utm_source=tiktok&utm_medium=organic&utm_campaign=video_1`)
- Analytics: Track TikTok → cekwajar.id → verdict_completion funnel

**Pass Criteria:**
- TikTok-sourced users: >40% click through to tool, then complete a verdict
- Comparable to direct traffic completion rate (both >40%)
- OR: TikTok completion rate is only slightly lower (35-40%, acceptable friction from platform switch)

**Fail Criteria:**
- TikTok-sourced users: <20% complete a verdict (high bounce rate, low engagement)
- Significantly lower than direct traffic (implies content is attracting wrong audience)

**Timeline:**
- Setup: 6-8 hours to record + edit first 3 videos
- Posting: Day 1-7 (post one every 2-3 days)
- Measurement: 14 days to collect statistically significant data (need 500+ TikTok clicks)
  - With 5K reach per video × 3% CTR = 150 clicks per video × 3 videos = 450 clicks (margin)

**Data Collection:**
- Dashboard: TikTok traffic by day, bounce rate, verdict completion rate, verdict type distribution
- Hypothesis test: Is TikTok completion rate significantly different from direct traffic?

**Confidence if Passed:** 75% that TikTok is viable GTM channel and should be scaled.
**Action if Passed:** Post 3-4 TikTok videos per week. Invest in content creation.
**Action if Failed:** Pivot TikTok content from "shocking salary data" to "how-to" educational content. Current hooks (viral angle) are not pre-qualifying audience.

---

### Critical Tests Summary Table

| Test | Pass = | Fail = | Action |
|------|--------|--------|--------|
| 1. Verdict sharing | >8% share rate | <3% share rate | If fail: redesign verdict emotional appeal |
| 2. Freemium gate conversion | >5% click, >2% convert | <1% click, <0.5% convert | If fail: test different gates |
| 3. Data accuracy | 80% within ±20% | 30% with >50% deviation | If fail: delay launch, fix data sourcing |
| 4. Willingness to pay | >5% email signup | <1% email signup | If fail: redesign value prop, test gates |
| 5. TikTok engagement | >40% verdict completion from TikTok | <20% completion from TikTok | If fail: pivot to educational content |

**Combined Confidence:** If all 5 tests pass, 85% probability of reaching Month 12 viability.

---

## PART D: Founder Self-Check (Monthly Monitoring)

Print this out. Every month, mark your metrics against these signals. Be honest.

**Month 3 Monitoring Checklist:**

```
GROWTH
□ MAU >= 3,000? (If <2K, growth strategy is wrong)
□ MoM growth >= 40%? (If <20%, acquisition is not working)
□ TikTok avg reach >= 5K per video? (If <2K, content is not resonating)

PRODUCT
□ NPS >= 40? (If <30, users don't like it)
□ <10% of users report "verdict is wrong"? (If >15%, data is bad)
□ D30 retention >= 25%? (If <15%, product is not sticky)

MONEY
□ Conversion rate >= 1%? (If <0.5%, gate is not valuable)
□ No critical bugs in production? (If >3 unresolved bugs, quality is degrading)

FOUNDER HEALTH
□ Shipped features this month? (If 0, burnout warning)
□ Slept >6 hours most nights? (If <5, unsustainable)
□ One full day off per week? (If 0, burnout warning)

DECISION
- 8+ checked = Continue as planned
- 5-7 checked = Some friction, stay course but monitor closely
- <5 checked = Friction is serious, prepare pivot analysis by Month 4
```

---

## CONCLUSION: The Brutal Truth

You are starting cekwajar.id with:
- **Advantage:** Untapped market (no dominant salary benchmark platform in Indonesia yet), fast execution (AI-first means you can move 10x faster than traditional startup)
- **Disadvantage:** Solo founder (burnout, single point of failure), consumer monetization (low conversion rates likely), TikTok dependency (algorithm risk), regulatory risk (tax/payroll is regulated)

**Probability of reaching Month 12 with original strategy intact:** 35%

**Probability of reaching Month 18 in some form (pivoted or scaled):** 65%

**Probability of learning something valuable and moving to next project:** 95%

The difference between those first two numbers (35% vs 65%) is not pessimism. It's the difference between:
- Executing perfectly as planned (35%)
- Executing well enough to notice problems at Month 3-6 and pivoting early (65%)

Your job is not to hit the 35%. Your job is to avoid being in the 35% who fail because they ignored early warning signals.

This document is your early warning system.

**Review this document every month. Update it as you learn.**

---

**End of Document**

*Last Updated: Month 0 (Pre-Launch)*
*Next Review: Month 3*

