# req_08 — API Contracts: cekwajar.id
**Document Type:** API Contract Specification  
**Version:** 1.0  
**Base URL:** `https://cekwajar.id/api/`  
**Auth:** Supabase JWT in `Authorization: Bearer {token}` header, or anonymous with session cookie

---

## 5.1 Internal API Routes

### Auth Header Convention

```
Authorization: Bearer {supabase_access_token}    # authenticated
X-Session-ID: {uuid}                             # anonymous (payslip only)
Content-Type: application/json
```

All routes return:
```typescript
interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;       // machine-readable e.g. "RATE_LIMIT_EXCEEDED"
    message: string;    // Bahasa Indonesia for client display
    details?: any;
  };
}
```

---

### Route: `POST /api/audit-payslip`

**Purpose:** Main Wajar Slip endpoint. Accepts payslip data, runs all calculations, returns violation results.

**Auth:** Optional (anonymous allowed with session ID)

**Rate limit:** 5 requests/IP/hour (anonymous), 20/user/day (authenticated free), unlimited (paid)

**Request schema:**

```typescript
interface AuditPayslipRequest {
  // Salary info
  grossSalary: number;          // IDR, required
  ptkpStatus: PtkpStatus;       // 'TK/0' | 'TK/1' | ... | 'K/I/3'
  city: string;                 // exact match against umk_2026.city
  monthNumber: number;          // 1-12
  year?: number;                // default: current year
  hasNPWP: boolean;
  
  // Reported deductions from payslip
  reportedDeductions: {
    pph21: number;
    jhtEmployee: number;
    jpEmployee: number;
    jkkEmployee: number;
    jkmEmployee: number;
    kesehatanEmployee: number;
    takeHome: number;
  };
  
  // Optional: OCR source metadata
  ocrSource?: 'google_vision' | 'tesseract' | 'manual';
  ocrConfidence?: number;
  payslipFilePath?: string;     // set if file was uploaded, references storage
}
```

**Response schema:**

```typescript
interface AuditPayslipResponse {
  auditId: string;              // UUID — used to retrieve later
  
  // Free tier gets this
  verdict: 'SESUAI' | 'ADA_PELANGGARAN';
  violationCount: number;
  violationCodes: string[];     // ['V02', 'V06'] — codes only for free
  
  // Paid tier additionally gets this (gated in response)
  violations?: ViolationDetail[];
  calculations?: {
    correctPph21: number;
    correctJht: number;
    correctJp: number;
    correctKesehatan: number;
    cityUMK: number;
  };
  
  // Always returned
  isGated: boolean;             // true if user is free tier and violations found
  subscriptionRequired: 'basic' | null;
  gateMessage?: string;         // "Upgrade ke Basic untuk melihat detail IDR"
}

interface ViolationDetail {
  code: string;                 // 'V02'
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  titleID: string;              // "BPJS JP Kurang Bayar"
  descriptionID: string;        // "JP dipotong IDR X, seharusnya IDR Y"
  differenceIDR: number | null; // null = gated for free tier
  actionID: string;             // "Minta klarifikasi ke HRD tertulis"
}
```

**Error codes:**

| Code | HTTP | Message |
|------|------|---------|
| `INVALID_CITY` | 400 | "Kota tidak ditemukan dalam database UMK kami" |
| `INVALID_SALARY` | 400 | "Gaji tidak valid (harus antara IDR 500.000 – IDR 1 miliar)" |
| `INVALID_PTKP` | 400 | "Status PTKP tidak valid" |
| `RATE_LIMIT_EXCEEDED` | 429 | "Terlalu banyak permintaan. Coba lagi besok." |
| `CALCULATION_ERROR` | 500 | "Terjadi kesalahan kalkulasi. Tim kami telah diberitahu." |

---

### Route: `POST /api/ocr/upload`

**Purpose:** Upload payslip image, trigger OCR, return extracted fields.

**Auth:** Optional (anonymous)

**Rate limit:** 3 uploads/IP/hour (anonymous), 10/day (authenticated)

**Content-Type:** `multipart/form-data`

**Request:**
```
file: <binary>          # JPEG, PNG, PDF — max 5MB
sessionId: string       # for anonymous tracking
```

