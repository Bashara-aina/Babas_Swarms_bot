# req_12 — Operations Spec: cekwajar.id
**Document Type:** Operations Specification  
**Version:** 1.0  
**Scope:** Deployment, monitoring, incident response, GTM calendar, sprint tracking

---

## 9.1 Deployment Runbook

### Deployment Philosophy

- **Trunk-based development:** One main branch. Feature branches merged via PR. No long-lived branches.
- **Preview deployments:** Every PR gets a Vercel preview URL automatically.
- **Production deployments:** Merge to `main` triggers automatic Vercel production deploy.
- **Database migrations:** Run manually before deploying code that depends on new schema.
- **Zero-downtime target:** Vercel handles rolling deployments. Supabase DDL changes may lock tables briefly — run during low-traffic.

---

### Standard Deployment Flow

```
Developer (founder) → GitHub PR → Vercel Preview → Test → Merge → Production
                                        ↓
                              Supabase migration (if needed) runs FIRST
```

**Step-by-step:**

```bash
# 1. Create feature branch
git checkout -b feature/wajar-gaji-crowdsource

# 2. Develop locally
npm run dev

# 3. Run local tests
npm test                          # unit tests
npm run test:integration          # integration tests (uses Supabase local)

# 4. Push to GitHub (triggers Vercel preview build)
git push origin feature/wajar-gaji-crowdsource

# 5. Check Vercel preview build status
# Vercel Dashboard → cekwajar-id → Deployments → Preview URL

# 6. Run migration on staging Supabase branch (if schema changed)
supabase db push --linked --branch staging

# 7. Smoke test on preview URL
# Open preview URL, manually test affected flows

# 8. Merge PR to main
# GitHub → Pull Request → Merge → Squash and merge

# 9. Vercel auto-deploys to production
# Monitor at: vercel.com/your-org/cekwajar-id

# 10. Run production migration (if needed)
supabase db push --linked                 # applies pending migrations to production

# 11. Verify production
# cekwajar.id → test key flows manually
# Check Sentry for new errors
# Check Vercel Analytics for traffic
```

---

### Database Migration Steps

**ALWAYS run migrations before deploying code that depends on new schema.**

```bash
# Check what migrations are pending
supabase db diff --linked

# Dry run (shows what will execute)
supabase db push --linked --dry-run

# Apply in production
supabase db push --linked

# Verify success
supabase db diff --linked  # should show no diff after successful push
```

**Migration safety rules:**
- Never drop a column in the same migration that removes code referencing it. Two-step: first deploy code that stops using column, then drop column.
- Never rename a column — add new, backfill, remove old.
- Add `NOT NULL` columns with a `DEFAULT` value first, then remove default if needed.
- Test migrations in Supabase Studio locally before production.

---

### Rollback Procedure

#### Code Rollback (Vercel)

```bash
# Via Vercel CLI:
vercel rollback --prod [deployment-url]

# Or via Dashboard:
# Vercel → cekwajar-id → Deployments → previous deployment → "..." → Promote to Production
```

**When to rollback:**
- Critical bug in production causing wrong calculations
- Complete outage (5xx on all requests)
- Security vulnerability deployed

**When NOT to rollback (fix forward instead):**
- Minor UI bug
- Non-critical feature malfunction
- Performance regression < 20%

#### Database Rollback

Database migrations are not auto-rolled back. Each migration file has a `-- rollback:` section with manual SQL. Execute in reverse order.

```bash
# Example: Rolling back migration 007
# 1. Connect to production DB
supabase db remote login

# 2. Run rollback SQL from migration file comment
psql $DATABASE_URL << 'EOF'
-- From 007_wajar_tanah_tables.sql rollback section:
DROP TABLE IF EXISTS property_submissions CASCADE;
DROP TABLE IF EXISTS property_benchmarks CASCADE;
EOF

# 3. Verify tables gone
psql $DATABASE_URL -c "\dt property*"

# 4. Update migration tracking (delete from supabase_migrations if needed)
```

