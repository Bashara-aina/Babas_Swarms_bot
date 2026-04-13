# req_10 — Security Spec: cekwajar.id
**Document Type:** Security Specification  
**Version:** 1.0  
**Framework:** STRIDE threat model, UU PDP No.27/2022, OWASP Top 10

---

## 7.1 Data Classification Table

Every data element processed by cekwajar.id is classified here. Classification drives consent requirements, storage decisions, and retention policy.

| Data Element | Classification | Consent Required | Retention | Anonymization | UU PDP Reference |
|-------------|---------------|-----------------|-----------|--------------|-----------------|
| Email address | Sensitif (PII) | Implicit (auth) | Until deletion | N/A | Pasal 4(b) |
| Full name | Sensitif (PII) | Implicit (auth) | Until deletion | N/A | Pasal 4(a) |
| IP address | Sensitif | No (never stored) | Never | Not stored | Pasal 4(i) |
| Gross salary | Sensitif (financial) | Explicit (form submit) | 12 months | Used in aggregate only | Pasal 4(e) |
| PTKP status | Sensitif (financial) | Explicit | 12 months | Not shown individually | Pasal 4(e) |
| NPWP status | Sensitif (tax ID reference) | Explicit | 12 months | Not stored as ID number | Pasal 4(f) |
| Payslip image | Sensitif Khusus (financial doc) | Explicit + separate | 30 days | Auto-deleted | Pasal 4(e) |
| Violation findings | Sensitif (financial) | Implicit (result) | 12 months | Linked to user only | Pasal 4(e) |
| City/location | Umum | Implicit | 12 months | City level, not address | — |
| Job title | Umum | Implicit | Until deletion of account | — | — |
| Property asking price | Sensitif | Explicit | 30 days (submission) | Only in aggregate | Pasal 4(e) |
| Subscription plan | Sensitif (financial) | Implicit (purchase) | 3 years | N/A | — |
| Payment transaction | Sensitif (financial) | Implicit (purchase) | 3 years | Handled by Midtrans | — |
| OCR confidence score | Internal | No | 30 days | Not user-facing | — |
| Session ID (anon) | Pseudonymous | Cookie consent | 7 days | Not linkable to PII | Pasal 4 |
| Salary submission | Pseudonymous (hashed) | Implicit + notice | 24 months | IP hash, no PII | Pasal 4 |
| Consent record | Sensitif | N/A | 5 years | N/A | Pasal 26(1) |

**Classification definitions:**
- **Sensitif Khusus:** Data that if exposed could cause significant harm (health data, financial documents, biometrics, sexual orientation)
- **Sensitif (PII):** Can identify an individual
- **Sensitif (financial):** Salary, tax, property transaction data
- **Umum:** Not directly identifying, but still handled with care
- **Pseudonymous:** Derived/hashed — not directly PII but traceable under some conditions

---

## 7.2 Threat Model (STRIDE)

### System Under Analysis: Payslip Upload + OCR Flow

This is the highest-risk flow because it handles:
- File upload (malware vector)
- Financial document content (sensitive data)
- Storage in Supabase bucket (access control critical)
- OCR extraction (accuracy attacks)

---

#### S — Spoofing

| Threat | Actor | Impact | Likelihood | Controls |
|--------|-------|--------|-----------|---------|
| User claims to be another user in API request | Authenticated user | Access other user's audits | LOW | Supabase JWT + RLS: `user_id = auth.uid()` |
| Attacker forges session cookie | External | Anonymous audit access | LOW | httpOnly + Secure cookie, no sensitive data in anon sessions |
| Webhook spoofing (fake Midtrans notification) | External | Free subscription activation | MEDIUM | SHA512 signature verification + timing-safe compare |
| Anonymous user reuses expired session | User | Access old audits | LOW | 2-hour window on anon SELECT policy |
| Google OAuth token replay | External | Account takeover | LOW | Supabase handles OAuth token validation |

**Control validation:** All API routes verify JWT via `createServerClient(cookies())`. Never trust client-passed `user_id`.

---

#### T — Tampering

| Threat | Actor | Impact | Likelihood | Controls |
|--------|-------|--------|-----------|---------|
| User modifies payslip file path to access other files | Authenticated user | Read other user's payslips | LOW | Storage RLS: path must start with `{auth.uid()}/` |
| Inject malicious SQL via job title input | External | DB corruption | LOW | Supabase parameterized queries; TypeScript ORM |
| Tamper audit record in transit | MITM | Wrong results shown | LOW | HTTPS enforced by Vercel |
| Modify Midtrans gross_amount in webhook | External | Free subscription | LOW | gross_amount verified against DB stored value |
| Tamper OCR result before calculation | User (frontend) | Bypass calculation | LOW | Server-side calculation only; client sends raw deductions |

