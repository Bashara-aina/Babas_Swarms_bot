// ==============================================================================
// cekwajar.id — GET /api/property/benchmark
// Property price benchmark with IQR-based verdict
// Query params: province, city, district, propertyType, landAreaSqm, askingPriceTotal
// ==============================================================================

import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

// --- Types --------------------------------------------------------------------

export type PropertyVerdict = 'MURAH' | 'WAJAR' | 'MAHAL' | 'SANGAT_MAHAL'
type SizeBand = 'KECIL' | 'SEDANG' | 'BESAR' | 'SANGAT_BESAR'

// --- Zod Schema ---------------------------------------------------------------

const QuerySchema = z.object({
  province: z.string().min(1),
  city: z.string().min(1),
  district: z.string().min(1),
  propertyType: z.enum(['RUMAH', 'TANAH', 'APARTEMEN', 'RUKO']),
  landAreaSqm: z.coerce.number().int().min(1).max(100000),
  askingPriceTotal: z.coerce.number().int().min(1),
})

type QueryParams = z.infer<typeof QuerySchema>

// --- Verdict Calculation ------------------------------------------------------

function estimatePercentile(
  askingPerSqm: number,
  p25: number,
  p50: number,
  p75: number
): number {
  if (askingPerSqm <= p25) {
    if (p25 === 0) return 10
    const ratio = askingPerSqm / p25
    return Math.max(5, Math.round(ratio * 25))
  }
  if (askingPerSqm <= p50) {
    const ratio = (askingPerSqm - p25) / (p50 - p25)
    return Math.round(25 + ratio * 25)
  }
  if (askingPerSqm <= p75) {
    const ratio = (askingPerSqm - p50) / (p75 - p50)
    return Math.round(50 + ratio * 25)
  }
  const ratio = (askingPerSqm - p75) / (p75 - p50 + 1)
  return Math.min(99, Math.round(75 + ratio * 20))
}

export function calculatePropertyVerdict(
  askingPricePerSqm: number,
  p25: number,
  p50: number,
  p75: number
): { verdict: PropertyVerdict; percentileEstimate: number; message: string } {
  const iqr = p75 - p25

  if (askingPricePerSqm < p25 - 0.5 * iqr) {
    return {
      verdict: 'MURAH',
      percentileEstimate: estimatePercentile(askingPricePerSqm, p25, p50, p75),
      message: 'Harga di bawah rata-rata pasar. Pastikan kondisi properti baik.',
    }
  }
  if (askingPricePerSqm <= p75) {
    return {
      verdict: 'WAJAR',
      percentileEstimate: estimatePercentile(askingPricePerSqm, p25, p50, p75),
      message: 'Harga sesuai dengan kisaran pasar area ini.',
    }
  }
  if (askingPricePerSqm <= p75 + 1.5 * iqr) {
    return {
      verdict: 'MAHAL',
      percentileEstimate: estimatePercentile(askingPricePerSqm, p25, p50, p75),
      message: 'Harga di atas median pasar. Ada ruang untuk negosiasi.',
    }
  }
  return {
    verdict: 'SANGAT_MAHAL',
    percentileEstimate: Math.min(99, 90),
    message: 'Harga jauh di atas pasar. Negosiasi agresif direkomendasikan.',
  }
}

// --- KJPP Disclaimer ----------------------------------------------------------

export const KJPP_DISCLAIMER =
  'Data ini bersumber dari listing properti publik dan bukan merupakan penilaian resmi dari Kantor Jasa Penilai Publik (KJPP). Untuk transaksi di atas Rp 500 juta, kami sarankan menggunakan jasa KJPP bersertifikat. cekwajar.id tidak bertanggung jawab atas kerugian dari keputusan properti berdasarkan data ini.'

// --- Size Band ----------------------------------------------------------------

function getSizeBand(landAreaSqm: number): SizeBand {
  if (landAreaSqm <= 50) return 'KECIL'
  if (landAreaSqm <= 100) return 'SEDANG'
  if (landAreaSqm <= 200) return 'BESAR'
  return 'SANGAT_BESAR'
}

// --- Get Benchmark Data ------------------------------------------------------

interface BenchmarkResult {
  hasData: boolean
  p25: number | null
  p50: number | null
  p75: number | null
  sampleCount: number
  freshness: string | null
  dataTier: 'DISTRICT' | 'CITY' | 'NONE'
}