**Processing flow:**
1. Validate file type + size
2. Upload to Supabase Storage `payslips/{userId or session}/{uuid}.{ext}`
3. Check Google Vision quota counter in Supabase KV
4. If quota available: call Google Vision → set `ocrSource = 'google_vision'`
5. If quota exhausted: call Tesseract.js Edge Function → set `ocrSource = 'tesseract'`
6. Return extracted fields + confidence

**Response:**

```typescript
interface OCRUploadResponse {
  filePath: string;             // storage path reference
  ocrSource: 'google_vision' | 'tesseract';
  confidence: number;           // 0.0 – 1.0
  routingDecision: 'AUTO_ACCEPT' | 'SOFT_CHECK' | 'MANUAL_REQUIRED';
  
  extractedFields: {
    grossSalary?: number;
    pph21?: number;
    jhtEmployee?: number;
    jpEmployee?: number;
    kesehatanEmployee?: number;
    takeHome?: number;
    // Each field has individual confidence
    fieldConfidences: Record<string, number>;
  };
  
  // Fields that need user confirmation (confidence < 0.80)
  requiresConfirmation: string[];
}
```

**Routing decision thresholds:**
- `confidence >= 0.92` → AUTO_ACCEPT (skip confirmation screen)
- `0.80 <= confidence < 0.92` → SOFT_CHECK (show confirmation screen, pre-filled)
- `confidence < 0.80` → MANUAL_REQUIRED (show empty form, OCR as hints only)

---

### Route: `GET /api/audit/history`

**Purpose:** User's audit history for dashboard.

**Auth:** Required

**Rate limit:** 60/hour

**Query params:**
```
limit: number    // default 10, max 50
offset: number   // pagination
tool: string     // 'wajar-slip' | 'wajar-gaji' etc. (optional filter)
```

**Response:**
```typescript
interface AuditHistoryResponse {
  audits: AuditHistoryItem[];
  total: number;
  hasMore: boolean;
}

interface AuditHistoryItem {
  id: string;
  tool: string;
  createdAt: string;         // ISO timestamp
  
  // Wajar Slip specific
  verdict?: string;
  violationCount?: number;
  grossSalary?: number;
  city?: string;
  
  // Wajar Gaji specific
  jobTitle?: string;
  benchmarkP50?: number;
  
  // All
  subscriptionTierAtTime: string;
}
```

**Tier gate:** Free users see last 5 audits. Basic: 3 months. Pro: unlimited.

---

### Route: `POST /api/salary/submit`

**Purpose:** Crowdsource salary submission for Wajar Gaji.

**Auth:** Not required (anonymous)

**Rate limit:** 2 submissions/IP/24h (dedup by fingerprint anyway)

**Request:**
```typescript
interface SalarySubmissionRequest {
  jobTitle: string;         // raw text, normalized server-side
  city: string;
  grossSalarym: number;     // IDR monthly
  experienceBucket: '0-2' | '3-5' | '6-10' | '10+';
  industry?: string;
  
  // For dedup — never stored as-is
  _clientFingerprint?: string;  // browser-generated, optional
}
```

**Response:**
```typescript
interface SalarySubmissionResponse {
  accepted: boolean;
  message: string;   // "Terima kasih! Data kamu membantu ribuan pencari kerja."
  isDuplicate: boolean;
  violatesOutlierRule: boolean;
}
```

**Server-side processing:**
1. Normalize job title → category
2. Compute dedup fingerprint (IP + title + city + salary bucket)
3. Check for recent duplicate
4. Run outlier detection
5. If accepted: insert with `is_validated = false`
6. Validation: Python agent runs nightly to set `is_validated = true` for non-outliers

---

### Route: `GET /api/salary/benchmark`

**Purpose:** Fetch salary benchmark for Wajar Gaji.

**Auth:** Optional (tier determines detail level)

**Rate limit:** 30/hour (anonymous), 200/hour (authenticated)

**Query params:**
```
jobTitle: string       // required
city: string           // required  
province: string       // required (help from frontend location picker)
experienceBucket: string // required
```

