// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Database Query Helpers
// Single source of truth for all Supabase query functions
// ══════════════════════════════════════════════════════════════════════════════

import { createBrowserClient } from '@supabase/ssr'
import type { SupabaseClient } from '@supabase/supabase-js'
import type {
  SubscriptionTier,
  TERCategory,
  BPJSComponent,
  BPJSParty,
} from '@/types/database.types'

// ─── Client Factory ────────────────────────────────────────────────────────────

/** Always use this for browser-side queries */
export function createQueryClient(): SupabaseClient {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  )
}

// ─── User & Subscription ─────────────────────────────────────────────────────

/**
 * Get user subscription tier — always from DB, never from client state.
 * Falls back to 'free' if user not found.
 */
export async function getUserTier(userId: string): Promise<SubscriptionTier> {
  const supabase = createQueryClient()
  const { data } = await supabase
    .from('user_profiles')
    .select('subscription_tier')
    .eq('id', userId)
    .single()

  const row = data as { subscription_tier: SubscriptionTier } | null
  return row?.subscription_tier ?? 'free'
}

// ─── UMK (Upah Minimum Kota) ──────────────────────────────────────────────────

/**
 * Get UMK (monthly minimum wage) for a city.
 * Uses ILIKE for fuzzy matching (e.g., 'jakarta' matches 'Kota Jakarta').
 * Returns null if city not found.
 */
export async function getUMKForCity(city: string): Promise<number | null> {
  const supabase = createQueryClient()
  const { data } = await supabase
    .from('umk_2026')
    .select('monthly_minimum_idr')
    .ilike('city', `%${city}%`)
    .order('effective_date', { ascending: false })
    .limit(1)
    .single()

  const row = data as { monthly_minimum_idr: number } | null
  return row?.monthly_minimum_idr ?? null
}

// ─── PPh21 TER (PMK 168/2023) ─────────────────────────────────────────────────

/**
 * Get TER (Tarif Effective Naratif) rate for a gross salary + TER category.
 * Returns 0 if no matching bracket found.
 */
export async function getTERRate(
  grossSalary: number,
  category: TERCategory
): Promise<number> {
  const supabase = createQueryClient()
  const { data } = await supabase
    .from('pph21_ter_rates')
    .select('monthly_rate_percent')
    .eq('category', category)
    .lte('min_salary', grossSalary)
    .gte('max_salary', grossSalary)
    .single()

  const row = data as { monthly_rate_percent: number } | null
  return row?.monthly_rate_percent ?? 0
}

/**
 * Get all TER rate brackets for a category (for building rate tables in UI).
 */
export async function getTERBrackets(category: TERCategory) {
  const supabase = createQueryClient()
  const { data } = await supabase
    .from('pph21_ter_rates')
    .select('*')
    .eq('category', category)
    .order('min_salary', { ascending: true })

  return data ?? []
}

// ─── BPJS Rates ───────────────────────────────────────────────────────────────

export interface BPJSRate {
  component: BPJSComponent
  party: BPJSParty
  rate_percent: number
  salary_cap_idr: number | null
  notes: string | null
}

/**
 * Get all active BPJS rates.
 */
export async function getBPJSRates(): Promise<BPJSRate[]> {
  const supabase = createQueryClient()
  const { data } = await supabase
    .from('bpjs_rates')
    .select('component, party, rate_percent, salary_cap_idr, notes')

  return (data as BPJSRate[]) ?? []
}

/**
 * Get BPJS employee rate for a specific component (used in calculations).
 */
export async function getBPJSEmployeeRate(
  component: BPJSComponent
): Promise<number> {
  const supabase = createQueryClient()
  const { data } = await supabase
    .from('bpjs_rates')
    .select('rate_percent')
    .eq('component', component)
    .eq('party', 'employee')
    .single()

  const row = data as { rate_percent: number } | null
  return row?.rate_percent ?? 0
}

/**
 * Get BPJS employer rate for a specific component.
 */
export async function getBPJSEmployerRate(
  component: BPJSComponent
): Promise<{ rate: number; salaryCap: number | null }> {
  const supabase = createQueryClient()
  const { data } = await supabase
    .from('bpjs_rates')
    .select('rate_percent, salary_cap_idr')
    .eq('component', component)
    .eq('party', 'employer')
    .single()

  const row = data as { rate_percent: number; salary_cap_idr: number | null } | null
  return {
    rate: row?.rate_percent ?? 0,
    salaryCap: row?.salary_cap_idr ?? null,
  }
}

// ─── PTKP (Penghasilan Tidak Kena Pajak) ─────────────────────────────────────

/**
 * Get PTKP annual value by status code.
 * Falls back to TK/0 (54,000,000) if code not found.
 */
export async function getPTKPValue(statusCode: string): Promise<number> {
  const supabase = createQueryClient()
  const { data } = await supabase
    .from('ptkp_values')
    .select('annual_value_idr')
    .eq('status_code', statusCode)
    .single()

  const row = data as { annual_value_idr: number } | null
  return row?.annual_value_idr ?? 54_000_000
}

// ─── OCR Quota Counter ──────────────────────────────────────────────────────────

/**
 * Increment the OCR counter for the current month (YYYY-MM).
 * Uses the database RPC function for atomic increment.
 * Returns the new count after increment.
 */
