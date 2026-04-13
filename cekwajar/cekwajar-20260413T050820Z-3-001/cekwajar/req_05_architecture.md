# req_05 — Architecture Documents: cekwajar.id
**Covers:** 2.1 System Architecture | 2.2 Tech Stack ADR | 2.3 Directory Structure | 2.4 Env Vars | 2.5 Service Dependency Map

---

## 2.1 System Architecture

### Data Flow Diagram (Text Representation)

```
┌─────────────────────────────────────────────────────────────┐
│                    USER (Browser / Mobile)                   │
│   Rina (Android), Dimas (MacBook), Sari (iPhone Safari)     │
└──────────────────────┬──────────────────────────────────────┘
                       │  HTTPS Request
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  VERCEL EDGE NETWORK                         │
│  • Edge Middleware: IP rate limiting (10 req/min on /api/)  │
│  • Static asset CDN (Tailwind CSS, fonts, images)           │
│  • Preview URLs per git branch                              │
│  Domain: cekwajar.id → Vercel                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│               NEXT.JS 15 APP ROUTER (Vercel)                 │
│                                                             │
│  /app/(tools)/wajar-slip/page.tsx                           │
│  /app/(tools)/wajar-gaji/page.tsx                           │
│  /app/(tools)/wajar-tanah/page.tsx                          │
│  /app/(tools)/wajar-kabur/page.tsx                          │
│  /app/(tools)/wajar-hidup/page.tsx                          │
│                                                             │
│  Server Components: SSR for SEO pages                       │
│  Client Components: Interactive forms, result cards         │
│                                                             │
│  /app/api/payslip-audit/route.ts ──────────────────────────┐│
│  /app/api/payment/create/route.ts                          ││
│  /app/api/payment/webhook/route.ts                         ││
│  /app/api/submit-salary/route.ts                           ││
│  /app/api/property-lookup/route.ts                         ││
│  /app/api/col-comparison/route.ts                          ││
│  /app/api/abroad-comparison/route.ts                       ││
└──────────────────────┬─────────────────────────────────────┘│
                       │  Supabase JS client                  │
                       ▼                                      │
┌─────────────────────────────────────────────────────────────┘
│               SUPABASE (ap-southeast-1, Singapore)           │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ PostgreSQL   │  │ Supabase     │  │ Supabase         │  │
│  │ (500MB free) │  │ Auth         │  │ Storage          │  │
│  │              │  │ (50K MAU)    │  │ (payslips bucket)│  │
│  │ All 19 tables│  │ Email + OAuth│  │ Private, 5MB max │  │
│  │ RLS enabled  │  │              │  │ 30-day auto-del  │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────┘  │
│         │                                                   │
│  ┌──────▼───────────────────────────────────────────────┐  │
│  │              SUPABASE EDGE FUNCTIONS (Deno)           │  │
│  │                                                       │  │
│  │  audit-payslip: receives form/OCR data → calc → store│  │
│  │  check-audit-limit: enforces free/paid tier limits   │  │
│  │  process-verdict: builds violation result JSON        │  │
│  │  send-payment-confirmation: Resend email trigger      │  │
│  │  purge-deleted-payslips: called by pg_cron daily      │  │
│  │  trigger-pipeline: starts Python agent pipeline       │  │
│  └──────────────────────────────────────────────────────┘  │
│         │                                                   │
│  ┌──────▼──────────────────────────────────────────────┐   │
│  │              pg_cron Jobs (Supabase)                 │   │
│  │  • delete-expired-payslips: 0 2 * * *               │   │
│  │  • daily-smoke-test: 0 3 * * *                      │   │
│  │  • cleanup-anonymous-data: 0 3 * * 0               │   │
│  │  • monthly-pipeline-trigger: 0 2 1 * *              │   │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
              ┌────────┴──────────┐
              ▼                   ▼
┌─────────────────────┐  ┌────────────────────────────────────┐
│  EXTERNAL APIs      │  │  PYTHON AGENT PIPELINE (Fly.io)    │
│                     │  │                                    │
│  Google Vision API  │  │  PropertyScraperAgent              │
│  (1K req/mo free)   │  │  SalaryScraperAgent                │
│        ↓            │  │  NumbeoScraperAgent                │
│  Amazon Textract    │  │  WorldBankDataAgent                │
│  (fallback)         │  │  BPSDataAgent                      │
│                     │  │  DataValidatorAgent                │
│  World Bank REST    │  │  BenchmarkAggregatorAgent          │
│  (free, no key)     │  │                                    │
│                     │  │  Runs: 1st of each month          │
│  Frankfurter.app    │  │  Writes to: Supabase via           │
│  (exchange rates)   │  │  service_role key                  │
│                     │  └────────────────────────────────────┘
│  Midtrans Snap      │
│  (payment gateway)  │
│                     │
│  Resend             │
│  (transactional     │
│   email)            │
└─────────────────────┘
```

