# Stage 9 — Monetization: Midtrans + Freemium Gates + Legal Pages
**cekwajar.id Vibe Coding Playbook**  
**Estimated time:** 4–5 hours  
**Prerequisites:** Stages 1–8 complete. All 5 tools working. Midtrans sandbox account ready.  
**Goal:** Real payment flow with Midtrans Snap, webhook handler, subscription activation, all freemium gates wired up, legal pages live.

---

## New Dependencies This Stage

```bash
# Midtrans Snap is loaded via CDN (no npm package needed)
# Just add the script tag in the payment page

# Email (Resend — free 3000/month)
pnpm add resend

# For cookie consent
pnpm add js-cookie @types/js-cookie
```

---

## ═══════════════════════════════════════════════
## MASTER PROMPT — SEND THIS TO CLAUDE CODE
## (Stage 9 — Monetization)
## ═══════════════════════════════════════════════

```
===START===
cekwajar.id — Stage 9: Full Monetization

Context: All 5 tools are working. Stages 1-8 complete.
Midtrans sandbox keys are in .env.local.
subscriptions and transactions tables exist with correct RLS.

YOUR TASK FOR STAGE 9:
Build complete payment flow, subscription activation via webhook, 
all freemium gates wired to real subscription data, legal pages, cookie consent.

════════════════════════════════════════════════════
PART A: MIDTRANS PAYMENT FLOW
════════════════════════════════════════════════════

Create src/app/api/payment/create-transaction/route.ts

POST body:
  { plan: 'basic' | 'pro', billingPeriod: 'monthly' | 'annual' }

Auth: Required (must be logged in)

Pricing:
  basic monthly: 29,000
  basic annual: 278,400  (= 29,000 × 12 × 0.80 — 20% discount)
  pro monthly: 79,000
  pro annual: 758,400   (= 79,000 × 12 × 0.80)

Handler:
  1. Get authenticated user (getCurrentUser()) — return 401 if not logged in
  2. Calculate gross_amount based on plan + period
  3. Generate order ID: `CW-${userId.slice(0,8)}-${Date.now()}-${plan}-${period}`
     Example: "CW-a1b2c3d4-1704067200000-basic-monthly"
  4. Store pending transaction in DB first
  5. Call Midtrans Snap API to create token
  6. Return snap_token to client

Midtrans Snap API call:
  const serverKey = process.env.MIDTRANS_SERVER_KEY!
  const isProduction = process.env.MIDTRANS_IS_PRODUCTION === 'true'
  const snapBaseUrl = isProduction 
    ? 'https://app.midtrans.com/snap/v1/transactions'
    : 'https://app.sandbox.midtrans.com/snap/v1/transactions'
  
  const authString = Buffer.from(serverKey + ':').toString('base64')
  
  const snapResponse = await fetch(snapBaseUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${authString}`,
    },
    body: JSON.stringify({
      transaction_details: {
        order_id: orderId,
        gross_amount: grossAmount,
      },
      item_details: [{
        id: `${plan}-${billingPeriod}`,
        price: grossAmount,
        quantity: 1,
        name: `cekwajar.id ${plan.charAt(0).toUpperCase() + plan.slice(1)} — ${billingPeriod === 'monthly' ? '1 bulan' : '12 bulan'}`,
      }],
      customer_details: {
        email: user.email,
      },
      enabled_payments: [
        'gopay', 'shopeepay', 'dana', 'ovo',
        'bca_va', 'bni_va', 'bri_va', 'mandiri_bill',
        'indomaret', 'alfamart',
        'credit_card',
      ],
      expiry: { duration: 24, unit: 'hour' },
    }),
  })
  
  const snapData = await snapResponse.json()
  return Response.json({ data: { snapToken: snapData.token, orderId } })

════════════════════════════════════════════════════
PART B: MIDTRANS WEBHOOK HANDLER
════════════════════════════════════════════════════

Create src/app/api/webhooks/midtrans/route.ts

CRITICAL: This route uses service_role client. Must verify signature before any DB action.

import crypto from 'crypto'

