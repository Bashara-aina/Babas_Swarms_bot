// ==============================================================================
// cekwajar.id — Midtrans Webhook Handler
// POST /api/webhooks/midtrans
// CRITICAL: Uses service_role client. Signature verification before any DB action.
// ==============================================================================

import crypto from 'crypto'
import { NextResponse } from 'next/server'
import { getServiceClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

interface MidtransWebhookPayload {
  order_id: string
  status_code: string
  gross_amount: string
  signature_key?: string
  transaction_status: 'settlement' | 'pending' | 'expire' | 'cancel' | 'deny'
  fraud_status?: 'accept' | 'challenge' | 'deny'
  payment_type?: string
  [key: string]: unknown
}

async function sendConfirmationEmail(
  userId: string,
  plan: string,
  amount: number,
  orderId: string
): Promise<void> {
  const resendApiKey = process.env.RESEND_API_KEY
  if (!resendApiKey) return

  const serviceClient = await getServiceClient()
  const { data } = await serviceClient.auth.admin.getUserById(userId)
  const email = data?.user?.email

  if (!email) return

  try {
    const { Resend } = await import('resend')
    const resend = new Resend(resendApiKey)

    await resend.emails.send({
      from: 'cekwajar.id <noreply@cekwajar.id>',
      to: email,
      subject: `Berhasil! Langganan ${plan} aktif — cekwajar.id`,
      html: `
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #059669;">Terima kasih telah berlangganan!</h2>
          <p>Paket <strong>${plan.toUpperCase()}</strong> kamu kini aktif.</p>
          <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
          <table style="width: 100%; border-collapse: collapse;">
            <tr>
              <td style="padding: 8px 0; color: #64748b;">Order ID</td>
              <td style="padding: 8px 0; font-weight: 600;">${orderId}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #64748b;">Jumlah</td>
              <td style="padding: 8px 0; font-weight: 600;">Rp ${amount.toLocaleString('id-ID')}</td>
            </tr>
          </table>
          <a href="https://cekwajar.id/dashboard"
             style="display: inline-block; margin-top: 24px; padding: 12px 24px;
                    background: #059669; color: white; text-decoration: none;
                    border-radius: 8px; font-weight: 600;">
            Mulai Gunakan Fitur Premium →
          </a>
        </div>
      `,
    })
  } catch (err) {
    console.error('Failed to send confirmation email:', err)
  }
}

async function activateSubscription(
  tx: { id: string; user_id: string },
  payload: MidtransWebhookPayload,
  serviceClient: Awaited<ReturnType<typeof getServiceClient>>
): Promise<void> {
  const parts = payload.order_id.split('-')
  const period = parts[parts.length - 1]   // 'monthly' | 'annual'
  const plan = parts[parts.length - 2]    // 'basic' | 'pro'

  const durationDays = period === 'annual' ? 366 : 32
  const endsAt = new Date(Date.now() + durationDays * 24 * 60 * 60 * 1000)

  // Upsert subscription
  await serviceClient.from('subscriptions').upsert({
    user_id: tx.user_id,
    plan_type: plan,
    status: 'active',
    starts_at: new Date().toISOString(),
    ends_at: endsAt.toISOString(),
    last_payment_order_id: payload.order_id,
  }, { onConflict: 'user_id' })

  // Update user profile tier
  await serviceClient.from('user_profiles').update({
    subscription_tier: plan,
    updated_at: new Date().toISOString(),
  }).eq('id', tx.user_id)

  // Send confirmation email (non-blocking)
  sendConfirmationEmail(
    tx.user_id,
    plan,
    parseInt(payload.gross_amount, 10),
    payload.order_id
  ).catch(err => console.error('Email send failed:', err))
}

export async function POST(request: Request) {
  let body: MidtransWebhookPayload
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  // 1. SIGNATURE VERIFICATION
  const serverKey = process.env.MIDTRANS_SERVER_KEY
  if (!serverKey) {
    console.error('MIDTRANS_SERVER_KEY not configured')
    return NextResponse.json({ error: 'Server misconfigured' }, { status: 500 })
  }

  const signatureKey = body.signature_key ?? ''
  const expectedSignature = crypto
    .createHash('sha512')
    .update(body.order_id + body.status_code + body.gross_amount + serverKey)
    .digest('hex')

  let isValid = false
  try {
    isValid = crypto.timingSafeEqual(
      Buffer.from(signatureKey),
      Buffer.from(expectedSignature)
    )
  } catch {
    isValid = false
  }

  if (!isValid) {
    console.error('Invalid Midtrans signature', {
      orderId: body.order_id,
      received: signatureKey.slice(0, 16) + '...',
    })
    return NextResponse.json({ error: 'Invalid signature' }, { status: 401 })
  }

  // 2. Find transaction in DB
  const serviceClient = await getServiceClient()
  const { data: tx } = await serviceClient
    .from('transactions')
    .select('id, user_id, gross_amount, is_webhook_processed')
    .eq('midtrans_order_id', body.order_id)
    .single()

  if (!tx) {
    return NextResponse.json({ error: 'Unknown order' }, { status: 404 })
  }

  // 3. Verify amount matches (prevent amount tampering)
  if (tx.gross_amount !== parseInt(body.gross_amount, 10)) {
    console.error('Amount mismatch', {
      expected: tx.gross_amount,
      received: body.gross_amount,
    })
    return NextResponse.json({ error: 'Amount mismatch' }, { status: 400 })
  }

  // 4. Idempotency check — skip if already processed as settlement
  if (tx.is_webhook_processed && body.transaction_status === 'settlement') {
    return NextResponse.json({ status: 'already_processed' })
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
    midtrans_payload: body as Record<string, unknown>,
    is_webhook_processed: isActivation || tx.is_webhook_processed,
    webhook_received_at: new Date().toISOString(),
  }).eq('id', tx.id)

  return NextResponse.json({ status: 'ok' })
}
