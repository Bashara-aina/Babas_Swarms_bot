---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/engineering/087-midtrans-integration.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:01.721751"
}
---

---
source_id: 087
title: "Midtrans Integration Production Webhook Handler"
source_type: ENGINEERING
authority: INDUSTRY
url: "https://docs.midtrans.com/docs/https-notification-webhooks"
last_verified: "2026-04-11"
tags: [midtrans, webhook, payment, integration, nextjs, verification]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# Midtrans Integration Production Webhook Handler

## Why This Matters for cekwajar.id
cekwajar.id processes subscription payments for payroll SaaS plans. The Midtrans webhook is the **single source of truth** for payment status updates. A broken webhook handler means:
- Subscriptions not activated
- Users lose access unexpectedly
- Revenue recognition errors
- Potential UU PDP violation if payment receipts aren't stored properly

## Core Knowledge

### Webhook Flow
1. Customer completes payment on Midtrans
2. Midtrans sends HTTP POST to your notification URL
3. Your server validates and processes the notification
4. You update subscription status in database
5. Return 200 OK to Midtrans

### Critical Webhook Fields

| Field | Description |
|-------|-------------|
| `order_id` | Your unique order identifier |
| `transaction_status` | `capture`, `settlement`, `pending`, `deny`, `cancel`, `expire`, `refund` |
| `status_code` | 200 = success |
| `transaction_id` | Midtrans transaction ID |
| `gross_amount` | Amount in IDR |
| `signature_key` | SHA512(ORDER_ID + STATUS_CODE + GROSS_AMOUNT + SERVER_KEY) |

### Transaction Status Cycle

```
pending → settlement  (payment success)
       → deny         (payment rejected)
       → expire       (payment timeout)
       → cancel       (merchant/admin cancel)

capture → settlement   (capture completed, typical for credit card)
       → refund        (full or partial refund)
```

### Signature Verification (CRITICAL)
```typescript
// app/api/webhooks/midtrans/route.ts
import { createHmac, createHash } from 'crypto';
import { NextResponse } from 'next/server';

const MIDTRANS_SERVER_KEY = process.env.MIDTRANS_SERVER_KEY;

function verifySignature(
  orderId: string,
  statusCode: string,
  grossAmount: string,
  signatureKey: string
): boolean {
  const data = orderId + statusCode + grossAmount;
  const expectedSignature = createHmac('sha512', MIDTRANS_SERVER_KEY!)
    .update(data)
    .digest('hex');
  
  return expectedSignature === signatureKey;
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const {
      order_id,
      status_code,
      gross_amount,
      signature_key,
      transaction_status,
      payment_type,
      transaction_id,
    } = body;
    
    // 1. Verify signature
    if (!verifySignature(order_id, status_code, gross_amount, signature_key)) {
      console.error('Invalid signature for order:', order_id);
      return NextResponse.json({ error: 'Invalid signature' }, { status: 401 });
    }
    
    // 2. Handle transaction status
    switch (transaction_status) {
      case 'settlement':
      case 'capture':
        await activateSubscription(order_id, transaction_id);
        break;
      case 'pending':
        // Log but don't activate
        break;
      case 'deny':
      case 'cancel':
      case 'expire':
        await deactivateSubscription(order_id);
        break;
      case 'refund':
        await handleRefund(order_id);
        break;
    }
    
    return NextResponse.json({ status: 'ok' });
  } catch (error) {
    console.error('Webhook error:', error);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

### Production Next.js Webhook Handler
```typescript
// app/api/webhooks/midtrans/route.ts
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

async function activateSubscription(orderId: string, transactionId: string) {
  const cookieStore = await cookies();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!, // Use service key for admin ops
    {
      cookies: {
        getAll: () => cookieStore.getAll(),
      },
    }
  );
  
  // Parse order_id: format "sub_<user_id>_<timestamp>"
  const parts = orderId.split('_');
  const userId = parts[1];
  
  // Update subscription
  const { error } = await supabase
    .from('subscriptions')
    .update({
      status: 'active',
      midtrans_transaction_id: transactionId,
      activated_at: new Date().toISOString(),
    })
    .eq('user_id', userId);
    
  if (error) {
    console.error('Failed to activate subscription:', error);
    throw error;
  }
}
```

### Idempotency Pattern
```typescript
// Store transaction_id to prevent duplicate processing
const { data: existing } = await supabase
  .from('payment_events')
  .select('id')
  .eq('midtrans_transaction_id', transaction_id)
  .single();

if (existing) {
  // Already processed, return success
  return NextResponse.json({ status: 'already_processed' });
}

// Process and store
await supabase.from('payment_events').insert({
  midtrans_transaction_id: transaction_id,
  order_id,
  transaction_status,
  processed_at: new Date().toISOString(),
});
```

### Notification URL Configuration
Configure in Midtrans MAP Dashboard:
1. Login to MAP: https://dashboard.midtrans.com
2. Go to **SETTINGS > CONFIGURATION**
3. Set **Payment Notification URL**: `https://yourdomain.com/api/webhooks/midtrans`
4. Must be publicly accessible (not localhost)

### Test with Ngrok Locally
```bash
# Terminal 1
ngrok http 3000

# Use the ngrok URL in MAP dashboard for testing
# https://abc123.ngrok.io/api/webhooks/midtrans
```

## Edge Cases and Common Mistakes

### Common Mistakes
1. **No signature verification**: Accept any request (security hole)
2. **localhost URLs**: Midtrans cannot send to localhost
3. **Missing HTTPS**: Use `https://` in production
4. **Wrong Server Key**: Use Server Key (backend), not Client Key (frontend)
5. **Not returning 200**: Midtrans will retry for up to 24 hours
6. **Duplicate processing**: No idempotency check

### Signature Verification Gotchas
- Always use Server Key (not Client Key)
- `gross_amount` must match exactly including decimals
- SHA512 output is hex-encoded

## cekwajar.id Implementation Notes

- **File to update**: `app/api/webhooks/midtrans/route.ts`
- **Function to modify/create**: `verifySignature()`, `activateSubscription()`, idempotency check
- **Data source to query**: `subscriptions` table, `payment_events` table
- **Update frequency**: Per transaction
- **Legion action**: Can implement webhook handler, needs Bashara for production testing

## Monetization Angle
Reliable payment webhook handling ensures:
- Immediate subscription activation → faster time-to-value for customers
- Accurate revenue recognition
- Reduced Churn (no users stuck on "pending" status)
- Enables premium plan revenue

## Sources and Cross-References
- Official URL: https://docs.midtrans.com/docs/https-notification-webhooks
- Midtrans API Reference: https://docs.midtrans.com/reference/http-notification-webhooks
- Transaction Status Cycle: https://docs.midtrans.com/docs/transaction-status-cycle
