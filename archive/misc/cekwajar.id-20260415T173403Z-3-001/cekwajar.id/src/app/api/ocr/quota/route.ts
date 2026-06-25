// ==============================================================================
// cekwajar.id ? GET /api/ocr/quota
// Returns current month's OCR usage and which OCR source is available
// ==============================================================================

import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

const VISION_MONTHLY_LIMIT = 950

export async function GET() {
  const supabase = await createClient()

  const { data: counter } = await supabase
    .from('ocr_quota_counter')
    .select('month_count, updated_at')
    .eq('month_key', getCurrentMonthKey())
    .single()

  const monthlyCount = counter?.month_count ?? 0
  const isQuotaAvailable = monthlyCount < VISION_MONTHLY_LIMIT

  return NextResponse.json({
    monthlyCount,
    limit: VISION_MONTHLY_LIMIT,
    isQuotaAvailable,
    source: isQuotaAvailable ? 'google_vision' : 'tesseract',
  })
}

function getCurrentMonthKey(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}