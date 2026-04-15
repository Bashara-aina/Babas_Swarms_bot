// ==============================================================================
// cekwajar.id — GET /api/salary/benchmark
// Returns salary benchmark data with Bayesian blending
// Query params: jobTitle, city, province, experienceBucket
// ==============================================================================

import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

// --- Zod Schema ---------------------------------------------------------------

const QuerySchema = z.object({
  jobTitle: z.string().min(1, 'Job title is required'),
  city: z.string().min(1, 'City is required'),
  province: z.string().min(1, 'Province is required'),
  experienceBucket: z.enum(['0-2', '3-5', '6-10', '10+']).optional().default('3-5'),
  userSalary: z.string().optional(), // Optional user salary for comparison
})

type QueryParams = z.infer<typeof QuerySchema>

// --- Types --------------------------------------------------------------------

type MatchType = 'EXACT' | 'FUZZY' | 'CANDIDATES' | 'NO_MATCH'
type DataTier = 'CITY_LEVEL' | 'CITY_LEVEL_LIMITED' | 'PROVINCE_LEVEL' | 'BPS_PRIOR' | 'NO_DATA'

interface MatchResultExact {
  matchType: 'EXACT'
  id: string
  title: string
  confidence: number
}

interface MatchResultFuzzy {
  matchType: 'FUZZY'
  id: string
  title: string
  confidence: number
}

interface MatchResultCandidates {
  matchType: 'CANDIDATES'
  candidates: Array<{ id: string; title: string; similarity: number }>
}

interface MatchResultNoMatch {
  matchType: 'NO_MATCH'
}

type MatchResult = MatchResultExact | MatchResultFuzzy | MatchResultCandidates | MatchResultNoMatch

// --- Bayesian Blending ---------------------------------------------------------

function blendBayesian(
  sampleP50: number | null,
  priorP50: number | null,
  n: number,
  k: number = 15
): number | null {
  if (!priorP50 && !sampleP50) return null
  if (!sampleP50) return priorP50
  if (!priorP50 || n >= 30) return sampleP50

  const weight = n / (n + k)
  return Math.round(weight * sampleP50 + (1 - weight) * priorP50)
}

// --- Job Title Normalization --------------------------------------------------

async function normalizeJobTitle(
  input: string,
  supabase: Awaited<ReturnType<typeof createClient>>
): Promise<MatchResult> {
  const trimmed = input.trim()

  // Exact match first (case-insensitive)
  const { data: exactMatch } = await supabase
    .from('job_categories')
    .select('id, title')
    .ilike('title', trimmed)
    .single()

  if (exactMatch) {
    return {
      matchType: 'EXACT',
      id: exactMatch.id,
      title: exactMatch.title,
      confidence: 1.0,
    }
  }

  // Fuzzy match using pg_trgm RPC
  const { data: fuzzyMatches } = await supabase.rpc('search_job_categories_fuzzy', {
    search_term: trimmed,
    threshold: 0.2,
  })

  if (fuzzyMatches && fuzzyMatches.length > 0) {
    const best = fuzzyMatches[0]

    if (best.similarity_score >= 0.5) {
      return {
        matchType: 'FUZZY',
        id: best.id,
        title: best.title,
        confidence: best.similarity_score,
      }
    }

    // Return candidates for user to pick
    return {
      matchType: 'CANDIDATES',
      candidates: fuzzyMatches.slice(0, 5).map((m: { id: string; title: string; similarity_score: number }) => ({
        id: m.id,
        title: m.title,
        similarity: m.similarity_score,
      })),
    }
  }

  return { matchType: 'NO_MATCH' }
}

// --- Get UMK for city --------------------------------------------------------

async function getUMK(
  city: string,
  supabase: Awaited<ReturnType<typeof createClient>>
): Promise<number | null> {
  const { data } = await supabase
    .from('umk_2026')
    .select('monthly_minimum_idr')
    .ilike('city', city)
    .order('effective_date', { ascending: false })
    .limit(1)
    .single()

  return data?.monthly_minimum_idr ?? null
}

// --- Get Benchmark Data -------------------------------------------------------

