---
title: cekwajar-id
type: project
status: active
tags: [indonesia, salary, fairness, web-app, nextjs, supabase, vecel, freemium, bpjs, pph21]
created: 2026-04-13
updated: 2026-04-13
summary: "cekwajar.id (meaning 'is it fair?' in Indonesian) is a wage fairness platform for Indonesian workers launching with Wajar Slip MVP: a payslip compliance auditor that verifies PPh21 TER, progressive tax, and 6-component BPJS deductions against regulatory formulas. Built with Next.js 15 App Router, Supabase PostgreSQL with Row Level Security, and Vercel deployment. Freemium model at IDR 29K Basic / IDR 79K Pro per month. Target: May 2026 launch with 136 engineering hours. Kill criteria: less than 0.5% conversion at Month 3 or any confirmed PPh21 calculation error."
wikilinks:
  - [[./entities/supabase]]
  - [[architecture/cekwajar-tech-stack]]
  - [[./concepts/freemium-gate]]
  - [[architecture/cekwajar-verdict-engine]]
  - [[projects/rumahlabuh-com]]
confidence: high
source: implementation
---

# cekwajar.id

## TL;DR

cekwajar.id is an Indonesian wage fairness platform targeting the 60%+ of formal workers who cannot independently verify whether their PPh21 and BPJS deductions are correct. The MVP launches with Wajar Slip only — a payslip compliance auditor powered by a deterministic calculation engine implementing PMK 168/2023 TER method, UU HPP No.7/2021 progressive brackets, and PP 46/2015/PP 45/2015 BPJS formulas. Built with Next.js 15 + Supabase + Vercel. Freemium model at IDR 29K Basic / IDR 79K Pro. Solo founder, 4-6h/day productive capacity, 136 engineering hours to MVP. Target launch: May 2026.

---

## 1. Problem Statement

Indonesian formal workers face a structural information asymmetry in payroll:

**PPh21 Complexity**: Since January 2024, PPh21 uses the TER (Tarif Efektif Rata-rata) method per PMK 168/2023 — a pre-computed effective rate table that simplifies monthly withholding but differs from the progressive bracket true-up required in December. Most employees do not understand this dual-system, and SME payroll systems frequently miscalculate.

**BPJS Opacity**: The 6-component BPJS system (JHT employee 2% + employer 3.7%, JP employee 1% + employer 2%, JKK employer 0.24-1.74%, JKM employer 0.30%, Kesehatan employee 1% + employer 4%) with two salary caps (JP capped at IDR 9.56M/month, Kesehatan capped at IDR 12M/month) is complex. Underpayment and missing deductions are common in SME payroll.

**Zero Verification Tools**: Workers have no accessible way to verify their payslip. Glassdoor is not Indonesia-localized. HR software is B2B-only. Tax consultants cost IDR 500K+ per consultation.

**cekwajar.id answer**: "Is my payslip correct?" — a self-service tool that reads or accepts payslip data, calculates what deductions SHOULD be, and reports violations with IDR amounts.

---

## 2. The 5-Tool Vision

cekWajar.id's long-term roadmap spans 5 distinct fairness tools, each addressing a specific life decision where Indonesian workers face information asymmetry:

**Wajar Slip** (MVP, May 2026): The payslip compliance auditor. Employees upload or manually enter payslip data; cekWajar calculates what PPh21 TER and 6-component BPJS should be deducted; reports violations with IDR shortfall amounts. This is the data foundation — every payslip audit creates an anonymized salary data point.

**Wajar Gaji** (Month 6-8 gate): City-level salary benchmarks crowdsourced from payslip flywheel data. Employee enters role, city, seniority; gets P25/P50/P75 market rates. Requires 500+ verified submissions before credible. Wajar Slip users become Wajar Gaji data contributors organically.

**Wajar Hidup** (Month 6-9 gate): Cost of living comparison using BPS Susenas CPI data. Compares purchasing power across 50+ Indonesian cities. Useful for transfer decisions, career negotiations, relocation planning.

**Wajar Tanah** (Month 10-12 gate): Property price fairness using NJOP + market transaction data + property portal partnerships. Compares asking prices to fair-value estimates by neighborhood. Requires formal ATR/BPN or property portal data partnership to avoid scraping legal liability.

**Wajar Kabur** (Month 12-18 gate): PPP-adjusted international comparison. Compares Indonesian salary to cost of living in Singapore, Malaysia, Australia, Japan. Sensitive political content — requires World Bank + OECD data pipeline and political risk assessment before launch.

