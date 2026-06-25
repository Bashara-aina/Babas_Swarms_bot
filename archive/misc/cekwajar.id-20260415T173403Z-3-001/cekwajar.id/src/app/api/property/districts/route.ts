// ==============================================================================
// cekwajar.id — GET /api/property/districts
// Returns unique districts for a province+city combination
// Query params: province, city
// ==============================================================================

import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

// --- Zod Schema ---------------------------------------------------------------

const QuerySchema = z.object({
  province: z.string().min(1),
  city: z.string().min(1),
})

// --- Handler ------------------------------------------------------------------

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams

  const parsed = QuerySchema.safeParse({
    province: searchParams.get('province'),
    city: searchParams.get('city'),
  })

  if (!parsed.success) {
    return NextResponse.json(
      { error: { code: 'INVALID_PARAMS', message: parsed.error.issues[0].message } },
      { status: 400 }
    )
  }

  const { province, city } = parsed.data
  const supabase = await createClient()

  const { data: districts, error } = await supabase
    .from('property_benchmarks')
    .select('district')
    .eq('province', province)
    .eq('city', city)
    .eq('is_outlier', false)
    .not('district', 'is', null)
    .order('district')

  if (error) {
    return NextResponse.json(
      { error: { code: 'DB_ERROR', message: 'Gagal mengambil data kecamatan.' } },
      { status: 500 }
    )
  }

  // Dedupe
  const unique = [...new Set(districts.map((d) => d.district))]

  return NextResponse.json({
    success: true,
    data: {
      districts: unique,
      count: unique.length,
    },
  })
}