export async function POST(request: Request) {
  const body = await request.json()
  
  // 1. SIGNATURE VERIFICATION (most important step)
  const serverKey = process.env.MIDTRANS_SERVER_KEY!
  const expectedSignature = crypto
    .createHash('sha512')
    .update(body.order_id + body.status_code + body.gross_amount + serverKey)
    .digest('hex')
  
  const isValid = crypto.timingSafeEqual(
    Buffer.from(body.signature_key ?? ''),
    Buffer.from(expectedSignature)
  )
  
  if (!isValid) {
    console.error('Invalid Midtrans signature', { orderId: body.order_id })
    return Response.json({ error: 'Invalid signature' }, { status: 401 })
  }
  
  // 2. Find transaction in DB
  const serviceClient = getServiceClient()
  const { data: tx } = await serviceClient
    .from('transactions')
    .select('id, user_id, gross_amount, is_webhook_processed')
    .eq('midtrans_order_id', body.order_id)
    .single()
  
  if (!tx) {
    return Response.json({ error: 'Unknown order' }, { status: 404 })
  }
  
  // 3. Verify amount matches (prevent amount tampering)
  if (tx.gross_amount !== parseInt(body.gross_amount)) {
    console.error('Amount mismatch', { expected: tx.gross_amount, received: body.gross_amount })
    return Response.json({ error: 'Amount mismatch' }, { status: 400 })
  }
  
  // 4. Idempotency check
  if (tx.is_webhook_processed && body.transaction_status === 'settlement') {
    return Response.json({ status: 'already_processed' })
  }
  
  // 5. Process based on status
  const isActivation = 
    body.transaction_status === 'settlement' && 
    (body.fraud_status === 'accept' || !body.fraud_status)
  
  if (isActivation) {
    await activateSubscription(tx, body, serviceClient)
  }
  
  // 6. Update transaction record
  await serviceClient.from('transactions').update({
    status: body.transaction_status,
    fraud_status: body.fraud_status,
    midtrans_payload: body,
    is_webhook_processed: isActivation,
    webhook_received_at: new Date().toISOString(),
  }).eq('id', tx.id)
  
  // Midtrans expects 200 OK
  return Response.json({ status: 'ok' })
}

async function activateSubscription(
  tx: { id: string; user_id: string },
  payload: any,
  supabase: SupabaseClient
) {
  // Parse plan from order_id: CW-{userId8}-{timestamp}-{plan}-{period}
  const parts = payload.order_id.split('-')
  const period = parts[parts.length - 1]   // 'monthly' | 'annual'
  const plan = parts[parts.length - 2]      // 'basic' | 'pro'
  
  const durationDays = period === 'annual' ? 366 : 32
  const endsAt = new Date(Date.now() + durationDays * 24 * 60 * 60 * 1000)
  
  // Upsert subscription (one per user)
  await supabase.from('subscriptions').upsert({
    user_id: tx.user_id,
    plan_type: plan,
    status: 'active',
    starts_at: new Date().toISOString(),
    ends_at: endsAt.toISOString(),
    last_payment_order_id: payload.order_id,
  }, { onConflict: 'user_id' })
  
  // Update user profile tier (CRITICAL — this gates all features)
  await supabase.from('user_profiles').update({
    subscription_tier: plan,
    updated_at: new Date().toISOString(),
  }).eq('id', tx.user_id)
  
  // Send confirmation email (don't block on this)
  sendConfirmationEmail(tx.user_id, plan, parseInt(payload.gross_amount), payload.order_id)
    .catch(err => console.error('Email send failed:', err))
}

async function sendConfirmationEmail(userId: string, plan: string, amount: number, orderId: string) {
  // Get user email
  const serviceClient = getServiceClient()
  const { data } = await serviceClient.auth.admin.getUserById(userId)
  const email = data?.user?.email
  
  if (!email || !process.env.RESEND_API_KEY) return
  
  const { Resend } = await import('resend')
  const resend = new Resend(process.env.RESEND_API_KEY)
  
  await resend.emails.send({
    from: 'noreply@cekwajar.id',
    to: email,
    subject: `Berhasil! Langganan ${plan} aktif — cekwajar.id`,
    html: `
      <h2>Terima kasih telah berlangganan!</h2>
      <p>Paket <strong>${plan}</strong> kamu kini aktif.</p>
      <p>Order ID: ${orderId}</p>
      <p>Jumlah: Rp ${amount.toLocaleString('id-ID')}</p>
      <p><a href="https://cekwajar.id/dashboard">Mulai gunakan fitur premium →</a></p>
    `,
  })
}

Add to .env.local (and Vercel):
  RESEND_API_KEY=re_xxxxxxxxxxxx
  (Get at resend.com → API Keys → Create)

════════════════════════════════════════════════════
PART C: PAYMENT UI
════════════════════════════════════════════════════

Create src/app/upgrade/page.tsx (replace stub)

This page shows pricing tiers and triggers Midtrans Snap on click.

The page is a CLIENT COMPONENT (needs Midtrans Snap JS).

Add Midtrans Snap script in layout or via dynamic import:
  In src/app/upgrade/page.tsx:
  useEffect(() => {
    const script = document.createElement('script')
    script.src = process.env.NEXT_PUBLIC_MIDTRANS_IS_PRODUCTION === 'true'
      ? 'https://app.midtrans.com/snap/snap.js'
      : 'https://app.sandbox.midtrans.com/snap/snap.js'
    script.setAttribute('data-client-key', process.env.NEXT_PUBLIC_MIDTRANS_CLIENT_KEY!)
    document.head.appendChild(script)
    return () => document.head.removeChild(script)
  }, [])