---

## 3. Target Users (3 Personas)

### Persona 1: Endang — HRD Staff (Jakarta, 28)
- **Primary tool**: Wajar Slip (verify payroll outputs), Wajar Gaji (benchmarks)
- **Use case**: Endang processes 50 employee payslips monthly at a mid-sized manufacturing company. She wants to verify Mekari/Gadjian-generated deductions are correct before the 25th payment run. She has found errors before — last year a new payroll officer misconfigured the JP cap, under-deducting for 3 months before detection.
- **WTP**: IDR 29K/month (Basic) — will pay from personal funds for work-related verification; company expense report is too slow
- **Pain point**: Her company uses Gadjian but she doesn't fully understand all the PPh21 TER nuances; has to rely on external tax consultant for year-end true-up
- **Trigger moment**: "I just ran December true-up and the number seems wrong — is this system bug or user error?"

### Persona 2: Dimas — Gen Z Software Engineer (Surabaya, 24)
- **Primary tool**: Wajar Slip (first payslip at new company), Wajar Kabur (comparing to Singapore offers)
- **Use case**: First real job out of university, received IDR 12M offer in Surabaya. Wants to know if this is fair for his skill level. Also comparing to a Singapore startup opportunity that offered SGD 4,500/month.
- **WTP**: IDR 79K once for a specific verification question (not recurring subscription)
- **Pain point**: No one in his circle has experience negotiating tech salaries; LinkedIn salary data is US-centric; Glassdoor Indonesia has <100 data points for his role
- **Trigger moment**: "Should I take the remote role at SGD 4,500 or stay in Surabaya at IDR 12M?"

### Persona 3: Sari — Supervisor (Bekasi, 32)
- **Primary tool**: Wajar Tanah (property), Wajar Gaji (benchmark before major purchase)
- **Use case**: Sari is considering a property purchase in Bekasi — a 2BR apartment asking IDR 850M near her factory job. She wants to know if the price is fair relative to her IDR 9M/month salary. Her colleague was quoted IDR 780M for a similar unit; another colleague says prices will drop 20% in 2026.
- **WTP**: IDR 29K once for a specific property fairness query
- **Pain point**: Real estate agent always has more information; NJOP data is 3 years stale and useless as benchmark; bank appraiser uses different methodology
- **Trigger moment**: "Is IDR 850M for this location fair? My mom says wait, my agent says buy now."

---

## 3. Tech Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| **Frontend** | Next.js 15 App Router | SSR for SEO, API routes for backend, React Server Components |
| **Database** | Supabase PostgreSQL | PostgreSQL with Row Level Security, auth, storage, pg_cron |
| **Auth** | Supabase Auth | Magic link email, phone auth for Indonesia |
| **Payments** | Midtrans | Dominant Indonesian payment gateway, supports individual merchant |
| **OCR** | Google Cloud Vision API (primary), Tesseract.js (fallback) | Best-in-class document OCR |
| **Deployment** | Vercel | Next.js native hosting, edge functions, preview deployments |
| **Document conversion** | markitdown | Microsoft library for PDF/DOCX to markdown conversion |
| **Styling** | Tailwind CSS | Utility-first, fast iteration |

### 3.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER (Mobile/Web)                        │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼ HTTPS
┌─────────────────────────────────────────────────────────────────┐
│                     VERCEL EDGE NETWORK                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Static/SSR  │  │  API Routes  │  │  Edge Fns   │          │
│  │  (Landing)   │  │  (Verdict)   │  │  (OCR prep) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                    │                    │
                    ▼                    ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│     SUPABASE (ap-southeast-1) │  │   GOOGLE CLOUD VISION  │
│  ┌──────────────────────┐  │  │   (OCR Processing)      │
│  │  PostgreSQL + RLS    │  │  └──────────────────────────┘
│  │  Auth + anon keys    │  │
│  │  Storage (payslips)  │  │
│  │  pg_cron (30-day     │  │
│  │  auto-delete)        │  │
│  └──────────────────────┘  │
└──────────────────────────────┘
                    │
                    ▼
