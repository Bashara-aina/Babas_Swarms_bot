// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Health Check API
// GET /api/health — Returns comprehensive service health status
// ══════════════════════════════════════════════════════════════════════════════

import { NextResponse } from 'next/server'
import { createClient, getServiceClient } from '@/lib/supabase/server'

export async function GET() {
  try {
    const supabase = await createClient()

    // Ping Supabase
    const { error: dbError } = await supabase
      .from('user_profiles')
      .select('id')
      .limit(1)
      .maybeSingle()

    if (dbError && dbError.code !== 'PGRST116') {
      console.error('Health check DB error:', dbError)
      return NextResponse.json(
        {
          status: 'error',
          timestamp: new Date().toISOString(),
          checks: {
            database: 'error',
            midtrans: process.env.MIDTRANS_IS_PRODUCTION === 'true' ? 'production' : 'sandbox',
            googleVision: !!process.env.GOOGLE_VISION_API_KEY ? 'ok' : 'error',
            ocrQuota: { monthCount: 0, isOk: false },
          },
          error: dbError.message,
        },
        { status: 500 }
      )
    }

    // Check OCR quota for current month
    const now = new Date()
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0]
    let ocrCount = 0
    try {
      const serviceClient = await getServiceClient()
      const { count } = await serviceClient
        .from('ocr_quota_counter')
        .select('*', { count: 'exact', head: true })
        .gte('period_start', monthStart)
      ocrCount = count ?? 0
    } catch {
      // Non-critical — default to OK
    }

    const isProduction = process.env.MIDTRANS_IS_PRODUCTION === 'true'
    const midtransStatus = isProduction ? 'production' : 'sandbox'

    return NextResponse.json({
      status: 'ok',
      timestamp: new Date().toISOString(),
      checks: {
        database: 'ok',
        midtrans: midtransStatus,
        googleVision: !!process.env.GOOGLE_VISION_API_KEY ? 'ok' : 'error',
        ocrQuota: {
          monthCount: ocrCount,
          isOk: true, // threshold is per-user, not global
        },
      },
    })
  } catch (err) {
    console.error('Health check error:', err)
    return NextResponse.json(
      {
        status: 'error',
        timestamp: new Date().toISOString(),
        checks: {
          database: 'error',
          midtrans: process.env.MIDTRANS_IS_PRODUCTION === 'true' ? 'production' : 'sandbox',
          googleVision: !!process.env.GOOGLE_VISION_API_KEY ? 'ok' : 'error',
          ocrQuota: { monthCount: 0, isOk: false },
        },
        error: String(err),
      },
      { status: 500 }
    )
  }
}