### Critical Path for Wajar Slip (Most Complex)

```
1. User submits form/photo → POST /api/payslip-audit
2. Middleware checks: rate limit (IP) + audit count (user tier)
3. If file: call Google Vision → parse fields → confidence check
   - ≥0.92: auto → step 4
   - 0.70–0.92: return to client for confirmation → user edits → step 4
   - <0.70: return manual fallback form to client
4. Server: call auditPayslip(input) TypeScript function
5. Server: insert result to payslip_audits table (Supabase, RLS scoped)
6. Server: return verdict to client
7. Client: render verdict card (free or paid tier based on subscription_tier)
8. If payment: POST /api/payment/create → Midtrans → webhook → DB update → 
   client auto-refresh

Total P99 latency target: <2 seconds (manual input path), <8 seconds (OCR path)
```

---

## 2.2 Tech Stack Decision Records (ADR)

### ADR-001: Frontend Framework — Next.js 15 (App Router)

**Decision:** Next.js 15 with App Router and TypeScript  
**Date:** January 2024  
**Status:** Accepted

**Context:** Need SSR for SEO (city/keyword pages), React for interactive forms, TypeScript for calculation engine type safety, deployment to Vercel for free hosting.

**Alternatives considered:**
- **Remix 2.x:** Excellent data loading model, better file-based routing, but smaller ecosystem, less Vercel-native, fewer UI component libraries with Next.js compatibility
- **SvelteKit:** Lightest bundle, excellent DX, but team knowledge gap — calculation engine TypeScript types would be harder to share with SvelteKit's different module system
- **Nuxt 3 (Vue):** Good but Vue ecosystem smaller for Indonesian dev community if contributors added later

**Decision rationale:** Next.js 15 App Router provides Server Components (reduces JS sent to browser), Partial Prerendering (fast city benchmark pages), and @vercel/og for share cards. Vercel's free Hobby tier is purpose-built for Next.js. Cursor IDE has strongest Next.js code generation. TypeScript is non-negotiable for the calculation engine — wrong PPh21 rate = real financial harm.

**Trade-offs accepted:** App Router learning curve is steeper than Pages Router; client/server component boundary requires discipline.

---

### ADR-002: Backend / Database — Supabase

**Decision:** Supabase (PostgreSQL + Auth + Edge Functions + Storage + pg_cron)  
**Date:** January 2024  
**Status:** Accepted

**Alternatives considered:**
- **PlanetScale:** MySQL-based, excellent for scale, but: (a) no built-in auth, (b) no file storage, (c) no Edge Functions, (d) no pg_cron — would require 4 separate services, raising cost
- **Firebase (Firestore):** Real-time is overkill; NoSQL schema makes relational salary/property data complex; pricing unpredictable at scale; no SQL = harder aggregation queries
- **Railway + PostgreSQL:** Good option, but no built-in auth, storage, or edge functions; requires more glue code
- **Planetscale + Clerk + Cloudflare Workers:** Three paid services where Supabase free tier covers all three

**Decision rationale:** Supabase free tier provides 500MB PostgreSQL + RLS + Auth (50K MAU) + Storage (1GB) + Edge Functions (50K calls/month) + pg_cron — all in one platform. ap-southeast-1 (Singapore) region required for UU PDP Pasal 56 cross-border data transfer compliance. RLS is critical for payslip data isolation — Supabase makes this first-class, not an afterthought.