export async function incrementOCRCounter(): Promise<number> {
  const supabase = createQueryClient()
  const { data, error } = await supabase.rpc('increment_ocr_counter')

  if (error) {
    console.error('[queries] increment_ocr_counter error:', error)
    return 999
  }

  return typeof data === 'number' ? data : 999
}

/**
 * Get current OCR usage count for the month.
 */
export async function getOCRCountForMonth(): Promise<number> {
  const supabase = createQueryClient()
  const now = new Date()
  const monthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

  const { data } = await supabase
    .from('ocr_quota_counter')
    .select('count')
    .eq('month_key', monthKey)
    .single()

  const row = data as { count: number } | null
  return row?.count ?? 0
}

// ─── COL Indices ─────────────────────────────────────────────────────────────

export interface COLIndex {
  city_code: string
  city_name: string
  province: string
  col_index: number
  data_year: number
  data_quarter: number
}

/**
 * Get COL index for a city by city code.
 */
export async function getCOLIndex(cityCode: string): Promise<COLIndex | null> {
  const supabase = createQueryClient()
  const { data } = await supabase
    .from('col_indices')
    .select('*')
    .eq('city_code', cityCode.toUpperCase())
    .single()

  return data as COLIndex | null
}

/**
 * Get all COL indices ordered by index descending.
 */
export async function getAllCOLIndices(): Promise<COLIndex[]> {
  const supabase = createQueryClient()
  const { data } = await supabase
    .from('col_indices')
    .select('*')
    .order('col_index', { ascending: false })

  return (data as COLIndex[]) ?? []
}

// ─── PPP Reference ──────────────────────────────────────────────────────────

export interface PPPReference {
  country_code: string
  country_name: string
  currency_code: string
  currency_symbol: string
  flag_emoji: string
    ppp_factor: number
  ppp_year: number
  is_free_tier: boolean
  display_order: number
}

/**
 * Get PPP reference data for a country.
 */
export async function getPPPCountry(
  countryCode: string
): Promise<PPPReference | null> {
  const supabase = createQueryClient()
  const { data } = await supabase
    .from('ppp_reference')
    .select('*')
    .eq('country_code', countryCode.toUpperCase())
    .single()

  return data as PPPReference | null
}

/**
 * Get all PPP countries ordered by display_order.
 */
export async function getAllPPPCountries(): Promise<PPPReference[]> {
  const supabase = createQueryClient()
  const { data } = await supabase
    .from('ppp_reference')
    .select('*')
    .order('display_order', { ascending: true })

  return (data as PPPReference[]) ?? []
}

// ─── Salary Benchmarks ────────────────────────────────────────────────────────

export interface SalaryBenchmark {
  id: string
  job_category_id: string | null
  city: string | null
  province: string
  experience_bucket: string | null
  data_source: string
  sample_count: number
  p25: number | null
  p50: number
  p75: number | null
  updated_at: string
}

/**
 * Get salary benchmark by city + job category + experience.
 */
export async function getSalaryBenchmark(
  city: string,
  jobCategoryId: string,
  experienceBucket: string
): Promise<SalaryBenchmark | null> {
  const supabase = createQueryClient()
  const { data } = await supabase
    .from('salary_benchmarks')
    .select('*')
    .eq('city', city)
    .eq('job_category_id', jobCategoryId)
    .eq('experience_bucket', experienceBucket)
    .single()

  return data as SalaryBenchmark | null
}

// ─── Property Benchmarks ─────────────────────────────────────────────────────

export interface PropertyBenchmark {
  id: string
  province: string
  city: string
  district: string
  property_type: string
  price_per_sqm: number
  land_area_sqm: number | null
  source: string
  is_outlier: boolean
}

/**
 * Get property benchmark statistics for a city + type (excluding outliers).
 */
export async function getPropertyStats(
  city: string,
  propertyType: string
): Promise<{ p25: number; p50: number; p75: number; sampleCount: number } | null> {
  const supabase = createQueryClient()
  const { data } = await supabase
    .from('property_benchmarks')
    .select('price_per_sqm, land_area_sqm')
    .eq('city', city)
    .eq('property_type', propertyType)
    .eq('is_outlier', false)
    .order('price_per_sqm', { ascending: true })

  if (!data || data.length === 0) {
    return null
  }

  const rows = data as { price_per_sqm: number; land_area_sqm: number | null }[]
  const prices = rows
    .map((r) => Number(r.price_per_sqm))
    .filter((p) => p > 0)

  if (prices.length === 0) return null

  const sorted = prices.slice().sort((a, b) => a - b)
  return {
    p25: sorted[Math.floor(sorted.length * 0.25)],
    p50: sorted[Math.floor(sorted.length * 0.5)],
    p75: sorted[Math.floor(sorted.length * 0.75)],
    sampleCount: sorted.length,
  }
}

// ─── User Consents ───────────────────────────────────────────────────────────

export interface UserConsent {
  id: string
  user_id: string
  policy_version: string
  privacy_policy_accepted: boolean
  terms_accepted: boolean
  marketing_accepted: boolean
  accepted_at: string
  ip_hash: string | null
}

/**
 * Get latest consent record for a user.
 */
export async function getUserConsent(
  userId: string
): Promise<UserConsent | null> {
  const supabase = createQueryClient()
  const { data } = await supabase
    .from('user_consents')
    .select('*')
    .eq('user_id', userId)
    .order('accepted_at', { ascending: false })
    .limit(1)
    .single()

  return data as UserConsent | null
}