┌──────────────────────────┐
│       MIDTRANS           │
│   (Payment Processing)   │
│   IDR 29K/79K/month      │
└──────────────────────────┘
```

### 3.2 Database Schema (Key Tables)

```sql
-- Payslip submissions (anonymized after 90 days)
CREATE TABLE payslip_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    period TEXT NOT NULL,  -- "2026-04"
    gaji_pokok BIGINT NOT NULL,
    tunjangan JSONB DEFAULT '{}',
    bpjs_extracted JSONB,
    pph21_extracted BIGINT,
    net_salary BIGINT NOT NULL,
    city TEXT NOT NULL,
    company_industry TEXT,
    ocr_confidence FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Payslip verdicts (permanent, no raw image reference)
CREATE TABLE payslip_verdicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID REFERENCES payslip_submissions(id),
    user_id UUID REFERENCES auth.users(id),
    calculation JSONB NOT NULL,  -- Full PPh21/BPJS calculations
    violations JSONB DEFAULT '[]',
    verdict_status TEXT NOT NULL,  -- COMPLIANT, VIOLATIONS_FOUND, BELOW_UMK
    confidence_score INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Anonymized benchmark data (from payslip flywheel)
CREATE TABLE salary_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    province TEXT NOT NULL,
    city TEXT,
    job_category TEXT NOT NULL,
    seniority_band TEXT DEFAULT 'mid',
    salary_p50 BIGINT,
    sample_size INT DEFAULT 0,
    source TEXT DEFAULT 'payslip_flywheel',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: Users can only read their own data
ALTER TABLE payslip_submissions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_submissions" ON payslip_submissions
    FOR SELECT USING (auth.uid() = user_id);