**Critical:** Calculation ALWAYS happens server-side. Never trust client-calculated results.

---

#### R — Repudiation

| Threat | Actor | Impact | Likelihood | Controls |
|--------|-------|--------|-----------|---------|
| User denies payslip upload consent | User | Legal/regulatory dispute | MEDIUM | `user_consents` table records explicit consent with timestamp + policy version |
| User denies salary submission | User | Data quality dispute | LOW | Submission fingerprint + timestamp stored (no PII, but timestamped) |
| User denies payment | User | Chargeback | LOW | Midtrans transaction ID stored; webhook payload stored in DB |

**Audit log:** All payments, consent events, and subscription changes are immutable records.

---

#### I — Information Disclosure

| Threat | Actor | Impact | Likelihood | Controls |
|--------|-------|--------|-----------|---------|
| Salary benchmark shows individual salary | Any | Re-identification, privacy violation | MEDIUM | k-anonymity gate (n≥10); only aggregated views exposed |
| Payslip file accessible after 30 days | External | Stale sensitive data | LOW | pg_cron daily delete + Storage RLS (no public URL) |
| Error messages reveal database structure | External | Facilitate attack | MEDIUM | Generic error messages to client; full errors logged to Sentry only |
| Stack traces in API responses | Any | Facilitate attack | LOW | Production: `NODE_ENV=production`, Next.js hides traces |
| Service role key exposed | Developer | Full DB access | CRITICAL | Vercel env vars only; never in client bundle; `.gitignore` for .env |
| User A reads User B's audits | Authenticated | Privacy violation | LOW | RLS: `user_id = auth.uid()` enforced at DB level |
| anon_audit SELECT window too wide | Anon user | Access shared device session | LOW | 2-hour window only |

**Storage security:** All payslip files in `payslips` bucket are private. Accessed via signed URLs with 1-hour expiry:
```typescript
const { data: signedUrl } = await supabase.storage
  .from('payslips')
  .createSignedUrl(filePath, 3600);  // 1 hour
```

---

#### D — Denial of Service

| Threat | Actor | Impact | Likelihood | Controls |
|--------|-------|--------|-----------|---------|
| Flood `/api/audit-payslip` with requests | Attacker | API rate limit hit, Vision quota exhausted | MEDIUM | Vercel Edge rate limiting (IP-based); OCR quota counter |
| Upload large files repeatedly | Attacker | Storage cost spike | LOW | 5MB file size limit enforced at Edge |
| Flood crowdsource endpoint | Attacker | DB write spike | LOW | 2/IP/24h rate limit + dedup fingerprint |
| Property scraper overtaxes Supabase | Internal | High read cost | LOW | Scrapers run monthly, results cached in DB |
| Expensive SQL query in benchmark | Internal | Slow response | MEDIUM | Pre-aggregated views; no real-time aggregation on request |

**Vision quota defense:** Once monthly counter hits 950, route ALL new OCR to Tesseract.js. Never exceed 1,000 Vision calls.

---

#### E — Elevation of Privilege

| Threat | Actor | Impact | Likelihood | Controls |
|--------|-------|--------|-----------|---------|
| Free user accesses paid API routes | Authenticated free user | Free premium access | MEDIUM | Tier check in every gated API response; also enforced in DB view |
| User manipulates `subscription_tier` in JWT claim | Authenticated user | Free premium access | LOW | `subscription_tier` read from `user_profiles` table (DB), not from JWT |
| Webhook activates subscription without payment | External | Free subscription | LOW | Signature verification + DB amount verification |
| Python agent key used from frontend | Developer mistake | Unlimited DB access | MEDIUM | Service role key never in frontend code; CSP headers block exfil |

**Tier enforcement:** Subscription tier is NEVER read from client-provided data. It's always fetched from `user_profiles` table using `auth.uid()` at request time.

```typescript
// CORRECT — always do this
const { data: profile } = await supabase
  .from('user_profiles')
  .select('subscription_tier')
  .eq('id', auth.uid())
  .single();

const tier = profile?.subscription_tier ?? 'free';

// WRONG — never trust this
const tier = request.headers.get('X-User-Tier');  // NEVER
```

