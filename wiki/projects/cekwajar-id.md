---
title: cekwajar-id
type: project
status: active
tags: [indonesia, salary, fairness, web-app, nextjs, supabase, vecel, freemium, bpjs, pph21]
created: 2026-04-13
updated: 2026-04-13
summary: "cekwajar.id (meaning 'is it fair?' in Indonesian) is a wage fairness platform for Indonesian workers launching with Wajar Slip MVP: a payslip compliance auditor that verifies PPh21 TER, progressive tax, and 6-component BPJS deductions against regulatory formulas. Built with Next.js 15 App Router, Supabase PostgreSQL with Row Level Security, and Vercel deployment. Freemium model at IDR 29K Basic / IDR 79K Pro per month. Target: May 2026 launch with 136 engineering hours. Kill criteria: less than 0.5% conversion at Month 3 or any confirmed PPh21 calculation error."
wikilinks:
  - [[supabase]]
  - [[cekwajar-tech-stack]]
  - [[freemium-gate]]
  - [[cekwajar-verdict-engine]]
  - [[rumahlabuh-com]]
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

## 2. Target Users (3 Personas)

### Persona 1: Rina — HRD Staff (Jakarta, 28)
- **Primary tool**: Wajar Slip (verify payroll outputs), Wajar Gaji (benchmarks)
- **Use case**: Rina processes 50 employee payslips monthly. She wants to verify Mekari/Gadjian-generated deductions are correct before payment run.
- **WTP**: IDR 29K/month (Basic) — will pay from personal funds for verification
- **Pain point**: Her company uses a payroll system she doesn't fully trust; has found errors before

### Persona 2: Dimas — Gen Z Software Engineer (Surabaya, 24)
- **Primary tool**: Wajar Slip (first payslip at new company), Wajar Kabur (comparing to Singapore offers)
- **Use case**: First real job, wants to know if IDR 12M offer is fair, whether to take overseas opportunity
- **WTP**: IDR 79K once for specific question (not recurring)
- **Pain point**: No one to ask, no data, negotiating blind

### Persona 3: Sari — Supervisor (Bekasi, 32)
- **Primary tool**: Wajar Tanah (property), Wajar Gaji (benchmark before buying)
- **Use case**: Considering property purchase in Bekasi, wants to know if IDR 850M asking price is fair for the area
- **WTP**: IDR 29K once for specific search
- **Pain point**: Agent always has more information, NJOP is useless as benchmark

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

## 4. Freemium Model

### 4.1 Pricing Tiers

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

### 4.2 Freemium Gate Logic

The gate moment is critical for conversion:
- **Free user sees**: "Ditemukan 2 pelanggaran (V02, V06)" — no amounts
- **Paid user sees**: "BPJS JHT underpaid IDR 37,200/bulan × 12 = IDR 446,400/year" + "Gaji pokok di bawah UMK Bekasi IDR 2,499,443"

The concrete IDR amount is the conversion trigger — "your employer owes you IDR X" is immediately actionable.

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

## 8. GTM Channels

### 8.1 Channel Mix

| Channel | Month 1-6 MAU Target | CAC | Conversion |
|---------|---------------------|-----|-----------|
| TikTok organic | 2,000-4,000 | IDR 60-120K | 2.0-3.0% |
| Google SEO | 500-1,500 | IDR 30-80K | 1.5-2.5% |
| WhatsApp/Telegram communities | 200-600 | IDR 10-30K | 3.0-5.0% |
| Reddit r/indonesia | 100-300 | IDR 5-20K | 4.0-7.0% |

### 8.2 TikTok Content Strategy

**60% viral + 40% trust in Month 1-3**:
- Viral: "Gaji lo wajar nggak?" salary reveal, "Boss gue nggak bayar BPJS — ini buktinya"
- Trust: Step-by-step "cara cek slip gajimu", real user proof of IDR X found

**Batch production**: Film 8-10 videos in one day per week. 12-15 hours/week total content time sustainable for solo founder.

---

## 9. Related Articles

- [[cekwajar-verdict-engine]] — Technical implementation of the compliance calculation
- [[cekwajar-tech-stack]] — Architecture details
- [[freemium-gate]] — Freemium access control pattern
- [[supabase]] — Database provider
- [[concepts/bpjs-reference]] — Regulatory formulas for 6-component BPJS
- [[concepts/tax-indonesia]] — PPh21 TER and progressive calculation
- [[concepts/labor-law-indonesia]] — Employment law for violation detection
- [[decisions/adr-2026-04-13-cekwajar-mvp-scope-lock]] — MVP scope decision