**Trade-offs accepted:** 500MB DB limit requires careful data lifecycle management (30-day payslip deletion is mandatory). Free tier Edge Function cold starts add ~300ms latency.

---

### ADR-003: Payment Gateway — Midtrans

**Decision:** Midtrans Snap  
**Date:** January 2024  
**Status:** Accepted

**Alternatives considered:**
- **Xendit:** Excellent product, better international coverage, but: (a) IDR 500K minimum for account activation on some plans, (b) developer experience slightly more complex for Snap-equivalent
- **DOKU:** Older infrastructure, less developer-friendly documentation, harder to test in sandbox
- **Stripe:** No GoPay/QRIS/OVO/VA support — Indonesian users require these; Stripe Indonesia launch is recent and lacks local payment methods at parity

**Decision rationale:** Midtrans is Indonesia's largest payment gateway with direct GoPay, QRIS, ShopeePay, OVO, DANA, BCA VA, Mandiri VA, BNI VA, BRI VA support. Zero setup cost. MDR 0.7% (QRIS) is lowest in market. Snap SDK is well-documented. Webhook SHA512 verification is straightforward to implement. Most Indonesian B2C SaaS companies use Midtrans.

**Trade-offs accepted:** International card MDR at 2.9% is higher than Stripe; payout settlement in IDR only (acceptable).

---

### ADR-004: OCR — Google Vision API (Primary) + Tesseract.js (Fallback)

**Decision:** Google Cloud Vision API as primary, Tesseract.js as client-side fallback  
**Date:** January 2024  
**Status:** Accepted

**Alternatives considered:**
- **AWS Textract:** Superior structured form extraction, better for payslip key-value pairs, but: (a) no free tier — $1.50 per 1,000 pages, (b) requires AWS account and credential management
- **Mindee:** Specialized document AI, excellent for receipts/invoices, but: (a) IDR equivalent cost is high, (b) no Indonesian payslip training data specifically, (c) free tier only 100 pages/month
- **Nanonets:** Good UI but expensive ($249/month for API); overkill for MVP
- **Azure Document Intelligence:** Similar to Textract, paid from first document

**Decision rationale:** Google Vision has 1,000 free DOCUMENT_TEXT_DETECTION calls per month — sufficient for early stage (33/day). DOCUMENT_TEXT_DETECTION handles multi-column payslip layouts better than simple OCR. Tesseract.js runs client-side (zero server cost, zero API call) as fallback — degrades gracefully. Can switch to Textract specifically for December batch processing later if accuracy insufficient.

**Trade-offs accepted:** 1,000/month Vision limit means ~33 OCR uploads/day before Tesseract fallback activates; Tesseract accuracy on phone photos is 60–70% vs Vision's 80–88%.

---

## 2.3 Monorepo Directory Structure Spec