---

### Environment Variables Management

**Production env vars live in Vercel Dashboard → Project Settings → Environment Variables.**

```bash
# Add/update via CLI (preferred — version controllable)
vercel env add MIDTRANS_SERVER_KEY production
vercel env add GOOGLE_VISION_API_KEY production

# List current (values hidden)
vercel env ls

# Pull to local (creates .env.local — in .gitignore)
vercel env pull .env.local
```

**Rotation checklist (when rotating any key):**
1. Generate new key from provider dashboard
2. Add new key to Vercel with `vercel env add`
3. Remove old key from Vercel
4. Redeploy: `vercel --prod`
5. Test that new key works (make one API call in production)
6. Update Python agents with new key if applicable
7. Document rotation in internal changelog

---

### Release Checklist (Before Every Production Deploy)

- [ ] All integration tests passing locally
- [ ] Vercel preview URL tested manually for affected flows
- [ ] No `console.log` with sensitive data in diff
- [ ] No hardcoded secrets in diff (run `detect-secrets scan`)
- [ ] Database migration tested on staging branch first
- [ ] Midtrans webhook URL still pointing to correct endpoint
- [ ] If adding new env var: added to Vercel production before deploying
- [ ] Sentry source maps uploaded (or Vercel does this automatically)

---

## 9.2 Monitoring & Alerting Spec

### Monitoring Stack (Free Tier First)

| Tool | Purpose | Free Limit | Alert Method |
|------|---------|-----------|-------------|
| Vercel Analytics | Traffic, Core Web Vitals | Unlimited (basic) | Dashboard only |
| Sentry | Error tracking | 5K errors/month | Email + (optional) Telegram |
| Supabase Dashboard | DB performance, connections | Included | Email on plan limits |
| Uptime Robot | Public uptime monitoring | 50 monitors free | Email + Telegram |
| pg_cron job results | Cron job health | DB query | Daily smoke test |

---

### Alert Triggers

| Alert | Trigger | Severity | Channel | Response Time |
|-------|---------|----------|---------|--------------|
| Site down | `cekwajar.id` HTTP != 200 | P1 | Telegram + Email | < 15 minutes |
| Wajar Slip API error rate > 5% | Sentry error rate spike | P1 | Telegram + Email | < 30 minutes |
| Midtrans webhook failing | Webhook 4xx/5xx responses | P1 | Email | < 1 hour |
| Google Vision quota > 900/month | OCR counter in DB | P2 | Email | < 1 day |
| pg_cron job failed | `cron.job_run_details.status = 'failed'` | P2 | Email | < 4 hours |
| Payslip file not deleted (30+ days) | Files in Storage older than 31 days | P2 | Email | < 24 hours |
| Supabase DB connections > 80% | Supabase dashboard | P2 | Email | < 4 hours |
| Payment conversion < 1% week over week | Midtrans analytics | P3 | Telegram | < 1 week |
| New Sentry error (first occurrence) | Sentry issue created | P3 | Email | < 1 day |

---

### Telegram Alert Bot Setup

```python
# For critical alerts (Telegram bot — free)
import httpx

TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

async def send_telegram_alert(message: str, severity: str = 'WARNING') -> None:
    emoji = '🔴' if severity == 'CRITICAL' else '🟡' if severity == 'WARNING' else 'ℹ️'
    
    await httpx.AsyncClient().post(
        f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
        json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': f'{emoji} *cekwajar.id Alert*\n\n{message}',
            'parse_mode': 'Markdown'
        }
    )
```

---

### Daily Smoke Test (pg_cron)

Runs every day at 16:00 UTC (23:00 WIB). Sends alert if any check fails.

