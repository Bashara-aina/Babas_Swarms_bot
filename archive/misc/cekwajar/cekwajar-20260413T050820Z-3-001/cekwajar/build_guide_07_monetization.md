# Build Guide 07: Monetization — Month 3 Paywall + GTM

**Goal:** First IDR revenue in Month 3. Traffic in Month 1–2. Convert in Month 3.  
**Model:** Freemium (free forever) + Basic IDR 29K/month + Pro IDR 79K/month  
**Payment:** Midtrans Snap (free setup, 1% MDR)  
**GTM:** TikTok + WhatsApp communities + SEO

---

## Revenue Timeline

| Month | Target | Action |
|-------|--------|--------|
| Month 1 | 200–500 unique users | Launch Wajar Slip + Wajar Gaji. TikTok 10 videos. |
| Month 2 | 500–2,000 users | Publish all 5 tools. Community seeding. SEO indexing. |
| Month 3 | First paying users | Activate paywall. Target 20–50 paying subs. IDR 580K–4M ARR |
| Month 4–5 | 50–200 subs | Scale TikTok + WhatsApp. Fix bugs from feedback. |
| Month 6 | 200–500 subs → IDR 6M–40M ARR | Upgrade Supabase Pro if >200 subs. Consider Mercer data. |

**Realistic Month 3 revenue:** 30 Basic subscribers = IDR 870K. Not life-changing, but it validates willingness to pay.

---

## Step 1: Midtrans Setup

`[MANUAL]` — Create Midtrans account

1. Register at: https://midtrans.com (Merchant account — free)
2. Complete business verification (KTP + NPWP as individual, or company docs)
3. Enable Snap payment page
4. **Required payment methods to enable:** GoPay, QRIS, OVO, Virtual Account (BCA/Mandiri), Credit Card
5. MDR rates:
   - QRIS/GoPay/OVO: 0.7% per transaction
   - Virtual Account: IDR 4,000 flat per transaction
   - Credit Card: 2.9%
6. Get Sandbox keys for testing, Production keys after approval (3–7 days)

`[CURSOR]` — Create: `lib/payments/midtrans.ts`

```typescript
// lib/payments/midtrans.ts
// Midtrans Snap documentation: https://docs.midtrans.com/reference/snap-overview

import crypto from 'crypto';

interface MidtransConfig {
  serverKey: string;
  clientKey: string;
  isProduction: boolean;
}

const config: MidtransConfig = {
  serverKey: process.env.MIDTRANS_SERVER_KEY!,
  clientKey: process.env.MIDTRANS_CLIENT_KEY!,
  isProduction: process.env.NODE_ENV === 'production',
};

export type SubscriptionTier = 'basic' | 'pro';

export const PRICING: Record<SubscriptionTier, { monthly: number; label: string; features: string[] }> = {
  basic: {
    monthly: 29_000,
    label: 'Basic',
    features: [
      'Semua 5 tools (fitur lengkap)',
      'Riwayat audit 3 bulan',
      'P25/P75 salary range',
      'Laporan PDF',
      '10 upload slip/bulan',
    ],
  },
  pro: {
    monthly: 79_000,
    label: 'Pro',
    features: [
      'Semua fitur Basic',
      'Upload slip unlimited',
      'Perbandingan industri',
      'Simulasi December true-up',
      'Analisis multi-kota',
      'Priority support',
    ],
  },
};

export interface CreateTransactionResponse {
  token: string;
  redirect_url: string;
}

export async function createSnapTransaction(
  orderId: string,
  userId: string,
  tier: SubscriptionTier,
  userEmail: string,
  userName: string
): Promise<CreateTransactionResponse> {
  const amount = PRICING[tier].monthly;
  
  const transactionDetails = {
    transaction_details: {
      order_id: orderId,
      gross_amount: amount,
    },
    item_details: [{
      id: `cekwajar_${tier}`,
      price: amount,
      quantity: 1,
      name: `cekwajar.id ${PRICING[tier].label} (1 bulan)`,
    }],
    customer_details: {
      email: userEmail,
      first_name: userName,
    },
    callbacks: {
      finish: `${process.env.NEXT_PUBLIC_APP_URL}/payment/success?order_id=${orderId}`,
      error: `${process.env.NEXT_PUBLIC_APP_URL}/payment/error`,
      pending: `${process.env.NEXT_PUBLIC_APP_URL}/payment/pending?order_id=${orderId}`,
    },
    credit_card: {
      secure: true,
    },
    // Enable multiple payment methods
    enabled_payments: ['gopay', 'qris', 'shopeepay', 'dana', 'bca_va', 'bni_va', 'bri_va', 'mandiri_va'],
    expiry: {
      unit: 'hours',
      duration: 24,
    },
  };
  
  const baseUrl = config.isProduction
    ? 'https://app.midtrans.com/snap/v1'
    : 'https://app.sandbox.midtrans.com/snap/v1';
  
  const auth = Buffer.from(`${config.serverKey}:`).toString('base64');
  
  const response = await fetch(`${baseUrl}/transactions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${auth}`,
    },
    body: JSON.stringify(transactionDetails),
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Midtrans error: ${error}`);
  }
  
  return response.json();
}