```
cekwajar-id/
├── .env.local                          # Dev env vars (never committed)
├── .env.example                        # Template for onboarding
├── .gitignore                          # Includes .env.local, .env.production
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.ts
│
├── app/                                # Next.js App Router
│   ├── layout.tsx                      # Root layout (nav, cookie consent, analytics)
│   ├── page.tsx                        # Landing page (hero + 5 tool cards)
│   ├── privacy/page.tsx                # Privacy Policy (Bahasa Indonesia)
│   ├── terms/page.tsx                  # Terms of Service
│   ├── dashboard/page.tsx              # Logged-in user history + subscription status
│   ├── payment/
│   │   ├── success/page.tsx
│   │   ├── error/page.tsx
│   │   └── pending/page.tsx
│   │
│   ├── (tools)/                        # Tool pages (grouped, shared layout)
│   │   ├── layout.tsx                  # Tool nav + disclaimer footer
│   │   ├── wajar-slip/
│   │   │   ├── page.tsx               # Main audit page
│   │   │   └── result/[auditId]/page.tsx  # Permalink result
│   │   ├── wajar-gaji/
│   │   │   ├── page.tsx
│   │   │   └── submit/page.tsx        # Crowdsource submission
│   │   ├── wajar-tanah/
│   │   │   └── page.tsx
│   │   ├── wajar-kabur/
│   │   │   └── page.tsx
│   │   └── wajar-hidup/
│   │       └── page.tsx
│   │
│   ├── blog/                           # SEO content pages (SSG)
│   │   └── [slug]/page.tsx            # "umk-jakarta-2024", "gaji-software-engineer"
│   │
│   └── api/                            # API Routes
│       ├── payslip-audit/route.ts      # POST: run payslip audit
│       ├── payslip-upload/route.ts     # POST: upload file, return OCR result
│       ├── submit-salary/route.ts      # POST: anonymous salary submission
│       ├── property-lookup/route.ts    # POST: property benchmark lookup
│       ├── col-comparison/route.ts     # POST: CoL comparison (Wajar Hidup)
│       ├── abroad-comparison/route.ts  # POST: PPP comparison (Wajar Kabur)
│       └── payment/
│           ├── create/route.ts         # POST: create Midtrans transaction
│           └── webhook/route.ts        # POST: Midtrans notification handler
│
├── components/                         # Shared UI components
│   ├── layout/
│   │   ├── Navbar.tsx
│   │   ├── Footer.tsx
│   │   └── ToolLayout.tsx
│   ├── common/
│   │   ├── VerdictCard.tsx            # BERSIH / ADA PELANGGARAN / MURAH / MAHAL
│   │   ├── ConfidenceBadge.tsx        # Low / Cukup / Terverifikasi
│   │   ├── FreemiumGate.tsx           # Blur overlay + upgrade CTA
│   │   ├── ConsentModal.tsx           # UU PDP consent before upload
│   │   ├── DisclaimerBanner.tsx       # Tool-specific disclaimer text
│   │   ├── LoadingSpinner.tsx
│   │   └── ErrorBoundary.tsx
│   ├── wajar-slip/
│   │   ├── PayslipUploadZone.tsx      # Drag-and-drop + file picker
│   │   ├── ManualInputForm.tsx        # Full deduction input form
│   │   ├── OCRConfirmForm.tsx         # Soft-check pre-fill confirmation
│   │   ├── ViolationAlert.tsx         # Single violation card (V01–V07)
│   │   └── AuditResultCard.tsx        # Full verdict display
│   ├── wajar-gaji/
│   │   ├── SalaryInputForm.tsx
│   │   ├── SalaryRangeBar.tsx         # P25/P50/P75 bar chart
│   │   └── SalarySubmitForm.tsx       # Anonymous crowdsource submission
│   ├── wajar-tanah/
│   │   ├── PropertyInputForm.tsx
│   │   ├── PropertyVerdictCard.tsx
│   │   └── PriceRangeChart.tsx
│   ├── wajar-kabur/
│   │   ├── AbilityInputForm.tsx
│   │   └── CountryComparisonCard.tsx
│   └── wajar-hidup/
│       ├── CityInputForm.tsx
│       └── COLBreakdownTable.tsx
│
├── lib/                                # Business logic (no UI)
│   ├── calculations/
│   │   ├── pph21.ts                   # PPh21 TER + progressive engine
│   │   ├── bpjs.ts                    # BPJS 6-component calculation
│   │   ├── violations.ts              # V01–V07 detection
│   │   ├── salary-blend.ts            # Bayesian blending
│   │   ├── property-verdict.ts        # MURAH/WAJAR/MAHAL logic
│   │   ├── col-adjustment.ts          # Cost of living formula
│   │   └── ppp-conversion.ts          # PPP conversion formula
│   ├── ocr/
│   │   ├── payslip-ocr.ts             # OCR orchestrator (Vision + Tesseract)
│   │   ├── field-extractor.ts         # Field parsing from raw OCR text
│   │   └── confidence-router.ts       # Routes to auto/confirm/manual path
│   ├── payments/
│   │   ├── midtrans.ts                # Snap transaction + webhook verify
│   │   └── subscription.ts            # Tier checking utilities
│   ├── data/
│   │   ├── world-bank.ts              # World Bank PPP API client
│   │   ├── exchange-rates.ts          # Frankfurter.app client
│   │   └── umk-lookup.ts             # City UMK lookup (from DB)
│   ├── supabase/
│   │   ├── client.ts                  # Browser client
│   │   ├── server.ts                  # Server client (Server Components + API Routes)
│   │   └── middleware.ts              # Auth session refresh
│   └── utils/
│       ├── format-idr.ts              # IDR number formatting
│       ├── date-utils.ts
│       └── validation.ts              # Input sanitization
│
├── agents/                             # Python AI agent pipeline
│   ├── requirements.txt
│   ├── config.py
│   ├── base_agent.py
│   ├── scrapers/
│   │   ├── property_scraper.py
│   │   ├── salary_scraper.py
│   │   ├── numbeo_scraper.py
│   │   └── levelsfyi_scraper.py
│   ├── data_loaders/
│   │   ├── bps_loader.py
│   │   ├── umk_loader.py
│   │   ├── njop_loader.py
│   │   └── world_bank_loader.py
│   ├── processors/
│   │   ├── data_validator.py
│   │   ├── benchmark_aggregator.py
│   │   └── anonymity_checker.py
│   └── orchestrators/
│       ├── monthly_data_refresh.py
│       └── scheduler.py
│
├── supabase/                           # Supabase project files
│   ├── migrations/
│   │   ├── 001_init.sql
│   │   ├── 002_rls.sql
│   │   ├── 003_payslip_tables.sql
│   │   ├── 004_salary_tables.sql
│   │   ├── 005_property_tables.sql
│   │   ├── 006_col_tables.sql
│   │   ├── 007_payments.sql
│   │   ├── 008_agent_logs.sql
│   │   └── 009_pg_cron_jobs.sql
│   ├── seed/
│   │   ├── umk_2024.sql
│   │   ├── bpjs_rates.sql
│   │   ├── pph21_ter_rates.sql        # NOTE: verify against official PMK 168/2023
│   │   └── col_indices_seed.sql
│   └── functions/
│       ├── audit-payslip/index.ts
│       ├── check-audit-limit/index.ts
│       ├── process-verdict/index.ts
│       ├── send-payment-confirmation/index.ts
│       ├── purge-deleted-payslips/index.ts
│       └── trigger-pipeline/index.ts
│
└── docs/                               # All requirement documents (this folder)
    ├── req_01_master_prd.md
    ├── req_02_user_story_map.md
    ├── req_03_personas.md
    ├── req_04_feature_matrix.md
    ├── req_05_architecture.md          # This file
    ├── req_06_database.md
    ├── req_07_calc_engines.md
    ├── req_08_api_contracts.md
    ├── req_09_frontend_ux.md
    ├── req_10_security.md
    ├── req_11_testing.md
    └── req_12_operations.md
```

