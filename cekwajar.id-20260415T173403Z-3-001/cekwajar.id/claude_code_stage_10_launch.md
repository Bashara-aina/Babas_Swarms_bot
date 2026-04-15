# Stage 10 — Production Hardening + Security + Launch
**cekwajar.id Vibe Coding Playbook**  
**Estimated time:** 3–4 hours  
**Prerequisites:** All stages 1–9 complete and working in development.  
**Goal:** Production-ready security hardening, switch Midtrans to production, custom domain, Sentry live, pre-launch checklist complete, first TikTok posted.

---

## ═══════════════════════════════════════════════
## MASTER PROMPT — SEND THIS TO CLAUDE CODE
## (Stage 10 — Production Hardening)
## ═══════════════════════════════════════════════

```
===START===
cekwajar.id — Stage 10: Production Hardening + Launch Preparation

Context: All 5 tools working in development. Payment working in sandbox.
Stages 1-9 complete.

YOUR TASK FOR STAGE 10:
Harden the application for production: security headers, proper rate limiting,
Sentry error monitoring, performance optimizations, and launch checklist verification.

════════════════════════════════════════════════════
PART A: SECURITY HEADERS + CSP
════════════════════════════════════════════════════

Update next.config.ts to add security headers:

const securityHeaders = [
  {
    key: 'X-DNS-Prefetch-Control',
    value: 'on',
  },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload',
  },
  {
    key: 'X-Frame-Options',
    value: 'SAMEORIGIN',
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff',
  },
  {
    key: 'Referrer-Policy',
    value: 'origin-when-cross-origin',
  },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=()',
  },
  {
    key: 'Content-Security-Policy',
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' https://app.sandbox.midtrans.com https://app.midtrans.com https://cdn.jsdelivr.net",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https: blob:",
      "font-src 'self'",
      "connect-src 'self' https://*.supabase.co https://api.worldbank.org https://api.frankfurter.app https://vision.googleapis.com https://app.sandbox.midtrans.com https://app.midtrans.com",
      "frame-src https://app.sandbox.midtrans.com https://app.midtrans.com",
      "object-src 'none'",
      "base-uri 'self'",
    ].join('; '),
  },
]

In next.config.ts, add:
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: securityHeaders,
      },
    ]
  }

════════════════════════════════════════════════════
PART B: PRODUCTION RATE LIMITING WITH VERCEL KV
════════════════════════════════════════════════════

Replace the in-memory rate limiter from Stage 4 with Vercel KV (Redis-compatible).

Install:
  pnpm add @vercel/kv

Set up Vercel KV:
  vercel link  (if not already linked)
  vercel kv create cekwajar-rl  (creates KV store)
  vercel env pull  (gets KV env vars: KV_URL, KV_REST_API_URL, etc.)

Create src/lib/ratelimit.ts:

import { kv } from '@vercel/kv'

interface RateLimitConfig {
  windowSeconds: number
  maxRequests: number
  keyPrefix: string
}

const LIMITS: Record<string, RateLimitConfig> = {
  '/api/audit-payslip': { windowSeconds: 3600, maxRequests: 5, keyPrefix: 'rl:audit' },
  '/api/ocr/upload': { windowSeconds: 3600, maxRequests: 3, keyPrefix: 'rl:ocr' },
  '/api/salary/benchmark': { windowSeconds: 3600, maxRequests: 30, keyPrefix: 'rl:salary' },
  '/api/property/benchmark': { windowSeconds: 3600, maxRequests: 30, keyPrefix: 'rl:property' },
  '/api/abroad/compare': { windowSeconds: 3600, maxRequests: 20, keyPrefix: 'rl:abroad' },
  '/api/col/compare': { windowSeconds: 3600, maxRequests: 30, keyPrefix: 'rl:col' },
  '/api/salary/submit': { windowSeconds: 86400, maxRequests: 2, keyPrefix: 'rl:submit' },
}

export async function checkRateLimit(
  ip: string,
  path: string
): Promise<{ allowed: boolean; remaining: number; resetAt: number }> {
  const config = LIMITS[path]
  if (!config) return { allowed: true, remaining: 999, resetAt: 0 }
  
  const key = `${config.keyPrefix}:${ip}`
  
  const count = await kv.incr(key)
  
  if (count === 1) {
    await kv.expire(key, config.windowSeconds)
  }
  
  const ttl = await kv.ttl(key)
  
  return {
    allowed: count <= config.maxRequests,
    remaining: Math.max(0, config.maxRequests - count),
    resetAt: Date.now() + ttl * 1000,
  }
}

Update middleware.ts to add rate limiting for API routes:
  Add rate limit check for /api/ routes using the function above.
  Return 429 with Retry-After header on limit breach.

════════════════════════════════════════════════════
PART C: SENTRY ERROR MONITORING
════════════════════════════════════════════════════

Run Sentry wizard:
  npx @sentry/wizard@latest -i nextjs

This auto-configures:
  sentry.client.config.ts
  sentry.server.config.ts
  sentry.edge.config.ts
  instrumentation.ts

After setup, add these Sentry integrations:
  // In sentry.server.config.ts
  Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    tracesSampleRate: 0.1,  // 10% of requests (to stay on free tier)
    environment: process.env.NODE_ENV,
    
    // Ignore these errors (expected, not bugs)
    ignoreErrors: [
      'RATE_LIMIT_EXCEEDED',
      'INVALID_CITY',
      'Next.js not found',
    ],
  })

Add to API routes for better error context:
  import * as Sentry from '@sentry/nextjs'
  
  // In catch blocks:
  Sentry.captureException(error, {
    extra: {
      endpoint: '/api/audit-payslip',
      userId: user?.id,
    }
  })

════════════════════════════════════════════════════
PART D: PERFORMANCE OPTIMIZATIONS
════════════════════════════════════════════════════

1. Add Next.js metadata for SEO:
  Update each tool page with metadata:
  
  export const metadata: Metadata = {
    title: 'Wajar Slip — Cek Kesesuaian Slip Gaji | cekwajar.id',
    description: 'Audit PPh21 dan BPJS slip gaji kamu secara gratis. Berbasis regulasi PMK 168/2023.',
    openGraph: {
      title: 'Cek Slip Gaji Kamu — cekwajar.id',
      description: 'Audit PPh21 dan BPJS dalam 30 detik. Gratis.',
      url: 'https://cekwajar.id/wajar-slip',
      siteName: 'cekwajar.id',
      locale: 'id_ID',
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title: 'Cek Slip Gaji — cekwajar.id',
    },
  }

2. Add React Query for client-side caching:
  Wrap app in QueryClientProvider.
  
  For city dropdown data (changes rarely):
    queryKey: ['cities']
    staleTime: 24 * 60 * 60 * 1000  // 24 hours
  
  For salary benchmark (changes monthly):
    queryKey: ['salary-benchmark', jobTitle, city, experience]
    staleTime: 60 * 60 * 1000  // 1 hour

3. Add loading states with suspense:
  Each tool page should show skeleton loaders during API calls.
  Create src/components/shared/ToolSkeleton.tsx with animated skeletons.

4. Add error boundaries:
  Create src/components/shared/ErrorBoundary.tsx
  Wrap each tool's main content area.

5. Lazy load Tesseract.js:
  Already handled in Stage 5, but verify it's not in the initial bundle.
  Run: pnpm build && pnpm analyze (install @next/bundle-analyzer first)
  Tesseract should NOT appear in initial bundle.

════════════════════════════════════════════════════
PART E: PRODUCTION SECRETS SWITCH
════════════════════════════════════════════════════

When ready to go live with real payments:

Update Vercel env vars to production values:
  MIDTRANS_SERVER_KEY: replace SB-Mid-server-... with Mid-server-...
  NEXT_PUBLIC_MIDTRANS_CLIENT_KEY: replace SB-Mid-client-... with Mid-client-...
  MIDTRANS_IS_PRODUCTION: change to 'true'
  NEXT_PUBLIC_MIDTRANS_IS_PRODUCTION: add this as 'true'

Update Midtrans notification URL in dashboard:
  Midtrans Dashboard → Settings → Configuration → Payment Notification URL
  Set to: https://cekwajar.id/api/webhooks/midtrans

Update CSP to remove sandbox URL:
  Replace https://app.sandbox.midtrans.com with https://app.midtrans.com
  Keep both during transition period.

Add this env var check to startup:
  Create src/lib/config/validate.ts:
  
  const REQUIRED_ENV_VARS = [
    'NEXT_PUBLIC_SUPABASE_URL',
    'NEXT_PUBLIC_SUPABASE_ANON_KEY',
    'SUPABASE_SERVICE_ROLE_KEY',
    'GOOGLE_VISION_API_KEY',
    'MIDTRANS_SERVER_KEY',
    'NEXT_PUBLIC_MIDTRANS_CLIENT_KEY',
  ]
  
  export function validateEnvVars() {
    const missing = REQUIRED_ENV_VARS.filter(key => !process.env[key])
    if (missing.length > 0) {
      throw new Error(`Missing environment variables: ${missing.join(', ')}`)
    }
  }
  
  // Call in src/app/layout.tsx (server component):
  import { validateEnvVars } from '@/lib/config/validate'
  validateEnvVars()

════════════════════════════════════════════════════
PART F: COMPREHENSIVE PRE-LAUNCH SECURITY AUDIT
════════════════════════════════════════════════════

Create scripts/security-audit.sh:

#!/bin/bash
echo "=== cekwajar.id Pre-Launch Security Audit ==="

# 1. Check for secrets in codebase
echo "1. Checking for secrets..."
grep -r "service_role" src/ --include="*.ts" --include="*.tsx" | grep -v "getServiceClient\|validateEnvVars"
echo "If any matches above: FAIL — service_role key found in source code"

# 2. Check .gitignore covers all sensitive files
echo "2. Checking .gitignore..."
git check-ignore .env .env.local agents/.env
echo "All 3 should show 'ignored'"

# 3. Verify no console.log with user data
echo "3. Checking for PII in console.log..."
grep -r "console.log" src/app/api/ --include="*.ts" | grep -i "email\|salary\|user"
echo "If any matches: Review for PII leak"

# 4. Check RLS is enabled
echo "4. Run this in Supabase SQL editor:"
echo "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"
echo "ALL tables must show rowsecurity=true"

# 5. Check rate limiting
echo "5. Run: for i in {1..6}; do curl -s -o /dev/null -w \"%{http_code}\\n\" -X POST localhost:3000/api/audit-payslip -H 'Content-Type: application/json' -d '{}'; sleep 0.1; done"
echo "Requests 1-5: 400 (bad request, not rate limited)"
echo "Request 6: 429 (rate limited)"

# 6. Check no direct DB connection strings exposed
grep -r "postgresql://" src/ --include="*.ts" --include="*.tsx"
echo "Should show 0 matches"

echo "=== Audit complete. Fix any FAIL items before launch. ==="

Run: bash scripts/security-audit.sh

════════════════════════════════════════════════════
PART G: UPTIME MONITORING SETUP
════════════════════════════════════════════════════

Set up Uptime Robot (free):
  1. uptimerobot.com → Add New Monitor
  2. Monitor type: HTTP(s)
  3. URL: https://cekwajar.id/api/health
  4. Check interval: 5 minutes
  5. Alert contacts: your email + Telegram bot (optional)

Telegram alert bot (optional but recommended):
  1. @BotFather → /newbot → get token
  2. Get your chat ID: message @userinfobot
  3. Add to .env.local: TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=...
  4. Uptime Robot → Alert contacts → Add Telegram

Create src/app/api/health/route.ts (update from Stage 1):
  Now returns comprehensive health status:
  
  {
    status: 'ok' | 'degraded' | 'error',
    timestamp: ISO string,
    checks: {
      database: 'ok' | 'error',
      midtrans: 'sandbox' | 'production' | 'error',
      googleVision: 'ok' | 'error',
      ocrQuota: { monthCount: number, isOk: boolean },
    }
  }
  
  For database check: SELECT 1 FROM pph21_ter_rates LIMIT 1
  For Midtrans: check if MIDTRANS_IS_PRODUCTION matches expected env
  For Vision: check GOOGLE_VISION_API_KEY exists (don't ping API to avoid quota waste)
  For OCR quota: read ocr_quota_counter for current month

════════════════════════════════════════════════════
PART H: FINAL LAUNCH CHECKLIST (EXECUTE IN ORDER)
════════════════════════════════════════════════════

Create scripts/launch-checklist.md:

PRE-LAUNCH (do these before pointing domain):

□ pnpm tsc --noEmit → zero errors
□ pnpm lint → zero errors
□ pnpm build → successful build, no build errors
□ All 5 tool pages load and calculate correctly
□ Auth (Google + email) works in production Supabase project
□ Privacy Policy at /privacy-policy
□ Terms of Service at /terms
□ Cookie consent shows on first visit
□ KJPP disclaimer shows on Wajar Tanah
□ PPP disclaimer shows on Wajar Kabur
□ Tax disclaimer shows on Wajar Slip
□ UMK data loaded (SELECT COUNT(*) FROM umk_2026 >= 50)
□ TER rate data loaded (SELECT COUNT(*) FROM pph21_ter_rates >= 30)
□ BPJS rates loaded (SELECT COUNT(*) FROM bpjs_rates = 12)
□ PTKP values loaded (SELECT COUNT(*) FROM ptkp_values = 12)
□ Col indices loaded (SELECT COUNT(*) FROM col_indices = 20)
□ PPP reference loaded (SELECT COUNT(*) FROM ppp_reference = 15)
□ RLS enabled on ALL tables (check from Supabase Studio)
□ payslips storage bucket is PRIVATE (not public)
□ Sentry DSN configured, error tracking working
□ Uptime Robot configured and monitoring

PAYMENT LAUNCH (only when ready to accept real money):

□ PSE Kominfo registration completed
□ Midtrans production keys in Vercel (not sandbox)
□ Midtrans webhook URL updated to https://cekwajar.id/api/webhooks/midtrans
□ Test one real payment (your own card/GoPay) for Rp 1 → verify subscription activates
□ Test webhook with real Midtrans production event
□ Confirm email arrives after payment

DOMAIN + DNS:

□ Domain cekwajar.id purchased (pandi.id or niagahoster.co.id)
□ DNS A record → Vercel IPs: 76.76.21.21
□ CNAME www → cekwajar.id.vercel-dns.com (or Vercel alias)
□ Vercel project → Domains → Add custom domain
□ SSL certificate active (Vercel handles this automatically)
□ Update NEXT_PUBLIC_APP_URL in Vercel: https://cekwajar.id
□ Update Supabase Site URL: https://cekwajar.id
□ Update Supabase Redirect URLs: https://cekwajar.id/auth/callback

POST-LAUNCH DAY 1:

□ Monitor Sentry for new errors (first 24h)
□ Monitor Uptime Robot for any downtime
□ Check Supabase Logs for unusual queries
□ Post TikTok Week 1 Video 1
□ Post launch on r/finansialku
□ Share beta link in WhatsApp HRD group
□ Monitor signup count in Supabase auth.users

════════════════════════════════════════════════════
PART I: ONE-CLICK DEPLOY COMMAND
════════════════════════════════════════════════════

Create scripts/deploy.sh:

#!/bin/bash
set -e

echo "🚀 Deploying cekwajar.id to production..."

# Run checks
echo "Running TypeScript check..."
pnpm tsc --noEmit

echo "Running lint..."
pnpm lint

echo "Building..."
pnpm build

echo "Running security audit..."
bash scripts/security-audit.sh

echo "Committing and pushing..."
git add .
git status

read -p "Review changes above. Continue? [y/N] " confirm
if [[ $confirm != [yY] ]]; then
  echo "Cancelled."
  exit 1
fi

git commit -m "deploy: stage 10 hardening"
git push origin main

echo "✅ Pushed to GitHub. Vercel will auto-deploy."
echo "Monitor deployment at: https://vercel.com/dashboard"

Run: bash scripts/deploy.sh

════════════════════════════════════════════════════
VERIFICATION:
════════════════════════════════════════════════════

FINAL SMOKE TEST (run after production deploy):

1. Open https://cekwajar.id → homepage loads
2. Visit /api/health → { status: 'ok' }
3. Sign up with a NEW Google account
4. Complete Wajar Slip with manual form
5. Upgrade to Basic with Midtrans (use sandbox OR real payment)
6. Verify violation details now visible
7. Check Sentry for any errors
8. Check Uptime Robot shows green

pnpm tsc --noEmit → zero errors
pnpm build → successful
===END===
```