**Response:**
```typescript
interface SalaryBenchmarkResponse {
  // Always returned
  jobCategoryId: string;
  matchedTitle: string;
  matchType: 'EXACT' | 'FUZZY' | 'SEMANTIC';
  
  // Province P50 — always shown (free)
  provinceP50: number | null;
  provinceName: string;
  umk: number | null;           // UMK for entered city
  confidenceBadge: {
    level: 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE';
    label: string;              // "Terverifikasi" | "Cukup" | "Estimasi" | "Belum ada data"
    sampleCount: number;
  };
  
  // Gated (Basic+)
  cityP25?: number;
  cityP50?: number;
  cityP75?: number;
  cityBreakdownChart?: ChartData;
  
  isGated: boolean;
  gateMessage?: string;
}
```

---

### Route: `GET /api/property/benchmark`

**Purpose:** Wajar Tanah price benchmark.

**Auth:** Optional

**Rate limit:** 30/hour (anonymous)

**Query params:**
```
province: string
city: string
district: string       // kelurahan
propertyType: 'RUMAH' | 'TANAH' | 'APARTEMEN' | 'RUKO'
landAreaSqm: number
askingPriceTotal: number    // total asking price IDR
```

**Response:**
```typescript
interface PropertyBenchmarkResponse {
  // Always (free)
  verdict: 'MURAH' | 'WAJAR' | 'MAHAL' | 'SANGAT_MAHAL';
  medianPricePerSqm: number;   // P50
  askingPricePerSqm: number;   // calculated
  njopPerSqm?: number;
  njopYear?: number;
  sampleCount: number;
  dataFreshness: string;       // "3 hari yang lalu"
  
  // Gated (Basic+)
  p25?: number;
  p75?: number;
  njopToMarketRatio?: number;  // market / NJOP
  
  // Always
  verdictMessage: string;
  kjppDisclaimer: string;
  isGated: boolean;
  hasData: boolean;            // false if "Belum ada data"
}
```

---

### Route: `GET /api/abroad/compare`

**Purpose:** Wajar Kabur PPP comparison.

**Auth:** Optional

**Rate limit:** 20/hour (anonymous — World Bank API calls are expensive)

**Query params:**
```
currentIDRSalary: number
jobRole: string
targetCountry: string    // ISO code: SG, MY, AU, US, GB, ...
```

**Response:**
```typescript
interface AbroadComparisonResponse {
  // Free (top 5 countries) or paid (all 15)
  isGated: boolean;
  
  // Always for free countries
  nominalEquivalent: number;
  nominalCurrency: string;
  realPurchasingPowerIntlUSD: number;
  pppFactor: number;
  pppYear: number;
  exchangeRate: number;
  
  // Basic+
  colBreakdown?: COLBreakdownItem[];
  marketSalaryInTarget?: {
    currency: string;
    p50: number;
    source: string;
  };
  
  // Pro only
  netSalaryEstimate?: {
    grossSalary: number;
    estimatedTax: number;
    socialContributions: number;
    netSalary: number;
    effectiveTaxRate: number;
  };
  
  disclaimer: string;
}
```

---

### Route: `GET /api/col/compare`

**Purpose:** Wajar Hidup cost of living comparison.

**Auth:** Optional

**Rate limit:** 30/hour

**Query params:**
```
fromCity: string
toCity: string
currentSalary: number
lifestyleTier: 'HEMAT' | 'STANDAR' | 'NYAMAN'
```

**Response:**
```typescript
interface COLCompareResponse {
  fromCOLIndex: number;
  toCOLIndex: number;
  adjustmentRatio: number;
  requiredSalary: number;
  salaryDifference: number;
  percentChange: number;
  verdict: 'LEBIH_MURAH' | 'SAMA' | 'LEBIH_MAHAL';
  verdictMessage: string;
  
  // Basic+
  categoryBreakdown?: {
    category: string;
    label: string;
    fromAmount: number;
    toAmount: number;
    difference: number;
  }[];
  
  isGated: boolean;
  hasData: boolean;
}
```

---

### Route: `POST /api/payment/create-transaction`

**Purpose:** Create Midtrans Snap transaction for subscription purchase.

**Auth:** Required

**Rate limit:** 5/user/hour

**Request:**
```typescript
interface CreateTransactionRequest {
  plan: 'basic' | 'pro';
  billingPeriod: 'monthly' | 'annual';  // annual = 20% discount
}
```