```sql
CREATE OR REPLACE FUNCTION daily_smoke_test()
RETURNS JSONB AS $$
DECLARE
  results JSONB := '{}';
  count_result INTEGER;
BEGIN
  -- Check 1: user_profiles table accessible
  SELECT COUNT(*) INTO count_result FROM user_profiles LIMIT 1;
  results := results || '{"user_profiles": "ok"}';
  
  -- Check 2: Reference data loaded
  SELECT COUNT(*) INTO count_result FROM pph21_ter_rates;
  IF count_result < 30 THEN
    results := results || '{"ter_rates": "MISSING_DATA"}';
  ELSE
    results := results || '{"ter_rates": "ok"}';
  END IF;
  
  -- Check 3: UMK data loaded
  SELECT COUNT(*) INTO count_result FROM umk_2026;
  IF count_result < 100 THEN
    results := results || '{"umk_2026": "MISSING_DATA"}';
  ELSE
    results := results || '{"umk_2026": "ok"}';
  END IF;
  
  -- Check 4: No cron failures in last 24h
  SELECT COUNT(*) INTO count_result 
  FROM cron.job_run_details 
  WHERE status = 'failed' AND start_time > now() - INTERVAL '24 hours';
  
  IF count_result > 0 THEN
    results := results || jsonb_build_object('cron_failures', count_result);
  ELSE
    results := results || '{"cron_jobs": "ok"}';
  END IF;
  
  -- Check 5: Payslip purge working (no files older than 32 days)
  SELECT COUNT(*) INTO count_result
  FROM payslip_audits
  WHERE delete_at < now() - INTERVAL '32 days'
  AND payslip_file_path IS NOT NULL;
  
  IF count_result > 0 THEN
    results := results || jsonb_build_object('stale_files', count_result);
    -- This is a UU PDP violation risk — alert immediately
    PERFORM net.http_post(
      url := 'https://cekwajar.id/api/internal/alert',
      body := jsonb_build_object('alert', 'STALE_PAYSLIP_FILES', 'count', count_result)
    );
  ELSE
    results := results || '{"payslip_purge": "ok"}';
  END IF;
  
  RETURN results;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

SELECT cron.schedule(
  'daily-smoke-test',
  '0 16 * * *',
  'SELECT daily_smoke_test();'
);
```

---

### Key Metrics Dashboard (What to Watch Weekly)

| Metric | Source | Target (Month 1) | Target (Month 3) |
|--------|--------|-----------------|-----------------|
| Wajar Slip audits/week | `payslip_audits` table | > 100 | > 1,000 |
| New user signups/week | Supabase Auth | > 50 | > 500 |
| Free → Basic conversion rate | `transactions` / `user_profiles` | > 5% | > 8% |
| Basic → Pro upgrade rate | `transactions` | > 10% | > 15% |
| Revenue/week (IDR) | `transactions` aggregate | IDR 200K | IDR 5M |
| OCR success rate | `payslip_audits.ocr_source` + confirm rate | > 70% auto | > 75% auto |
| NPS (from in-app survey) | In-app form → Supabase | > 30 | > 50 |
| p99 API latency | Vercel Analytics | < 3s | < 2s |
| Error rate | Sentry | < 1% | < 0.5% |

---

## 9.3 Incident Response Playbook

### Tier Classification

| Tier | Definition | Example | SLA |
|------|-----------|---------|-----|
| Tier 1 (Critical) | Complete outage or data loss | Site down, DB unreachable, all payments failing | Respond in 15 min, resolve in 2 hours |
| Tier 2 (High) | Major feature broken | Wajar Slip returns wrong verdicts, OCR always fails | Respond in 1 hour, resolve in 8 hours |
| Tier 3 (Medium) | Minor feature broken, workaround exists | OCR fails but manual works, rate limiting too aggressive | Respond in 4 hours, resolve in 48 hours |

---

### Tier 1 Playbook: Complete Site Outage

**Detection:** Uptime Robot alert OR user reports OR Telegram alert