// Webhook signature verification (CRITICAL — never skip this)
export function verifyMidtransSignature(
  orderId: string,
  statusCode: string,
  grossAmount: string,
  signatureKey: string
): boolean {
  const rawString = `${orderId}${statusCode}${grossAmount}${config.serverKey}`;
  const expectedSignature = crypto
    .createHash('sha512')
    .update(rawString)
    .digest('hex');
  
  // Use timing-safe comparison to prevent timing attacks
  try {
    return crypto.timingSafeEqual(
      Buffer.from(signatureKey),
      Buffer.from(expectedSignature)
    );
  } catch {
    return false;
  }
}
```

---

## Step 2: Payment API Routes

`[CURSOR]` — Create: `app/api/payment/create/route.ts`

```typescript
// app/api/payment/create/route.ts
import { createClient } from '@/lib/supabase/server';
import { createSnapTransaction, PRICING } from '@/lib/payments/midtrans';
import { NextRequest, NextResponse } from 'next/server';
import { nanoid } from 'nanoid';

export async function POST(req: NextRequest) {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  
  if (!user) {
    return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
  }
  
  const { tier } = await req.json();
  if (!['basic', 'pro'].includes(tier)) {
    return NextResponse.json({ error: 'Invalid tier' }, { status: 400 });
  }
  
  // Generate unique order ID
  const orderId = `CW-${Date.now()}-${nanoid(6).toUpperCase()}`;
  
  // Get user email
  const { data: profile } = await supabase.from('user_profiles').select('full_name').eq('id', user.id).single();
  
  try {
    // Create pending transaction in DB
    await supabase.from('transactions').insert({
      user_id: user.id,
      order_id: orderId,
      tier,
      amount: PRICING[tier as 'basic' | 'pro'].monthly,
      status: 'pending',
    });
    
    // Create Midtrans Snap token
    const snapData = await createSnapTransaction(
      orderId,
      user.id,
      tier as 'basic' | 'pro',
      user.email!,
      profile?.full_name || 'User'
    );
    
    return NextResponse.json({
      snapToken: snapData.token,
      orderId,
      amount: PRICING[tier as 'basic' | 'pro'].monthly,
    });
  } catch (error) {
    console.error('Payment creation error:', error);
    return NextResponse.json({ error: 'Payment creation failed' }, { status: 500 });
  }
}
```

`[CURSOR]` — Create: `app/api/payment/webhook/route.ts`

```typescript
// app/api/payment/webhook/route.ts
// IMPORTANT: Add this URL to Midtrans dashboard > Settings > Payment Notifications