interface BenchmarkData {
  cityP25: number | null
  cityP50: number | null
  cityP75: number | null
  provinceP50: number | null
  bpsPriorP50: number | null
  sampleCount: number
  dataTier: DataTier
  isBlended: boolean
  blendWeight: number | null
  umk: number | null
  experienceBucket: string
}

async function getBenchmarkData(
  jobCategoryId: string,
  city: string,
  province: string,
  experienceBucket: string,
  supabase: Awaited<ReturnType<typeof createClient>>
): Promise<BenchmarkData> {
  const defaultResult: BenchmarkData = {
    cityP25: null,
    cityP50: null,
    cityP75: null,
    provinceP50: null,
    bpsPriorP50: null,
    sampleCount: 0,
    dataTier: 'NO_DATA',
    isBlended: false,
    blendWeight: null,
    umk: null,
    experienceBucket,
  }

  // Get city-level data
  const { data: cityData } = await supabase
    .from('salary_benchmarks')
    .select('p25, p50, p75, sample_count, data_source')
    .eq('job_category_id', jobCategoryId)
    .ilike('city', city)
    .eq('experience_bucket', experienceBucket)
    .limit(1)
    .single()

  // Get province-level data (from crowdsourced)
  const { data: provinceData } = await supabase
    .from('salary_benchmarks')
    .select('p25, p50, p75, sample_count, data_source')
    .eq('job_category_id', jobCategoryId)
    .ilike('province', province)
    .is('city', null)
    .eq('experience_bucket', experienceBucket)
    .limit(1)
    .single()

  // Get BPS prior data (no experience bucket filter for prior)
  const { data: bpsPrior } = await supabase
    .from('salary_benchmarks')
    .select('p50, sample_count')
    .eq('job_category_id', jobCategoryId)
    .ilike('province', province)
    .eq('data_source', 'bps_sakernas')
    .limit(1)
    .single()

  // Get UMK
  const umk = await getUMK(city, supabase)

  // Determine data tier and apply Bayesian blending
  if (cityData && cityData.sample_count >= 30) {
    // Sufficient city-level data
    return {
      cityP25: cityData.p25,
      cityP50: cityData.p50,
      cityP75: cityData.p75,
      provinceP50: provinceData?.p50 ?? null,
      bpsPriorP50: bpsPrior?.p50 ?? null,
      sampleCount: cityData.sample_count,
      dataTier: 'CITY_LEVEL',
      isBlended: false,
      blendWeight: null,
      umk,
      experienceBucket,
    }
  }

  if (cityData && cityData.sample_count > 0) {
    // Limited city data - apply Bayesian blending with BPS prior
    const blendedP50 = blendBayesian(
      cityData.p50,
      bpsPrior?.p50 ?? null,
      cityData.sample_count,
      15
    )
    const isBlended = bpsPrior && cityData.sample_count < 30

    return {
      cityP25: isBlended ? null : cityData.p25, // Don't show city P25 if blended
      cityP50: blendedP50,
      cityP75: isBlended ? null : cityData.p75,
      provinceP50: provinceData?.p50 ?? null,
      bpsPriorP50: bpsPrior?.p50 ?? null,
      sampleCount: cityData.sample_count,
      dataTier: 'CITY_LEVEL_LIMITED',
      isBlended: !!isBlended,
      blendWeight: isBlended
        ? Math.round((cityData.sample_count / (cityData.sample_count + 15)) * 100)
        : null,
      umk,
      experienceBucket,
    }
  }

  // No city data - fall back to province level
  if (provinceData && provinceData.sample_count > 0) {
    const blendedP50 = blendBayesian(
      provinceData.p50,
      bpsPrior?.p50 ?? null,
      provinceData.sample_count,
      15
    )
    const isBlended = bpsPrior && provinceData.sample_count < 30

    return {
      cityP25: null,
      cityP50: blendedP50,
      cityP75: null,
      provinceP50: blendedP50,
      bpsPriorP50: bpsPrior?.p50 ?? null,
      sampleCount: provinceData.sample_count,
      dataTier: 'PROVINCE_LEVEL',
      isBlended: !!isBlended,
      blendWeight: isBlended
        ? Math.round((provinceData.sample_count / (provinceData.sample_count + 15)) * 100)
        : null,
      umk,
      experienceBucket,
    }
  }

  // No crowdsourced data - use BPS prior only
  if (bpsPrior) {
    return {
      cityP25: null,
      cityP50: bpsPrior.p50,
      cityP75: null,
      provinceP50: bpsPrior.p50,
      bpsPriorP50: bpsPrior.p50,
      sampleCount: 0,
      dataTier: 'BPS_PRIOR',
      isBlended: false,
      blendWeight: null,
      umk,
      experienceBucket,
    }
  }

  return { ...defaultResult, umk }
}