```
T+0:    Alert received
T+5:    Open cekwajar.id — confirm outage
T+5:    Check Vercel Status: vercel-status.com
T+10:   Check Supabase Status: status.supabase.com
T+10:   Check last deployment — did recent deploy break it?
T+15:   If recent deploy: vercel rollback --prod [previous-deployment-url]
T+15:   If Vercel outage: post on Twitter "Kami sedang mengalami gangguan teknis. Segera diperbaiki."
T+30:   Root cause identified
T+60:   Fix deployed or rollback complete
T+120:  Full service restored
T+180:  Incident post-mortem drafted
```

**Post-incident:** Update status on Twitter + r/finansialku if outage > 2 hours.

---

### Tier 2 Playbook: Wrong Calculation Results

**This is the highest-impact silent failure.** Users trust the tool to detect payslip errors — if the tool itself is wrong, it causes direct financial harm to users.

```
T+0:    User reports wrong result (bug report or WhatsApp/email)
T+15:   Reproduce issue with the exact input
T+30:   Identify if it's a code bug or data bug (TER rate table wrong?)
T+30:   If data bug: fix seed data + run migration
T+30:   If code bug: fix + write test for the case
T+60:   Deploy fix to preview, test
T+90:   Deploy to production
T+120:  Notify affected user(s) directly with corrected result
T+24h:  Post errata on site: "We fixed a calculation error in [scenario]. Check your audit."
```

**Affected user notification template (Bahasa Indonesia):**
```
Halo [nama],

Kami menemukan bug pada kalkulasi [PPh21/BPJS] yang mempengaruhi 
slip gaji kamu yang dicek pada [tanggal].

Hasil yang salah: [deskripsi kesalahan]
Hasil yang benar: [deskripsi koreksi]

Kami sudah memperbaiki bug ini dan mengupdate hasilmu secara otomatis.
Cek kembali di: cekwajar.id/dashboard

Mohon maaf atas ketidaknyamanan ini.

Tim cekwajar.id
```

---

### Tier 2 Playbook: Payment System Failure

**Midtrans Snap not loading / webhooks not firing:**

```
T+0:    Alert: Upgrade attempts failing (from Sentry or user report)
T+15:   Check Midtrans Status: status.midtrans.com
T+15:   Check Vercel logs for webhook endpoint errors
T+15:   Test webhook manually: send test payload with Midtrans dashboard
T+30:   If Midtrans outage: post notice, pause payment promotions
T+30:   If webhook URL wrong: update in Midtrans dashboard (Settings → Configuration → Payment Notification)
T+60:   If webhook missed payments: manually process via Midtrans transaction history
T+120:  All pending payments processed manually if needed
```

**Manual subscription activation (emergency):**
```sql
-- Use only if webhook confirmed payment but didn't activate
UPDATE user_profiles 
SET subscription_tier = 'basic' 
WHERE id = '[user_id]';

INSERT INTO subscriptions (user_id, plan_type, status, starts_at, ends_at)
VALUES ('[user_id]', 'basic', 'active', now(), now() + INTERVAL '32 days');
```

---

### Tier 3 Playbook: OCR Accuracy Degradation

**Detection:** OCR correction rate > 20% in `ocr_field_corrections`

```
T+0:    Weekly metrics review shows high correction rate
T+4h:   Pull sample of recent bad OCR cases from DB
T+8h:   Identify pattern (specific payslip format? time of day?)
T+24h:  If Google Vision API changed behavior: update field extraction regex
T+24h:  If specific format failing: add to test corpus, improve parser
T+48h:  Deploy fix
T+72h:  Monitor correction rate drops below 10%
```

---

## 9.4 Content + GTM Calendar (13-Week Plan)

### TikTok Content Strategy

**Posting frequency:** 3–4 videos/week  
**Format:** Educational + tool demo (max 60 seconds)  
**Target accounts to study:** @cermati_com, @lifepal_id, @bibit_id for tone reference

**3 Content Archetypes:**

1. **"Fakta mengejutkan"** (surprising fact) — hooks with shocking statistic, leads to tool
2. **"Tutorial singkat"** (quick tutorial) — screen recording of tool + voiceover
3. **"Testimoni / user journey"** (case study) — user story + outcome

---