---

## Complete Stage Summary

Once all 10 stages are complete, you have:

| Stage | What's Live |
|-------|------------|
| 1 | Scaffold + Nav + 5 tool stubs + Vercel deploy |
| 2 | All 19 DB migrations + seed data + RLS + pg_cron |
| 3 | Auth (Google + email) + Dashboard + PremiumGate |
| 4 | Wajar Slip manual form + calculation engine + verdict |
| 5 | Wajar Slip OCR (Vision + Tesseract fallback) |
| 6 | Wajar Gaji benchmark + crowdsource + BPS loader + JobStreet scraper |
| 7 | Wajar Tanah verdict + 99.co + Rumah123 scrapers |
| 8 | Wajar Kabur PPP comparison + Wajar Hidup COL comparison |
| 9 | Midtrans payments + webhook + subscription activation + legal pages |
| 10 | Security headers + KV rate limiting + Sentry + launch checklist |

---

## Quick Reference: All Dependencies

```bash
# npm/pnpm (production)
@supabase/supabase-js @supabase/ssr
@radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-select
@radix-ui/react-toast @radix-ui/react-tabs @radix-ui/react-progress
lucide-react class-variance-authority clsx tailwind-merge
react-hook-form @hookform/resolvers zod
@tanstack/react-query
date-fns
@sentry/nextjs
tesseract.js
react-dropzone
sharp
resend
@vercel/kv
js-cookie

# npm/pnpm (dev)
@types/node @types/sharp @types/js-cookie

# Python (agents/)
swarms playwright playwright-stealth
supabase python-dotenv
openpyxl pandas numpy httpx asyncio aiohttp
pytest pytest-asyncio

# Global CLI tools
pnpm vercel supabase claude
```

---

## Quick Reference: All API Keys Needed

| Key | Where to Get | Environment |
|-----|-------------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase → Settings → API | All |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase → Settings → API | All |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Settings → API | Server only |
| `SUPABASE_DB_URL` | Supabase → Settings → Database | Server only |
| `GOOGLE_VISION_API_KEY` | GCP → Credentials | Server only |
| `MIDTRANS_SERVER_KEY` | Midtrans → Settings → Access Keys | Server only |
| `NEXT_PUBLIC_MIDTRANS_CLIENT_KEY` | Midtrans → Settings → Access Keys | All |
| `MIDTRANS_IS_PRODUCTION` | Set manually | All |
| `NEXT_PUBLIC_SENTRY_DSN` | Sentry → Project → Settings | All |
| `RESEND_API_KEY` | resend.com → API Keys | Server only |
| `KV_URL` (auto) | Vercel KV | Server only |

**Total external services:** 7 (Supabase, GCP, Midtrans, Sentry, Resend, Vercel KV, Frankfurter/WorldBank = free)  
**Monthly cost at launch:** IDR 0 (all free tiers)  
**Monthly cost at 500+ subscribers:** IDR ~300K (Supabase Pro plan upgrade)