---

## 7.3 Rate Limiting Policy

### Layer 1: Vercel Edge (IP-based)

Applied globally before request reaches Next.js app. Uses Vercel KV for counters.

```typescript
const RATE_LIMIT_CONFIG = {
  '/api/audit-payslip':    { windowSeconds: 3600, maxRequests: 5 },    // 5/IP/hour anonymous
  '/api/ocr/upload':       { windowSeconds: 3600, maxRequests: 3 },    // 3/IP/hour anonymous
  '/api/salary/benchmark': { windowSeconds: 3600, maxRequests: 30 },   // 30/IP/hour
  '/api/property/benchmark': { windowSeconds: 3600, maxRequests: 30 },
  '/api/abroad/compare':   { windowSeconds: 3600, maxRequests: 20 },
  '/api/col/compare':      { windowSeconds: 3600, maxRequests: 30 },
  '/api/salary/submit':    { windowSeconds: 86400, maxRequests: 2 },   // 2/IP/day
  '/api/payment/create-transaction': { windowSeconds: 3600, maxRequests: 10 },
};
```

**Response on limit breach:**
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Terlalu banyak permintaan. Coba lagi dalam 1 jam.",
    "retryAfterSeconds": 3600
  }
}
```

---

### Layer 2: Supabase RLS (User-based)

After authentication, additional limits enforced via database:

```sql
-- Prevent more than 20 audits per user per day (free tier)
CREATE OR REPLACE FUNCTION check_daily_audit_limit(user_uuid UUID)
RETURNS BOOLEAN AS $$
DECLARE
  today_count INTEGER;
  user_tier TEXT;
BEGIN
  SELECT subscription_tier INTO user_tier 
  FROM user_profiles WHERE id = user_uuid;
  
  -- Paid users: no daily limit
  IF user_tier IN ('basic', 'pro') THEN
    RETURN TRUE;
  END IF;
  
  -- Free users: max 20/day
  SELECT COUNT(*) INTO today_count
  FROM payslip_audits
  WHERE user_id = user_uuid
  AND created_at >= CURRENT_DATE;
  
  RETURN today_count < 20;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---

### Layer 3: OCR Quota Counter (Google Vision)

```sql
-- Called before each Vision API call
SELECT increment_ocr_counter() AS new_count;

-- In API route:
const count = await incrementOCRCounter();
if (count > 950) {
  return 'tesseract';  // fallback to free OCR
}
return 'google_vision';
```

**Counter table:**
```sql
CREATE TABLE ocr_quota_counter (
  month_key TEXT PRIMARY KEY,  -- 'YYYY-MM'
  count INTEGER DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 7.4 Secret Management Policy

### Secret Categories

| Secret | Type | Where Stored | Rotation Frequency |
|--------|------|-------------|-------------------|
| `SUPABASE_SERVICE_ROLE_KEY` | Database master key | Vercel Env (encrypted) | On breach only |
| `SUPABASE_ANON_KEY` | Public key | Vercel Env + client bundle | Never (public by design) |
| `MIDTRANS_SERVER_KEY` | Payment gateway | Vercel Env | Annual |
| `MIDTRANS_CLIENT_KEY` | Payment gateway | Vercel Env + client bundle | Annual |
| `GOOGLE_VISION_API_KEY` | AI API | Vercel Env | Quarterly |
| `RESEND_API_KEY` | Email service | Vercel Env | Quarterly |
| `SENTRY_DSN` | Monitoring (non-secret) | Vercel Env | Never |
| `SUPABASE_JWT_SECRET` | Auth token signing | Supabase internal | Never (Supabase manages) |
| Fly.io API token | Deploy | GitHub Actions Secret | Annual |

---

### Service Role Key Rules

The `SUPABASE_SERVICE_ROLE_KEY` bypasses ALL RLS. It must NEVER be:
1. In client-side JavaScript bundle
2. In git repository (even `.env.local`)
3. Logged to any system (Sentry, console, monitoring)
4. Passed as URL parameter
5. Included in error messages

**Allowed uses of service_role:**
- Edge Functions (server-side Deno)
- Python Swarms agents (server-side)
- pg_cron functions (within database)
- Admin scripts run locally by founder

**Detection:** Run `grep -r "service_role" src/` before every deployment. Should return zero results.

---

### `.gitignore` Requirements

```gitignore
# Environment variables — CRITICAL
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Python agent secrets
agents/.env
agents/service_account.json