```

---

## 5. Freemium Model

### 5.1 Pricing Tiers

| Feature | Free | Basic IDR 29K/mo | Pro IDR 79K/mo |
|---------|------|-----------------|----------------|
| PPh21 calculation | ✅ | ✅ | ✅ |
| BPJS calculation | ✅ | ✅ | ✅ |
| Violation codes (V01-V07) | First 1 only | All codes | All |
| IDR shortfall amounts | ❌ | ✅ | ✅ |
| OCR upload | 1/lifetime | 10/month | Unlimited |
| Audit history | None | 3 months | Unlimited |
| PDF report | ❌ | ✅ | ✅ |
| December true-up sim | ❌ | ❌ | ✅ |

### 5.2 Freemium Gate Mechanics

The freemium gate is designed around a single insight: **Indonesian workers pay when they know exactly how much money is at stake**. Abstract fairness concerns do not convert; concrete IDR amounts do.

**Free user experience**:
1. Upload payslip PDF or enter manual data
2. System calculates PPh21 TER and 6-component BPJS
3. Free verdict: "COMPLIANT ✅" OR "2 VIOLATIONS FOUND ⚠️"
4. If violations: See violation codes only (e.g., "V02: BPJS JHT underpaid" — no amount)
5. Paywall prompt: "Unlock IDR shortfall amounts — subscribe for IDR 29K/month"

**Paid user experience**:
1. All free features
2. See exact IDR shortfall per violation (e.g., "BPJS JHT underpaid IDR 37,200/bulan × 12 = IDR 446,400/year")
3. See IDR amount employer owes for all violations combined
4. PDF report for HR negotiation or legal counsel
5. December PPh21 progressive true-up simulation (Pro tier)

**Conversion psychology**: The free tier shows the violation exists. The paid tier reveals the stakes. "Your employer has been underpaying your JHT by IDR 446,400/year for 2 years = IDR 892,800 owed" is a different conversation than "your payslip has a violation."

### 5.3 Freemium Funnel Metrics

Target funnel metrics for MVP launch:
- Landing page → Sign up: 8-12%
- Sign up → First audit: 60-70%
- First audit → Paid conversion: 2-4%
- Paid 30-day retention: >70%
- Paid 90-day retention: >50%

Conversion failure modes:
- Too many steps to first audit → simplify onboarding
- OCR failures → improve fallback to manual entry
- Payment friction → Midtrans installment options for Pro
- No violations found → freemium users feel no urgency; need trust-building content

### 5.4 Annual vs Monthly Subscription

Single-tier monthly (IDR 29K Basic, IDR 79K Pro) for MVP. Annual subscriptions (2 months free = IDR 290K/348K) added at Month 4-6 after:
- Midtrans recurring payment integration validated
- 30+ monthly subscribers to test annual conversion
- Content calendar for annual subscriber retention campaigns

---

## 5. Current MVP Scope (v1 — Wajar Slip Only)

Per ADR-2026-04-13-cekwajar-mvp-scope-lock, v1 excludes Wajar Gaji, Wajar Tanah, Wajar Kabur, Wajar Hidup until release gates are met.

**136 engineering hours breakdown**:
- PDF payslip upload: 8h
- OCR integration (Vision + Tesseract fallback): 16h
- PPh21 TER engine: 20h
- PPh21 progressive annual true-up: 12h
- BPJS 6-component engine: 16h
- Violation detection (V01-V07): 10h
- UU PDP consent flow: 6h
- Manual field override: 8h
- Freemium gate: 4h
- Midtrans integration: 10h
- Share card generation: 6h
- 30-day auto-delete cron: 4h
- Basic dashboard: 12h
- Verdict history: 4h
- PSE registration: 0h code

---

## 6. Launch Timeline

| Milestone | Target | Dependencies |
|-----------|--------|--------------|
| MVP feature complete | Week 5 | All 136h done |
| Tax consultant audit | Week 6 | PKP reviews TC-01 through TC-15 |
| UU PDP consent flow | Week 4 | Legal review |
| Midtrans sandbox | Week 3 | Production after audit |
| Supabase migration (us-east-1 → ap-southeast-1) | Week 1 | Cross-border transfer compliance |
| Privacy Policy + ToS | Week 5-6 | Lawyer review |
| Public beta (200 users) | Week 7 | All above |
| Public launch | Week 8 (May 2026) | Beta feedback incorporated |

---

## 7. Kill Criteria

### Tool-Level (Wajar Slip)
- **Calculation error**: Any confirmed PPh21/BPJS error → pull tool, fix, re-audit all 15 test cases
- **OCR accuracy**: AUTO_ACCEPT rate < 50% at launch → disable OCR path, manual form only
- **Zero paying users after 60 days** → pivot pricing or tool framing

### Platform-Level
- Government (DJP, Kemnaker, OJK) sends formal cease-and-desist
- Security breach exposing user payslip data
- Confirmed systematic PPh21 errors affecting >100 users
- MAU < 100 for 3 consecutive months after Month 6

---

## 9. GTM Channels

### 9.1 Channel Mix

| Channel | Month 1-6 MAU Target | CAC | Conversion |
|---------|---------------------|-----|-----------|
| TikTok organic | 2,000-4,000 | IDR 60-120K | 2.0-3.0% |
| Google SEO | 500-1,500 | IDR 30-80K | 1.5-2.5% |
| WhatsApp/Telegram communities | 200-600 | IDR 10-30K | 3.0-5.0% |
| Reddit r/indonesia | 100-300 | IDR 5-20K | 4.0-7.0% |

### 9.2 TikTok Content Strategy

**60% viral + 40% trust in Month 1-3**:
- Viral: "Gaji lo wajar nggak?" salary reveal, "Boss gue nggak bayar BPJS — ini buktinya"
- Trust: Step-by-step "cara cek slip gajimu", real user proof of IDR X found

**Batch production**: Film 8-10 videos in one day per week. 12-15 hours/week total content time sustainable for solo founder.

**Content pillars for Month 1-6**:
1. **Salary reveal** (30%): "Gaji gue di [company类型] sekarang [amount] — wajar nggak?" — engagement bait, community building
2. **Violation proof** (20%): "Cek slip gue nemuin masalah [violation type] — ini cara gue nemuin" — trust building, conversion
3. **Tutorial** (25%): "Step-by-step cek slip gajimu dalam 5 menit" — SEO value, trust, evergreen
4. **Industry news** (15%): PPh21 regulation changes, UMK updates, BPJS cap changes — timely, shareable
5. **User testimonials** (10%): After 50+ paying users — "Gue nemuin IDR X dari payslip gue" — social proof

### 9.3 Google SEO Strategy

Target keywords for organic acquisition:
- Primary: "cara cek slip gaji" (500-800 monthly searches), "cek pajak gaji" (300-500)
- Secondary: "BPJS kesehatan potongan" (200-400), "PPh21 TER" (100-200)
- Long-tail: "aplikasi cek payslip" (50-100), "verifikasi slip gaji online" (30-50)

SEO approach:
- Landing page optimized for primary keywords
- Blog content for secondary/long-tail (tax calculator guides, Indonesian payroll explainers)
- Internal linking between blog posts and tool
- Build backlinks via tax consultant partnerships and HR software reviews

### 9.4 Community Channels

WhatsApp and Telegram communities for Indonesian workers:
- Reddit r/indonesia (English and Bahasa threads)
- Facebook groups: "Gaji Indonesia", "Kerja di Jakarta", "HR Indonesia"
- Telegram: @grabgajian (salary discussion), @digitalnomad_id (expat/remote)
- Kaskus forum (older demographic, underutilized)

Community strategy:
- Provide genuine value (payroll tips, regulation updates) before promotion
- Engage authentically — solo founder voice, not corporate
- Target communities with HR/finance professionals who will share with their networks

### 9.5 May 2026 Launch Timeline

| Week | Milestone | Success Criteria |
|------|-----------|------------------|
| 1-2 | Soft launch to 50 personal network users | 30+ audits completed, zero crashes |
| 3-4 | Invite 200 beta users (HR communities) | AUTO_ACCEPT rate >55%, NPS >40 |
| 5 | Tax consultant audit (TC-01 to TC-15) | Zero calculation errors |
| 6 | Midtrans production activation | Payment flow tested |
| 7 | Public beta with waitlist | 500+ signups from TikTok |
| 8 (May 2026) | Public launch | 1,000+ MAU, first paying subscribers |

### 9.6 Kill Criteria

**Launch gate (Week 8)**:
- <200 signups by Week 6: Investigate channel mix, improve content
- <0.5% trial-to-paid by Week 8: Re-examine paywall positioning, lower entry price
- Any confirmed PPh21/BPJS calculation error: Pause launch, fix, re-audit

**Post-launch (Month 3)**:
- <50 paying subscribers: Pivot freemium model or GTM
- AUTO_ACCEPT rate <50%: Disable OCR, manual form only
- >3 confirmed calculation errors: Pull tool, full audit, relaunch

**Platform-level kill criteria**:
- Government (DJP, Kemnaker) formal C&D: Immediate compliance review
- Security breach: Shutter immediately, notify users per UU PDP
- >100 users affected by systematic error: Full platform audit before resume

---

---

## 10. Financial Model

### Unit Economics

| Metric | Value |
|--------|-------|
| ARPU | IDR 45.5K/month |
| LTV:CAC ratio | **7:1** (target) |
| CAC payback | 1.4 months |
| Monthly churn | 8% |
| Breakeven | Month 17–19 (base case) |

### 3-Year Scenarios

| Scenario | Month 36 Revenue | Month 36 MAU | Survival? |
|----------|-----------------|--------------|-----------|
| Pessimistic | IDR 125M/mo | 3,000 | ✅ Month 19 |
| **Base** | IDR 360M/mo | 10,000 | ✅ Month 17 |
| Optimistic | IDR 1.2B/mo | 30,000 | ✅ Month 14 |

### Cost Structure (Monthly, Base Case)

| Category | Month 6 | Month 18 | Month 36 |
|----------|---------|----------|----------|
| Vercel (Pro) | IDR 1.2M | IDR 2.5M | IDR 5M |
| Supabase (Pro) | IDR 1.5M | IDR 3M | IDR 6M |
| Midtrans fees | 2.5% | 2.5% | 2.5% |
| LLM APIs | IDR 1M | IDR 2M | IDR 5M |
| Swarms agents | IDR 0.5M | IDR 2M | IDR 5M |
| Total COGS | ~IDR 5M | ~IDR 12M | ~IDR 25M |

### 17 Swarms Agents

| Agent | Role |
|-------|------|
| `DataHarvestAgent` | Scrapes UMK data from Kemnaker |
| `UMRUpdaterAgent` | Updates UMK database per province |
| `PPh21UpdaterAgent` | Tracks TER table changes (PMK 168/2023) |
| `NJOPHarvesterAgent` | Collects NJOP per municipality |
| `ListingScraperAgent` | Scrapes 99.co/Rumah123 listings |
| `CrowdsourceValidatorAgent` | Validates crowdsourced salary data |
| `ContentFactoryAgent` | Generates SEO blog content |
| `SEOPageGeneratorAgent` | Generates tool pages per keyword |
| `SupportBotAgent` | Handles Tier 1 support queries |
| `BenchmarkAggregatorAgent` | Aggregates salary benchmarks |
| `ChurnPredictorAgent` | Identifies at-risk subscribers |
| `AbuseDetectorAgent` | Detects OCR/payslip fraud |
| `AlertingAgent` | Monitors calculation anomalies |
| `DataQualityAgent` | Validates crowdsource submissions |
| `CompetitorMonitorAgent` | Tracks Glints/WaChrome pricing |
| `RevenueReportAgent` | Generates daily revenue dashboards |
| `UserOnboardingAgent` | Guides new free → paid conversion |

---

## 11. Technical Architecture

### Rendering Strategy (Next.js 15)

| Page | Strategy | Rationale |
|------|---------|-----------|
| Landing page | SSG | SEO, near-instant |
| Tool pages (wajar-slip) | ISR (1hr) | Fresh P50 data without rebuild |
| User dashboard | SSR | Personalized, auth required |
| Blog posts | SSG + ISR | SEO + fresh content |
| API routes | Edge | Low latency verdict responses |
| Webhook handlers | Edge | Payment processing |

### Supabase Edge Functions

| Function | Purpose |
|----------|---------|
| `calculate_salary_verdict` | Wajar Gaji benchmark aggregation |
| `calculate_slip_compliance` | Wajar Slip violation detection |
| `calculate_land_verdict` | Wajar Tanah price fairness |

### Midtrans Payment Flows

| Flow | Trigger | Midtrans Method |
|------|---------|----------------|
| Monthly subscription | Basic/Pro monthly | `subscription` |
| Annual subscription | 2 months free deal | `subscription` with `reccurance_token` |
| One-time report | Wajar Tanah single query | `snap.createTransaction` |
| B2B invoice | SME/Enterprise billing | `snap.createTransaction` with cust_email |

### 3-Layer Rate Limiting

1. **Vercel Edge**: 100 req/min per IP (free tier)
2. **Redis** (Upstash): 1000 req/min per user for verdict APIs
3. **Supabase RLS**: Anonymous users limited to 5 audits/month

### UU PDP Compliance

- Consent banner on first visit (not on return visits)
- Payslip images **never stored** — OCR → text → raw image deleted immediately
- Benchmark data anonymized via k-anonymity (n ≥ 10 per cell)
- Data retention: 90 days for audit history (auto-delete via pg_cron)
- Export/delete: User can request full data export or account deletion

---

## 12. Fundraising Framework

### Decision Tree

```
Start (Bootstrap)
  │
  ├─► Month 6 revenue > IDR 50M/mo?
  │     YES → Consider Angel (IDR 500M-1B for 10-15%)
  │     NO  → Continue bootstrap
  │
  └─► Month 12 revenue > IDR 100M/mo?
        YES → Consider Seed (IDR 3-5B for 15-20%)
        NO  → Reassess or wind down