// --- Main Handler -------------------------------------------------------------

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams

  const parsed = QuerySchema.safeParse({
    jobTitle: searchParams.get('jobTitle'),
    city: searchParams.get('city'),
    province: searchParams.get('province'),
    experienceBucket: searchParams.get('experienceBucket') ?? '3-5',
    userSalary: searchParams.get('userSalary'),
  })

  if (!parsed.success) {
    return NextResponse.json(
      { error: { code: 'INVALID_PARAMS', message: parsed.error.issues[0].message } },
      { status: 400 }
    )
  }

  const { jobTitle, city, province, experienceBucket, userSalary } = parsed.data

  const supabase = await createClient()

  // Step 1: Normalize job title
  const matchResult = await normalizeJobTitle(jobTitle, supabase)

  // Return candidates if fuzzy match needs user confirmation
  if (matchResult.matchType === 'CANDIDATES') {
    return NextResponse.json({
      success: true,
      data: {
        matchType: 'CANDIDATES',
        candidates: matchResult.candidates,
        message: 'Silakan pilih judul yang paling sesuai',
      },
    })
  }

  // Return no match
  if (matchResult.matchType === 'NO_MATCH') {
    return NextResponse.json({
      success: true,
      data: {
        matchType: 'NO_MATCH',
        message: 'Judul pekerjaan tidak dikenali. Silakan pilih dari daftar.',
      },
    })
  }

  // Step 2: Get benchmark data
  const benchmark = await getBenchmarkData(
    matchResult.id,
    city,
    province,
    experienceBucket,
    supabase
  )

  // Step 3: Calculate user's salary position if provided
  let userSalaryPosition: 'above' | 'below' | 'within' | null = null
  let userSalaryComparison: { diff: number; percentage: number } | null = null
  let userSalaryNum = 0

  if (userSalary) {
    userSalaryNum = parseInt(userSalary, 10)
    if (!isNaN(userSalaryNum) && benchmark.cityP50) {
      const diff = userSalaryNum - benchmark.cityP50
      const percentage = Math.round((diff / benchmark.cityP50) * 100)

      if (diff > benchmark.cityP50 * 0.05) {
        userSalaryPosition = 'above'
      } else if (diff < -benchmark.cityP50 * 0.05) {
        userSalaryPosition = 'below'
      } else {
        userSalaryPosition = 'within'
      }

      userSalaryComparison = { diff, percentage }
    }
  }

  // Step 4: Build response
  const response = {
    success: true,
    data: {
      matchedTitle: matchResult.title,
      matchType: matchResult.matchType,
      matchConfidence: matchResult.confidence,
      benchmark: {
        cityP25: benchmark.cityP25,
        cityP50: benchmark.cityP50,
        cityP75: benchmark.cityP75,
        provinceP50: benchmark.provinceP50,
        bpsPriorP50: benchmark.bpsPriorP50,
        sampleCount: benchmark.sampleCount,
        dataTier: benchmark.dataTier,
        isBlended: benchmark.isBlended,
        blendWeight: benchmark.blendWeight,
        umk: benchmark.umk,
        experienceBucket: benchmark.experienceBucket,
      },
      userSalary: userSalaryNum ? {
        value: userSalaryNum,
        position: userSalaryPosition,
        comparison: userSalaryComparison,
      } : null,
    },
  }

  return NextResponse.json(response)
}
