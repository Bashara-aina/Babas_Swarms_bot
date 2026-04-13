---
title: adr-2026-04-13-cekwajar-tech-stack
type: decision
status: active
tags: [cekwajar, tech-stack, nextjs, supabase, vercel, markitdown, database, architecture-decision]
created: 2026-04-13
updated: 2026-04-13
summary: "Decision to build cekwajar.id on Next.js 15 App Router, Supabase PostgreSQL with Row Level Security, Vercel deployment, and markitdown for document conversion. Rationale: Next.js 15 provides SSR+API routes in one framework; Supabase RLS enforces user data isolation; Vercel is native Next.js host with edge functions; markitdown handles PDF/DOCX conversion reliably. Individual Midtrans merchant account enables IDR 29K/79K/month subscription payments."
wikilinks:
  - [[cekwajar-id]]
  - [[entities/supabase]]
  - [[entities/openrouter]]
  - [[cekwajar-verdict-engine]]
confidence: high
source: implementation
---

# ADR-2026-04-13: cekwajar.id Tech Stack

**Date**: 2026-04-13  
**Status**: DECIDED  
**Decider**: Founder  
**Stack Components**: Next.js 15 + Supabase + Vercel + markitdown + Midtrans

---

## Context

cekwajar.id requires a tech stack that:
1. Enables rapid MVP development (136h engineering budget)
2. Handles Indonesian market realities (Midtrans payments, bahasa Indonesia UI)
3. Meets UU PDP data protection requirements (Row Level Security, data residency)
4. Supports OCR processing pipeline (Google Vision API integration)
5. Scales to 10,000+ MAU without infrastructure management overhead

As a solo founder with limited ops capacity, avoiding server management, Kubernetes, and complex DevOps is not optional — it's a survival requirement.

---

## Decision

### Primary Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| **Frontend + Backend** | Next.js 15 App Router | SSR for landing pages (SEO), API routes for verdict engine, React Server Components |
| **Database + Auth** | Supabase PostgreSQL | PostgreSQL with RLS, built-in auth (email + phone for Indonesia), storage |
| **Deployment** | Vercel | Native Next.js host, edge functions, preview deployments, zero-config |
| **Payments** | Midtrans | Dominant Indonesian payment gateway, individual merchant account support |
| **Document Conversion** | markitdown | Microsoft library for PDF→markdown, handles Indonesian payslip formats |
| **LLM (future)** | OpenRouter/litellm | Unified API for model routing if AI narrative is added post-MVP |

### Excluded Technologies

| Technology | Reason for Exclusion |
|------------|---------------------|
| AWS Lambda单独的 | Vercel edge functions sufficient; avoids AWS complexity |
| Amazon Textract | Google Vision Document AI has better table/form handling for payslips |
| Heroku | Deprecated pipeline; Vercel superior for Next.js |
| DigitalOcean App Platform | Less Next.js native support than Vercel |
| Prisma | Supabase client library sufficient for MVP; adds complexity |
| Separate auth service | Supabase Auth covers email + phone (Indonesia-relevant) |

---

## Alternatives Considered

### Alternative 1: Firebase + Cloud Run

**Pros**: 
- Firebase Auth has excellent phone auth (Indonesia-relevant via +62)
- Cloud Run scales well for OCR processing
- Firestore for document storage

**Cons**:
- Firebase Auth is expensive at scale
- No native PostgreSQL (Firestore is NoSQL)
- RLS equivalent (Firestore rules) is less ergonomic
- Vendor lock-in more severe than Supabase

**Verdict**: Firebase Auth phone support is valuable but PostgreSQL requirement (RLS, complex queries) makes this a no-go.

### Alternative 2: AWS Amplify + Aurora Serverless

**Pros**:
- Aurora Serverless scales to zero (cost efficiency)
- Amplify has excellent Next.js support

**Cons**:
- Complex AWS IAM setup
- Aurora Serverless cold start latency issues
- More expensive than Supabase for MVP stage

**Verdict**: Overengineered for MVP. Reconsider at 1M+ MAU.

### Alternative 3: PocketBase

**Pros**:
- Single binary, extremely simple deployment
- SQLite (no database server)
- Built-in auth and UI

**Cons**:
- SQLite limitations: no concurrent writes, 1TB max
- Not built for scale beyond small app
- Limited ecosystem compared to Supabase

**Verdict**: Good for solo prototypes, not for platform with 10K+ MAU ambition.

---

## Detailed Component Decisions

### Next.js 15 App Router

**Why App Router (not Pages Router)**:
- React Server Components for reduced client-side JS
- Better streaming for verdict results
- Layouts for consistent UI structure
- Native support for loading.tsx and error.tsx

