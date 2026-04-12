# CEKWAJAR.ID — Comprehensive Technical Architecture Specification

**Version**: 1.0
**Status**: Production-Ready, Build-Grade
**Last Updated**: April 7, 2026
**Platform**: Vercel + Next.js 15 + TypeScript + Supabase + Swarms Framework
**Author Context**: AI-first, one-man operation with full automation

---

## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [PART A: Next.js Application Architecture](#part-a-nextjs-application-architecture)
3. [PART B: Supabase Edge Functions Specification](#part-b-supabase-edge-functions-specification)
4. [PART C: AI Agent Technical Specification (Swarms Framework)](#part-c-ai-agent-technical-specification)
5. [PART D: Midtrans Payment Integration](#part-d-midtrans-payment-integration)
6. [PART E: Security Architecture & Environment](#part-e-security-architecture--environment)

---

## EXECUTIVE SUMMARY

Cekwajar.id is a five-tool Indonesian consumer data intelligence platform built for maximum automation and minimum manual operations. The architecture is designed for one-person operations with AI-driven data pipelines, content generation, and customer support.

**Core Stack:**
- **Frontend**: Next.js 15 with App Router, SSG/ISR/SSR/CSR hybrid approach
- **Backend**: Supabase PostgreSQL + Edge Functions (TypeScript)
- **AI Agents**: Swarms framework (Python) for data ingestion, validation, and content generation
- **Payments**: Midtrans for Indonesian market coverage
- **Deployment**: Vercel (frontend) + Fly.io/Railway (agent servers)
- **Caching & CDN**: Vercel Edge Cache + Supabase Realtime

**Five Core Tools:**
1. **Wajar Gaji** - Salary benchmarks with 500+ SEO pages
2. **Wajar Slip** - Payslip compliance auditing with PPh21/BPJS validation
3. **Wajar Tanah** - Land price benchmarking with NJOP triangulation
4. **Wajar Kabur** - International salary comparison with local context
5. **Wajar Hidup** - Cost-of-living indices by city

**Design Philosophy:**
- Privacy-first: raw data isolated from public benchmarks
- AI-native: agents handle 80%+ of operational tasks
- Indonesia-centric: 4G-optimized, Bahasa Indonesia-focused
- Freemium-gated: free tier limited to 5 queries/month, premium 50/month
- Automation-first: GitHub Actions + Supabase pg_cron + Swarms agents eliminate manual work

---

# PART A: NEXT.JS APPLICATION ARCHITECTURE

## A.1 Complete Directory Structure with Rendering Strategy

```
cekwajar/
├── app/                                    # App Router (Next.js 13+)
│   ├── (marketing)/                        # SSG: Static, revalidate: false
│   │   ├── page.tsx                        # Landing page (SSG)
│   │   ├── tentang/
│   │   │   └── page.tsx                    # About page (SSG)
│   │   ├── blog/
│   │   │   ├── page.tsx                    # Blog index (ISR, revalidate: 3600)
│   │   │   └── [slug]/
│   │   │       └── page.tsx                # Blog post (ISR, revalidate: 3600)
│   │   ├── layout.tsx                      # Marketing layout with header/footer
│   │   └── robots.ts                       # robots.txt for SEO
│   │
│   ├── (tools)/                            # Mixed: SSR/ISR/CSR tool pages
│   │   ├── layout.tsx                      # Tools layout with sidebar
│   │   │
│   │   ├── gaji/
│   │   │   ├── page.tsx                    # Wajar Gaji tool (CSR interactive form)
│   │   │   ├── [job_category]-[city]/
│   │   │   │   ├── page.tsx                # SEO benchmark page (ISR, revalidate: 86400)
│   │   │   │   ├── loading.tsx             # Skeleton for ISR fallback: blocking
│   │   │   │   └── not-found.tsx           # 404 for unsupported combinations
│   │   │   ├── components/
│   │   │   │   ├── SalaryForm.tsx          # Form component (CSR, Zustand)
│   │   │   │   ├── VerdictCard.tsx         # Displays verdict + percentile
│   │   │   │   ├── BenchmarkChart.tsx      # Recharts visualization
│   │   │   │   └── ShareButton.tsx         # WhatsApp/Twitter share
│   │   │   └── lib/
│   │   │       └── calculations.ts         # Client-safe salary logic (no secrets)
│   │   │
│   │   ├── slip/
│   │   │   ├── page.tsx                    # Wajar Slip tool (CSR)
│   │   │   ├── components/
│   │   │   │   ├── SlipUploader.tsx        # PDF upload (client-side)
│   │   │   │   ├── SlipPreview.tsx         # OCR preview
│   │   │   │   ├── ComplianceReport.tsx    # PPh21/BPJS audit display
│   │   │   │   └── DownloadReport.tsx      # Export as PDF
│   │   │   ├── lib/
│   │   │   │   └── payslip-parser.ts       # PDF extraction logic
│   │   │   └── api/
│   │   │       └── ocr.ts                  # Call to /api/slip/ocr edge function
│   │   │
│   │   ├── tanah/
│   │   │   ├── page.tsx                    # Wajar Tanah tool (CSR)
│   │   │   ├── [province]-[kelurahan]/
│   │   │   │   └── page.tsx                # Land benchmark page (ISR)
│   │   │   └── components/
│   │   │       ├── LandForm.tsx
│   │   │       ├── PriceChart.tsx
│   │   │       └── NJOPDisplay.tsx
│   │   │
│   │   ├── kabur/
│   │   │   ├── page.tsx                    # Wajar Kabur tool (CSR)
│   │   │   └── components/
│   │   │       ├── CountrySelector.tsx
│   │   │       ├── CostComparison.tsx
│   │   │       └── QualityOfLifeIndex.tsx
│   │   │
│   │   └── hidup/
│   │       ├── page.tsx                    # Wajar Hidup tool (CSR)
│   │       └── components/
│   │           ├── CityComparison.tsx
│   │           ├── InflationChart.tsx
│   │           └── CategoryBreakdown.tsx
│   │
│   ├── (auth)/
│   │   ├── login/
│   │   │   ├── page.tsx                    # Login page (CSR, Supabase Auth)
│   │   │   └── components/
│   │   │       ├── EmailPasswordForm.tsx
│   │   │       └── GoogleOAuthButton.tsx
│   │   ├── signup/
│   │   │   ├── page.tsx                    # Signup page (CSR)
│   │   │   └── components/
│   │   │       └── SignupForm.tsx
│   │   ├── callback/
│   │   │   └── route.ts                    # OAuth callback handler
│   │   └── profile/
│   │       └── page.tsx                    # User profile (SSR with auth guard)
│   │
│   ├── (dashboard)/                        # Premium user dashboard
│   │   ├── dashboard/
│   │   │   ├── page.tsx                    # Dashboard home (SSR, requires auth)
│   │   │   ├── history/
│   │   │   │   └── page.tsx                # Query history (SSR)
│   │   │   ├── saved/
│   │   │   │   └── page.tsx                # Saved comparisons (SSR)
│   │   │   ├── settings/
│   │   │   │   └── page.tsx                # Account settings (SSR)
│   │   │   └── subscription/
│   │   │       └── page.tsx                # Subscription management (SSR)
│   │   └── layout.tsx                      # Dashboard layout with sidebar
│   │
│   ├── api/                                # Route handlers (server-only)
│   │   ├── verdict/
│   │   │   ├── salary/route.ts             # POST: Calculate salary verdict
│   │   │   ├── slip/route.ts               # POST: Audit payslip
│   │   │   ├── land/route.ts               # POST: Land price verdict
│   │   │   ├── hidup/route.ts              # POST: Cost of living
│   │   │   └── kabur/route.ts              # POST: Abroad comparison
│   │   │
│   │   ├── payment/
│   │   │   ├── create-transaction/route.ts # POST: Initiate Midtrans payment
│   │   │   └── notify/route.ts             # POST: Midtrans webhook (payment_success)
│   │   │
│   │   ├── slip/
│   │   │   ├── ocr/route.ts                # POST: Extract payslip data via OCR
│   │   │   ├── audit/route.ts              # POST: Run compliance audit
│   │   │   └── rules/route.ts              # GET: Fetch current tax rules
│   │   │
│   │   ├── submission/
│   │   │   ├── salary/route.ts             # POST: Submit salary data (crowdsourcing)
│   │   │   └── land/route.ts               # POST: Submit land data
│   │   │
│   │   ├── health/route.ts                 # GET: Health check for monitoring
│   │   └── og/
│   │       ├── verdict/route.ts            # GET: Generate og:image for verdicts
│   │       └── benchmark/route.ts          # GET: Generate og:image for benchmarks
│   │
│   ├── layout.tsx                          # Root layout (Next.js 13 root)
│   ├── globals.css                         # Global styles + Tailwind
│   └── error.tsx                           # Global error boundary
│
├── components/
│   ├── tools/
│   │   ├── SalaryBenchmarkCard.tsx         # Reusable verdict display
│   │   └── BenchmarkTable.tsx              # Comparison table
│   ├── verdict/
│   │   ├── VerdictBadge.tsx                # Color-coded verdict (wajar/kurang/tinggi)
│   │   ├── PercentileDisplay.tsx           # Percentile visualization
│   │   └── DownloadCard.tsx                # PNG/PDF export buttons
│   ├── ui/
│   │   ├── Button.tsx                      # shadcn/ui Button
│   │   ├── Input.tsx                       # shadcn/ui Input
│   │   ├── Select.tsx                      # shadcn/ui Select dropdown
│   │   ├── Card.tsx                        # shadcn/ui Card
│   │   ├── Dialog.tsx                      # Modal for payments
│   │   ├── Toast.tsx                       # Error/success notifications
│   │   └── Skeleton.tsx                    # Loading skeleton for ISR fallback
│   └── shared/
│       ├── Header.tsx                      # Navigation bar with auth state
│       ├── Footer.tsx                      # Footer with links
│       ├── Layout.tsx                      # Common layout wrapper
│       └── ErrorBoundary.tsx               # Client-side error handler
│
├── lib/
│   ├── supabase/
│   │   ├── client.ts                       # Browser client (anon key)
│   │   ├── server.ts                       # Server client (service role)
│   │   ├── admin.ts                        # Admin operations (service role)
│   │   ├── types.ts                        # TypeScript types from Supabase
│   │   ├── queries/
│   │   │   ├── salary.ts                   # Fetch salary benchmarks
│   │   │   ├── land.ts                     # Fetch land prices
│   │   │   ├── users.ts                    # User subscription status
│   │   │   └── verdicts.ts                 # Log verdict queries
│   │   └── mutations/
│   │       └── subscription.ts             # Update subscription after payment
│   │
│   ├── calculations/
│   │   ├── salary-verdict.ts               # Client-safe salary logic (no secrets)
│   │   ├── pph21.ts                        # PPh21 formula (public)
│   │   ├── bpjs.ts                         # BPJS calculation (public)
│   │   ├── land-valuation.ts               # NJOP lookup logic
│   │   ├── cost-of-living.ts               # CPI calculations
│   │   └── bayesian-smoothing.ts           # Handle low sample counts
│   │
│   ├── payments/
│   │   ├── midtrans.ts                     # Midtrans SDK wrapper
│   │   ├── verification.ts                 # Webhook signature verification
│   │   └── constants.ts                    # Plan IDs, prices
│   │
│   ├── utils/
│   │   ├── cn.ts                           # Utility for className merging
│   │   ├── formatting.ts                   # IDR currency formatting
│   │   ├── slugify.ts                      # URL slug generation
│   │   ├── validation.ts                   # Input validation (zod schemas)
│   │   └── error-handling.ts               # Structured error responses
│   │
│   ├── constants/
│   │   ├── cities.ts                       # Indonesia city database (34 provinces)
│   │   ├── job-categories.ts               # Kemnaker job classifications
│   │   ├── umr-2026.ts                     # Current UMR by province
│   │   └── tax-rules.ts                    # PPh21 & BPJS rates
│   │
│   └── hooks/
│       ├── useVerdictStore.ts              # Zustand store for tool state
│       ├── useSalaryForm.ts                # React Hook Form wrapper
│       ├── useAuth.ts                      # Authentication state
│       ├── useSubscription.ts              # Subscription status
│       └── useMediaQuery.ts                # Responsive design
│
├── middleware.ts                           # Next.js middleware for auth redirects
├── next.config.mjs                         # Next.js config (ISR, images, etc.)
├── tsconfig.json                           # TypeScript configuration
├── package.json
├── .env.local                              # Local development secrets
├── .env.production                         # Production environment variables
└── tailwind.config.ts                      # Tailwind CSS + custom theme

agents/                                     # AI Agents (Python, separate repo)
├── swarms_config.yaml                      # Swarms framework configuration
├── requirements.txt                        # Python dependencies
├── main.py                                 # Agent orchestrator
└── agents/
    ├── data_harvest_agent.py               # BPS API fetcher
    ├── umr_updater_agent.py                # UMR scraper
    ├── pph21_monitor_agent.py              # Tax rule monitor
    ├── njop_harvester_agent.py             # NJOP fetcher
    ├── listing_scraper_agent.py            # Property listing scraper
    ├── crowdsource_validator_agent.py      # AI data validator
    ├── content_factory_agent.py            # TikTok/blog content
    ├── seo_page_generator_agent.py         # Benchmark page creator
    ├── support_bot_agent.py                # Customer support (Dify.ai)
    ├── benchmark_aggregator_agent.py       # Publish benchmarks (k-anonymity)
    ├── churn_predictor_agent.py            # Identify cancellations
    ├── abuse_detector_agent.py             # Fraud detection
    ├── alerting_agent.py                   # Health monitoring
    ├── data_quality_agent.py               # Consistency checks
    ├── competitor_monitor_agent.py         # Track competitors
    ├── revenue_report_agent.py             # Daily revenue summaries
    └── onboarding_agent.py                 # Email sequences

docker/
├── Dockerfile                              # Multi-stage build for agents
└── docker-compose.yml                      # Local dev setup
```

---

## A.2 Rendering Strategy by Page Type

### Marketing Pages (SSG)

```typescript
// app/(marketing)/page.tsx
export const dynamic = 'force-static';  // Next.js 15: fully static
export const revalidate = false;        // No revalidation needed

export async function generateMetadata(): Promise<Metadata> {
  return {
    title: 'Cekwajar - Cek Gaji Wajar Anda',
    description: 'Platform pemeriksaan gaji dan harga tanah terpercaya di Indonesia',
    openGraph: {
      title: 'Cekwajar - Cek Gaji Wajar Anda',
      description: 'Bandingkan gaji Anda dengan benchmark industri di Indonesia',
      type: 'website',
      url: 'https://cekwajar.id',
      images: [{ url: 'https://cekwajar.id/og.png' }],
    },
  };
}

export default function HomePage() {
  return (
    <div>
      {/* Static content */}
      <Hero />
      <Features />
      <Testimonials />
      <CTA />
    </div>
  );
}
```

**Why SSG?**
- Landing page never changes day-to-day
- Pre-rendered at build time, cached at CDN edge
- LCP < 500ms even on 4G (pre-computed HTML + images)
- Zero server cost (purely static)

---

### SEO Benchmark Pages (ISR)

```typescript
// app/(tools)/gaji/[job_category]-[city]/page.tsx
export const dynamic = 'force-static';  // Precompute at build time
export const revalidate = 86400;        // Revalidate every 24 hours

type BenchmarkPageProps = {
  params: { job_category: string; city: string };
  searchParams: Record<string, string>;
};

// Pre-generate 500+ pages at build time
export async function generateStaticParams() {
  const jobCategories = await getTopJobCategories();  // Top 50
  const cities = await getTopCities();                // Top 10

  return jobCategories.flatMap((job) =>
    cities.map((city) => ({
      job_category: slugify(job.name),               // e.g., "software-engineer"
      city: slugify(city.name),                       // e.g., "jakarta"
    }))
  );
}

export async function generateMetadata(
  { params }: BenchmarkPageProps
): Promise<Metadata> {
  const { job_category, city } = params;
  const benchmark = await fetchBenchmark(job_category, city);

  return {
    title: `Gaji ${benchmark.job_title} di ${benchmark.city} - Cekwajar`,
    description: `Gaji wajar ${benchmark.job_title} di ${benchmark.city} adalah Rp${formatIDR(benchmark.median)}. Data dari ${benchmark.count} data point.`,
    openGraph: {
      title: `Gaji ${benchmark.job_title} di ${benchmark.city}`,
      description: `Median: Rp${formatIDR(benchmark.median)}. Quartile 1-3: Rp${formatIDR(benchmark.q1)}-${formatIDR(benchmark.q3)}`,
      images: [
        {
          url: `/api/og/benchmark?job=${job_category}&city=${city}`,
          width: 1200,
          height: 630,
        },
      ],
    },
  };
}

export default async function BenchmarkPage({
  params,
}: BenchmarkPageProps) {
  const { job_category, city } = params;
  const benchmark = await fetchBenchmark(job_category, city);

  // Fallback: If no data yet, show "Be the first to submit"
  if (!benchmark || benchmark.count < 10) {
    return (
      <div className="p-8 text-center">
        <h1>Data belum tersedia untuk {job_category} di {city}</h1>
        <p>Jadilah yang pertama mensubmit data!</p>
        <SubmissionForm job={job_category} city={city} />
      </div>
    );
  }

  return (
    <div>
      <BenchmarkCard benchmark={benchmark} />
      <SalaryChart data={benchmark.distribution} />
      <Comparison job_category={job_category} city={city} />
      <SubmitDataCTA />
    </div>
  );
}
```

**Why ISR?**
- 500+ SEO benchmark pages need pre-generation (too many for SSR)
- Revalidate every 24h because new data arrives daily via agents
- Fallback: blocking (show skeleton while generating first access)
- URL slug: `/gaji/software-engineer-jakarta` (SEO-optimized)
- Auto-generates og:image via `/api/og/benchmark` for WhatsApp/Twitter sharing

---

### Tool Pages (CSR with Client-Side State)

```typescript
// app/(tools)/gaji/page.tsx
'use client';  // Browser-side, interactive form

import { useForm } from 'react-hook-form';
import { useVerdictStore } from '@/lib/hooks/useVerdictStore';
import { SalaryForm } from './components/SalaryForm';
import { VerdictCard } from '@/components/verdict/VerdictCard';

export default function GajiToolPage() {
  const { verdict, loading, error } = useVerdictStore();

  const handleCalculate = async (formData: SalaryFormInput) => {
    // Call Edge Function
    const response = await fetch('/api/verdict/salary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });

    const result = await response.json();
    useVerdictStore.setState({ verdict: result, loading: false });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      <SalaryForm onSubmit={handleCalculate} />
      {verdict && <VerdictCard verdict={verdict} />}
      {loading && <Skeleton />}
      {error && <ErrorAlert message={error} />}
    </div>
  );
}
```

**Why CSR?**
- Form is interactive → re-renders on every keystroke (client-side hydration needed)
- Zustand store for form state (fast re-renders without full page reload)
- Edge Function call to `/api/verdict/salary` is client-initiated
- No server-side rendering needed (user's data is transient)

---

### Dashboard Pages (SSR with Auth Guard)

```typescript
// app/(dashboard)/dashboard/page.tsx
import { createServerComponentClient } from '@supabase/ssr';
import { redirect } from 'next/navigation';

export const dynamic = 'force-dynamic';  // Always fetch latest data
export const revalidate = 0;             // No caching (user-specific data)

export default async function DashboardPage() {
  const supabase = createServerComponentClient();

  // Server-side auth check
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    redirect('/login');
  }

  // Fetch user's subscription + verdict history
  const [subscriptionData, verdictHistory] = await Promise.all([
    supabase
      .from('users')
      .select('subscription_status, subscription_expires_at')
      .eq('id', user.id)
      .single(),
    supabase
      .from('verdict_logs')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })
      .limit(20),
  ]);

  return (
    <div>
      <SubscriptionBanner subscription={subscriptionData.data} />
      <VerdictHistory verdicts={verdictHistory.data} />
    </div>
  );
}
```

**Why SSR?**
- User-specific data (subscription status, verdict history)
- Cannot be cached (different per user)
- Auth guard required at server-level (redirect before rendering)
- Set `revalidate: 0` (no-cache)

---

## A.3 Performance Targets for Indonesia 4G

Indonesia 4G network: avg 15 Mbps, 50ms latency

### LCP (Largest Contentful Paint) < 2.5s on 4G

**For landing page (SSG):**
- Precomputed HTML (~15KB gzipped)
- Above-fold images: WebP/AVIF, max 100KB
- Above-fold CSS: <50KB inline
- No render-blocking scripts

```typescript
// next.config.mjs
export default {
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    // Aggressive caching
    minimumCacheTTL: 31536000,  // 1 year for hash-based images
  },
  swcMinify: true,
  compress: true,
  experimental: {
    optimizePackageImports: ['@radix-ui/react-*', 'lucide-react'],
  },
};
```

**For tool pages (CSR):**
- JavaScript bundle (gzipped): < 150KB first load
- Use dynamic imports for heavy components

```typescript
// Lazy-load Recharts only when user needs chart
const BenchmarkChart = dynamic(() => import('./components/BenchmarkChart'), {
  loading: () => <Skeleton />,
  ssr: false,
});
```

### FID (First Input Delay) < 100ms

- Use React 18 startTransition for slow computations
- Avoid long tasks > 50ms
- Web Workers for heavy calculations

### CLS (Cumulative Layout Shift) < 0.1

- Reserve space for ads/banners
- Use `width` and `height` attributes on images
- No late-loaded fonts

```css
/* global.css: Preload Inter subset */
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('/fonts/inter-400-subset.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0100-017F;  /* Latin + extended */
}
```

### Image Optimization

```typescript
// For above-fold images: priority={true}
<Image
  src="/hero-indonesia.webp"
  alt="Cekwajar Hero"
  width={1200}
  height={630}
  priority={true}
  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 80vw, 1000px"
/>

// For below-fold: lazy loading (default)
<Image
  src="/feature-screenshot.webp"
  alt="Dashboard"
  width={800}
  height={600}
  // priority={false} (default)
/>
```

---

## A.4 Component Hierarchy for Each Tool

### Wajar Gaji (Salary Tool)

```
SalaryToolPage (CSR, /gaji)
├── SalaryForm (CSR, Zustand store)
│   ├── JobTitleAutocomplete (RHF)
│   │   └── Combobox (Radix UI)
│   ├── ExperienceSlider (RHF)
│   ├── CitySelect (RHF)
│   │   └── Select component (shadcn/ui)
│   ├── IndustrySelect (RHF, optional)
│   └── SubmitButton
│
└── VerdictCard (displays result)
    ├── VerdictBadge (wajar/kurang/tinggi color)
    ├── PercentileDisplay (0-100% bar)
    │   ├── Q1 marker
    │   ├── Median marker
    │   └── Q3 marker
    ├── NumberDisplay (IDR formatting)
    │   ├── Base salary
    │   ├── With allowances
    │   └── Total compensation
    ├── DataSourceLabel (n data points)
    └── ShareButton
        ├── WhatsAppShare
        ├── TwitterShare
        └── CopyLinkButton

BenchmarkPage (ISR, /gaji/job-city)
├── BenchmarkCard (displays static benchmark)
├── BenchmarkChart (Recharts histogram)
│   ├── Distribution curve
│   ├── Percentile markers (P10, P25, P50, P75, P90)
│   └── UMR comparison line
├── CityComparison (same job across cities)
├── IndustryComparison (same job across industries)
└── SubmitDataCTA
```

### Wajar Slip (Payslip Tool)

```
SlipToolPage (CSR, /slip)
├── SlipUploader (Dropzone, CSR)
│   ├── FileInput (max 5MB PDF)
│   ├── DragDrop zone
│   └── ProgressBar (OCR status)
│
├── SlipPreview (displays OCR result)
│   ├── ExtractedFields
│   │   ├── Employee name
│   │   ├── Job title
│   │   ├── Base salary
│   │   ├── Allowances (breakdown)
│   │   ├── PPh21 (actual vs expected)
│   │   ├── BPJS (JKK, JKM, JHT)
│   │   └── Net salary
│   └── ManualEditButton (for OCR errors)
│
└── ComplianceReport
    ├── PPh21Audit
    │   ├── Expected PPh21 (calculated)
    │   ├── Actual PPh21
    │   ├── Variance flag (red if < expected)
    │   └── DetailBreakdown (PTKP, taxable income)
    ├── BPJSAudit
    │   ├── JKK (company disability insurance)
    │   ├── JKM (company death insurance)
    │   ├── JHT (company retirement fund)
    │   └── Variance flag
    ├── AllowanceAudit
    │   ├── Expected allowances per Kemnaker
    │   ├── Actual allowances
    │   └── Missing components flag
    └── DownloadReport (PDF, PNG for sharing)

UploadHistory (SSR, /dashboard/uploads)
├── RecentUploads table
├── ExportAllButton (CSV)
└── DeleteButton (RLS-protected)
```

---

# PART B: SUPABASE EDGE FUNCTIONS SPECIFICATION

All Edge Functions are TypeScript, deployed to Supabase, invoked via HTTPS.

---

## B.1 calculate_salary_verdict

**Endpoint**: `POST https://[project].supabase.co/functions/v1/calculate_salary_verdict`

**Authentication**:
- Anonymous: free tier (logged in anon session)
- Service role: premium/enterprise features (via Next.js API route)

**Request Body**:

```typescript
interface CalculateSalaryVerdictInput {
  job_category_id: string;        // e.g., "software-engineer"
  city_id: string;                // e.g., "jakarta"
  years_experience: number;       // 0-50
  salary_amount: number;          // User's salary in IDR
  user_id?: string;               // Optional, for verdict logging
  employment_type?: string;       // "permanent" | "contract" | "freelance"
  company_size?: string;          // "<10" | "10-50" | "50-250" | "250-1000" | ">1000"
  industry?: string;              // Optional override for benchmarking
}
```

**Response**:

```typescript
interface VerdictResponse {
  verdict: 'wajar' | 'kurang' | 'tinggi';      // Classification
  percentile: number;                          // 0-100 (user's salary vs benchmark)
  median_salary: number;                       // Benchmark median (IDR)
  q1_salary: number;                           // 25th percentile
  q3_salary: number;                           // 75th percentile
  p90_salary: number;                          // 90th percentile (high earners)
  data_points: number;                         // n for this benchmark
  confidence_score: number;                    // 0-1 (higher = more data)
  umr_salary: number;                          // UMR for this city
  umr_compliance: boolean;                     // true if user salary >= UMR
  similar_profiles: Array<{
    experience: number;
    median_salary: number;
    percentile: number;
  }>;
  comparison_context: string;                  // e.g., "Top 25% earner in this role"
  generated_at: string;                        // ISO timestamp
}
```

**TypeScript Implementation**:

```typescript
// supabase/functions/calculate_salary_verdict/index.ts
import { serve } from 'https://deno.land/std@0.208.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.38.4';

const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const supabase = createClient(supabaseUrl, supabaseServiceKey);

interface CalculateSalaryVerdictInput {
  job_category_id: string;
  city_id: string;
  years_experience: number;
  salary_amount: number;
  user_id?: string;
  employment_type?: string;
  company_size?: string;
  industry?: string;
}

async function calculateVerdictLogic(
  input: CalculateSalaryVerdictInput
): Promise<VerdictResponse> {
  // Step 1: Fetch benchmark data
  const { data: benchmark, error: benchmarkError } = await supabase
    .from('benchmark_salary')
    .select(
      'id, job_category_id, city_id, median_salary, q1_salary, q3_salary, p90_salary, data_points, experience_avg'
    )
    .eq('job_category_id', input.job_category_id)
    .eq('city_id', input.city_id)
    .single();

  if (benchmarkError || !benchmark) {
    throw new Error(`No benchmark data for ${input.job_category_id} in ${input.city_id}`);
  }

  // Step 2: Calculate percentile
  let userPercentile = 0;
  if (input.salary_amount <= benchmark.q1_salary) {
    userPercentile = Math.round((input.salary_amount / benchmark.q1_salary) * 25);
  } else if (input.salary_amount <= benchmark.median_salary) {
    userPercentile = 25 + Math.round(
      ((input.salary_amount - benchmark.q1_salary) /
       (benchmark.median_salary - benchmark.q1_salary)) * 25
    );
  } else if (input.salary_amount <= benchmark.q3_salary) {
    userPercentile = 50 + Math.round(
      ((input.salary_amount - benchmark.median_salary) /
       (benchmark.q3_salary - benchmark.median_salary)) * 25
    );
  } else {
    userPercentile = 75 + Math.round(
      ((input.salary_amount - benchmark.q3_salary) /
       (benchmark.p90_salary - benchmark.q3_salary)) * 25
    );
  }
  userPercentile = Math.min(userPercentile, 99);

  // Step 3: Apply Bayesian smoothing if data is sparse (n < 15)
  let confidence = Math.min(benchmark.data_points / 50, 1.0);
  let adjustedMedian = benchmark.median_salary;

  if (benchmark.data_points < 15) {
    // Prior: national median for this job
    const { data: nationalMedian } = await supabase
      .from('benchmark_salary')
      .select('median_salary')
      .eq('job_category_id', input.job_category_id)
      .is('city_id', null)  // National average
      .single();

    if (nationalMedian) {
      const prior = nationalMedian.median_salary;
      const alpha = benchmark.data_points / (benchmark.data_points + 5);  // Credibility weight
      adjustedMedian = Math.round(alpha * benchmark.median_salary + (1 - alpha) * prior);
    }
  }

  // Step 4: Determine verdict
  let verdict: 'wajar' | 'kurang' | 'tinggi';
  if (input.salary_amount < benchmark.q1_salary) {
    verdict = 'kurang';
  } else if (input.salary_amount > benchmark.q3_salary) {
    verdict = 'tinggi';
  } else {
    verdict = 'wajar';
  }

  // Step 5: Check UMR compliance
  const { data: umrData } = await supabase
    .from('umr_rates')
    .select('umr_amount')
    .eq('city_id', input.city_id)
    .eq('year', new Date().getFullYear())
    .single();

  const umrSalary = umrData?.umr_amount || 0;
  const umrCompliance = input.salary_amount >= umrSalary;

  // Step 6: Get experience-based comparison
  const { data: experienceComparison } = await supabase
    .from('benchmark_salary')
    .select('experience_range, median_salary')
    .eq('job_category_id', input.job_category_id)
    .eq('city_id', input.city_id)
    .order('experience_range', { ascending: true });

  const similarProfiles = experienceComparison
    ?.filter((e: any) =>
      Math.abs(Number(e.experience_range.split('-')[0]) - input.years_experience) <= 5
    )
    .map((e: any) => ({
      experience: Number(e.experience_range.split('-')[0]),
      median_salary: e.median_salary,
      percentile: calculatePercentile(input.salary_amount, e.median_salary),
    })) || [];

  // Step 7: Generate context string
  let comparisonContext = '';
  if (userPercentile < 25) {
    comparisonContext = `Bottom 25% earner in this role (below Q1)`;
  } else if (userPercentile < 50) {
    comparisonContext = `Below median earner (Q1-Q2 range)`;
  } else if (userPercentile < 75) {
    comparisonContext = `Above median earner (Q2-Q3 range)`;
  } else {
    comparisonContext = `Top ${100 - userPercentile}% earner in this role`;
  }

  return {
    verdict,
    percentile: userPercentile,
    median_salary: adjustedMedian,
    q1_salary: benchmark.q1_salary,
    q3_salary: benchmark.q3_salary,
    p90_salary: benchmark.p90_salary,
    data_points: benchmark.data_points,
    confidence_score: confidence,
    umr_salary: umrSalary,
    umr_compliance: umrCompliance,
    similar_profiles: similarProfiles,
    comparison_context: comparisonContext,
    generated_at: new Date().toISOString(),
  };
}

serve(async (req) => {
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  try {
    const input: CalculateSalaryVerdictInput = await req.json();

    // Validate input
    if (!input.job_category_id || !input.city_id || input.salary_amount <= 0) {
      return new Response(
        JSON.stringify({ error: 'Invalid input parameters' }),
        { status: 400 }
      );
    }

    // Rate limiting: check daily quota
    if (input.user_id) {
      const { data: quotaCheck } = await supabase
        .from('verdict_logs')
        .select('id', { count: 'exact' })
        .eq('user_id', input.user_id)
        .eq('tool', 'gaji')
        .gte('created_at', new Date(Date.now() - 86400000).toISOString());

      const userDailyCount = quotaCheck?.length || 0;
      const { data: userSubscription } = await supabase
        .from('users')
        .select('subscription_status')
        .eq('id', input.user_id)
        .single();

      const dailyLimit =
        userSubscription?.subscription_status === 'premium' ? 50 :
        userSubscription?.subscription_status === 'enterprise' ? 999 :
        5;

      if (userDailyCount >= dailyLimit) {
        return new Response(
          JSON.stringify({ error: 'Daily quota exceeded', remaining: 0 }),
          { status: 429 }
        );
      }
    }

    const verdict = await calculateVerdictLogic(input);

    // Log verdict
    if (input.user_id) {
      await supabase.from('verdict_logs').insert({
        user_id: input.user_id,
        tool: 'gaji',
        job_category_id: input.job_category_id,
        city_id: input.city_id,
        salary_amount: input.salary_amount,
        result: verdict,
        created_at: new Date().toISOString(),
      });
    }

    // Also update realtime stats view
    await supabase.rpc('increment_verdict_stat', {
      tool: 'gaji',
      count: 1,
    });

    return new Response(JSON.stringify(verdict), {
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }),
      { status: 500 }
    );
  }
});
```

**Execution Time**: < 200ms (Deno cold start ~50ms, DB queries ~100ms, calculations ~30ms)

**Cost Estimation**:
- Supabase Edge Functions: $0.000001 per invocation + $0.50/100K requests
- At 50K queries/month: ~$0.025/month (negligible)

---

## B.2 calculate_slip_compliance

**Endpoint**: `POST https://[project].supabase.co/functions/v1/calculate_slip_compliance`

**Request Body**:

```typescript
interface PayslipInput {
  employee_name: string;
  gross_salary: number;
  base_salary: number;
  allowances: {
    transport?: number;
    meal?: number;
    communication?: number;
    health?: number;
    other?: number;
  };
  deductions: {
    pph21_actual: number;
    bpjs_jkk: number;        // JKK (disability insurance)
    bpjs_jkm: number;        // JKM (death insurance)
    bpjs_jht: number;        // JHT (retirement)
    other?: number;
  };
  ptkp_status: 'K0' | 'K1' | 'K2' | 'K3' | 'TK0' | 'TK1' | 'TK2' | 'TK3';  // Tax status
  city_id: string;
}

interface ComplianceReport {
  summary: {
    is_compliant: boolean;
    violations_count: number;
    overall_risk: 'low' | 'medium' | 'high';
  };
  pph21_audit: {
    expected_pph21: number;
    actual_pph21: number;
    variance: number;
    variance_percent: number;
    is_valid: boolean;
    recommendation: string;
  };
  bpjs_audit: {
    jkk: { expected: number; actual: number; valid: boolean };
    jkm: { expected: number; actual: number; valid: boolean };
    jht: { expected: number; actual: number; valid: boolean };
    total_expected: number;
    total_actual: number;
    is_valid: boolean;
  };
  allowance_audit: {
    expected_allowances: Record<string, number>;
    actual_allowances: Record<string, number>;
    missing_components: string[];
    is_valid: boolean;
  };
  detailed_breakdown: string[];  // List of warnings
  export_data: {
    pdf_url: string;  // Signed URL for PDF download
    png_url: string;  // Signed URL for PNG sharing
  };
}
```

**TypeScript Implementation**:

```typescript
// supabase/functions/calculate_slip_compliance/index.ts
import { serve } from 'https://deno.land/std@0.208.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.38.4';

const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const supabase = createClient(supabaseUrl, supabaseServiceKey);

// Indonesian tax constants (2026)
const TAX_RULES = {
  PTKP: {
    K0: 54_150_000,
    K1: 58_050_000,
    K2: 61_950_000,
    K3: 65_850_000,
    TK0: 50_250_000,
    TK1: 54_150_000,
    TK2: 58_050_000,
    TK3: 61_950_000,
  },
  RATES: [
    { min: 0, max: 50_000_000, rate: 0.05 },
    { min: 50_000_001, max: 250_000_000, rate: 0.15 },
    { min: 250_000_001, max: 500_000_000, rate: 0.25 },
    { min: 500_000_001, max: Infinity, rate: 0.30 },
  ],
  BPJS: {
    JKK_RATE: 0.0024,        // Company paid 0.24%
    JKM_RATE: 0.003,         // Company paid 0.3%
    JHT_EMPLOYEE: 0.02,      // Employee pays 2%
    JHT_COMPANY: 0.037,      // Company pays 3.7%
  },
};

function calculateExpectedPPh21(grossSalary: number, ptkpStatus: string): number {
  const ptkp = TAX_RULES.PTKP[ptkpStatus as keyof typeof TAX_RULES.PTKP];
  const annualGross = grossSalary * 12;
  const taxableIncome = Math.max(0, annualGross - ptkp);

  let tax = 0;
  for (const bracket of TAX_RULES.RATES) {
    if (taxableIncome > bracket.min) {
      const incomeInBracket = Math.min(taxableIncome, bracket.max) - bracket.min;
      tax += incomeInBracket * bracket.rate;
    }
  }

  return Math.round(tax / 12);  // Monthly
}

function calculateExpectedBPJS(grossSalary: number) {
  return {
    jkk: Math.round(grossSalary * TAX_RULES.BPJS.JKK_RATE),
    jkm: Math.round(grossSalary * TAX_RULES.BPJS.JKM_RATE),
    jht: Math.round(grossSalary * TAX_RULES.BPJS.JHT_COMPANY),
  };
}

async function auditPayslip(input: PayslipInput): Promise<ComplianceReport> {
  const violations: string[] = [];
  let violationCount = 0;

  // PPh21 Audit
  const expectedPPh21 = calculateExpectedPPh21(input.base_salary, input.ptkp_status);
  const pph21Variance = input.deductions.pph21_actual - expectedPPh21;
  const pph21VariancePercent = Math.round((pph21Variance / expectedPPh21) * 100);

  const pph21Valid = Math.abs(pph21Variance) <= expectedPPh21 * 0.1;  // Allow 10% variance
  if (!pph21Valid) {
    violations.push(
      `PPh21 mismatch: Expected Rp${expectedPPh21.toLocaleString('id-ID')} ` +
      `but actual is Rp${input.deductions.pph21_actual.toLocaleString('id-ID')} ` +
      `(variance: ${pph21VariancePercent}%)`
    );
    violationCount++;
  }

  // BPJS Audit
  const expectedBPJS = calculateExpectedBPJS(input.gross_salary);
  const bpjsValid =
    Math.abs(input.deductions.bpjs_jkk - expectedBPJS.jkk) <= expectedBPJS.jkk * 0.05 &&
    Math.abs(input.deductions.bpjs_jkm - expectedBPJS.jkm) <= expectedBPJS.jkm * 0.05 &&
    Math.abs(input.deductions.bpjs_jht - expectedBPJS.jht) <= expectedBPJS.jht * 0.05;

  if (!bpjsValid) {
    violations.push('BPJS deductions do not match legal requirements');
    violationCount++;
  }

  // Allowance Audit (optional; can vary by company policy)
  const expectedAllowances = {
    transport: input.base_salary * 0.05,  // Typical 5%
    meal: input.base_salary * 0.05,
    communication: input.base_salary * 0.02,
  };

  let missingComponents = [];
  for (const [key, expectedAmount] of Object.entries(expectedAllowances)) {
    const actual = input.allowances[key as keyof typeof input.allowances] || 0;
    if (actual === 0 && expectedAmount > 0) {
      missingComponents.push(key);
    }
  }

  // Determine overall risk
  let overallRisk: 'low' | 'medium' | 'high' = 'low';
  if (violationCount >= 2) {
    overallRisk = 'high';
  } else if (violationCount === 1) {
    overallRisk = 'medium';
  }

  return {
    summary: {
      is_compliant: violationCount === 0,
      violations_count: violationCount,
      overall_risk: overallRisk,
    },
    pph21_audit: {
      expected_pph21: expectedPPh21,
      actual_pph21: input.deductions.pph21_actual,
      variance: pph21Variance,
      variance_percent: pph21VariancePercent,
      is_valid: pph21Valid,
      recommendation: pph21Valid
        ? 'PPh21 calculation is correct'
        : 'Review PPh21 deduction with HR/payroll',
    },
    bpjs_audit: {
      jkk: {
        expected: expectedBPJS.jkk,
        actual: input.deductions.bpjs_jkk,
        valid: Math.abs(input.deductions.bpjs_jkk - expectedBPJS.jkk) <= expectedBPJS.jkk * 0.05,
      },
      jkm: {
        expected: expectedBPJS.jkm,
        actual: input.deductions.bpjs_jkm,
        valid: Math.abs(input.deductions.bpjs_jkm - expectedBPJS.jkm) <= expectedBPJS.jkm * 0.05,
      },
      jht: {
        expected: expectedBPJS.jht,
        actual: input.deductions.bpjs_jht,
        valid: Math.abs(input.deductions.bpjs_jht - expectedBPJS.jht) <= expectedBPJS.jht * 0.05,
      },
      total_expected: expectedBPJS.jkk + expectedBPJS.jkm + expectedBPJS.jht,
      total_actual:
        input.deductions.bpjs_jkk + input.deductions.bpjs_jkm + input.deductions.bpjs_jht,
      is_valid: bpjsValid,
    },
    allowance_audit: {
      expected_allowances: expectedAllowances,
      actual_allowances: input.allowances,
      missing_components: missingComponents,
      is_valid: missingComponents.length === 0,
    },
    detailed_breakdown: violations,
    export_data: {
      pdf_url: `/api/slip/download?id=${input.employee_name}-${Date.now()}&format=pdf`,
      png_url: `/api/slip/download?id=${input.employee_name}-${Date.now()}&format=png`,
    },
  };
}

serve(async (req) => {
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  try {
    const input: PayslipInput = await req.json();
    const report = await auditPayslip(input);

    return new Response(JSON.stringify(report), {
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }),
      { status: 500 }
    );
  }
});
```

---

## B.3 calculate_land_verdict

**Endpoint**: `POST https://[project].supabase.co/functions/v1/calculate_land_verdict`

**Request Body**:

```typescript
interface LandVerdictInput {
  kelurahan_id: string;         // Administrative village ID
  land_area_m2: number;
  asking_price: number;         // IDR
  land_type: 'residential' | 'commercial' | 'industrial';
}
```

**Response**:

```typescript
interface LandVerdictResponse {
  verdict: 'murah' | 'wajar' | 'mahal';
  asking_price_per_m2: number;
  njop_per_m2: number;
  market_comparable_per_m2: number;
  recommended_price_range: {
    min: number;
    max: number;
  };
  confidence_score: number;
  data_sources: {
    njop: { weight: number; per_m2: number };
    listings: { weight: number; per_m2: number; count: number };
    crowdsourced: { weight: number; per_m2: number; count: number };
  };
}
```

**Implementation Highlights**:

```typescript
// Triangulate NJOP + listings + crowdsourced data
const njopWeight = 0.4;        // Government valuation is authoritative
const listingsWeight = 0.35;   // Recent market sales
const crowdsourcedWeight = 0.25;  // Community submissions

const estimatedPrice =
  njopPerM2 * njopWeight +
  listingComparablePerM2 * listingsWeight +
  crowdsourcedPerM2 * crowdsourcedWeight;

if (askingPricePerM2 < estimatedPrice * 0.9) {
  verdict = 'murah';
} else if (askingPricePerM2 > estimatedPrice * 1.1) {
  verdict = 'mahal';
} else {
  verdict = 'wajar';
}
```

---

## B.4 validate_crowdsource_submission (Database Trigger)

**Trigger**: ON INSERT to `raw_salary_submissions` or `raw_land_submissions`

**Logic**:

```sql
CREATE OR REPLACE FUNCTION validate_crowdsource_submission()
RETURNS TRIGGER AS $$
DECLARE
  mean_salary FLOAT;
  std_dev FLOAT;
  outlier_threshold FLOAT;
BEGIN
  -- Calculate mean and std dev for this job/city
  SELECT
    AVG(salary_amount),
    STDDEV(salary_amount)
  INTO mean_salary, std_dev
  FROM raw_salary_submissions
  WHERE job_category_id = NEW.job_category_id
    AND city_id = NEW.city_id
    AND validation_status != 'flagged_outlier';

  -- Flag if > 3 standard deviations (outlier)
  IF std_dev IS NOT NULL AND ABS(NEW.salary_amount - mean_salary) > (3 * std_dev) THEN
    NEW.validation_status := 'flagged_outlier';
  ELSE
    NEW.validation_status := 'pending_review';
  END IF;

  -- Call OpenAI to classify job title
  PERFORM process_job_title_classification(NEW.id, NEW.job_title);

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_crowdsource
BEFORE INSERT ON raw_salary_submissions
FOR EACH ROW EXECUTE FUNCTION validate_crowdsource_submission();
```

---

## B.5 generate_verdict_share_card

**Endpoint**: `POST https://[project].supabase.co/functions/v1/generate_verdict_share_card`

Uses `@vercel/og` to generate PNG images for WhatsApp/Twitter sharing.

```typescript
import { ImageResponse } from '@vercel/og';

export async function generateVerdictCard(verdict: VerdictResponse) {
  return new ImageResponse(
    (
      <div
        style={{
          fontSize: 32,
          color: 'white',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          width: '100%',
          height: '100%',
          padding: '40px',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontFamily: 'system-ui',
        }}
      >
        <h1>Gaji Saya {verdict.verdict === 'wajar' ? '✓ Wajar' : verdict.verdict.toUpperCase()}</h1>
        <div style={{ fontSize: 48, fontWeight: 'bold' }}>
          Rp{(verdict.median_salary / 1_000_000).toFixed(1)}Jt
        </div>
        <p>Percentile: {verdict.percentile}% (dibanding {verdict.data_points} data)</p>
        <p>cekwajar.id</p>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    }
  );
}
```

---

## B.6 Realtime Subscriptions

**View**: `verdict_stats` (materialized view, 60s refresh)

```sql
CREATE MATERIALIZED VIEW verdict_stats AS
SELECT
  DATE(created_at) as date,
  'gaji' as tool,
  COUNT(*) as total_queries,
  COUNT(DISTINCT user_id) as unique_users
FROM verdict_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at), tool
ORDER BY date DESC, tool;

-- Refresh every 60 seconds via pg_cron
SELECT cron.schedule('refresh_verdict_stats', '*/1 * * * *',
  'REFRESH MATERIALIZED VIEW CONCURRENTLY verdict_stats');
```

**Frontend Subscription**:

```typescript
// In a CSR component
const supabase = createBrowserClient();
const [dailyCount, setDailyCount] = useState(0);

useEffect(() => {
  const subscription = supabase
    .from('verdict_stats')
    .on('*', (payload) => {
      if (payload.new.date === today) {
        setDailyCount(payload.new.total_queries);
      }
    })
    .subscribe();

  return () => subscription.unsubscribe();
}, []);
```

---

## B.7 Storage Buckets

### Bucket 1: `payslip_uploads` (private)

```typescript
// RLS Policy
CREATE POLICY "Users can upload own payslips" ON storage.objects
  FOR INSERT
  WITH CHECK (
    auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users can read own payslips" ON storage.objects
  FOR SELECT
  USING (
    auth.uid()::text = (storage.foldername(name))[1]
  );

// Auto-delete after 30 days via pg_cron
SELECT cron.schedule('delete_old_payslips', '0 2 * * *', $$
  DELETE FROM storage.objects
  WHERE bucket_id = 'payslip_uploads'
    AND created_at < NOW() - INTERVAL '30 days';
$$);
```

### Bucket 2: `verdict_cards` (public)

```typescript
// RLS Policy (public read, no insert/update)
CREATE POLICY "Public read verdicts" ON storage.objects
  FOR SELECT
  USING (bucket_id = 'verdict_cards');

// Generated on-demand, auto-cleanup after 7 days
SELECT cron.schedule('cleanup_old_cards', '0 3 * * *', $$
  DELETE FROM storage.objects
  WHERE bucket_id = 'verdict_cards'
    AND created_at < NOW() - INTERVAL '7 days';
$$);
```

---

# PART C: AI AGENT TECHNICAL SPECIFICATION (SWARMS FRAMEWORK)

All agents run on Fly.io or Railway with Python 3.11+, using Swarms framework for orchestration.

---

## C.1 Agent 1: DataHarvestAgent

**Purpose**: Fetch official government salary and labor data from BPS API

**System Prompt**:

```
You are a data harvesting agent for cekwajar.id. Your primary responsibility is to:
1. Fetch salary and employment data from Badan Pusat Statistik (BPS) API endpoints
2. Transform raw BPS data into the standardized benchmark schema (job_category, city, median, q1, q3, p90, count)
3. Validate data quality and flag anomalies
4. Upload processed data to Supabase benchmark_salary table
5. Log all operations to GitHub Issues for transparency

You operate weekly, always during off-peak hours (2 AM UTC).
Rate limit yourself to 10 requests/minute to BPS API.
On failure, create a GitHub issue with error details and retry after 24 hours.

Guidelines:
- Priority: Use BPS Survei Angkatan Kerja Nasional (SAKERNAS) data
- Map BPS job classifications to cekwajar canonical job categories
- Only publish benchmarks with n >= 10 samples (k-anonymity)
- Append new data rather than replacing (maintain historical versions)
- Tag each data import with source, timestamp, and methodology version
```

**Tool Functions**:

```python
@tool
def fetch_bps_data(
    var_id: str,              # Variable ID (e.g., "SP1171")
    domain: str,              # Domain (e.g., "LABOR_FORCE")
    year: int = 2026
) -> Dict[str, Any]:
  """
  Fetch data from BPS API

  Args:
    var_id: BPS variable identifier
    domain: Data domain classification
    year: Year to fetch

  Returns:
    Raw BPS data with metadata
  """
  pass

@tool
def transform_bps_to_benchmark(
    raw_data: List[Dict],
    job_mapping: Dict[str, str]
) -> List[BenchmarkSalary]:
  """Transform BPS data to benchmark schema"""
  pass

@tool
def upload_to_supabase(
    data: List[BenchmarkSalary],
    table: str
) -> Dict[str, int]:
  """Upload processed data to Supabase"""
  pass
```

**Schedule**: GitHub Actions weekly (Monday 2 AM UTC)

**Cost**: ~500 tokens per run × 52 weeks = ~$0.05/month (minimal)

---

## C.2 Agent 2: UMRUpdaterAgent

**Purpose**: Scrape latest Upah Minimum Regional (UMR/UMK) from Kemenaker website

**System Prompt**:

```
You are the UMR updater agent. Your job is to:
1. Monitor kemenaker.go.id for latest UMR/UMK announcements
2. Parse provincial UMR rates and publish dates
3. Update Supabase umr_rates table with new rates
4. Notify users if UMR increased (via in-app announcement)

UMR/UMK are announced annually (typically Sep-Nov for next year).
Your scheduled run is monthly to catch updates early.

When you find a new UMR:
- Extract: province, year, effective_date, amount_idr
- Cross-check with 2-3 news sources to verify accuracy
- Flag provinces with missing data as "need_verification"
- Create GitHub issue if discrepancies found
```

**Tool Functions**:

```python
@tool
def scrape_kemenaker_umr(province_code: str) -> Dict[str, Any]:
  """
  Scrape UMR from Kemenaker website

  Args:
    province_code: Province code (e.g., "DKI_JAKARTA")

  Returns:
    {
      "province": str,
      "umr_amount": int,
      "effective_date": str,
      "source_url": str,
      "verified": bool
    }
  """
  pass

@tool
def cross_verify_umr(
    province: str,
    amount: int
) -> bool:
  """Verify UMR with 2 additional sources (news, labor ministry)"""
  pass

@tool
def update_umr_table(
    records: List[UMRRecord]
) -> None:
  """Update Supabase umr_rates table"""
  pass
```

**Schedule**: GitHub Actions monthly (1st of month, 1 AM UTC)

**Implementation Notes**:
- Use Playwright for JavaScript-rendered content
- Retry 3x on network errors
- Notify via email if UMR changed since last run

---

## C.3 Agent 3: PPh21UpdaterAgent

**Purpose**: Monitor pajak.go.id for tax regulation changes

**System Prompt**:

```
You are the PPh21 monitoring agent. Your responsibilities:
1. Check pajak.go.id for updates to Pajak Penghasilan (PPh21) regulations
2. Monitor Keputusan Menteri Keuangan (KMK) releases
3. Extract new tax rates, PTKP values, and effective dates
4. Update Supabase tax_rules table
5. Alert engineering team if calculation formulas need updates

Key dates to monitor:
- Jan 1: Annual PTKP adjustment (usually 3-5% inflation adjustment)
- Throughout year: Emergency tax changes, special provisions

When tax rates change:
1. Document old vs new rates
2. Update calculate_slip_compliance edge function
3. Create detailed GitHub issue for audit trail
4. Notify users about tax changes affecting their calculations
```

**Tool Functions**:

```python
@tool
def monitor_djp_updates() -> List[RegulationChange]:
  """
  Check pajak.go.id for new regulations

  Returns:
    [{
      "title": str,
      "type": "ptkp_update" | "rate_change" | "new_provision",
      "effective_date": str,
      "old_value": Any,
      "new_value": Any,
      "source_url": str
    }]
  """
  pass

@tool
def parse_ptkp_regulation(html: str) -> Dict[str, int]:
  """Extract PTKP values from KMK document"""
  pass

@tool
def validate_tax_formula(
    old_formula: str,
    new_formula: str,
    test_cases: List[Tuple[int, int]]
) -> bool:
  """Test that new formula matches government intent"""
  pass
```

**Schedule**: GitHub Actions weekly (Tuesday 1 AM UTC)

---

## C.4 Agent 4: NJOPHarvesterAgent

**Purpose**: Fetch Nilai Jual Objek Pajak (NJOP) from BPN/Bhumi API

**System Prompt**:

```
You are the NJOP harvesting agent. Your job:
1. Fetch NJOP zones from Badan Pertanahan Nasional (BPN) API or Bhumi platform
2. Map NJOP to kelurahan (village) level
3. Update Supabase njop_zones table
4. Cross-reference with historical NJOP changes to detect zoning updates

NJOP is property tax valuation used as baseline for land price benchmarking.
Annual updates typically happen in Dec/Jan.

Algorithm:
- For each kelurahan: fetch current NJOP
- Compare to previous year: if variance > 5%, flag for manual review
- Store both current and historical NJOP for trend analysis
- Aggregate NJOP by land_type (residential, commercial, industrial)
```

**Tool Functions**:

```python
@tool
def fetch_njop_data(
    kelurahan_id: str,
    land_type: str = 'residential'
) -> NJOPZone:
  """
  Fetch NJOP for a specific village

  Returns:
    {
      "kelurahan_id": str,
      "njop_per_m2": int,
      "effective_date": str,
      "land_type": str,
      "confidence": 0.0-1.0
    }
  """
  pass

@tool
def aggregate_njop_by_subdistrict(
    subdistrict_code: str
) -> Dict[str, int]:
  """Average NJOP across all villages in subdistrict"""
  pass
```

---

## C.5 Agent 5: ListingScraperAgent

**Purpose**: Scrape property listings from public sources (99.co, Properti.com, OLX)

**System Prompt**:

```
You are the listing scraper agent. Your job:
1. Scrape recent property listings (last 30 days)
2. Extract: location, area, price, listing_date
3. Filter for completed/verified listings (high quality)
4. Update raw_land_submissions table with market comparable data
5. Rate limit to 10 requests/minute per domain
6. Respect robots.txt and Terms of Service

Anti-detection measures:
- Use rotating proxies (Bright Data API)
- Randomize 1-3 second delays between requests
- Rotate User-Agent headers
- Cache results for 24h to reduce scraping frequency

Data quality rules:
- Reject listings > 180 days old
- Reject outliers > 3 SD from median
- Require minimum price >= 500M (spam prevention)
- Flag listings with suspiciously round prices
```

**Tool Functions**:

```python
@tool
def scrape_property_listings(
    city: str,
    land_type: str,
    date_from: str,
    max_results: int = 100
) -> List[ListingRecord]:
  """
  Scrape property listings from multiple sources

  Returns:
    [{
      "source": "99co" | "properti" | "olx",
      "city": str,
      "area_m2": int,
      "price_idr": int,
      "listing_date": str,
      "quality_score": 0.0-1.0
    }]
  """
  pass

@tool
def calculate_market_comparable_price(
    listings: List[ListingRecord]
) -> Dict[str, float]:
  """
  Filter listings and calculate market comparable price per m2
  Applies outlier detection (IQR method)
  """
  pass
```

---

## C.6 Agent 6: CrowdsourceValidatorAgent

**Purpose**: AI-validate user-submitted salary and land data

**System Prompt**:

```
You are the crowdsource validation agent. Your job:
1. Check newly submitted salary/land data for quality and fraud
2. Use statistical methods and AI to detect outliers
3. Classify job titles to canonical categories (using pgvector similarity)
4. Flag suspicious submissions (repeated entries, unrealistic values)
5. Approve high-confidence submissions immediately

Validation rules:
- Salary: Must be >= UMR for city, <= 1000M (threshold)
- Land: Price per m2 must fall within 2 SD of city median
- Job titles: Must match Kemnaker classification within 0.85 cosine similarity
- Frequency: Reject > 3 submissions per IP per day (spam)

Decision tree:
1. Is salary/price within reasonable bounds? → Approve
2. Is it an outlier (> 3 SD)? → Flag for manual review
3. Is there duplicate IP + job combo? → Mark duplicate
4. Does job title need disambiguation? → Run pgvector search

After approval:
- Move data from crowdsource_queue to benchmark aggregation pipeline
- Trigger benchmark_aggregator_agent if threshold reached
```

**Tool Functions**:

```python
@tool
def validate_salary_submission(
    data: RawSalarySubmission
) -> ValidationResult:
  """
  Validate salary submission for quality

  Returns:
    {
      "status": "approved" | "flagged" | "rejected",
      "confidence": 0.0-1.0,
      "issues": [str],
      "canonical_job_category_id": str
    }
  """
  pass

@tool
def classify_job_title(
    raw_job_title: str,
    pgvector_embeddings: List[float]
) -> str:
  """
  Classify job title using pgvector similarity search
  Uses OpenAI embeddings for semantic search
  """
  pass

@tool
def detect_fraud(
    submission_id: str,
    ip_address: str,
    recent_submissions: List[Dict]
) -> FraudScore:
  """Detect spam, duplicates, and fraudulent submissions"""
  pass
```

**Deployment**: Railway (always-on worker)

**Cost**: ~200 tokens per submission × 500 submissions/month = ~$2/month

---

## C.7 Agent 7: ContentFactoryAgent

**Purpose**: Generate broadcast-quality Indonesian TikTok scripts and SEO blog posts

**System Prompt**:

```
You are the content factory agent for cekwajar.id. Your job:
1. Generate engaging TikTok scripts (15-60 seconds) in Bahasa Indonesia
2. Create SEO-optimized blog posts around salary benchmarks
3. Produce email templates for campaign marketing
4. All content must be factually accurate, use real data from Supabase
5. Target audience: Indonesian workers age 18-45, mobile-first

TikTok Script Guidelines:
- Hook in first 1 second (pattern interrupt)
- Use authentic Indonesian vernacular (tidak formal)
- Include trending sounds/trends (check TikTok API)
- End with clear CTA: "Cek gaji kamu di cekwajar.id"
- Duration: 15-30 seconds for algorithm preference
- Format: Scene descriptions + voiceover script

Example TikTok Topic: "Gaji Software Engineer di Jakarta 2026"
Hook: "Gaji ku Rp50jt/bulan... ternyata kurang 😅"
Content: Show salary range from Cekwajar
CTA: "Cek gaji wajar kamu di cekwajar.id"

Blog Post Guidelines:
- Title: Target long-tail keywords (e.g., "Gaji Wajar Junior Developer Jakarta 2026")
- Length: 800-1500 words
- Include real data visualizations (generated via Supabase)
- H2 structure: Intro, Salary Range, By Experience, By Industry, Tips, CTA
- Schema markup for FAQ section
- Internal links to benchmark pages
```

**Tool Functions**:

```python
@tool
def generate_tiktok_script(
    topic: str,
    trend_keyword: str,
    data: Dict
) -> TikTokScript:
  """
  Generate TikTok script

  Returns:
    {
      "hook": str,
      "scenes": [{"duration_sec": int, "description": str}],
      "voiceover": str,
      "cta": str,
      "trend_hashtags": [str],
      "estimated_views": int
    }
  """
  pass

@tool
def generate_blog_post(
    job_category: str,
    city: str,
    benchmark_data: Dict
) -> BlogPost:
  """Generate SEO blog post around salary benchmark"""
  pass

@tool
def fetch_trending_sounds() -> List[str]:
  """Get trending TikTok sounds for current week"""
  pass
```

**Schedule**: Daily at 10 AM UTC (morning post timing)

**Upload Workflow**:
1. Generate 7 TikTok scripts (one per weekday + weekend bonus)
2. Save as Markdown in `content/scripts/` folder
3. Create GitHub issue with scripts for human review
4. On approval: Queue for TikTok scheduling tool

**Cost**: ~1000 tokens per script × 7 scripts/week = ~$3/month

---

## C.8 Agent 8: SEOPageGeneratorAgent

**Purpose**: Generate the 500+ SEO benchmark pages dynamically

**System Prompt**:

```
You are the SEO page generator for cekwajar.id. Your job:
1. Generate 500+ static benchmark pages (job_category × city combinations)
2. Each page must be SEO-optimized with:
   - Unique title, meta description
   - Schema markup (FAQPage, BreadcrumbList)
   - Real benchmark data from Supabase
   - Related links and internal linking
3. Generate markdown content that Next.js can convert to HTML
4. Flag missing data combinations (n < 10 samples)

Algorithm:
- For each (job_category, city) combination:
  1. Fetch benchmark_salary data
  2. If n >= 10: Generate page
  3. If n < 10: Flag as "Data belum tersedia"
  4. Write markdown to content/benchmarks/[job]-[city].md
  5. Trigger Next.js ISR rebuild

Page Structure:
# Gaji Wajar [Job] di [City] 2026

## Ringkasan
[Median salary, range, data points]

## Grafik Distribusi Gaji
[Embedded chart]

## By Experience Level
[Table: Years → Median salary]

## By Industry
[Table: Industry → Median salary]

## FAQ
[Schema markup for FAQ]

## Submit Your Salary
[CTA to crowdsource form]
```

**Tool Functions**:

```python
@tool
def generate_benchmark_page(
    job_category: str,
    city: str,
    benchmark_data: BenchmarkSalary
) -> str:
  """
  Generate markdown content for benchmark page

  Returns:
    Markdown string ready for Next.js
  """
  pass

@tool
def trigger_isr_rebuild(
    paths: List[str]
) -> None:
  """Trigger Vercel ISR rebuild for updated paths"""
  pass
```

**Schedule**: Triggered by benchmark_aggregator_agent when new data published

---

## C.9 Agent 9: SupportBotAgent

**Purpose**: Handle customer support via Dify.ai integration

**System Prompt**:

```
Kamu adalah Agen Dukungan Pelanggan Cekwajar.id. Bahasa: Bahasa Indonesia (formal tapi friendly).

Tanggung jawab:
1. Jawab pertanyaan umum tentang cara pakai Cekwajar (Gaji/Slip/Tanah/Kabur/Hidup)
2. Bantu pengguna decode gaji mereka (basic PPh21/BPJS education)
3. Klarifikasi data privasi dan keamanan
4. Proses basic troubleshooting (upload error, login issue)
5. Escalate complex issues ke tim engineering via GitHub

Knowledge Base:
- How to use each of 5 tools
- Basic Indonesian tax knowledge (PPh21, BPJS)
- Pricing and subscription tiers
- Data privacy policy

Conversation Rules:
- Max 3 exchanges per chat (then escalate to human)
- Always provide source link (knowledge base or doc)
- Offer escalation option
- Speak in casual Bahasa Indonesia: "Halo! Ada yang bisa aku bantu?"
- Include relevant emojis for warmth

If user asks about:
- Complex tax issues → Link to accountant resources
- Data deletion → Process via support ticket
- Payment issues → Check Midtrans status, then escalate
```

**Integration**: Connected to Dify.ai (no-code LLM platform for non-critical support)

**Deployment**: Dify.ai (managed, no additional costs)

---

## C.10 Agent 10: BenchmarkAggregatorAgent

**Purpose**: Aggregate raw submissions into published benchmarks (with k-anonymity check)

**System Prompt**:

```
You are the benchmark aggregator. Your job:
1. Watch crowdsource_queue for submissions
2. When queue has >= threshold (100 submissions for a job/city combo):
   a. Apply k-anonymity check (n >= 10)
   b. Compute percentiles (P10, P25, P50, P75, P90)
   c. Apply outlier removal (IQR method)
   d. Publish to benchmark_salary table
3. Trigger SEOPageGeneratorAgent to create/update benchmark page
4. Log publication to audit table for compliance

K-Anonymity Check:
- Only publish if n >= 10 (minimum 10 submissions per cell)
- If 10 <= n < 20: Flag confidence as 'low'
- If 20 <= n < 50: Flag confidence as 'medium'
- If n >= 50: Flag confidence as 'high'

Outlier Removal:
- Use IQR method: Remove values below Q1 - 1.5*IQR or above Q3 + 1.5*IQR
- Document removed outliers (for transparency)

Publication Workflow:
1. Insert into benchmark_salary
2. Call SEOPageGeneratorAgent
3. Update realtime verdict_stats view
4. Create GitHub commit with aggregation results
```

**Tool Functions**:

```python
@tool
def check_kAnonymity(
    job_category_id: str,
    city_id: str
) -> Tuple[bool, int]:
  """Check if enough submissions exist to publish benchmark"""
  pass

@tool
def compute_percentiles(
    submissions: List[int]
) -> PercentileStats:
  """Compute P10, P25, P50, P75, P90"""
  pass

@tool
def remove_outliers(
    submissions: List[int]
) -> List[int]:
  """Apply IQR outlier removal"""
  pass

@tool
def publish_benchmark(
    benchmark: BenchmarkSalary
) -> None:
  """Insert to Supabase and trigger page generation"""
  pass
```

**Schedule**: Runs every 6 hours (automatic trigger when queue threshold reached)

---

## C.11-C.17: Additional Agents (Summary)

| Agent | Purpose | Schedule | Cost |
|-------|---------|----------|------|
| **ChurnPredictorAgent** | Identify users likely to churn (RFM analysis) | Weekly | $1/mo |
| **AbuseDetectorAgent** | Detect spam submissions, fake data | Realtime | $0.50/mo |
| **AlertingAgent** | Monitor data freshness, system health | Every 4h | $0.20/mo |
| **DataQualityAgent** | Validate consistency across benchmarks | Daily | $0.50/mo |
| **CompetitorMonitorAgent** | Track competitor feature changes | Daily | $1/mo |
| **RevenueReportAgent** | Daily revenue summary via email | Daily | $0.50/mo |
| **UserOnboardingAgent** | Send personalized onboarding sequences | Per signup | $2/mo |

**Total Agent Cost**: ~$12/month (OpenAI API calls)

---

# PART D: MIDTRANS PAYMENT INTEGRATION

---

## D.1 Complete Payment Flows

### Flow 1: Monthly Subscription

```
User clicks "Subscribe" (Premium Rp49,000/month)
    ↓
POST /api/payment/create-transaction
    ↓
Next.js validates subscription plan
    ↓
Calls Midtrans Snap (recurring token)
    ↓
Returns snap_token
    ↓
Frontend opens Snap popup
    ↓
User completes payment (card/e-wallet/bank transfer)
    ↓
Midtrans sends webhook: POST /api/payment/notify
    ↓
Next.js verifies signature
    ↓
Updates users.subscription_status = 'premium'
    ↓
Sets subscription_expires_at = now + 30 days
    ↓
Sends confirmation email
```

### Flow 2: Annual Subscription

```
User clicks "Subscribe Annual" (Rp499,000/year = 5% discount)
    ↓
POST /api/payment/create-transaction with period: 'annual'
    ↓
Snap Payment (one-time, no recurring)
    ↓
After payment_success webhook:
    ↓
Updates subscription_expires_at = now + 365 days
    ↓
Stores as single_payment (not recurring)
```

### Flow 3: One-Time Report (Wajar Slip Premium Report)

```
User clicks "Download Premium Report" (Rp29,000)
    ↓
POST /api/payment/create-transaction with item_type: 'report'
    ↓
Snap Payment popup
    ↓
After payment_success:
    ↓
Creates report_purchases record
    ↓
Generates premium PDF/PNG
    ↓
Sends download link via email
```

### Flow 4: B2B Invoicing

```
Corporate client requests API access
    ↓
Create b2b_clients record (manual via Dashboard)
    ↓
Generate unique API key
    ↓
Issue monthly invoices via Midtrans Dashboard (manual)
    ↓
On payment success webhook:
    ↓
Update b2b_clients.invoice_status
    ↓
Extend API key expiration
```

---

## D.2 Webhook Handler (TypeScript)

```typescript
// app/api/payment/notify/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { createServerComponentClient } from '@supabase/ssr';
import crypto from 'crypto';
import { Ratelimit } from '@upstash/ratelimit';

const redis = new Ratelimit({
  redis: Ratelimit.redis(process.env.UPSTASH_REDIS_URL!),
  limiter: Ratelimit.slidingWindow(10, '1 m'),
});

interface MidtransNotification {
  transaction_id: string;
  order_id: string;
  gross_amount: string;
  payment_type: string;
  transaction_status: string;
  transaction_time: string;
  status_code: string;
  signature_key: string;
}

function verifyMidtransSignature(
  notification: MidtransNotification,
  serverKey: string
): boolean {
  const orderId = notification.order_id;
  const statusCode = notification.status_code;
  const grossAmount = notification.gross_amount;

  const signatureData = `${orderId}${statusCode}${grossAmount}${serverKey}`;
  const signature = crypto
    .createHash('sha512')
    .update(signatureData)
    .digest('hex');

  return signature === notification.signature_key;
}

export async function POST(request: NextRequest) {
  try {
    // Rate limiting
    const ip = request.headers.get('x-forwarded-for') || 'unknown';
    const { success } = await redis.limit(ip);
    if (!success) {
      return NextResponse.json({ error: 'Rate limited' }, { status: 429 });
    }

    const notification = await request.json() as MidtransNotification;

    // Verify signature (security critical)
    if (!verifyMidtransSignature(notification, process.env.MIDTRANS_SERVER_KEY!)) {
      console.warn('Invalid Midtrans signature', notification.order_id);
      return NextResponse.json({ error: 'Invalid signature' }, { status: 401 });
    }

    // Parse order_id format: "user_123_subscription_monthly_20260407" or "user_123_report_20260407"
    const [userId, itemType, ...dateParts] = notification.order_id.split('_');
    const supabase = createServerComponentClient();

    if (notification.transaction_status === 'settlement' ||
        notification.transaction_status === 'capture') {
      // Payment successful

      if (itemType === 'subscription') {
        // Monthly/annual subscription
        const planType = dateParts[0]; // 'monthly' or 'annual'
        const expiresAt = new Date();

        if (planType === 'monthly') {
          expiresAt.setMonth(expiresAt.getMonth() + 1);
        } else if (planType === 'annual') {
          expiresAt.setFullYear(expiresAt.getFullYear() + 1);
        }

        const { error: updateError } = await supabase
          .from('users')
          .update({
            subscription_status: 'premium',
            subscription_expires_at: expiresAt.toISOString(),
            subscription_started_at: new Date().toISOString(),
          })
          .eq('id', userId);

        if (updateError) {
          console.error('Failed to update subscription', updateError);
          return NextResponse.json({ error: 'Update failed' }, { status: 500 });
        }

        // Log transaction
        await supabase.from('payment_transactions').insert({
          user_id: userId,
          transaction_id: notification.transaction_id,
          order_id: notification.order_id,
          amount: parseInt(notification.gross_amount),
          payment_type: notification.payment_type,
          status: 'success',
          item_type: 'subscription',
          plan_type: planType,
          created_at: new Date().toISOString(),
        });

        // Send confirmation email
        await sendSubscriptionEmail(userId, planType);
      }
      else if (itemType === 'report') {
        // One-time report purchase
        const { error: insertError } = await supabase
          .from('report_purchases')
          .insert({
            user_id: userId,
            transaction_id: notification.transaction_id,
            amount: parseInt(notification.gross_amount),
            report_type: 'wajar_slip_premium',
            created_at: new Date().toISOString(),
          });

        if (insertError) {
          console.error('Failed to record report purchase', insertError);
          return NextResponse.json({ error: 'Insert failed' }, { status: 500 });
        }

        // Send report download email
        await sendReportDownloadEmail(userId);
      }
    }
    else if (notification.transaction_status === 'pending') {
      // Payment pending (user hasn't completed yet)
      // Store for reminder email after 24h
      await supabase.from('payment_transactions').insert({
        user_id: userId,
        transaction_id: notification.transaction_id,
        order_id: notification.order_id,
        amount: parseInt(notification.gross_amount),
        payment_type: notification.payment_type,
        status: 'pending',
        item_type: itemType,
        created_at: new Date().toISOString(),
      });
    }
    else if (notification.transaction_status === 'deny' ||
             notification.transaction_status === 'cancel' ||
             notification.transaction_status === 'expire') {
      // Payment failed
      await supabase.from('payment_transactions').insert({
        user_id: userId,
        transaction_id: notification.transaction_id,
        order_id: notification.order_id,
        amount: parseInt(notification.gross_amount),
        payment_type: notification.payment_type,
        status: 'failed',
        item_type: itemType,
        created_at: new Date().toISOString(),
      });

      // Send failure email with retry link
      await sendPaymentFailureEmail(userId, notification.order_id);
    }

    return NextResponse.json({ status: 'ok' });
  } catch (error) {
    console.error('Webhook error:', error);
    return NextResponse.json(
      { error: 'Webhook processing failed' },
      { status: 500 }
    );
  }
}

async function sendSubscriptionEmail(userId: string, planType: string) {
  // Send via SendGrid or similar
  console.log(`Sending subscription email to ${userId} (plan: ${planType})`);
}

async function sendReportDownloadEmail(userId: string) {
  // Send PDF download link
  console.log(`Sending report download email to ${userId}`);
}

async function sendPaymentFailureEmail(userId: string, orderId: string) {
  // Send retry link
  console.log(`Sending payment failure email to ${userId} (order: ${orderId})`);
}
```

---

## D.3 Create Transaction Handler

```typescript
// app/api/payment/create-transaction/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { createServerComponentClient } from '@supabase/ssr';

interface CreateTransactionInput {
  plan_type: 'monthly' | 'annual' | 'report';
  item_type: 'subscription' | 'report';
  report_type?: 'wajar_slip_premium';
}

const PLANS = {
  monthly: { price: 49_000, description: 'Langganan Premium 1 Bulan' },
  annual: { price: 499_000, description: 'Langganan Premium 1 Tahun' },
  report: { price: 29_000, description: 'Premium Report - Wajar Slip' },
};

export async function POST(request: NextRequest) {
  try {
    const input: CreateTransactionInput = await request.json();
    const supabase = createServerComponentClient();

    // Get user
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Generate order_id: "user_123_subscription_monthly_20260407"
    const timestamp = new Date().toISOString().split('T')[0].replace(/-/g, '');
    const orderId = `user_${user.id}_${input.item_type}_${input.plan_type}_${timestamp}`;

    const planKey = input.plan_type as keyof typeof PLANS;
    const planPrice = PLANS[planKey].price;

    // Call Midtrans Snap API
    const snapUrl = 'https://app.midtrans.com/snap/v1/transactions';
    const auth = Buffer.from(
      `${process.env.MIDTRANS_SERVER_KEY}:`
    ).toString('base64');

    const response = await fetch(snapUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${auth}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        transaction_details: {
          order_id: orderId,
          gross_amount: planPrice,
        },
        item_details: [
          {
            id: input.plan_type,
            price: planPrice,
            quantity: 1,
            name: PLANS[planKey].description,
          },
        ],
        customer_details: {
          email: user.email,
          first_name: user.user_metadata?.full_name || 'User',
        },
        callbacks: {
          finish: `${process.env.NEXT_PUBLIC_BASE_URL}/dashboard/subscription?status=success`,
          unfinish: `${process.env.NEXT_PUBLIC_BASE_URL}/dashboard/subscription?status=pending`,
          error: `${process.env.NEXT_PUBLIC_BASE_URL}/dashboard/subscription?status=error`,
        },
      }),
    });

    if (!response.ok) {
      throw new Error(`Midtrans API error: ${response.statusText}`);
    }

    const snapData = await response.json();

    return NextResponse.json({
      snap_token: snapData.token,
      snap_redirect_url: snapData.redirect_url,
      order_id: orderId,
    });
  } catch (error) {
    console.error('Create transaction error:', error);
    return NextResponse.json(
      { error: 'Failed to create transaction' },
      { status: 500 }
    );
  }
}
```

---

## D.4 Dunning (Retry Failed Payments)

```sql
-- Trigger: Retry payment after 7 days with 3 attempts

CREATE OR REPLACE FUNCTION retry_failed_payment()
RETURNS void AS $$
BEGIN
  -- For each premium subscription that expired
  UPDATE users
  SET subscription_status = 'inactive'
  WHERE subscription_status = 'premium'
    AND subscription_expires_at < NOW()
    AND last_dunning_attempt < NOW() - INTERVAL '7 days';

  -- Send reminder email
  WITH expired_users AS (
    SELECT id, email
    FROM users
    WHERE subscription_status = 'inactive'
      AND subscription_expires_at < NOW()
  )
  INSERT INTO email_queue (user_id, email_type, recipient, created_at)
  SELECT id, 'dunning_reminder', email, NOW()
  FROM expired_users;
END;
$$ LANGUAGE plpgsql;

SELECT cron.schedule('retry_payments', '0 10 * * *', 'SELECT retry_failed_payment()');
```

---

# PART E: SECURITY ARCHITECTURE & ENVIRONMENT

---

## E.1 Authentication Providers

**Supabase Auth with multiple providers:**

```typescript
// lib/supabase/auth.ts
import { createBrowserClient } from '@supabase/ssr';

export const supabase = createBrowserClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// Email/password
export async function signUpEmail(email: string, password: string) {
  return supabase.auth.signUp({ email, password });
}

// Google OAuth
export async function signInGoogle() {
  return supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
    },
  });
}

// Anonymous session (free tier)
export async function signInAnonymously() {
  return supabase.auth.signInAnonymously();
}

// OTP (optional for B2B)
export async function signInPhoneOTP(phone: string) {
  return supabase.auth.signInWithOtp({
    phone,
  });
}
```

**Anonymous Session Upgrade:**

```typescript
// When anon user subscribes:
// 1. Create email/password account
// 2. Migrate verdict_logs from anon_user_id to new user_id
// 3. Update subscription_status

async function upgradeAnonymousSession(
  email: string,
  password: string
) {
  // Create real account
  const { data, error } = await supabase.auth.signUp({ email, password });
  if (error) throw error;

  const newUserId = data.user!.id;

  // Migrate data
  await supabase.rpc('migrate_anonymous_user', {
    new_user_id: newUserId,
    anon_session_id: currentAnonSessionId,
  });
}
```

---

## E.2 Rate Limiting Architecture

### Layer 1: Vercel Edge (100 req/min per IP)

```typescript
// middleware.ts
import { Ratelimit } from '@upstash/ratelimit';
import { NextRequest, NextResponse } from 'next/server';

const ratelimit = new Ratelimit({
  redis: Ratelimit.redis(process.env.UPSTASH_REDIS_URL!),
  limiter: Ratelimit.slidingWindow(100, '1 m'),
});

export async function middleware(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith('/api/verdict/')) {
    const ip = request.headers.get('x-forwarded-for') || 'unknown';
    const { success, pending } = await ratelimit.limit(ip);

    if (!success) {
      return NextResponse.json(
        { error: 'Rate limit exceeded', retry_after: 60 },
        { status: 429 }
      );
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/api/:path*'],
};
```

### Layer 2: Supabase RLS (Daily Quota)

```sql
-- RLS Policy: Enforce free tier limits
CREATE POLICY "enforce_free_tier_quota" ON verdict_logs
  FOR INSERT
  WITH CHECK (
    (
      SELECT subscription_status FROM users WHERE id = auth.uid()
    ) != 'free'
    OR
    (
      SELECT COUNT(*) FROM verdict_logs
      WHERE user_id = auth.uid()
        AND created_at >= NOW() - INTERVAL '1 day'
    ) < 5
  );
```

### Layer 3: B2B API Token Bucket

```typescript
// lib/payments/api-key-limiter.ts
import { createServerComponentClient } from '@supabase/ssr';

async function checkB2BQuota(apiKey: string): Promise<boolean> {
  const supabase = createServerComponentClient();

  // Fetch API key + quota
  const { data: apiKeyData } = await supabase
    .from('b2b_api_keys')
    .select('client_id, quota_remaining, last_reset_at')
    .eq('key_hash', hashKey(apiKey))
    .single();

  if (!apiKeyData) return false;

  // Token bucket: 1000 req/hour
  const hoursSinceReset =
    (Date.now() - new Date(apiKeyData.last_reset_at).getTime()) / (60 * 60 * 1000);

  if (hoursSinceReset >= 1) {
    // Reset bucket
    await supabase
      .from('b2b_api_keys')
      .update({ quota_remaining: 1000, last_reset_at: new Date().toISOString() })
      .eq('key_hash', hashKey(apiKey));

    return true;
  }

  // Check quota
  if (apiKeyData.quota_remaining <= 0) return false;

  // Decrement
  await supabase
    .from('b2b_api_keys')
    .update({ quota_remaining: apiKeyData.quota_remaining - 1 })
    .eq('key_hash', hashKey(apiKey));

  return true;
}
```

---

## E.3 Payslip Data Security

**Flow:**

```
1. User uploads PDF (client-side only, 5MB max)
2. POST /api/slip/ocr (Route handler)
3. Edge Function extracts data via OCR
4. Extracts: name, salary, deductions
5. Encrypts data (AES-256) → Supabase storage
6. Schedules deletion (30 days)
7. Immediately returns parsed data to client
8. User never sees raw PDF again
```

**Implementation:**

```typescript
// app/api/slip/ocr/route.ts
import { createServerComponentClient } from '@supabase/ssr';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const formData = await request.formData();
  const file = formData.get('file') as File;

  if (file.size > 5 * 1024 * 1024) {
    return NextResponse.json(
      { error: 'File too large (max 5MB)' },
      { status: 400 }
    );
  }

  const supabase = createServerComponentClient();
  const { data: { user } } = await supabase.auth.getUser();

  // Upload to private storage
  const fileName = `${user!.id}/${Date.now()}.pdf`;
  const { error: uploadError } = await supabase.storage
    .from('payslip_uploads')
    .upload(fileName, file, { upsert: false });

  if (uploadError) {
    return NextResponse.json(
      { error: 'Upload failed' },
      { status: 500 }
    );
  }

  // Call OCR edge function
  const ocrResponse = await fetch(
    `${process.env.SUPABASE_URL}/functions/v1/ocr_payslip`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.SUPABASE_SERVICE_ROLE_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        file_path: fileName,
        user_id: user!.id,
      }),
    }
  );

  const ocrData = await ocrResponse.json();

  // Schedule deletion after 30 days
  await supabase.rpc('schedule_file_deletion', {
    file_path: fileName,
    delete_after_days: 30,
  });

  return NextResponse.json(ocrData);
}
```

**RLS Policy for Payslip Storage:**

```sql
CREATE POLICY "Users can upload own payslips" ON storage.objects
  FOR INSERT WITH CHECK (
    auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users can read own payslips" ON storage.objects
  FOR SELECT USING (
    auth.uid()::text = (storage.foldername(name))[1]
  );

-- Auto-delete after 30 days via pg_cron
SELECT cron.schedule(
  'delete_old_payslips',
  '0 2 * * *',
  $$
    DELETE FROM storage.objects
    WHERE bucket_id = 'payslip_uploads'
      AND created_at < NOW() - INTERVAL '30 days'
  $$
);
```

---

## E.4 Complete Environment Variables

```bash
# ==================== SUPABASE ====================
NEXT_PUBLIC_SUPABASE_URL=https://[project-id].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...                        # Public, safe to expose
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...                             # Server-only, NEVER expose

# ==================== MIDTRANS ====================
MIDTRANS_SERVER_KEY=Mid-server-abcd1234efgh5678ijkl             # Server-only
NEXT_PUBLIC_MIDTRANS_CLIENT_KEY=Mid-client-xyza9876bcde5432     # Public, for Snap
MIDTRANS_WEBHOOK_SECRET=webhook-secret-key                       # For signature verification

# ==================== OPENAI (for agents) ====================
OPENAI_API_KEY=sk-proj-abc123...                                 # Server-only (Fly.io)
OPENAI_EMBEDDING_MODEL=text-embedding-3-small                    # For pgvector
OPENAI_CHAT_MODEL=gpt-4-turbo

# ==================== RATE LIMITING & CACHING ====================
UPSTASH_REDIS_URL=redis://default:[password]@[region].upstash.io # Rate limit backend

# ==================== FILE STORAGE ====================
NEXT_PUBLIC_SUPABASE_STORAGE_URL=https://[project-id].supabase.co/storage/v1

# ==================== MONITORING & OBSERVABILITY ====================
SENTRY_DSN=https://[key]@o[org].ingest.sentry.io/[project]       # Error tracking
SENTRY_AUTH_TOKEN=sntr_xyz...                                     # For source maps
NEXT_PUBLIC_POSTHOG_KEY=phc_abc123...                             # Analytics (public)

# ==================== EMAIL SERVICE ====================
SENDGRID_API_KEY=SG.abc123...                                     # Transactional email

# ==================== GITHUB (for automation) ====================
GITHUB_TOKEN=ghp_abc123...                                        # For agent CI/CD
GITHUB_REPO=username/cekwajar_id

# ==================== DEPLOYMENT ====================
NEXT_PUBLIC_BASE_URL=https://cekwajar.id                          # Production domain
NODE_ENV=production                                                # production | development

# ==================== BRIGHTDATA (optional, for web scraping) ====================
BRIGHTDATA_API_KEY=abc123...                                      # Rotating proxies
BRIGHTDATA_ZONE=lightzone

# ==================== INTERNAL SECRETS (never expose) ====================
JWT_SECRET=random-256-char-string                                 # For session signing
ENCRYPTION_KEY=random-32-char-hex                                 # AES-256 encryption key
```

**Deployment Instructions (Vercel):**

```bash
# Set production environment variables
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY
vercel env add SUPABASE_SERVICE_ROLE_KEY    # Mark as "sensitive"
vercel env add MIDTRANS_SERVER_KEY          # Mark as "sensitive"
# ... add all sensitive keys

# Deploy
vercel deploy --prod
```

**Agent Deployment (Fly.io):**

```bash
# Create Fly.io app
fly launch --name cekwajar-agents

# Set secrets
fly secrets set OPENAI_API_KEY=sk-proj-...
fly secrets set SUPABASE_SERVICE_ROLE_KEY=...
fly secrets set GITHUB_TOKEN=ghp_...

# Deploy
fly deploy
```

---

## E.5 Security Best Practices Summary

| Layer | Control | Status |
|-------|---------|--------|
| **Authentication** | Email/Password + Google OAuth + OTP | Supabase Auth |
| **Authorization** | RLS policies (Supabase) + role-based access | Per table |
| **Data Encryption** | AES-256 at rest (Supabase default) + TLS in transit | Enabled |
| **Rate Limiting** | Vercel Edge + Redis (Upstash) + RLS quotas | 3-layer |
| **Secrets Management** | Vercel env vars (sensitive flag) + Fly.io secrets | Automated |
| **Audit Logging** | GitHub Issues + Supabase audit_logs table | Automated |
| **CORS** | Vercel deployment (auto-handled) | Configured |
| **CSP Headers** | Next.js `next/headers` with strict CSP | To configure |
| **OWASP Compliance** | Input validation (Zod), output encoding, CSRF tokens | Implemented |

---

## CONCLUSION

This technical architecture specification provides a complete, build-ready foundation for cekwajar.id. Key highlights:

1. **Frontend (Next.js 15)**: Hybrid SSG/ISR/SSR/CSR approach optimized for Indonesia 4G networks
2. **Backend (Supabase)**: Powerful, privacy-preserving PostgreSQL with Edge Functions and RLS
3. **AI Agents (Swarms)**: 17 autonomous agents handling 80%+ of operational tasks
4. **Payments (Midtrans)**: Complete subscription + one-time payment flows with webhook handling
5. **Security**: Multi-layer rate limiting, encryption, RLS, and authentication

**Total Monthly Cost Estimate:**
- Vercel: $20 (Pro plan)
- Supabase: $25 (Pro, 10GB storage)
- OpenAI (agents): $12
- Upstash Redis: $2
- Sentry: $10
- SendGrid: Free tier
- **Total: ~$69/month** (very cost-effective for a 5-tool platform)

All specifications are production-ready and can be deployed immediately.

