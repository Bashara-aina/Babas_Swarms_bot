// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — PPh21 Calculator (PMK 168/2023 TER Method)
// ══════════════════════════════════════════════════════════════════════════════

import type { SupabaseClient } from '@supabase/supabase-js'
import type { PtkpStatus } from '@/types'

export type TERCategory = 'A' | 'B' | 'C'

export interface PPh21Input {
  grossSalary: number
  ptkpStatus: PtkpStatus
  monthNumber: number
  year: number
  hasNPWP: boolean
  /** Cumulative YTD gross for December true-up (defaults to grossSalary × 11) */
  cumulativeYtd?: number
}

export interface PPh21CalculationDetails {
  terCategory: TERCategory
  terRate: number
  ptkpAnnual: number
  method: 'TER' | 'PROGRESSIVE'
  annualizedGross: number
  pkp: number
  progressiveBrackets?: {
    bracketLabel: string
    taxableAmount: number
    rate: number
    tax: number
  }[]
}

export interface PPh21Result {
  terCategory: TERCategory
  terRate: number
  pph21Amount: number
  method: 'TER' | 'PROGRESSIVE'
  details: PPh21CalculationDetails
}

// PTKP values (annual) — from migration 014
const PTKP_VALUES: Record<PtkpStatus, number> = {
  'TK/0': 54_000_000,
  'TK/1': 58_500_000,
  'TK/2': 63_000_000,
  'TK/3': 67_500_000,
  'K/0': 58_500_000,
  'K/1': 63_000_000,
  'K/2': 67_500_000,
  'K/3': 72_000_000,
  'K/I/0': 112_500_000,
  'K/I/1': 117_000_000,
  'K/I/2': 121_500_000,
  'K/I/3': 126_000_000,
}

// TER Category mapping
function getTERCategory(ptkpStatus: PtkpStatus): TERCategory {
  if (['TK/0', 'TK/1'].includes(ptkpStatus)) return 'A'
  if (['K/0', 'K/1', 'TK/2', 'TK/3'].includes(ptkpStatus)) return 'B'
  return 'C'
}

// Progressive tax brackets (UU HPP No.7/2021)
const PROGRESSIVE_BRACKETS = [
  { max: 60_000_000, rate: 0.05, label: '0 – 60 juta' },
  { max: 250_000_000, rate: 0.15, label: '60 juta – 250 juta' },
  { max: 500_000_000, rate: 0.25, label: '250 juta – 500 juta' },
  { max: 5_000_000_000, rate: 0.30, label: '500 juta – 5 miliar' },
  { max: Infinity, rate: 0.35, label: '> 5 miliar' },
]

function calculateProgressiveTax(annualTaxableIncome: number): { total: number; brackets: PPh21Result['details']['progressiveBrackets'] } {
  let remaining = annualTaxableIncome
  let totalTax = 0
  const brackets: PPh21Result['details']['progressiveBrackets'] = []
  let previousMax = 0

  for (const bracket of PROGRESSIVE_BRACKETS) {
    if (remaining <= 0) break
    const taxableInBracket = Math.min(remaining, bracket.max - previousMax)
    const tax = Math.round(taxableInBracket * bracket.rate)
    brackets.push({
      bracketLabel: bracket.label,
      taxableAmount: Math.round(taxableInBracket),
      rate: bracket.rate,
      tax,
    })
    totalTax += tax
    remaining -= taxableInBracket
    previousMax = bracket.max
  }

  return { total: totalTax, brackets }
}

/**
 * Get TER rate for a given category and gross salary from DB.
 * Falls back to closest bracket if exact match not found.
 */
async function getTERRate(
  supabase: SupabaseClient,
  category: TERCategory,
  grossSalary: number
): Promise<number> {
  const { data } = await supabase
    .from('pph21_ter_rates')
    .select('monthly_rate_percent')
    .eq('category', category)
    .lte('min_salary', grossSalary)
    .gte('max_salary', grossSalary)
    .maybeSingle()

  if (data) return Number(data.monthly_rate_percent)

  // Fallback: get closest lower bracket
  const { data: fallback } = await supabase
    .from('pph21_ter_rates')
    .select('monthly_rate_percent')
    .eq('category', category)
    .lte('max_salary', grossSalary)
    .order('max_salary', { ascending: false })
    .limit(1)
    .maybeSingle()

  return fallback ? Number(fallback.monthly_rate_percent) : 0
}

/**
 * Calculate PPh21 using TER method (PMK 168/2023).
 * For December (month 12), uses progressive method with true-up.
 */
export async function calculatePPh21(
  input: PPh21Input,
  supabase: SupabaseClient
): Promise<PPh21Result> {
  const { grossSalary, ptkpStatus, monthNumber, hasNPWP, cumulativeYtd } = input

  const terCategory = getTERCategory(ptkpStatus)
  const ptkpAnnual = PTKP_VALUES[ptkpStatus] ?? 54_000_000

  // December → progressive true-up method
  if (monthNumber === 12) {
    const annualGross = (cumulativeYtd ?? grossSalary * 11) + grossSalary
    const pkp = Math.max(0, annualGross - ptkpAnnual)
    const { total: annualTax, brackets } = calculateProgressiveTax(pkp)

    // TER paid in months 1-11
    const terRate = await getTERRate(supabase, terCategory, grossSalary)
    const monthlyTER = grossSalary * (terRate / 100)
    const terMonthsTotal = monthlyTER * 11
    const decemberTax = Math.max(0, annualTax - Math.round(terMonthsTotal))

    const baseTax = hasNPWP ? decemberTax : decemberTax * 1.20

    return {
      terCategory,
      terRate,
      pph21Amount: Math.round(baseTax),
      method: 'PROGRESSIVE',
      details: {
        terCategory,
        terRate,
        ptkpAnnual,
        method: 'PROGRESSIVE',
        annualizedGross: annualGross,
        pkp,
        progressiveBrackets: brackets,
      },
    }
  }

  // Months 1-11 → TER method
  const terRate = await getTERRate(supabase, terCategory, grossSalary)
  const monthlyTax = grossSalary * (terRate / 100)
  const baseTax = hasNPWP ? monthlyTax : monthlyTax * 1.20

  return {
    terCategory,
    terRate,
    pph21Amount: Math.round(baseTax),
    method: 'TER',
    details: {
      terCategory,
      terRate,
      ptkpAnnual,
      method: 'TER',
      annualizedGross: grossSalary * 12,
      pkp: Math.max(0, grossSalary * 12 - ptkpAnnual),
    },
  }
}