# Supabase local
supabase/.branches
supabase/.temp

# Never commit these
*.pem
*.key
service_account*.json
```

**Pre-commit hook (required):**
```bash
# Install: pip install detect-secrets
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

---

### Rotation Schedule

| Secret | When to Rotate | How to Rotate |
|--------|---------------|---------------|
| Google Vision API Key | Quarterly or on team change | GCP Console → Credentials → Regenerate; update Vercel |
| Midtrans Keys | Annual or on breach | Midtrans Dashboard → Production → API Keys; update Vercel + test webhook |
| Resend API Key | Quarterly | Resend Dashboard → API Keys; update Vercel |
| Service Role Key | On breach only | Supabase → Settings → API → Regenerate; update Vercel + all agents immediately |

---

## 7.5 Pre-Launch Security Checklist

Checklist must be completed before switching Midtrans to production mode and enabling real payments.

### Database Security

- [ ] RLS enabled on ALL 19 tables — verify with: `SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';` — every row must show `t`
- [ ] No table without any RLS policy — verify: `SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename NOT IN (SELECT tablename FROM pg_policies WHERE schemaname='public');` — should be empty
- [ ] `user_profiles.subscription_tier` cannot be updated by users directly — test with Supabase client using anon key
- [ ] Storage bucket `payslips` is private (not public) — check in Supabase Storage dashboard
- [ ] Storage policies correctly limit user to own folder — test with two different user accounts

### Application Security

- [ ] `git-secrets scan` passes with zero findings in repository
- [ ] `detect-secrets scan --baseline .secrets.baseline` passes
- [ ] No `console.log` statements with user data in production code
- [ ] `SUPABASE_SERVICE_ROLE_KEY` not in client bundle — run `grep -r "service_role" .next/` after build
- [ ] All API routes validate input with zod schemas before processing
- [ ] SQL injection tested: Try `'; DROP TABLE payslip_audits; --` in city field — must return 400, not 500
- [ ] Midtrans signature verification tested in sandbox with wrong signature — must return 401
- [ ] Rate limiting tested — 6th request to `/api/audit-payslip` from same IP must return 429

### Transport Security

- [ ] HTTPS enforced — `curl -I http://cekwajar.id` must redirect to HTTPS
- [ ] HSTS header present: `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- [ ] CSP header configured in `next.config.js` (blocks inline scripts, limits fetch origins)
- [ ] CORS: API routes only accept requests from `cekwajar.id` and `localhost` in dev

### Data Protection

- [ ] 30-day payslip deletion tested in staging — upload file, wait for pg_cron to run, verify file gone
- [ ] Privacy Policy page published at `/privacy-policy`
- [ ] Terms of Service page published at `/terms`
- [ ] Cookie consent banner live and working (records consent in `user_consents`)
- [ ] PSE Kominfo registration completed (kominfo.go.id)

### Payment Security

- [ ] Midtrans webhook tested in sandbox with correct + incorrect signatures
- [ ] Idempotency tested — same webhook payload delivered twice = single activation
- [ ] `gross_amount` verified against DB on every webhook (not just signature)
- [ ] Fraud status `'deny'` results in no activation (tested)
- [ ] Test payment with GoPay sandbox completes full flow

---

## 7.6 Breach Response SOP

### Definition of Breach (UU PDP Pasal 46)

A "personal data breach" under UU PDP means any accidental or unlawful destruction, loss, alteration, unauthorized disclosure, or access to personal data.

**Examples that trigger this SOP:**
- Supabase `service_role` key exposed in GitHub
- RLS misconfiguration allowing cross-user data access
- Payslip files accessible without authentication
- Database dumped by SQL injection
- Midtrans keys exposed (financial impact)

**Examples that do NOT trigger (but still investigate):**
- Rate limit bypass (no data accessed)
- Automated scraping of public pages (our own data used against us)
- Single user's account compromised by their own password reuse

---

### 4-Step Response

#### Step 1: ISOLATE (0–2 hours)

| Action | Who | Tool |
|--------|-----|------|
| Identify affected system | Founder | Sentry + Supabase logs |
| Disable compromised credential | Founder | Supabase Dashboard / GCP Console |
| Enable Vercel "Maintenance Mode" if needed | Founder | Vercel Dashboard → Domains |
| Preserve logs before any cleanup | Founder | `supabase logs pull --project-ref ...` |
| Document: what is confirmed exposed, what is unknown | Founder | Private doc |

**If Supabase service_role key is compromised:**
1. Immediately: Supabase Dashboard → Settings → API → Regenerate service role key
2. Update Vercel env vars with new key
3. Redeploy: `vercel --prod`
4. Update Python agents
5. Check `cron.job_run_details` for any unauthorized execution in last 24h

---

#### Step 2: ASSESS (2–24 hours)

| Question | Source |
|----------|--------|
| What data was accessed? | Supabase audit logs (`auth.audit_log_entries`) |
| How many users affected? | Query `payslip_audits` by timeframe |
| Was financial data accessed? | Check `transactions`, `subscriptions` |
| Was payslip content accessed? | Check storage access logs |
| Is the breach ongoing? | Disable key, re-check logs |
| What was the attack vector? | Code review + Sentry error history |

**Scope classification:**

| Scope | Example | Response |
|-------|---------|---------|
| Narrow | 1 user's data | Private notification to that user |
| Medium | < 100 users, no financial data | In-app notification + email |
| Wide | > 100 users or any financial/payslip | Full UU PDP notification required |

---

#### Step 3: NOTIFY (24–72 hours)

**UU PDP Pasal 46(1):** Notification to affected users must be in Bahasa Indonesia, within reasonable time after discovery.

**UU PDP Pasal 46(2):** Notification to KOMINFO (via kominfo.go.id) within 14 calendar days of breach confirmation.

**User notification email template (Bahasa Indonesia):**
```
Kepada Pengguna cekwajar.id yang Terhormat,