import { createClient } from '@/lib/supabase/server';
import { verifyMidtransSignature } from '@/lib/payments/midtrans';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const notification = await req.json();
  const supabase = createClient();
  
  const {
    order_id,
    transaction_status,
    fraud_status,
    gross_amount,
    status_code,
    signature_key,
  } = notification;
  
  // ALWAYS verify signature first
  const isValid = verifyMidtransSignature(order_id, status_code, gross_amount, signature_key);
  if (!isValid) {
    console.error(`Invalid Midtrans signature for order: ${order_id}`);
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
  }
  
  // Get transaction from DB
  const { data: transaction } = await supabase
    .from('transactions')
    .select('*')
    .eq('order_id', order_id)
    .single();
  
  if (!transaction) {
    return NextResponse.json({ error: 'Transaction not found' }, { status: 404 });
  }
  
  // Process based on status
  if (transaction_status === 'capture' || transaction_status === 'settlement') {
    if (fraud_status === 'accept' || !fraud_status) {
      // Payment successful — activate subscription
      const expiresAt = new Date();
      expiresAt.setMonth(expiresAt.getMonth() + 1); // +1 month
      
      await Promise.all([
        // Update transaction
        supabase.from('transactions').update({
          status: 'paid',
          paid_at: new Date().toISOString(),
        }).eq('order_id', order_id),
        
        // Upgrade user profile
        supabase.from('user_profiles').update({
          subscription_tier: transaction.tier,
          subscription_expires_at: expiresAt.toISOString(),
        }).eq('id', transaction.user_id),
      ]);
      
      console.log(`✅ Payment success: ${order_id} — Tier: ${transaction.tier}`);
    }
  } else if (['deny', 'expire', 'cancel'].includes(transaction_status)) {
    await supabase.from('transactions').update({
      status: transaction_status,
    }).eq('order_id', order_id);
  }
  
  return NextResponse.json({ status: 'ok' });
}
```

---

## Step 3: Transactions Table

`[SUPABASE]`:

```sql
CREATE TABLE public.transactions (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  order_id TEXT UNIQUE NOT NULL,
  tier TEXT NOT NULL CHECK (tier IN ('basic', 'pro')),
  amount NUMERIC(15,2) NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'deny', 'expire', 'cancel')),
  paid_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;

-- Users can see their own transactions
CREATE POLICY "Users see own transactions" ON public.transactions
  FOR SELECT USING (auth.uid() = user_id);
```

---

## Step 4: Freemium Gate Component

`[CURSOR]` — Create: `components/PremiumGate.tsx`

```typescript
// components/PremiumGate.tsx
'use client';

import { useState } from 'react';
import { useUser } from '@/hooks/useUser';

interface PremiumGateProps {
  feature: string;
  requiredTier: 'basic' | 'pro';
  children: React.ReactNode;
  blur?: boolean;
}

export function PremiumGate({ feature, requiredTier, children, blur = true }: PremiumGateProps) {
  const { user, subscriptionTier } = useUser();
  const [showModal, setShowModal] = useState(false);
  
  const hasAccess = subscriptionTier === 'pro' 
    || (requiredTier === 'basic' && ['basic', 'pro'].includes(subscriptionTier));
  
  if (hasAccess) return <>{children}</>;
  
  return (
    <div className="relative">
      {blur && (
        <div className="absolute inset-0 backdrop-blur-sm bg-white/60 z-10 flex items-center justify-center rounded-lg">
          <div className="text-center p-4">
            <div className="text-2xl mb-2">🔒</div>
            <p className="font-semibold text-gray-800">{feature}</p>
            <p className="text-sm text-gray-600 mt-1">Tersedia untuk pengguna {requiredTier === 'basic' ? 'Basic (Rp29K/bulan)' : 'Pro (Rp79K/bulan)'}</p>
            <button
              onClick={() => setShowModal(true)}
              className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
            >
              Upgrade Sekarang
            </button>
          </div>
        </div>
      )}
      <div className={blur ? 'blur-sm pointer-events-none select-none' : ''}>
        {children}
      </div>
      
      {showModal && <UpgradeModal onClose={() => setShowModal(false)} requiredTier={requiredTier} />}
    </div>
  );
}
```

---

## Step 5: TikTok GTM (Month 1–3)

**Content strategy:** 3 video types, 3–5 videos/week

### Type 1: "Ngecek slip gaji kamu" (Tutorial)
Script format:
```
Hook (0-3s): "Slip gajimu ada yang dipotong ini ngga?"
Main (3-25s): Open cekwajar.id/wajar-slip → masukkan gaji → cek hasil → show violation badge
CTA (25-30s): "Link di bio. Gratis, 30 detik aja."
```

### Type 2: "Eh tau ngga?" (Edukasi)
Script format:
```
Hook: "Ternyata kalau gajimu di bawah [UMK kota], perusahaan bisa kena denda."
Edukasi: Brief explanation of regulation
CTA: "Cek gaji kamu wajar ngga di cekwajar.id"
```

### Type 3: "Hasil real user" (Social proof)
```
Hook: "Temen aku cek slip gaji, ternyata PPh21-nya dipotong terlalu banyak."
Story: Brief story of someone who found discrepancy
CTA: "Mau ngecek slip gajimu? Gratis di cekwajar.id"
```

**TikTok posting schedule:**
- Week 1–2 (tool soft launch): 3 videos — focus on Wajar Slip education
- Week 3–4 (public launch): 5 videos/week — mix all 3 types
- Month 2–3: 3 videos/week (sustainable pace)

---

## Step 6: WhatsApp + Community Seeding

`[MANUAL]` — Month 1, Week 1

**Target communities:**
1. r/finansialku (Reddit Indonesia) — financial discussion
2. r/indonesia (Reddit) — general audience
3. Facebook Groups: "HR Indonesia", "Karyawan Indonesia", "Komunitas Finansial Indonesia"
4. LinkedIn: Post personal story about finding payslip discrepancy
5. WhatsApp: "Komunitas Karyawan" groups (join, contribute value first, then share)
6. Twitter/X: Indonesian HR professionals, tax consultants

**Posting script (WhatsApp/Reddit):**
```
Hai semua, saya baru bikin cekwajar.id — tools gratis untuk ngecek apakah gaji + 
potongan di slip gaji kamu sudah sesuai regulasi PPh21 dan BPJS.