---

## 2.4 Environment Variables Manifest

**Storage rule:** `.env.local` for development only (never committed). Production variables in Vercel Dashboard → Settings → Environment Variables. Agent variables in Fly.io secrets.

| Variable | Purpose | Where to Get | Env |
|----------|---------|-------------|-----|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | Supabase Dashboard → Settings → API | Dev + Prod |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Public anon key (browser-safe) | Supabase Dashboard → Settings → API | Dev + Prod |
| `SUPABASE_SERVICE_ROLE_KEY` | Admin key — server-side ONLY | Supabase Dashboard → Settings → API | Dev + Prod (Vercel) |
| `SUPABASE_URL` | Same as NEXT_PUBLIC but for server agents | Same source | Python agents |
| `MIDTRANS_SERVER_KEY` | Midtrans server key for Snap API calls | Midtrans Dashboard → Settings → Access Keys | Prod only |
| `MIDTRANS_CLIENT_KEY` | Midtrans client key (Snap JS SDK) | Same | Dev (sandbox) + Prod |
| `MIDTRANS_IS_PRODUCTION` | Toggle sandbox/production | Manual: "true" for prod | Per env |
| `GOOGLE_VISION_API_KEY` | Google Vision REST API key | Google Cloud Console → APIs → Vision | Dev + Prod |
| `GROQ_API_KEY` | LLM for Python agents (free tier) | console.groq.com | Python agents |
| `RESEND_API_KEY` | Transactional email | resend.com dashboard | Dev + Prod |
| `NEXT_PUBLIC_APP_URL` | Base URL for callbacks | Manual: "https://cekwajar.id" | Prod; "http://localhost:3000" dev |
| `SENTRY_DSN` | Error monitoring | Sentry dashboard | Dev + Prod |
| `NUMBEO_API_KEY` | Numbeo free API (optional) | numbeo.com/api | Python agents |
| `CRON_SECRET` | Secret for securing pg_cron → Edge Function calls | Generate: `openssl rand -hex 32` | Prod |

