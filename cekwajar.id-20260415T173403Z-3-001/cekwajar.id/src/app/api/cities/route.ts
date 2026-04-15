// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — GET /api/cities
// Returns all cities from umk_2026 table for dropdown population
// ══════════════════════════════════════════════════════════════════════════════

import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET() {
  const supabase = await createClient()

  const { data, error } = await supabase
    .from('umk_2026')
    .select('city, province, monthly_minimum_idr as umk')
    .order('province')
    .order('city')

  if (error) {
    return NextResponse.json({ error: 'Failed to fetch cities' }, { status: 500 })
  }

  return NextResponse.json(
    { cities: data ?? [] },
    {
      headers: {
        'Cache-Control': 'public, max-age=86400, stale-while-revalidate=3600',
      },
    }
  )
}