**Response:**
```typescript
interface CreateTransactionResponse {
  snapToken: string;         // Midtrans Snap token
  orderId: string;           // internal order ID
  grossAmount: number;       // IDR total
  expiryAt: string;          // ISO timestamp — Snap tokens expire in 24h
}
```

**Server processing:**
1. Calculate gross amount based on plan + period
2. Generate order ID: `CW-{userId[:8]}-{timestamp}`
3. Call Midtrans `/snap/v1/transactions`
4. Store pending transaction in DB
5. Return snap_token to client

---

### Route: `GET /api/subscription/status`

**Purpose:** Current user subscription status.

**Auth:** Required

**Response:**
```typescript
interface SubscriptionStatusResponse {
  tier: 'free' | 'basic' | 'pro';
  isActive: boolean;
  expiresAt: string | null;
  daysRemaining: number | null;
  
  // Feature access flags
  canSeeViolationAmounts: boolean;
  canSeeP25P75: boolean;
  canExportPDF: boolean;
  canSeeAllCountries: boolean;
  auditHistoryMonths: number | null;   // null = unlimited
}
```

---

## 5.2 Edge Function Specs

All Edge Functions run in Deno on Supabase Edge. They use the `service_role` key to bypass RLS.

### Edge Function: `audit-payslip`

**Trigger:** Called by `/api/audit-payslip` route (for CPU-intensive calculation offload)

**Alternative:** For v1, calculation runs in Next.js API route directly (simpler). Move to Edge Function only if cold start becomes an issue.

**Purpose:** Run PPh21 + BPJS calculation engine in isolated environment.

```typescript
// supabase/functions/audit-payslip/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  );
  
  const body = await req.json();
  
  // Run calculation
  const result = await runAuditCalculation(body, supabase);
  
  return new Response(JSON.stringify(result), {
    headers: { 'Content-Type': 'application/json' }
  });
});
```

---

### Edge Function: `check-audit-limit`

**Purpose:** Verify anonymous user hasn't exceeded daily free audit limit.

**Called by:** `POST /api/audit-payslip` before processing

**Logic:**
```typescript
async function checkAuditLimit(sessionId: string, ipHash: string): Promise<boolean> {
  const { count } = await supabase
    .from('payslip_audits')
    .select('*', { count: 'exact', head: true })
    .eq('session_id', sessionId)
    .gte('created_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString());
  
  return (count ?? 0) < 3;  // 3 free audits per day per session
}
```

---

### Edge Function: `process-verdict`

**Purpose:** Apply subscription gate logic to audit results. Ensures violation IDR amounts are only in response if user is Basic+.

**Input:** Raw audit result + user tier  
**Output:** Gated audit result with appropriate fields visible

```typescript
function applyVerdictGate(
  rawResult: RawAuditResult,
  userTier: string
): GatedAuditResult {
  if (userTier === 'free') {
    return {
      ...rawResult,
      violations: rawResult.violations.map(v => ({
        ...v,
        differenceIDR: null,    // hide amounts
        isGated: true,
      })),
      calculations: undefined,   // hide all IDR calculations
      isGated: true,
    };
  }
  return { ...rawResult, isGated: false };
}
```

---

### Edge Function: `send-payment-confirmation`

**Purpose:** Send transactional email after successful payment.

**Trigger:** Called by Midtrans webhook handler after successful payment

**Template (Resend):**
```typescript
async function sendPaymentConfirmation(
  userEmail: string,
  plan: string,
  amount: number,
  orderId: string
) {
  await resend.emails.send({
    from: 'noreply@cekwajar.id',
    to: userEmail,
    subject: `Berhasil! Langganan ${plan} aktif — cekwajar.id`,
    html: `
      <h2>Terima kasih telah berlangganan!</h2>
      <p>Langganan ${plan} kamu kini aktif.</p>
      <p>Order ID: ${orderId}</p>
      <p>Jumlah dibayar: ${formatIDR(amount)}</p>
      <p>Mulai gunakan fitur premium: <a href="https://cekwajar.id">cekwajar.id</a></p>
    `
  });
}
```

---