**Never hardcode:** `SUPABASE_SERVICE_ROLE_KEY`, `MIDTRANS_SERVER_KEY`, `GOOGLE_VISION_API_KEY`

**Secret rotation schedule:**
- `SUPABASE_SERVICE_ROLE_KEY`: Rotate quarterly (Supabase: Settings → API → Rotate)
- `MIDTRANS_SERVER_KEY`: Never expose; rotate if any exposure suspected
- `GOOGLE_VISION_API_KEY`: Restrict to specific API + IP in Google Cloud Console

---

## 2.5 Third-Party Service Dependency Map

| Service | Purpose | Free Tier Limit | Fallback if Down | Upgrade Trigger |
|---------|---------|----------------|-----------------|----------------|
| **Vercel** | Frontend hosting + CDN | 100GB bandwidth/mo, 6K build minutes | — (critical dependency) | 100GB reached → Vercel Pro ($20/mo) |
| **Supabase** | PostgreSQL + Auth + Edge + Storage | 500MB DB, 50K Edge calls, 1GB storage, 50K MAU | — (critical dependency) | 80% any limit → Pro ($25/mo) |
| **Google Vision API** | Payslip OCR (primary) | 1,000 DOCUMENT_TEXT_DETECTION/mo | Tesseract.js client-side | 1,000 hit → pay $1.50/1K |
| **Tesseract.js** | OCR fallback (client-side) | Unlimited (runs in browser) | Manual form (always available) | Never (always free) |
| **Midtrans** | Payment processing | Free setup, 1% MDR | If Midtrans down: manual payment (email) | No upgrade needed |
| **World Bank REST API** | PPP conversion data | 500 req/min, no key needed | Cached data in Supabase (30-day cache) | Never (always free) |
| **Frankfurter.app** | Exchange rates (daily) | Unlimited (truly free, open source) | Fallback to hardcoded weekly rates | Never |
| **Resend** | Transactional email | 3,000 emails/mo free | Skip email (no hard failure) | 3K limit → $20/mo |
| **Sentry** | Error monitoring | 5K errors/mo free | None (monitoring-only, no user impact) | 5K hit → $26/mo |
| **Groq API** | LLM for Python agents | 30 req/min, 14,400 tokens/min free | Ollama local (if Fly.io has GPU — unlikely) | Large agent volume → pay |
| **Playwright** | Web scraping | Free (open source) | Requests+BeautifulSoup (simpler but less accurate) | Never (always free) |
| **Fly.io** | Python agent hosting | Free (256MB, 3 shared VMs) | Run agents locally on demand | 256MB OOM → $3/mo for 512MB |
| **Numbeo free API** | CoL data | 1,000 calls/mo (with registration) | Scraped Numbeo data from previous run | Never (register free) |
| **Exchangerate-api.com** | Exchange rate backup | 1,500 req/mo free | Frankfurter.app (primary) | Never (backup only) |

**Critical path analysis:** Only Vercel and Supabase are single points of failure with no graceful fallback. Both have 99.9% SLA on their paid tiers. Free tier SLA is "best effort" — acceptable for pre-revenue stage.

**Monitoring alert triggers (see req_12_operations.md):**
- Supabase DB at 80% (400MB): trigger alert
- Supabase Edge Functions at 80% (40K calls): trigger alert
- Vision API at 900 calls: switch all remaining to Tesseract
- Midtrans webhook failure rate >5%: trigger immediate investigation