**API Routes vs Edge Functions**:
- Use API Routes for verdict engine (Node.js runtime, longer timeouts)
- Use Edge Functions for OCR file validation (sub-second, geo-distributed)

### Supabase PostgreSQL + RLS

**Why Supabase (not Railway/Render/Vercel Postgres)**:
- Built-in auth with phone/email support
- Row Level Security is first-class, not bolted-on
- pg_cron for 30-day payslip auto-deletion
- Supabase Storage for payslip files
- Dashboard for monitoring RLS policy effects

**Row Level Security Implementation**:

```sql
-- Users can only read their own submissions
CREATE POLICY "users_read_own_submissions" ON payslip_submissions
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own submissions
CREATE POLICY "users_insert_own" ON payslip_submissions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Verdict is readable only by submission owner
CREATE POLICY "users_read_own_verdicts" ON payslip_verdicts
    FOR SELECT USING (auth.uid() = user_id);

-- Anonymized benchmark data is publicly readable (no PII)
CREATE POLICY "public_read_benchmarks" ON salary_benchmarks
    FOR SELECT USING (true);
```

### Vercel Deployment

**Why Vercel (not Railway/ Render/ Fly.io)**:
- Native Next.js support: zero-configuration deployment
- Preview deployments per branch (automatic for Legion repo)
- Edge Middleware for rate limiting
- Analytics dashboard for Core Web Vitals
- Serverless function timeout: 10s (sufficient for verdict engine)

**Environment Variables**:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...    # Frontend only
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...       # Server-side only, NEVER exposed
MIDTRANS_SERVER_KEY=xxx
MIDTRANS_CLIENT_KEY=xxx
GOOGLE_CLOUD_VISION_API_KEY=xxx
```

**Critical**: `SUPABASE_SERVICE_ROLE_KEY` must NEVER appear in frontend code, browser environment, or git commit.

### markitdown for Document Conversion

**Why markitdown**:
- Microsoft-maintained library for PDF/DOCX/XLSX → markdown
- Handles complex table structures in payslips better than pdf-parse
- Pure JavaScript (no native dependencies)
- Works in Vercel Edge Functions (no filesystem access needed)

**Alternative considered**: pdf-parse (more popular but worse at tables)

### Midtrans Payment Integration

**Why Midtrans (not Xendit/Flip)**:
- Midtrans is the dominant payment gateway in Indonesia
- Supports individual merchant account (KTP + NPWP, no PT required for MVP)
- SnapJS for checkout popup (reduces cart abandonment)
- Subscription support for recurring IDR 29K/79K/month

**Webhook Events to Handle**:
```typescript
// Critical webhook events
'payment.success'     → activate subscription
'payment.failed'      → retry (Day 1, 3, 7), then downgrade to free  
'payment.expired'     → downgrade to free, win-back email
'subscription.cancel'  → log cancellation reason
```

---

## Architecture Constraints

### 1. Supabase Region: ap-southeast-1 (Singapore)

UU PDP Pasal 56 prohibits cross-border transfer without adequacy determination or DPA. US region (us-east-1) creates compliance risk. Singapore is closest to Indonesian users and has compatible PDPA.

**Migration**: New Supabase project in Singapore → schema dump/restore → DNS update. ~1 hour.

### 2. Payslip Data: 30-Day Auto-Delete

Per UU PDP Pasal 28 (data retention), payslip files must be deleted when no longer needed.

```sql
-- pg_cron job: delete payslip files older than 30 days
SELECT cron.schedule(
    'delete-old-payslips',
    '0 2 * * *',  -- 2 AM every day
    $$
    DELETE FROM payslip_files 
    WHERE created_at < NOW() - INTERVAL '30 days';
    $$
);
```

### 3. No PII in Benchmarks

Company name → industry + size category (after 90 days). NIK (if on payslip) → redacted before storage.

---

## Consequences

### Positive
- Rapid MVP development (136h budget achievable)
- Supabase RLS eliminates 80% of auth/security code
- Vercel preview deployments enable Legion review workflow
- Midtrans individual account enables fast payment launch

### Negative  
- Vendor lock-in to Supabase + Vercel
- Vercel cold starts on serverless functions (mitigate with edge caching)
- markitdown may struggle with scanned PDFs (mitigate with Google Vision primary)

### Mitigation of Lock-In
- Supabase is standard PostgreSQL — exportable anytime
- Next.js on Vercel is portable to any Node.js host
- All secrets in environment variables (not hardcoded)

---

## Related Articles

- [[cekwajar-id]] — Project using this stack
- [[cekwajar-verdict-engine]] — Verdict engine running on this stack
- [[entities/supabase]] — Database provider
- [[cekwajar-ocr-pipeline]] — OCR pipeline using this infrastructure