Pricing display (3 columns):
  FREE:
    "Gratis" 
    Rp 0/bulan
    Features: 3 audit/hari, Benchmark provinsi, Top 5 negara, 2 kota perbandingan
    [Mulai Gratis] → /wajar-slip
    
  BASIC (recommended):
    "Basic" — highlighted with border
    Rp 29.000/bulan (or Rp 23.200/bulan jika tahunan)
    Annual toggle → show discounted price
    Features: Semua Gratis + Detail IDR pelanggaran, P25-P75 kota, 15 negara, Breakdown kategori COL
    [Pilih Basic] → handleUpgrade('basic', period)
    
  PRO:
    "Pro"
    Rp 79.000/bulan
    Features: Semua Basic + Net salary abroad, Ekspor PDF, Prioritas support
    [Pilih Pro] → handleUpgrade('pro', period)

Annual/Monthly toggle at top of pricing section.

handleUpgrade function:
  async function handleUpgrade(plan: string, period: string) {
    setLoading(true)
    
    // Get Snap token
    const response = await fetch('/api/payment/create-transaction', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plan, billingPeriod: period }),
    })
    
    if (!response.ok) {
      setError('Gagal membuat transaksi. Coba lagi.')
      setLoading(false)
      return
    }
    
    const { data } = await response.json()
    
    // Open Midtrans Snap
    window.snap.pay(data.snapToken, {
      onSuccess: (result) => {
        setLoading(false)
        router.push('/dashboard?upgraded=true')
      },
      onPending: (result) => {
        setLoading(false)
        router.push('/dashboard?payment=pending')
      },
      onError: (result) => {
        setLoading(false)
        setError('Pembayaran gagal. Coba metode lain.')
      },
      onClose: () => {
        setLoading(false)
      },
    })
  }

Add TypeScript declaration for window.snap:
  In src/types/index.ts:
  declare global {
    interface Window {
      snap: {
        pay: (snapToken: string, options: SnapPayOptions) => void
      }
    }
  }

════════════════════════════════════════════════════
PART D: DASHBOARD UPGRADE NOTIFICATION
════════════════════════════════════════════════════

Update src/app/dashboard/page.tsx:
  If searchParams.upgraded === 'true': show success toast
  "🎉 Selamat! Langganan [plan] kamu kini aktif."

  Also show "Pembayaran menunggu konfirmasi..." if payment=pending
  (Midtrans sometimes takes 1-5 minutes for settlement)

════════════════════════════════════════════════════
PART E: WIRE ALL FREEMIUM GATES TO REAL DATA
════════════════════════════════════════════════════

Now that payment works, ensure ALL tool pages read actual tier from DB.

Update all tool pages to:
  1. Use getCurrentUser() server-side to get tier
  2. Pass tier as prop to client components
  3. PremiumGate uses the real tier

For pages that are CLIENT COMPONENTS:
  Create a custom hook: src/hooks/useUserTier.ts
  
  export function useUserTier() {
    const supabase = createBrowserClient(...)
    const [tier, setTier] = useState<SubscriptionTier>('free')
    
    useEffect(() => {
      async function fetchTier() {
        const { data: { user } } = await supabase.auth.getUser()
        if (!user) return setTier('free')
        
        const { data } = await supabase
          .from('user_profiles')
          .select('subscription_tier')
          .eq('id', user.id)
          .single()
        
        setTier((data?.subscription_tier ?? 'free') as SubscriptionTier)
      }
      fetchTier()
    }, [])
    
    return tier
  }

Use in each tool page:
  const userTier = useUserTier()
  // Pass to PremiumGate components

════════════════════════════════════════════════════
PART F: LEGAL PAGES
════════════════════════════════════════════════════

Create src/app/privacy-policy/page.tsx
Server component. Static content in Bahasa Indonesia.

Include these sections:
1. Data apa yang kami kumpulkan
2. Bagaimana kami menggunakan data kamu
3. Berapa lama data disimpan
4. Hak kamu atas data (UU PDP No.27/2022)
5. Data sharing (kami tidak menjual data)
6. Keamanan data
7. Kontak: privacy@cekwajar.id

Key data retention points (match req_10_security.md):
  - Foto slip gaji: 30 hari otomatis dihapus
  - Data audit: 12 bulan
  - Submission gaji anonim: 24 bulan
  - Transaksi pembayaran: 3 tahun (kewajiban pajak)
  - Akun pengguna: hingga penghapusan (kirim email ke privacy@cekwajar.id)