### Edge Function: `purge-deleted-payslips`

**Purpose:** Delete payslip files from Storage for audits past their 30-day retention. Called by pg_cron daily.

```typescript
serve(async () => {
  const supabase = createClient(url, serviceKey);
  
  // Find file paths that should be deleted
  const { data: toDelete } = await supabase
    .from('payslip_audits')
    .select('id, payslip_file_path')
    .lt('delete_at', new Date().toISOString())
    .not('payslip_file_path', 'is', null);
  
  let deleted = 0;
  for (const audit of toDelete ?? []) {
    // Delete from Storage
    await supabase.storage
      .from('payslips')
      .remove([audit.payslip_file_path]);
    
    // Null the path in DB
    await supabase
      .from('payslip_audits')
      .update({ payslip_file_path: null })
      .eq('id', audit.id);
    
    deleted++;
  }
  
  return new Response(JSON.stringify({ deleted }));
});
```

---

### Edge Function: `schedule-dunning-email`

**Purpose:** Send renewal reminder to subscribers expiring in 3 days.

**Trigger:** pg_cron daily at 18:00 UTC

```typescript
serve(async () => {
  const threedays = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString();
  const tomorrow = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();
  
  const { data: expiring } = await supabase
    .from('subscriptions')
    .select('user_id, plan_type, ends_at, user_profiles(email)')
    .eq('status', 'active')
    .gte('ends_at', tomorrow)
    .lte('ends_at', threedays);
  
  for (const sub of expiring ?? []) {
    await sendDunningEmail(sub.user_profiles.email, sub.plan_type, sub.ends_at);
  }
  
  return new Response(JSON.stringify({ sent: expiring?.length ?? 0 }));
});
```

---

## 5.3 Webhook Handling Spec

### Midtrans Webhook

**Endpoint:** `POST /api/webhooks/midtrans`

**Auth:** Signature verification (not JWT)

**Idempotency:** Webhook may be called multiple times for the same transaction. Must be idempotent.

**Payload mapping:**

| Midtrans Field | Our Action |
|----------------|------------|
| `transaction_status` | Map to subscription action (see table below) |
| `order_id` | Lookup our `transactions` table |
| `gross_amount` | Verify against our stored amount |
| `signature_key` | Verify SHA512 signature |
| `fraud_status` | `'accept'` required to activate |

**Status → Action mapping:**

| `transaction_status` | `fraud_status` | Action |
|---------------------|----------------|--------|
| `settlement` | `accept` | Activate subscription, send confirmation email |
| `settlement` | `deny` | Do NOT activate. Log fraud_status. |
| `capture` | `accept` | Pending — wait for settlement |
| `capture` | `challenge` | Hold — manual review needed |
| `pending` | any | No action — update transaction status |
| `cancel` | any | No action — update to cancelled |
| `deny` | any | No action — update to denied |
| `expire` | any | Update to expired — no activation |
| `refund` | any | Deactivate subscription if active |

**Full webhook handler:**