Banyak karyawan yang ngga tau kalau ada pemotongan yang kurang atau berlebih. 
Aku sendiri cek dan ketemu perbedaan 150rb/bulan di PPh21.

Gratis, no login required, 30 detik. Link: cekwajar.id/wajar-slip

Ada yang mau coba dan kasih feedback?
```

---

## Step 7: SEO (Long Game)

`[CURSOR]` — Create blog/article pages

Target keywords (Indonesian, high search volume):
```
"cek slip gaji online" — 1,200 searches/month
"kalkulator pph21 2024" — 8,100 searches/month
"bpjs karyawan berapa persen" — 2,400 searches/month
"gaji standar [kota] 2024" — varies by city
"harga tanah [kota] per meter" — high intent
"biaya hidup di [kota] 2024" — varies
"gaji di singapura berapa" — 3,600 searches/month
```

`[CURSOR]` Prompt:
> "Create a static blog page generator in Next.js that takes a city name, year, and tool type as parameters and generates SEO-optimized pages like /blog/umk-jakarta-2024, /blog/biaya-hidup-surabaya-2024, /blog/gaji-software-engineer-bandung. Include structured data (JSON-LD), meta tags, and links to the relevant tool."

---

## Revenue Milestone Gates

| Milestone | Revenue | Action |
|-----------|---------|--------|
| 10 paying users | IDR 290K–790K/mo | Proof of concept. Continue. |
| 50 paying users | IDR 1.5M–4M/mo | Start Midtrans payout setup |
| 100 paying users | IDR 2.9M–7.9M/mo | Upgrade Supabase Pro (IDR 250K/mo) |
| 200 paying users | IDR 5.8M–15.8M/mo | Hire 1 part-time community manager |
| 500 paying users | IDR 14.5M–39.5M/mo | Consider Mercer data purchase, PKP auditor |

---

## Reality Check: Month 3 Revenue Target

| Scenario | Subs | Revenue |
|----------|------|---------|
| Pessimistic | 10 Basic | IDR 290K/mo |
| Base | 30 Basic + 5 Pro | IDR 1,270K/mo |
| Optimistic | 100 Basic + 20 Pro | IDR 4,480K/mo |

**Why pessimistic is likely at Month 3:**
- 200–500 total users → 2–5% conversion = 4–25 paying users
- Indonesian users are price-sensitive: expect 2% conversion, not 10%
- Trust is not yet established — first-time users rarely pay immediately

**Key insight:** At Month 3, the goal is NOT profit. The goal is proof: "At least 1 stranger paid for this." Even IDR 29K from a stranger proves willingness to pay and validates the entire model.
