// ==============================================================================
// cekwajar.id — Payment transaction creation
// POST /api/payment/create-transaction
// ==============================================================================

import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

// --- Pricing ---------------------------------------------------------------

const PRICING = {
  basic: {
    monthly: 29000,
    annual: 278400, // 29k × 12 × 0.80
  },
  pro: {
    monthly: 79000,
    annual: 758400, // 79k × 12 × 0.80
  },
} as const

// --- Zod Schema ---------------------------------------------------------------

const BodySchema = z.object({
  plan: z.enum(['basic', 'pro']),
  billingPeriod: z.enum(['monthly', 'annual']),
})

type Plan = 'basic' | 'pro'
type Period = 'monthly' | 'annual'

// --- Handler ----------------------------------------------------------------

export async function POST(request: NextRequest) {
  // Auth check
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return NextResponse.json({ error: { code: 'UNAUTHORIZED', message: 'Login diperlukan.' } }, { status: 401 })
  }

  let body: z.infer<typeof BodySchema>
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: { code: 'INVALID_JSON', message: 'JSON tidak valid.' } }, { status: 400 })
  }

  const parsed = BodySchema.safeParse(body)
  if (!parsed.success) {
    return NextResponse.json(
      { error: { code: 'INVALID_PARAMS', message: parsed.error.issues[0].message } },
      { status: 400 }
    )
  }

  const { plan, billingPeriod } = parsed.data
  const grossAmount = PRICING[plan][billingPeriod]

  // Generate order ID
  const orderId = `CW-${user.id.slice(0, 8)}-${Date.now()}-${plan}-${billingPeriod}`

  // Store pending transaction in DB
  const { error: insertError } = await supabase.from('transactions').insert({
    user_id: user.id,
    midtrans_order_id: orderId,
    plan_type: plan,
    billing_period: billingPeriod,
    gross_amount: grossAmount,
    status: 'pending',
  })

  if (insertError) {
    console.error('Failed to insert transaction:', insertError)
    return NextResponse.json(
      { error: { code: 'DB_ERROR', message: 'Gagal menyimpan transaksi.' } },
      { status: 500 }
    )
  }

  // Call Midtrans Snap API
  const serverKey = process.env.MIDTRANS_SERVER_KEY!
  const isProduction = process.env.MIDTRANS_IS_PRODUCTION === 'true'
  const snapBaseUrl = isProduction
    ? 'https://app.midtrans.com/snap/v1/transactions'
    : 'https://app.sandbox.midtrans.com/snap/v1/transactions'

  const authString = Buffer.from(`${serverKey}:`).toString('base64')

  const billingLabel = billingPeriod === 'monthly' ? '1 bulan' : '12 bulan'

  let snapToken: string
  try {
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
          name: `cekwajar.id ${plan.charAt(0).toUpperCase() + plan.slice(1)} — ${billingLabel}`,
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

    if (!snapResponse.ok || !snapData.token) {
      console.error('Midtrans error:', snapData)
      return NextResponse.json(
        { error: { code: 'MIDTRANS_ERROR', message: snapData.error_message ?? 'Gagal membuat transaksi.' } },
        { status: 502 }
      )
    }

    snapToken = snapData.token
  } catch (err) {
    console.error('Midtrans fetch failed:', err)
    return NextResponse.json(
      { error: { code: 'MIDTRANS_ERROR', message: 'Tidak dapat terhubung ke Midtrans.' } },
      { status: 502 }
    )
  }

  return NextResponse.json({
    success: true,
    data: { snapToken, orderId },
  })
}