```typescript
// app/api/webhooks/midtrans/route.ts
import crypto from 'crypto';

export async function POST(request: Request) {
  const body = await request.json();
  
  // 1. Signature verification
  const expectedSignature = crypto
    .createHash('sha512')
    .update(body.order_id + body.status_code + body.gross_amount + process.env.MIDTRANS_SERVER_KEY!)
    .digest('hex');
  
  if (!crypto.timingSafeEqual(
    Buffer.from(body.signature_key),
    Buffer.from(expectedSignature)
  )) {
    console.error('Invalid Midtrans signature', { orderId: body.order_id });
    return Response.json({ error: 'Invalid signature' }, { status: 401 });
  }
  
  // 2. Idempotency check — did we already process this?
  const { data: existingTx } = await supabase
    .from('transactions')
    .select('id, status, is_webhook_processed')
    .eq('midtrans_order_id', body.order_id)
    .single();
  
  if (!existingTx) {
    console.error('Unknown order', body.order_id);
    return Response.json({ error: 'Unknown order' }, { status: 404 });
  }
  
  if (existingTx.is_webhook_processed && body.transaction_status === 'settlement') {
    // Already processed — return 200 to stop Midtrans retrying
    return Response.json({ status: 'already_processed' });
  }
  
  // 3. Process based on status
  const isActivation = 
    body.transaction_status === 'settlement' && 
    (body.fraud_status === 'accept' || !body.fraud_status);
  
  if (isActivation) {
    await activateSubscription(existingTx.id, body);
  }
  
  // 4. Update transaction record
  await supabase.from('transactions').update({
    status: body.transaction_status,
    midtrans_payload: body,
    is_webhook_processed: isActivation,
    webhook_received_at: new Date().toISOString(),
  }).eq('id', existingTx.id);
  
  // 5. Midtrans expects 200 OK for all legitimate webhooks
  return Response.json({ status: 'ok' });
}

async function activateSubscription(transactionId: string, payload: any) {
  // Parse plan from order_id: CW-{userId8}-{timestamp}-{plan}
  const parts = payload.order_id.split('-');
  const plan = parts[parts.length - 1];  // 'basic' or 'pro'
  const period = parts[parts.length - 2]; // 'monthly' or 'annual'
  
  const durationDays = period === 'annual' ? 366 : 32;  // slight buffer
  const endsAt = new Date(Date.now() + durationDays * 24 * 60 * 60 * 1000);
  
  // Get user from transaction
  const { data: tx } = await supabase
    .from('transactions')
    .select('user_id')
    .eq('id', transactionId)
    .single();
  
  // Upsert subscription
  await supabase.from('subscriptions').upsert({
    user_id: tx.user_id,
    plan_type: plan,
    status: 'active',
    starts_at: new Date().toISOString(),
    ends_at: endsAt.toISOString(),
    last_payment_order_id: payload.order_id,
  }, { onConflict: 'user_id' });
  
  // Update user_profiles.subscription_tier
  await supabase.from('user_profiles').update({
    subscription_tier: plan,
    updated_at: new Date().toISOString(),
  }).eq('id', tx.user_id);
  
  // Send confirmation email via Edge Function
  const { data: user } = await supabase.auth.admin.getUserById(tx.user_id);
  if (user?.user?.email) {
    await invokeEdgeFunction('send-payment-confirmation', {
      userEmail: user.user.email,
      plan,
      amount: parseInt(payload.gross_amount),
      orderId: payload.order_id,
    });
  }
}
```

---

## 5.4 External API Integration Spec

### BPS (Badan Pusat Statistik)

| Property | Value |
|----------|-------|
| **What we use** | BPS Sakernas (salary data), BPS CPI (cost of living), UMK Excel files |
| **Auth** | None (public data) |
| **Format** | Excel (.xlsx), some via API |
| **API endpoint** | `https://webapi.bps.go.id/v1/api/list/` — but unreliable. Prefer manual download + Python loader. |
| **Download URL** | `https://bps.go.id/id/statistics-table` (Sakernas), `https://bps.go.id/id/subject/3/inflasi` (CPI) |
| **Update frequency** | Sakernas: annual. CPI: monthly. UMK: annual (Jan) |
| **Parsing** | Python openpyxl — see `agents/loaders/bps_loader.py` |
| **Fallback** | Hardcoded prior year data if BPS format changes |
| **Error handling** | If BPS API fails, fall back to last cached Excel. Alert dev on Telegram. |

**BPS API example (reference — not primary):**
```
GET https://webapi.bps.go.id/v1/api/list/model/data/lang/ind/id/672/page/1/?key={BPS_API_KEY}
```

Free key at bps.go.id/id/api-documentation. Limit: 1000 req/month.

---

### Google Vision API

| Property | Value |
|----------|-------|
| **Auth** | Service Account JSON + GOOGLE_VISION_API_KEY |
| **Endpoint** | `https://vision.googleapis.com/v1/images:annotate` |
| **Features used** | `DOCUMENT_TEXT_DETECTION` (optimized for dense text like payslips) |
| **Free tier** | 1,000 requests/month |
| **Quota tracking** | KV counter in Supabase: `SELECT increment_ocr_counter()` |
| **Rate limit** | 1,800/min (safe to call without throttling) |
| **Fallback** | Tesseract.js when monthly counter ≥ 950 (50 buffer) |

