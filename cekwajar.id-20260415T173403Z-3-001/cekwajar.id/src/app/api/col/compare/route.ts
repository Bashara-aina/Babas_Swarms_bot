// ==============================================================================
// cekwajar.id — GET /api/col/compare
// Cost of Living city comparison
// Query: fromCity, toCity, currentSalary, lifestyleTier
// ==============================================================================

import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

// --- Zod Schema ---------------------------------------------------------------

const QuerySchema = z.object({
  fromCity: z.string().min(1),
  toCity: z.string().min(1),
  currentSalary: z.coerce.number().int().min(500000),
  lifestyleTier: z.enum(['HEMAT', 'STANDAR', 'NYAMAN']),
})

// --- Types --------------------------------------------------------------------

type COLVerdict = 'LEBIH_MURAH' | 'SAMA' | 'LEBIH_MAHAL'

interface COLResult {
  fromCOLIndex: number
  toCOLIndex: number
  adjustmentRatio: number
  requiredSalary: number
  salaryDifference: number
  percentChange: number
  verdict: COLVerdict
  verdictMessage: string
  categoryBreakdown?: {
    category: string
    fromAmount: number
    toAmount: number
    difference: number
  }[]
}

// --- Calculation -------------------------------------------------------------

function buildVerdictMessage(verdict: COLVerdict, percentChange: number, toCity: string): string {
  const absPct = Math.abs(Math.round(percentChange))
  if (verdict === 'LEBIH_MURAH') {
    return `Dengan gaya hidup yang sama, kamu butuh ${absPct}% lebih sedikit untuk hidup di ${toCity}.`
  }
  if (verdict === 'LEBIH_MAHAL') {
    return `Kamu butuh ${absPct}% lebih banyak untuk gaya hidup yang sama di ${toCity}.`
  }
  return `Biaya hidup di kedua kota relatif setara.`
}

function calculateCOLAdjustment(
  currentSalary: number,
  fromIndex: number,
  toIndex: number,
  lifestyleTier: string
): COLResult {
  const LIFESTYLE_MULTIPLIER: Record<string, number> = {
    HEMAT: 0.70,
    STANDAR: 1.00,
    NYAMAN: 1.30,
  }

  const baseRatio = toIndex / fromIndex
  const mult = LIFESTYLE_MULTIPLIER[lifestyleTier] ?? 1.0

  // Adjusted ratio: 1 + (distance from 1) × multiplier
  const adjustedRatio = 1 + (baseRatio - 1) * mult
  const requiredSalary = Math.round(currentSalary * adjustedRatio)
  const difference = requiredSalary - currentSalary
  const percentChange = (adjustedRatio - 1) * 100

  const verdict: COLVerdict =
    difference < -100_000 ? 'LEBIH_MURAH' :
    difference > 100_000 ? 'LEBIH_MAHAL' : 'SAMA'

  return {
    fromCOLIndex: fromIndex,
    toCOLIndex: toIndex,
    adjustmentRatio: Math.round(adjustedRatio * 1000) / 1000,
    requiredSalary,
    salaryDifference: difference,
    percentChange: Math.round(percentChange * 10) / 10,
    verdict,
    verdictMessage: '',
  }
}

// --- Handler ------------------------------------------------------------------

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams

  const parsed = QuerySchema.safeParse({
    fromCity: searchParams.get('fromCity'),
    toCity: searchParams.get('toCity'),
    currentSalary: searchParams.get('currentSalary'),
    lifestyleTier: searchParams.get('lifestyleTier'),
  })

  if (!parsed.success) {
    return NextResponse.json(
      { error: { code: 'INVALID_PARAMS', message: parsed.error.issues[0].message } },
      { status: 400 }
    )
  }

  const { fromCity, toCity, currentSalary, lifestyleTier } = parsed.data

  if (fromCity === toCity) {
    return NextResponse.json(
      {
        error: {
          code: 'SAME_CITY_ERROR',
          message: 'Kota asal dan tujuan tidak boleh sama.',
        },
      },
      { status: 400 }
    )
  }

  const supabase = await createClient()

  // Fetch both cities
  const [{ data: fromData }, { data: toData }] = await Promise.all([
    supabase.from('col_indices').select('city_name, col_index').eq('city_code', fromCity).single(),
    supabase.from('col_indices').select('city_name, col_index').eq('city_code', toCity).single(),
  ])

  if (!fromData || !toData) {
    return NextResponse.json(
      { error: { code: 'NOT_FOUND', message: 'Data kota tidak ditemukan.' } },
      { status: 404 }
    )
  }

  const fromIndex = Number(fromData.col_index)
  const toIndex = Number(toData.col_index)

  const result = calculateCOLAdjustment(currentSalary, fromIndex, toIndex, lifestyleTier)
  result.verdictMessage = buildVerdictMessage(result.verdict, result.percentChange, toData.city_name)

  // Fetch category breakdown for Basic+ tier
  const { data: categories } = await supabase
    .from('col_categories')
    .select('category_code, label_id, hemat_weight, standar_weight, nyaman_weight')
    .order('category_code')

  const weightKey = `${lifestyleTier.toLowerCase()}_weight` as 'hemat_weight' | 'standar_weight' | 'nyaman_weight'

  const categoryBreakdown = (categories ?? []).map((cat) => {
    const weight = Number(cat[weightKey]) ?? 0.25
    const fromAmount = Math.round(currentSalary * weight)
    const toAmount = Math.round(fromAmount * (toIndex / fromIndex))
    return {
      category: cat.label_id,
      fromAmount,
      toAmount,
      difference: toAmount - fromAmount,
    }
  })

  return NextResponse.json({
    success: true,
    data: {
      fromCity: fromData.city_name,
      toCity: toData.city_name,
      fromCOLIndex: result.fromCOLIndex,
      toCOLIndex: result.toCOLIndex,
      adjustmentRatio: result.adjustmentRatio,
      requiredSalary: result.requiredSalary,
      salaryDifference: result.salaryDifference,
      percentChange: result.percentChange,
      verdict: result.verdict,
      verdictMessage: result.verdictMessage,
      categoryBreakdown,
    },
  })
}