Create src/app/terms/page.tsx
Server component. Terms in Bahasa Indonesia.

Include:
  - Deskripsi layanan
  - Batasan tanggung jawab (kalkulasi bersifat indikatif)
  - Hak kekayaan intelektual
  - Larangan penggunaan
  - Pembatasan layanan
  - Hukum yang berlaku: Hukum Indonesia

Create src/app/kontak/page.tsx
Simple contact page: email, about the founder.

════════════════════════════════════════════════════
PART G: COOKIE CONSENT
════════════════════════════════════════════════════

Update src/components/layout/CookieConsent.tsx (replace placeholder from Stage 1)

Client component. Shown at bottom of screen on first visit.

Cookie consent stores choice in localStorage AND records consent in user_consents table if user is logged in.

Banner:
  Text: "Kami menggunakan cookie untuk meningkatkan pengalaman kamu. Baca Kebijakan Privasi kami."
  Buttons: [Setuju] [Tolak] [Pelajari lebih]
  
  On Setuju: 
    localStorage.setItem('cookie_consent', 'accepted')
    If user logged in: INSERT INTO user_consents
    Hide banner
  
  On Tolak:
    localStorage.setItem('cookie_consent', 'rejected')
    Hide banner (app still works without analytics cookies)

Show banner only if localStorage.getItem('cookie_consent') is null.

════════════════════════════════════════════════════
PART H: MIDTRANS SANDBOX TESTING
════════════════════════════════════════════════════

Create scripts/test-webhook.ts for testing webhook locally:

This script sends a fake Midtrans webhook payload to your local API.
Useful for testing without completing actual payment.

import crypto from 'crypto'

const SERVER_KEY = process.env.MIDTRANS_SERVER_KEY!
const ORDER_ID = 'CW-test1234-1704067200000-basic-monthly'
const GROSS_AMOUNT = '29000'
const STATUS_CODE = '200'

const signature = crypto
  .createHash('sha512')
  .update(ORDER_ID + STATUS_CODE + GROSS_AMOUNT + SERVER_KEY)
  .digest('hex')

const payload = {
  transaction_status: 'settlement',
  fraud_status: 'accept',
  order_id: ORDER_ID,
  gross_amount: GROSS_AMOUNT,
  status_code: STATUS_CODE,
  signature_key: signature,
  payment_type: 'gopay',
}

fetch('http://localhost:3000/api/webhooks/midtrans', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload),
}).then(r => r.json()).then(console.log)

First create a test transaction in DB manually so the webhook has something to find:
  INSERT INTO transactions (user_id, midtrans_order_id, plan_type, billing_period, gross_amount, status)
  VALUES ('[your_user_id]', 'CW-test1234-1704067200000-basic-monthly', 'basic', 'monthly', 29000, 'pending');

════════════════════════════════════════════════════
VERIFICATION:
════════════════════════════════════════════════════

Test 1: Sandbox payment flow
  - Visit localhost:3000/upgrade
  - Click "Pilih Basic"
  - Midtrans Snap should open
  - Use Midtrans sandbox test credentials:
    GoPay: enter any phone, then set to 'approve' in simulator
  - After payment: redirect to /dashboard?upgraded=true
  - Check DB: user_profiles.subscription_tier = 'basic'
  - Check DB: subscriptions row active

Test 2: Webhook signature verification
  npx ts-node scripts/test-webhook.ts
  Expected: { status: 'ok' }
  DB: subscription activated

Test 3: Invalid signature
  Manually modify signature in test script
  Expected: 401 { error: 'Invalid signature' }

Test 4: Freemium gates
  - With free account: Wajar Slip violation details should be blurred
  - After Basic upgrade: details should be visible
  - Verify by checking userTier in React DevTools

Test 5: Legal pages
  Visit /privacy-policy, /terms → both render with Indonesian content

pnpm tsc --noEmit → zero errors
===END===
```

---

## Verification Checklist for Stage 9

```bash
# Payment flow
# 1. Create transaction
curl -X POST localhost:3000/api/payment/create-transaction \
  -H "Content-Type: application/json" \
  -H "Cookie: [your_session_cookie]" \
  -d '{"plan":"basic","billingPeriod":"monthly"}'
# Expected: { data: { snapToken: "...", orderId: "..." } }

# 2. Test webhook
npx ts-node scripts/test-webhook.ts
# Expected: { status: 'ok' }

# 3. Check subscription activated
psql $SUPABASE_DB_URL -c "SELECT subscription_tier FROM user_profiles WHERE id = '[your_id]'"

# TypeScript
pnpm tsc --noEmit
```

**Next:** Stage 10 — Production Hardening + Launch