Kami ingin menginformasikan bahwa pada [tanggal], kami mendeteksi 
insiden keamanan yang mungkin mempengaruhi akun Anda.

Data yang berpotensi terdampak: [daftar data spesifik]
Periode terjadinya insiden: [tanggal awal – tanggal akhir]

Langkah yang telah kami ambil:
1. Kami segera mengamankan sistem yang terdampak
2. Kami menyelidiki penyebab insiden
3. Kami telah melapor kepada Kominfo

Langkah yang kami rekomendasikan untuk Anda:
- Ganti password akun Anda segera
- Pantau rekening bank untuk aktivitas mencurigakan

Kami meminta maaf atas ketidaknyamanan ini. 
Hubungi kami di: security@cekwajar.id

Hormat kami,
Tim cekwajar.id
```

---

#### Step 4: REPORT (14 days)

**KOMINFO notification requirements (UU PDP Pasal 46):**
- Submit via: https://kominfo.go.id/layanan/pelaporanpdp (or designated portal)
- Required information: description of incident, categories of data, number of users affected, likely consequences, measures taken
- Timeline: Within 14 calendar days of confirmation

**Post-mortem document (internal):**
1. Timeline of events (detection, containment, resolution)
2. Root cause analysis
3. What worked in response
4. What didn't work
5. Preventive measures implemented
6. Changes to security procedures

---

### Breach Severity Matrix

| Severity | Criteria | Response Time | Who to Notify |
|----------|---------|--------------|--------------|
| P1 (Critical) | Payslip files accessed; financial data exposed; >100 users | 2 hours contain, 24h notify users | Users + KOMINFO |
| P2 (High) | <100 users' salary data accessed; service_role key exposed | 4 hours contain, 48h notify users | Users (if data accessed) + KOMINFO |
| P3 (Medium) | No user data accessed; logic error; potential future risk | 24 hours fix | No external notification unless required |
| P4 (Low) | Rate limit bypass; scraping of our own public data | 1 week fix | None |

---

### Security Contacts

| Role | Contact | When to Contact |
|------|---------|----------------|
| Founder / Solo developer | [yourname]@cekwajar.id | All incidents |
| Supabase Support | support@supabase.com | Database breaches, RLS failures |
| Vercel Support | vercel.com/support | Edge function / deployment issues |
| KOMINFO | pdp@kominfo.go.id | P1/P2 incidents within 14 days |
| Midtrans Security | security@midtrans.com | Payment-related incidents |

---

### UU PDP Timeline Reference

| Milestone | Deadline | Action |
|-----------|---------|--------|
| Detection → Initial containment | 2 hours (P1) | Step 1 complete |
| Containment → Scope assessment | 24 hours | Step 2 complete |
| Assessment → User notification | 24–72 hours | Step 3 user email sent |
| Confirmation → KOMINFO report | 14 calendar days | Step 4 submitted |
| KOMINFO report → Post-mortem | 30 days | Internal document complete |
