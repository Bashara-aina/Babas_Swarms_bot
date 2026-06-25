import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export const revalidate = 300 // cache 5 minutes

export async function GET() {
  try {
    const supabase = await createClient()
    const since = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()

    const { count: slipCount } = await supabase
      .from('payslip_audits')
      .select('*', { count: 'exact', head: true })
      .gte('created_at', since)

    const { count: gajiCount } = await supabase
      .from('salary_queries')
      .select('*', { count: 'exact', head: true })
      .gte('created_at', since)

    const total = (slipCount ?? 0) + (gajiCount ?? 0)

    return NextResponse.json(
      { count: total },
      { headers: { 'Cache-Control': 's-maxage=300, stale-while-revalidate=60' } }
    )
  } catch {
    return NextResponse.json({ count: 0 })
  }
}
