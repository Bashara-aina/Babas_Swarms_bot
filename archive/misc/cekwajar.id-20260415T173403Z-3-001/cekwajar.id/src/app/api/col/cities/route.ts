// ==============================================================================
// cekwajar.id — GET /api/col/cities
// Returns all cities from col_indices
// ==============================================================================

import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET() {
  const supabase = await createClient()

  const { data: cities, error } = await supabase
    .from('col_indices')
    .select('city_code, city_name, province, col_index')
    .order('col_index', { ascending: false })

  if (error) {
    return NextResponse.json(
      { error: { code: 'DB_ERROR', message: 'Gagal mengambil data kota.' } },
      { status: 500 }
    )
  }

  return NextResponse.json({
    success: true,
    data: { cities: cities ?? [] },
  })
}