```

### Target Acquirers

| Company | Rationale |
|---------|----------|
| BCA Digital | Digital banking + payroll integration |
| GOTO (Gojek) | Employee benefits platform play |
| PropertyGuru (Indonesia) | Wajar Tanah data synergy |
| Glints | Recruitment + salary data |
| KoinWorks | MSME payroll + lending |

**Target valuation at exit**: IDR 1.2B–2.4B (2–4× ARR at 10K MAU, IDR 360M ARR)

---

## 13. Out of Scope (Permanent)

- SPT 1770/1721-A1 form generation (tax filing)
- Property listings (benchmarks only)
- B2B payroll processing ( Month 9+ only)
- Investment or financial product referral
- Real-time stock or crypto data
- Legal document generation
- English/Mandarin support before Month 9
- Native iOS/Android app before Month 12

---

## 14. Related Articles

- [[architecture/cekwajar-verdict-engine]] — Technical implementation of the compliance calculation
- [[architecture/cekwajar-tech-stack]] — Architecture details
- [[architecture/cekwajar-data-sources]] — Data sources per tool (BPS, Kemnaker, World Bank)
- [[architecture/cekwajar-ocr-pipeline]] — OCR pipeline with confidence thresholds
- [[./concepts/freemium-gate]] — Freemium access control pattern
- [[./entities/supabase]] — Database provider
- [[concepts/bpjs-reference]] — Regulatory formulas for 6-component BPJS
- [[concepts/tax-indonesia]] — PPh21 TER and progressive calculation
- [[concepts/labor-law-indonesia]] — Employment law for violation detection
- [[concepts/bayesian-blending]] — Wajar Gaji P50 formula with k=15 smoothing
- [[concepts/market-data-indonesia]] — Data collection strategy
- [[decisions/adr-2026-04-13-cekwajar-mvp-scope-lock]] — MVP scope decision