**Integration:**
```typescript
async function callGoogleVision(imageBase64: string): Promise<string> {
  const response = await fetch(
    `https://vision.googleapis.com/v1/images:annotate?key=${process.env.GOOGLE_VISION_API_KEY}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        requests: [{
          image: { content: imageBase64 },
          features: [{ type: 'DOCUMENT_TEXT_DETECTION', maxResults: 1 }],
          imageContext: { languageHints: ['id', 'en'] }
        }]
      })
    }
  );
  
  const data = await response.json();
  return data.responses[0].fullTextAnnotation?.text ?? '';
}
```

**Quota tracking:**
```sql
CREATE TABLE ocr_quota_counter (
  month_key  TEXT PRIMARY KEY,  -- 'YYYY-MM'
  count      INTEGER DEFAULT 0
);

CREATE OR REPLACE FUNCTION increment_ocr_counter()
RETURNS INTEGER AS $$
DECLARE
  month_key TEXT := TO_CHAR(NOW(), 'YYYY-MM');
  new_count INTEGER;
BEGIN
  INSERT INTO ocr_quota_counter (month_key, count)
  VALUES (month_key, 1)
  ON CONFLICT (month_key)
  DO UPDATE SET count = ocr_quota_counter.count + 1
  RETURNING count INTO new_count;
  RETURN new_count;
END;
$$ LANGUAGE plpgsql;
```

---

### Tesseract.js (Client-side fallback)

| Property | Value |
|----------|-------|
| **Type** | Client-side WebAssembly (runs in browser) |
| **Languages** | `ind` (Indonesian) + `eng` (English) |
| **Free** | Yes, fully |
| **When used** | When Google Vision quota ≥ 950 or Vision returns error |
| **Accuracy** | ~75-80% for photos, ~85-90% for scanned PDFs |
| **Confidence penalty** | -15% applied to all Tesseract results before routing |
| **Bundle size** | ~5MB WASM (lazy-loaded only on OCR flow) |

**Integration:**
```typescript
// Client-side, lazy-loaded
async function extractWithTesseract(imageFile: File): Promise<OCRResult> {
  const { createWorker } = await import('tesseract.js');
  
  const worker = await createWorker(['ind', 'eng'], 1, {
    logger: (m) => console.log(m),
  });
  
  const { data } = await worker.recognize(imageFile);
  await worker.terminate();
  
  return {
    text: data.text,
    confidence: data.confidence / 100,  // tesseract returns 0-100
    source: 'tesseract',
    // Apply confidence penalty for Tesseract
    adjustedConfidence: (data.confidence / 100) * 0.85
  };
}
```

---

### World Bank API

| Property | Value |
|----------|-------|
| **Auth** | None |
| **Endpoint** | `https://api.worldbank.org/v2/country/{code}/indicator/PA.NUS.PPP?format=json&mrv=1` |
| **Free** | Yes, completely |
| **Rate limit** | None stated (very generous — 50+ req/sec) |
| **Cache** | 30 days in Supabase (annual data, no need to refresh often) |
| **Fallback** | Last cached value. If missing: display "Data PPP tidak tersedia" |
| **Countries** | 15 target countries + Indonesia |

**Parsing:**
```typescript
interface WorldBankAPIResponse {
  [0]: { page: number; pages: number; total: number };
  [1]: Array<{
    indicator: { id: string; value: string };
    country: { id: string; value: string };
    countryiso3code: string;
    date: string;
    value: number | null;
    unit: string;
  }>;
}
```

---

### Frankfurter.app (Exchange Rates)

| Property | Value |
|----------|-------|
| **Auth** | None |
| **Endpoint** | `https://api.frankfurter.app/latest?from=IDR&to=SGD` |
| **Free** | Yes, truly unlimited (public service) |
| **Rate limit** | None documented |
| **Source** | European Central Bank |
| **Cache** | 1 day (exchange rates update daily) |
| **Fallback** | Last cached rate + warning "Kurs mungkin tidak up-to-date" |

---

### Numbeo

