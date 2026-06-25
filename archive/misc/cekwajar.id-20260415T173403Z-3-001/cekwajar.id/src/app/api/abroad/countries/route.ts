// ==============================================================================
// cekwajar.id — GET /api/abroad/countries
// Returns all countries from ppp_reference with free tier flags
// ==============================================================================

import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET() {
  const supabase = await createClient()

  const { data: countries, error } = await supabase
    .from('ppp_reference')
    .select('country_code, country_name, currency_code, flag_emoji, is_free_tier')
    .order('display_order')

  if (error) {
    return NextResponse.json(
      { error: { code: 'DB_ERROR', message: 'Gagal mengambil data negara.' } },
      { status: 500 }
    )
  }

  return NextResponse.json({
    success: true,
    data: { countries: countries ?? [] },
  })
}