### 13-Week GTM Calendar

| Week | Milestone | TikTok Content | Community | SEO/Blog |
|------|-----------|---------------|-----------|---------|
| 1 | Wajar Slip beta invite | Video 1: "Kamu tau ngga berapa PPh21 yang bener buat gajimu?" | Share beta link r/finansialku | — |
| 1 | | Video 2: Tutorial upload slip gaji | Post in WhatsApp HRD group | — |
| 2 | Beta testing | Video 3: "3 pelanggaran paling sering di slip gaji Indonesia" | Respond to all comments | — |
| 2 | | Video 4: Case study — Rina's journey | | — |
| 3 | Public launch Wajar Slip | Video 5: "Kita launch!" announcement | r/finansialku launch post | Blog: "Cara hitung PPh21 TER 2024" |
| 3 | | Video 6: Tutorial lengkap Wajar Slip | | |
| 4 | Wajar Gaji beta | Video 7: "Gajimu wajar atau ngga?" | LinkedIn post | Blog: "UMK 2026 seluruh Indonesia" |
| 4 | | Video 8: "Benchmark gaji Backend Dev di Surabaya" | | |
| 5 | Public launch Wajar Gaji | Video 9: Wajar Gaji demo | Twitter/X tech community | — |
| 5 | | Video 10: "Submit gaji anonim kamu" | | |
| 6 | Growth + UGC | Video 11: Repost user testimonials | | — |
| 6 | | Video 12: "5 pekerjaan paling underpaid di Jakarta" | | Blog: "Benchmark gaji IT 2026" |
| 7 | Wajar Tanah launch | Video 13: "Rumah IDR 1M/m² di Bekasi — MURAH atau MAHAL?" | Facebook KPR groups | Blog: "NJOP vs harga pasar" |
| 7 | | Video 14: Tutorial Wajar Tanah | | |
| 8 | Wajar Kabur launch | Video 15: "Kerja di Singapura — beneran lebih besar?" | Twitter/X tech | Blog: "PPP salary comparison" |
| 8 | | Video 16: "SGD 4500 vs IDR 8.5M — yang mana lebih besar?" | | |
| 9 | Wajar Hidup launch | Video 17: "Pindah ke Surabaya — gaji harus naik berapa?" | | Blog: "Cost of living Jakarta vs Surabaya" |
| 9 | | Video 18: Tutorial Wajar Hidup | | |
| 10 | All tools live | Video 19: "5 tools gratis buat karir & keuanganmu" | | Blog: roundup post |
| 10 | | Video 20: User story compilation | | |
| 11 | Monetization push | Video 21: "Bedanya Basic vs Gratis" | | — |
| 11 | | Video 22: Feature unlock demo | | |
| 12 | Midtrans go live | Video 23: "Sekarang bisa upgrade!" | | — |
| 12 | | Video 24: Early bird pricing promo | | |
| 13 | GTM wrap-up | Video 25: Data & insights compilation | | — |
| 13 | | Video 26: "Thank you 10K users" (if milestone hit) | | |

---

### Sample TikTok Script: Week 1, Video 1

```
[Hook — 0-3s]
"Apakah kamu tau berapa PPh21 yang bener buat gaji kamu bulan ini?"

[Problem — 3-10s]
"Di Indonesia, ada aturan baru namanya TER — Tarif Efektif Rata-Rata.
Mulai 2024, cara hitung PPh21 berubah total. Tapi banyak perusahaan
masih pakai cara lama, atau salah menghitung."

[Solution — 10-30s]
[Screen recording: upload slip gaji → hasil audit]
"Dengan cekwajar.id, kamu bisa upload foto slip gaji kamu
dan langsung tahu apakah potongan kamu udah bener."

[CTA — 30-45s]
"Coba gratis sekarang di cekwajar.id/wajar-slip.
Kalau ada pelanggaran, kamu tau hak kamu.
Tujukan ke HRD, minta perbaikan."

[Social proof — 45-60s]
"Sudah X pengguna cek slip gaji mereka minggu ini."

Hashtag: #pph21 #slipgaji #hakkaryawan #cekwajar #finansial
```