| Property | Value |
|----------|-------|
| **Auth** | Free API key available, or scrape public pages |
| **API endpoint** | `https://www.numbeo.com/api/city_prices?api_key={key}&city={City}&currency=USD` |
| **Free API key** | Request at numbeo.com (limited) |
| **Scraping** | Public cost of living pages (no login required) |
| **Legal risk** | ToS violation if scraping — accepted (same as property scraping) |
| **Cache** | 7 days (CoL data changes slowly) |
| **Fallback** | Manual seed data for top 8 cities (hardcoded) |
| **Conversion** | Results in USD → convert to IDR using frankfurter rate |

**API example:**
```
GET https://www.numbeo.com/api/city_prices?api_key=KEY&city=Singapore&currency=IDR
Response: { "currency": "IDR", "prices": [{ "item_id": 1, "average_price": 95000, "item_name": "Meal, Inexpensive Restaurant" }] }
```

---

### Midtrans

| Property | Value |
|----------|-------|
| **Auth** | Base64(server_key + ":") in Authorization header |
| **Sandbox** | `https://api.sandbox.midtrans.com` |
| **Production** | `https://api.midtrans.com` |
| **Snap endpoint** | `POST /snap/v1/transactions` |
| **Webhook source IPs** | 103.208.23.0/24, 103.208.23.6 — verify in prod firewall |
| **Signature** | SHA512 of `order_id + status_code + gross_amount + server_key` |
| **Payment methods** | GoPay, OVO, Dana, ShopeePay, BCA VA, BNI VA, Mandiri VA, Indomaret, Alfamart |

**Snap request:**
```typescript
const snapPayload = {
  transaction_details: {
    order_id: orderId,
    gross_amount: grossAmount,
  },
  item_details: [{
    id: plan,
    price: grossAmount,
    quantity: 1,
    name: `cekwajar.id ${plan.charAt(0).toUpperCase() + plan.slice(1)} — 1 bulan`,
  }],
  customer_details: {
    email: userEmail,
  },
  enabled_payments: [
    'gopay', 'shopeepay', 'dana', 'ovo',
    'bca_va', 'bni_va', 'bri_va', 'mandiri_bill',
    'indomaret', 'alfamart'
  ],
  expiry: {
    duration: 24,
    unit: 'hour'
  }
};
```

---

### Rate Limiting — Summary Table

| Route | Anonymous | Free User | Basic/Pro | Notes |
|-------|-----------|-----------|-----------|-------|
| `POST /api/audit-payslip` | 5/IP/hour | 20/user/day | Unlimited | Also gated by OCR quota |
| `POST /api/ocr/upload` | 3/IP/hour | 10/user/day | 30/user/day | OCR quota separate |
| `GET /api/salary/benchmark` | 30/IP/hour | 200/user/hour | 500/user/hour | |
| `GET /api/property/benchmark` | 30/IP/hour | 200/user/hour | 500/user/hour | |
| `GET /api/abroad/compare` | 20/IP/hour | 100/user/hour | 200/user/hour | World Bank call cost |
| `GET /api/col/compare` | 30/IP/hour | 200/user/hour | 500/user/hour | |
| `POST /api/salary/submit` | 2/IP/24h | 2/user/24h | 5/user/24h | Dedup fingerprint also |
| `POST /api/payment/create-transaction` | ❌ | 5/user/hour | 5/user/hour | Must be authenticated |
| `POST /api/webhooks/midtrans` | N/A | N/A | N/A | Verified by signature |

**Rate limit implementation (Vercel Edge Middleware):**
```typescript
// middleware.ts
import { ipAddress } from '@vercel/edge';
import { kv } from '@vercel/kv';

export async function middleware(request: Request) {
  const ip = ipAddress(request) ?? 'unknown';
  const path = new URL(request.url).pathname;
  
  // Get limit config for this path
  const config = RATE_LIMIT_CONFIG[path];
  if (!config) return NextResponse.next();
  
  const key = `rl:${ip}:${path}`;
  const count = await kv.incr(key);
  
  if (count === 1) {
    await kv.expire(key, config.windowSeconds);
  }
  
  if (count > config.maxRequests) {
    return new Response(
      JSON.stringify({ error: { code: 'RATE_LIMIT_EXCEEDED', message: 'Terlalu banyak permintaan. Coba lagi nanti.' } }),
      { status: 429, headers: { 'Content-Type': 'application/json' } }
    );
  }
  
  return NextResponse.next();
}
```
