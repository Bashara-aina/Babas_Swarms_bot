// ==============================================================================
// cekwajar.id — GET /api/abroad/compare
// PPP-based international salary comparison
// Query: currentIDRSalary, targetCountry, [offerSalary], [tier]
// ==============================================================================

import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { createClient } from '@/lib/supabase/server'
import { getWorldBankPPP } from '@/lib/external/worldbank'
import { getExchangeRate } from '@/lib/external/exchangerates'
import { rateLimit } from '@/lib/rate-limit'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

// --- Zod Schema ---------------------------------------------------------------

const QuerySchema = z.object({
  currentIDRSalary: z.coerce.number().int().min(100000),
  targetCountry: z.string().min(2).max(6),
  offerSalary: z.coerce.number().int().min(100000).optional(),
  tier: z.enum(['free', 'basic', 'basic_plus', 'premium']).default('free'),
})

// --- Types --------------------------------------------------------------------

interface PPPResult {
  idSalary: number
  nominalEquivalent: number
  nominalCurrency: string
  userPowerIntlUSD: number
  idPPPFactor: number
  foreignPPPFactor: number
  exchangeRate: number
  offerPowerIntlUSD?: number
  realRatio?: number
  isPPPBetter?: boolean
}

// --- Calculation -------------------------------------------------------------

function calculatePPPComparison(
  idSalary: number,
  idPPPFactor: number,
  foreignPPPFactor: number,
  nominalEquivalent: number,
  exchangeRate: number,
  offerSalary?: number
): PPPResult {
  const userPowerIntlUSD = idSalary / idPPPFactor

  const result: PPPResult = {
    idSalary,
    nominalEquivalent,
    nominalCurrency: '',
    userPowerIntlUSD,
    idPPPFactor,
    foreignPPPFactor,
    exchangeRate,
  }

  if (offerSalary && offerSalary > 0) {
    const offerPowerIntlUSD = offerSalary / foreignPPPFactor
    result.offerPowerIntlUSD = offerPowerIntlUSD
    result.realRatio = offerPowerIntlUSD / userPowerIntlUSD
    result.isPPPBetter = offerPowerIntlUSD > userPowerIntlUSD
  }

  return result
}

// --- Handler ------------------------------------------------------------------

export async function GET(request: NextRequest) {
  const limit = rateLimit(request, 'abroad-compare', {
    limit: 20,
    windowMs: 60 * 1000,
  })
  if (!limit.ok) {
    const retryAfter = Math.max(
      0,
      Math.ceil((limit.resetAt - Date.now()) / 1000),
    )
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'RATE_LIMITED',
          message: 'Terlalu banyak permintaan. Coba lagi sebentar lagi.',
        },
      },
      { status: 429, headers: { 'Retry-After': String(retryAfter) } },
    )
  }

  const searchParams = request.nextUrl.searchParams

  const parsed = QuerySchema.safeParse({
    currentIDRSalary: searchParams.get('currentIDRSalary'),
    targetCountry: searchParams.get('targetCountry'),
    offerSalary: searchParams.get('offerSalary'),
    tier: searchParams.get('tier') ?? 'free',
  })

  if (!parsed.success) {
    return NextResponse.json(
      { error: { code: 'INVALID_PARAMS', message: parsed.error.issues[0].message } },
      { status: 400 }
    )
  }

  const { currentIDRSalary, targetCountry, offerSalary, tier } = parsed.data
  const supabase = await createClient()

  // Check tier gate
  const { data: countryMeta } = await supabase
    .from('ppp_reference')
    .select('country_name, is_free_tier')
    .eq('country_code', targetCountry)
    .single()

  if (!countryMeta) {
    return NextResponse.json(
      { error: { code: 'NOT_FOUND', message: 'Negara tidak ditemukan.' } },
      { status: 404 }
    )
  }

  const isGated = !countryMeta.is_free_tier && tier === 'free'

  if (isGated) {
    return NextResponse.json({
      success: true,
      data: {
        isGated: true,
        countryName: countryMeta.country_name,
        requiresUpgrade: true,
        upgradeUrl: '/upgrade',
      },
    })
  }

  // Fetch Indonesia PPP factor
  const idPPP = await getWorldBankPPP('ID')
  if (!idPPP) {
    return NextResponse.json(
      { error: { code: 'PPP_UNAVAILABLE', message: 'Data PPP Indonesia tidak tersedia.' } },
      { status: 503 }
    )
  }

  // Fetch target country PPP factor
  const foreignPPP = await getWorldBankPPP(targetCountry)
  if (!foreignPPP) {
    return NextResponse.json(
      { error: { code: 'PPP_UNAVAILABLE', message: 'Data PPP negara tujuan tidak tersedia.' } },
      { status: 503 }
    )
  }

  // Get currency code for target country
  const { data: countryInfo } = await supabase
    .from('ppp_reference')
    .select('currency_code, country_name')
    .eq('country_code', targetCountry)
    .single()

  const currencyCode = countryInfo?.currency_code ?? 'USD'
  const countryName = countryInfo?.country_name ?? foreignPPP.countryName

  // Get exchange rate (IDR per unit of foreign currency)
  // Frankfurter uses EUR base, so we get IDR/EUR then compute
  let idrPerForeignUnit = 1

  // Build currency pair for IDR to target
  const idrToTargetRate = await getExchangeRate('IDR', currencyCode)
  if (idrToTargetRate) {
    idrPerForeignUnit = idrToTargetRate
  }

  // Nominal equivalent: IDR salary in foreign currency
  const nominalEquivalent = currentIDRSalary / idrPerForeignUnit

  // Calculate PPP comparison
  const result = calculatePPPComparison(
    currentIDRSalary,
    idPPP.pppFactor,
    foreignPPP.pppFactor,
    nominalEquivalent,
    idrPerForeignUnit,
    offerSalary
  )

  return NextResponse.json({
    success: true,
    data: {
      isGated: false,
      countryName,
      currencyCode,
      idSalary: result.idSalary,
      nominalEquivalent: Math.round(result.nominalEquivalent * 100) / 100,
      nominalCurrency: currencyCode,
      userPowerIntlUSD: Math.round(result.userPowerIntlUSD * 100) / 100,
      idPPPFactor: idPPP.pppFactor,
      foreignPPPFactor: foreignPPP.pppFactor,
      pppYear: Math.max(idPPP.year, foreignPPP.year),
      exchangeRate: Math.round(idrPerForeignUnit * 10000) / 10000,
      offerSalary: offerSalary ?? null,
      offerPowerIntlUSD: result.offerPowerIntlUSD
        ? Math.round(result.offerPowerIntlUSD * 100) / 100
        : null,
      realRatio: result.realRatio
        ? Math.round(result.realRatio * 100) / 100
        : null,
      isPPPBetter: result.isPPPBetter ?? null,
      disclaimer:
        'PPP adalah ukuran ekonometrik. Perbandingan berguna sebagai referensi umum, bukan konsultasi keuangan resmi.',
    },
  })
}