---

### Community Engagement Plan

| Platform | Strategy | Frequency |
|----------|---------|-----------|
| r/finansialku (Reddit) | Post launch, answer payroll questions, never spam | 2x/month |
| WhatsApp HRD Groups | Share tool, collect feedback, genuinely helpful | 1x/week |
| Facebook "KPR & Properti Indonesia" | Share Wajar Tanah, answer price questions | 2x/week after Tanah launch |
| Twitter/X Indonesian Tech Twitter | Engage on salary threads, share Wajar Kabur | Daily when relevant |
| LinkedIn | Share case studies, target HR managers and finance staff | 2x/week |

**Golden rule:** Never post as a pure promotion. Always lead with value (answer a question, share data). Tool mention comes second.

---

## 9.5 Week-by-Week Sprint Tracker

### Format

Each week:
- **Goal:** What single thing moves the needle most?
- **Done:** Completed items
- **In Progress:** Active work
- **Blocked:** What's stopping something

---

### Week 1–2: Foundation

**Goal:** Supabase + Next.js scaffold live on Vercel. Auth working. Navigation between 5 tool stubs.

**Done:**
- [ ] Supabase project created (ap-southeast-1)
- [ ] Next.js 15 App Router initialized
- [ ] Tailwind + shadcn/ui configured
- [ ] Supabase Auth (Email + Google OAuth) working
- [ ] 5 tool pages created as empty stubs
- [ ] Global nav bar with 5 links
- [ ] Vercel project connected, auto-deploy from main

**In Progress:**
- Migrations 001–004 (extensions, user tables, subscriptions, base RLS)

**Blocked:**
- PSE Kominfo registration (need to complete manually)

---

### Week 3–4: Wajar Slip Core

**Goal:** Manual form → PPh21 + BPJS calculation → verdict display working end-to-end.

**Done:**
- [ ] `payslip_audits` table + RLS
- [ ] PPh21 TER engine implemented + tested
- [ ] BPJS calculation engine implemented + tested
- [ ] All 7 violation detectors implemented
- [ ] UMK lookup (top 20 cities hardcoded)
- [ ] Manual input form with all fields
- [ ] Verdict display (free tier: codes only)
- [ ] Freemium gate modal component

**In Progress:**
- City dropdown (all 514 cities from umk_2026)

**Blocked:**
- Nothing

---

### Week 5–6: Wajar Slip OCR + Wajar Gaji P0

**Goal:** OCR upload flow working. Wajar Gaji benchmark (BPS prior + crowdsource) displaying.

**Done:**
- [ ] Google Vision integration + Indonesian field parser
- [ ] OCR confidence routing (AUTO_ACCEPT / SOFT_CHECK / MANUAL_REQUIRED)
- [ ] Tesseract.js fallback (client-side)
- [ ] `payslips` Storage bucket + policies
- [ ] OCR quota counter in Supabase
- [ ] BPS Sakernas Python loader (province P50 data)
- [ ] UMK Python loader (514 cities)
- [ ] `salary_benchmarks`, `salary_submissions` tables
- [ ] Wajar Gaji form (job title autocomplete + city + experience)
- [ ] Crowdsource submission form

**In Progress:**
- JobStreet Playwright scraper (P1 feature, can skip for now)

---

### Week 7–8: Wajar Tanah P0

**Goal:** Property verdict showing for major Indonesian cities.

**Done:**
- [ ] `property_benchmarks` table + RLS
- [ ] 99.co Playwright scraper (Python Swarms agent)
- [ ] Rumah123 Playwright scraper
- [ ] `PropertyScraper` Swarms orchestrator
- [ ] First scrape run (seed property data)
- [ ] Location drill-down UI (Province → City → District)
- [ ] Property type + area input form
- [ ] `calculatePropertyVerdict()` TypeScript function
- [ ] MURAH/WAJAR/MAHAL/SANGAT_MAHAL verdict card
- [ ] NJOP reference display
- [ ] KJPP disclaimer

