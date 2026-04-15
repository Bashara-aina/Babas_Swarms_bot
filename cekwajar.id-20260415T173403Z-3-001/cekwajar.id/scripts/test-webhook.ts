// ==============================================================================
// cekwajar.id — Midtrans Webhook Test Script
// Usage: npx ts-node scripts/test-webhook.ts
// ==============================================================================

import crypto from 'crypto'

const SERVER_KEY = process.env.MIDTRANS_SERVER_KEY ?? 'your-server-key-here'
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

const TARGET = process.env.WEBHOOK_URL ?? 'http://localhost:3000/api/webhooks/midtrans'

console.log('🧪 Sending test webhook to:', TARGET)
console.log('📦 Payload:', JSON.stringify(payload, null, 2))

fetch(TARGET, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload),
})
  .then(r => r.json())
  .then(data => {
    console.log('✅ Response:', JSON.stringify(data, null, 2))
  })
  .catch(err => {
    console.error('❌ Error:', err)
  })
