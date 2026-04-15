// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Health Check API
// GET /api/health — Returns service health status
// ══════════════════════════════════════════════════════════════════════════════

import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

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
      // PGRST116 = table exists but no rows — that's fine
      console.error('Health check DB error:', dbError)
      return NextResponse.json(
        {
          status: 'error',
          supabase: 'error',
          error: dbError.message,
          timestamp: new Date().toISOString(),
        },
        { status: 500 }
      )
    }

    return NextResponse.json({
      status: 'ok',
      supabase: 'connected',
      timestamp: new Date().toISOString(),
    })
  } catch (err) {
    console.error('Health check error:', err)
    return NextResponse.json(
      {
        status: 'error',
        supabase: 'error',
        error: String(err),
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    )
  }
}
