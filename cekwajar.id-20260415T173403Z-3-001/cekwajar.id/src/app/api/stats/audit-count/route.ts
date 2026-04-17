import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export const revalidate = 300 // cache 5 minutes

export async function GET() {
  try {
    const supabase = await createClient()
    const { count } = await supabase
      .from('payslip_audits')
      .select('*', { count: 'exact', head: true })
      .gte('created_at', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString())

    return NextResponse.json({ count: count ?? 0 })
  } catch {
    return NextResponse.json({ count: 0 })
  }
}