async function getBenchmarkData(
  province: string,
  city: string,
  district: string,
  propertyType: string,
  landAreaSqm: number,
  supabase: Awaited<ReturnType<typeof createClient>>
): Promise<BenchmarkResult> {
  const sizeBand = getSizeBand(landAreaSqm)

  // Try district-level first
  const { data: districtData } = await supabase.rpc('get_property_benchmark_stats', {
    p_province: province,
    p_city: city,
    p_district: district,
    p_property_type: propertyType,
    p_size_band: sizeBand,
  })

  if (districtData && districtData.sample_count >= 5) {
    return {
      hasData: true,
      p25: districtData.p25,
      p50: districtData.p50,
      p75: districtData.p75,
      sampleCount: districtData.sample_count,
      freshness: districtData.freshness,
      dataTier: 'DISTRICT',
    }
  }

  // Fall back to city-level
  const { data: cityData } = await supabase
    .from('property_benchmarks')
    .select('price_per_sqm')
    .eq('province', province)
    .eq('city', city)
    .eq('property_type', propertyType)
    .eq('is_outlier', false)
    .not('district', 'ilike', `%${district}%`) // Exclude same district for fallback
    .limit(200)

  if (cityData && cityData.length >= 5) {
    const prices = cityData.map((r) => r.price_per_sqm).sort((a, b) => a - b)
    const p25Idx = Math.floor(prices.length * 0.25)
    const p50Idx = Math.floor(prices.length * 0.5)
    const p75Idx = Math.floor(prices.length * 0.75)

    return {
      hasData: true,
      p25: prices[p25Idx],
      p50: prices[p50Idx],
      p75: prices[p75Idx],
      sampleCount: prices.length,
      freshness: null,
      dataTier: 'CITY',
    }
  }

  return {
    hasData: false,
    p25: null,
    p50: null,
    p75: null,
    sampleCount: 0,
    freshness: null,
    dataTier: 'NONE',
  }
}

// --- Main Handler -------------------------------------------------------------

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams

  const parsed = QuerySchema.safeParse({
    province: searchParams.get('province'),
    city: searchParams.get('city'),
    district: searchParams.get('district'),
    propertyType: searchParams.get('propertyType'),
    landAreaSqm: searchParams.get('landAreaSqm'),
    askingPriceTotal: searchParams.get('askingPriceTotal'),
  })

  if (!parsed.success) {
    return NextResponse.json(
      { error: { code: 'INVALID_PARAMS', message: parsed.error.issues[0].message } },
      { status: 400 }
    )
  }

  const { province, city, district, propertyType, landAreaSqm, askingPriceTotal } = parsed.data

  const supabase = await createClient()

  // Calculate price per sqm
  const askingPricePerSqm = Math.round(askingPriceTotal / landAreaSqm)

  // Get benchmark data
  const benchmark = await getBenchmarkData(
    province,
    city,
    district,
    propertyType,
    landAreaSqm,
    supabase
  )

  // No data case
  if (!benchmark.hasData) {
    return NextResponse.json({
      success: true,
      data: {
        hasData: false,
        askingPricePerSqm,
        askingPriceTotal,
        landAreaSqm,
        message:
          'Belum ada data yang cukup untuk kecamatan ini. Coba gunakan data tingkat kota.',
        suggestion: 'Gunakan filter kota untuk melihat data yang tersedia.',
      },
    })
  }

  // Calculate verdict
  const verdictResult = calculatePropertyVerdict(
    askingPricePerSqm,
    benchmark.p25!,
    benchmark.p50!,
    benchmark.p75!
  )

  // Calculate days since freshness
  let freshnessLabel: string | null = null
  if (benchmark.freshness) {
    const daysAgo = Math.floor(
      (Date.now() - new Date(benchmark.freshness).getTime()) / (1000 * 60 * 60 * 24)
    )
    freshnessLabel = `${daysAgo} hari`
  }

  return NextResponse.json({
    success: true,
    data: {
      hasData: true,
      verdict: verdictResult.verdict,
      percentileEstimate: verdictResult.percentileEstimate,
      message: verdictResult.message,
      askingPricePerSqm,
      askingPriceTotal,
      landAreaSqm,
      benchmark: {
        p25: benchmark.p25,
        p50: benchmark.p50,
        p75: benchmark.p75,
        sampleCount: benchmark.sampleCount,
        freshness: freshnessLabel,
        dataTier: benchmark.dataTier,
      },
      location: { province, city, district },
      propertyType,
      disclaimer: KJPP_DISCLAIMER,
    },
  })
}