---

### Week 9–10: Wajar Kabur + Wajar Hidup P0

**Goal:** All 5 tools have working P0 features.

**Done:**
- [ ] World Bank PPP API integration + caching
- [ ] Frankfurter.app exchange rate integration
- [ ] PPP result display (top 5 countries free)
- [ ] Country selector (15 countries, 5 free + 10 locked)
- [ ] BPS CPI loader (Python agent)
- [ ] 20-city COL index seed data
- [ ] COL adjustment calculation
- [ ] HEMAT/STANDAR/NYAMAN lifestyle selector
- [ ] Verdict badge (LEBIH_MURAH / SAMA / LEBIH_MAHAL)

---

### Week 11–12: Monetization + Legal + Hardening

**Goal:** Midtrans live. Freemium gates active. Legal pages published. Security checklist complete.

**Done:**
- [ ] Midtrans Snap integration + sandbox testing
- [ ] Webhook handler + signature verification + idempotency
- [ ] `transactions`, `subscriptions` tables + RLS
- [ ] Subscription gate enforcement (all 5 tools)
- [ ] Privacy Policy page (Bahasa Indonesia)
- [ ] Terms of Service page
- [ ] Cookie consent banner + `user_consents` table
- [ ] Disclaimer banners (PPh21, KJPP, PPP)
- [ ] Pre-launch security checklist completed
- [ ] pg_cron jobs registered (purge, expiry check, dunning)
- [ ] Sentry error monitoring configured
- [ ] Vercel Analytics configured
- [ ] Uptime Robot configured

**Switch Midtrans to production:**
```bash
# In Vercel Dashboard:
MIDTRANS_SERVER_KEY=Mid-server-...  # production key (not SB-)
MIDTRANS_IS_PRODUCTION=true
# Redeploy
```

---

### Month 2: P1 Features

**Goal:** OCR accuracy improvements, audit history dashboard, JobStreet data, property P25/P75, Numbeo CoL.

**Priority order:**
1. Google Vision OCR accuracy improvements based on beta feedback
2. User dashboard with audit history
3. PDF export for Wajar Slip (Pro feature — high WTP)
4. City-level P25/P75 for Wajar Gaji (Basic gate)
5. P25/P75 property range (Basic gate)
6. Numbeo CoL integration for Wajar Kabur
7. Subscription expiry email notification
8. Resend transactional email (welcome + confirmation)

---

### Month 3+: Revenue-Funded P2 Features

**Only proceed if:** Monthly revenue > IDR 5M AND MAU > 2,000

**P2 queue (in priority order):**
1. PDF "mini valuation" report for Wajar Tanah (Sari persona — high WTP)
2. December true-up simulation for Wajar Slip (Pro)
3. YoY salary trend for Wajar Gaji (Pro)
4. After-tax net salary for Wajar Kabur (Pro)
5. Multi-city comparison for Wajar Hidup (Pro)
6. Employer contribution breakdown for Wajar Slip (HRD use case)
7. pgvector semantic job title matching for Wajar Gaji
8. Property price trend (3-month) for Wajar Tanah
9. Share card (OG image) for viral loops
10. BPS CPI trend overlay for Wajar Hidup

---

### Kill Conditions (When to Stop)

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Zero paid subscribers after Month 2 | 0 | Pivot to B2B API or shut down |
| Monthly revenue < costs at Month 4 | Costs > IDR 500K/month | Evaluate subscription pricing |
| OCR error rate > 25% sustained | > 25% user reports | Disable OCR, ship manual-only |
| Legal action from scraped sites | Cease and desist received | Comply, switch to crowdsource-only |
| Critical calculation error found post-launch | Any confirmed wrong verdict | Pull Wajar Slip, fix, re-launch |
| MAU declining 3 months straight | Trend down 3 months | Content strategy overhaul |
