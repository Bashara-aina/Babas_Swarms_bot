/**
 * PPh 21 TER and BPJS calculation engine.
 * All constants from lib/regulations.ts — zero magic numbers.
 */

import type { TERSlab } from "@/lib/regulations"
import {
  TER_A,
  TER_B,
  TER_C,
  PTKP,
  TER_CATEGORY,
  BIAYA_JABATAN,
  PASAL_17,
  BPJS_KESEHATAN,
  BPJS_JHT,
  BPJS_JP,
  BPJS_JKK,
  BPJS_JKM,
  VERDICT_THRESHOLDS,
  REGULATION_SOURCES,
} from "@/lib/regulations"

export type PTKPStatus =
  | "TK/0" | "TK/1" | "TK/2" | "TK/3"
  | "K/0" | "K/1" | "K/2" | "K/3"
  | "K/I/0" | "K/I/1" | "K/I/2" | "K/I/3"

export type TERCategory = "A" | "B" | "C"
export type VerdictType = "WAJAR" | "PERLU_DICEK" | "TIDAK_WAJAR"

export { REGULATION_SOURCES }

const TER_SLABS: Record<TERCategory, TERSlab[]> = {
  A: TER_A,
  B: TER_B,
  C: TER_C,
}

function getTERRateFromSlabs(slabs: TERSlab[], gross: number): number {
  for (const slab of slabs) {
    if (gross >= slab.min && (slab.max === null || gross <= slab.max)) return slab.rate
  }
  return 0
}

function progressiveTax(pkp: number, brackets: TERSlab[]): number {
  let remaining = Math.max(0, pkp)
  let tax = 0
  for (const slab of brackets) {
    // Half-open [min, max): bracket boundaries per UU HPP Pasal 17
    const bandWidth = slab.max === null ? Infinity : slab.max - slab.min
    const amountInBand = Math.min(remaining, bandWidth)
    tax += amountInBand * slab.rate
    remaining -= amountInBand
    if (remaining <= 0) break
  }
  return Math.round(tax)
}

/** JP cap changes effective 1 March each year. Jan–Feb of year X use year X-1 cap. */
export function getJpCap(year: number, month: number): number {
  const effectiveYear = month < 3 ? year - 1 : year
  if (effectiveYear <= 2023) return BPJS_JP.wage_cap_2024
  if (effectiveYear === 2024) return BPJS_JP.wage_cap_2024
  if (effectiveYear === 2025) return BPJS_JP.wage_cap_2025
  return BPJS_JP.wage_cap_2026
}

export interface SlipInput {
  month: number
  tax_year?: number
  ptkp_status: PTKPStatus
  gaji_pokok: number
  tunjangan_tetap: number
  tunjangan_tidak_tetap: number
  pph21_charged: number
  bpjs_kesehatan_charged: number
  bpjs_jht_charged: number
  bpjs_jp_charged: number
  bpjs_jkk_charged: number
  bpjs_jkm_charged: number
  potongan_lain: number
  annual_gross?: number
  annual_iuran_pensiun?: number
  annual_zakat?: number
  annual_pph21_paid_before_last_period?: number
}

export function isDecemberInput(
  input: SlipInput
): input is SlipInput & { annual_gross: number } {
  return input.month === 12 && typeof input.annual_gross === "number"
}

export function validateSlipInput(input: SlipInput): string[] {
  const errors: string[] = []
  if (input.month < 1 || input.month > 12) {
    errors.push("Bulan harus antara 1–12")
  }
  if (input.gaji_pokok < 0) {
    errors.push("Gaji pokok tidak boleh negatif")
  }
  if (input.month === 12 && input.annual_gross === undefined) {
    errors.push(
      "Bulan Desember membutuhkan total penghasilan tahunan (annual_gross) " +
        "untuk rekonsiliasi PPh 21 yang akurat"
    )
  }
  if (input.month === 12 && input.annual_gross !== undefined) {
    const monthlyApprox =
      input.gaji_pokok + input.tunjangan_tetap + input.tunjangan_tidak_tetap
    if (input.annual_gross < monthlyApprox) {
      errors.push(
        "annual_gross tampak lebih kecil dari penghasilan satu bulan — " +
          "pastikan ini total tahunan (bukan bulanan)"
      )
    }
  }
  return errors
}

export interface ComponentResult {
  label: string
  charged: number
  expected: number
  diff: number
  isCorrect: boolean
  isIllegal?: boolean
  note?: string
}

type CalculationItem = {
  expected: number
  actual: number
  diff: number
  verdict: VerdictType
  regulation: string
  explanation_id: string
}

type Pph21ResultItem = Omit<CalculationItem, "expected"> & { expected: number | null }

export interface CalculateAllResult {
  pph21: Pph21ResultItem
  bpjsKesehatan: CalculationItem
  bpjsJHT: CalculationItem
  bpjsJP: CalculationItem
  jkk: {
    shouldBeZero: boolean
    actual: number
    verdict: VerdictType
    explanation_id: string
  }
  jkm: {
    shouldBeZero: boolean
    actual: number
    verdict: VerdictType
    explanation_id: string
  }
  overallVerdict: VerdictType
  totalOvercharge: number
  annualImpact: number
  annualImpactWithInterest: number
  jp_cap_unverified: boolean
  flags: string[]
  terCategory: TERCategory
  terRate: number
  gross: number
  isDecember: boolean
}

export interface SlipResult {
  verdict: VerdictType
  terCategory: TERCategory
  terRate: number
  gross: number
  pph21: ComponentResult
  bpjsKesehatan: ComponentResult
  bpjsJht: ComponentResult
  bpjsJp: ComponentResult
  bpjsJkk: ComponentResult
  bpjsJkm: ComponentResult
  totalCharged: number
  totalExpected: number
  totalOvercharge: number
  annual_overcharge_estimate: number
  annual_overcharge_with_interest: number
  jp_cap_unverified: boolean
  explanation: string
  legalBasis: string[]
  isDecember: boolean
  pph21DataIncomplete: boolean
}

function fmt(n: number): string {
  return "Rp " + new Intl.NumberFormat("id-ID").format(Math.round(n))
}

function classifyDiff(diff: number): VerdictType {
  const abs = Math.abs(diff)
  if (abs <= VERDICT_THRESHOLDS.wajar_tolerance) return "WAJAR"
  if (abs <= VERDICT_THRESHOLDS.perlu_dicek_max) return "PERLU_DICEK"
  return "TIDAK_WAJAR"
}

function worstVerdict(a: VerdictType, b: VerdictType): VerdictType {
  const rank: Record<VerdictType, number> = { WAJAR: 0, PERLU_DICEK: 1, TIDAK_WAJAR: 2 }
  return rank[a] >= rank[b] ? a : b
}

function calculateBiayaJabatan(annualGross: number): number {
  return Math.min(
    annualGross * BIAYA_JABATAN.rate,
    BIAYA_JABATAN.monthly_cap * 12,
    BIAYA_JABATAN.annual_cap
  )
}

function calculateAnnualPph21Expected(input: SlipInput): { expected: number; debugNoBiaya: number } {
  const annualGross = input.annual_gross ?? 0
  if (annualGross <= 0) {
    return { expected: 0, debugNoBiaya: 0 }
  }
  const annualIuranPensiun = input.annual_iuran_pensiun ?? 0
  const annualZakat = input.annual_zakat ?? 0
  const paidJanNov = input.annual_pph21_paid_before_last_period ?? 0
  const ptkpAnnual = PTKP[input.ptkp_status] ?? 0

  const biayaJabatanApplied = calculateBiayaJabatan(annualGross)
  const pkpLegal = Math.max(0, annualGross - biayaJabatanApplied - annualIuranPensiun - annualZakat - ptkpAnnual)
  const annualTaxLegal = progressiveTax(pkpLegal, PASAL_17)
  const expected = Math.max(0, annualTaxLegal - paidJanNov)

  const pkpNoBiaya = Math.max(0, annualGross - annualIuranPensiun - annualZakat - ptkpAnnual)
  const annualTaxNoBiaya = progressiveTax(pkpNoBiaya, PASAL_17)
  const debugNoBiaya = Math.max(0, annualTaxNoBiaya - paidJanNov)

  return {
    expected: Math.round(expected),
    debugNoBiaya: Math.round(debugNoBiaya),
  }
}

export function getTERCategory(ptkp: PTKPStatus): TERCategory {
  const result = TER_CATEGORY[ptkp]
  if (!result) {
    if (process.env.NODE_ENV === "development") {
      console.error(
        `[cekwajar] Unknown PTKP status: "${ptkp}". Defaulting to "A".`
      )
    }
    return "A"
  }
  return result as TERCategory
}

export function getTERRate(category: TERCategory, gross: number): number {
  return getTERRateFromSlabs(TER_SLABS[category], gross)
}

export function calculateAll(input: SlipInput): CalculateAllResult {
  const gross = (input.gaji_pokok || 0) + (input.tunjangan_tetap || 0) + (input.tunjangan_tidak_tetap || 0)
  const category = getTERCategory(input.ptkp_status)
  const terRate = getTERRate(category, gross)
  const isDecember = input.month === 12
  const taxYear = input.tax_year ?? new Date().getFullYear()

  const pph21Expected: number | null = isDecember
    ? input.annual_gross !== undefined
      ? calculateAnnualPph21Expected(input).expected
      : null  // data tidak cukup untuk dihitung
    : Math.round(gross * terRate)

  const bpjsKesehatanExpected = Math.round(
    Math.min(gross, BPJS_KESEHATAN.wage_cap) * BPJS_KESEHATAN.employee_rate
  )
  const bpjsJHTExpected = Math.round(gross * BPJS_JHT.employee_rate)
  const jpCap = getJpCap(taxYear, input.month)
  const bpjsJPExpected = Math.round(Math.min(gross, jpCap) * BPJS_JP.employee_rate)

  const pph21Actual = input.pph21_charged || 0
  const bpjsKesehatanActual = input.bpjs_kesehatan_charged || 0
  const bpjsJHTActual = input.bpjs_jht_charged || 0
  const bpjsJPActual = input.bpjs_jp_charged || 0
  const jkkActual = input.bpjs_jkk_charged || 0
  const jkmActual = input.bpjs_jkm_charged || 0

  const pph21Diff = pph21Actual - (pph21Expected ?? 0)
  const kesehatanDiff = bpjsKesehatanActual - bpjsKesehatanExpected
  const jhtDiff = bpjsJHTActual - bpjsJHTExpected
  const jpDiff = bpjsJPActual - bpjsJPExpected

  const flags: string[] = []
  let pph21Verdict: VerdictType
  if (pph21Expected === null) {
    pph21Verdict = "PERLU_DICEK"
    flags.push("Bulan Desember: isi total penghasilan tahunan untuk hasil akurat")
  } else {
    pph21Verdict = classifyDiff(pph21Diff)
  }
  const kesehatanVerdict = classifyDiff(kesehatanDiff)
  const jhtVerdict = classifyDiff(jhtDiff)
  const jpVerdict = classifyDiff(jpDiff)

  // JP 2026 cap is now verified: Rp11.086.300 per SE BPJS B/1226/022026
  const jp_cap_unverified = false

  const jkkVerdict: VerdictType = jkkActual > 0 ? "TIDAK_WAJAR" : "WAJAR"
  if (jkkActual > 0) flags.push("JKK dipotong dari karyawan (harus beban pemberi kerja)")

  const jkmVerdict: VerdictType = jkmActual > 0 ? "TIDAK_WAJAR" : "WAJAR"
  if (jkmActual > 0) flags.push("JKM dipotong dari karyawan (harus beban pemberi kerja)")

  if (bpjsKesehatanActual > BPJS_KESEHATAN.employee_max) {
    flags.push("Potongan BPJS Kesehatan karyawan melebihi batas Rp 120.000")
  }
  const kesehatanCapVerdict: VerdictType =
    bpjsKesehatanActual > BPJS_KESEHATAN.employee_max ? "TIDAK_WAJAR" : kesehatanVerdict

  if (gross > jpCap && bpjsJPActual > bpjsJPExpected) {
    flags.push("Potongan JP dihitung pada gaji di atas batas upah JP")
  }
  const jpCapVerdict: VerdictType =
    gross > jpCap && bpjsJPActual > bpjsJPExpected ? "TIDAK_WAJAR" : jpVerdict

  let biayaJabatanVerdict: VerdictType = "WAJAR"
  if (isDecember && input.annual_gross !== undefined) {
    const annualCheck = calculateAnnualPph21Expected(input)
    const looksLikeNoBiaya =
      Math.abs(pph21Actual - annualCheck.debugNoBiaya) <= VERDICT_THRESHOLDS.wajar_tolerance
    const legalFar =
      Math.abs(pph21Actual - annualCheck.expected) > VERDICT_THRESHOLDS.perlu_dicek_max
    if (looksLikeNoBiaya && legalFar) {
      biayaJabatanVerdict = "TIDAK_WAJAR"
      flags.push("Biaya jabatan tidak diterapkan sebelum hitung PPh 21 rekonsiliasi")
    }
  }
  let overallVerdict = pph21Verdict
  overallVerdict = worstVerdict(overallVerdict, kesehatanCapVerdict)
  overallVerdict = worstVerdict(overallVerdict, jhtVerdict)
  overallVerdict = worstVerdict(overallVerdict, jpCapVerdict)
  overallVerdict = worstVerdict(overallVerdict, jkkVerdict)
  overallVerdict = worstVerdict(overallVerdict, jkmVerdict)
  overallVerdict = worstVerdict(overallVerdict, biayaJabatanVerdict)

  const totalOvercharge =
    (pph21Expected !== null ? Math.max(0, pph21Diff) : 0) +
    Math.max(0, kesehatanDiff) +
    Math.max(0, jhtDiff) +
    Math.max(0, jpDiff) +
    Math.max(0, jkkActual) +
    Math.max(0, jkmActual)

  return {
    pph21: {
      expected: pph21Expected,  // null when December and annual_gross not provided
      actual: pph21Actual,
      diff: pph21Diff,
      verdict: pph21Verdict,
      regulation: isDecember ? "PMK 168/2023 rekonsiliasi Desember + Pasal 17" : "PMK 168/2023 TER",
      explanation_id: isDecember
        ? "PPh 21 masa terakhir dihitung dengan rekonsiliasi tahunan Pasal 17."
        : "PPh 21 Jan-Nov dihitung pakai tarif efektif rata-rata (TER).",
    },
    bpjsKesehatan: {
      expected: bpjsKesehatanExpected,
      actual: bpjsKesehatanActual,
      diff: kesehatanDiff,
      verdict: kesehatanCapVerdict,
      regulation: REGULATION_SOURCES.bpjs_kesehatan.name,
      explanation_id: `BPJS Kesehatan karyawan ${(BPJS_KESEHATAN.employee_rate * 100).toFixed(0)}% dari upah dengan batas upah ${fmt(BPJS_KESEHATAN.wage_cap)}.`,
    },
    bpjsJHT: {
      expected: bpjsJHTExpected,
      actual: bpjsJHTActual,
      diff: jhtDiff,
      verdict: jhtVerdict,
      regulation: REGULATION_SOURCES.bpjs_jht.name,
      explanation_id: `JHT karyawan ${(BPJS_JHT.employee_rate * 100).toFixed(0)}% dari upah bulanan.`,
    },
    bpjsJP: {
      expected: bpjsJPExpected,
      actual: bpjsJPActual,
      diff: jpDiff,
      verdict: jpCapVerdict,
      regulation: REGULATION_SOURCES.bpjs_jp.name,
      explanation_id: `JP karyawan ${(BPJS_JP.employee_rate * 100).toFixed(0)}% dengan batas upah ${fmt(jpCap)} untuk tahun ${taxYear}.`,
    },
    jkk: {
      shouldBeZero: !BPJS_JKK.employee_deduction_allowed,
      actual: jkkActual,
      verdict: jkkVerdict,
      explanation_id: "JKK adalah beban pemberi kerja, tidak boleh dipotong dari karyawan.",
    },
    jkm: {
      shouldBeZero: !BPJS_JKM.employee_deduction_allowed,
      actual: jkmActual,
      verdict: jkmVerdict,
      explanation_id: "JKM adalah beban pemberi kerja, tidak boleh dipotong dari karyawan.",
    },
    overallVerdict,
    totalOvercharge,
    annualImpact: totalOvercharge * 12,
    annualImpactWithInterest: Math.round(totalOvercharge * 12 * 1.06),
    jp_cap_unverified,
    flags,
    terCategory: category,
    terRate,
    gross,
    isDecember,
  }
}

function buildExplanation(result: CalculateAllResult): string {
  if (result.overallVerdict === "WAJAR") {
    return "Potongan di slip sesuai parameter regulasi yang dihitung sistem."
  }

  const parts: string[] = []
  if (result.pph21.verdict !== "WAJAR") parts.push("PPh 21 berbeda dari hasil perhitungan regulasi.")
  if (result.bpjsKesehatan.verdict !== "WAJAR") parts.push("BPJS Kesehatan berbeda dari batas 1% dan cap upah.")
  if (result.bpjsJP.verdict !== "WAJAR") parts.push("BPJS JP berbeda dari batas upah JP yang berlaku.")
  if (result.jkk.verdict === "TIDAK_WAJAR") parts.push("JKK dipotong dari karyawan padahal beban pemberi kerja.")
  if (result.jkm.verdict === "TIDAK_WAJAR") parts.push("JKM dipotong dari karyawan padahal beban pemberi kerja.")
  if (result.flags.length) parts.push(`Temuan: ${result.flags.join("; ")}.`)
  parts.push(`Estimasi potongan berlebih per bulan: ${fmt(result.totalOvercharge)}.`)

  return parts.join(" ")
}

export function calculateSlip(input: SlipInput): SlipResult {
  const all = calculateAll(input)

  const totalExpected =
    (all.pph21.expected ?? 0) +
    all.bpjsKesehatan.expected +
    all.bpjsJHT.expected +
    all.bpjsJP.expected
  const totalCharged =
    all.pph21.actual +
    all.bpjsKesehatan.actual +
    all.bpjsJHT.actual +
    all.bpjsJP.actual +
    all.jkk.actual +
    all.jkm.actual

  const legalBasis = [
    REGULATION_SOURCES.pph21_ter.name,
    REGULATION_SOURCES.bpjs_kesehatan.name,
    REGULATION_SOURCES.bpjs_jht.name,
    REGULATION_SOURCES.bpjs_jp.name,
    REGULATION_SOURCES.bpjs_jkk_jkm.name,
  ]

  return {
    verdict: all.overallVerdict,
    terCategory: all.terCategory,
    terRate: all.terRate,
    gross: all.gross,
    pph21: {
      label: "PPh 21",
      charged: all.pph21.actual,
      expected: all.pph21.expected ?? 0,
      diff: all.pph21.diff,
      isCorrect: all.pph21.verdict === "WAJAR",
      note: all.isDecember
        ? all.pph21.expected === null
          ? "Desember: isi total penghasilan tahunan untuk perhitungan"
          : "Masa terakhir: rekonsiliasi tahunan Pasal 17"
        : `TER ${all.terCategory} x ${(all.terRate * 100).toFixed(2)}%`,
    },
    bpjsKesehatan: {
      label: "BPJS Kesehatan",
      charged: all.bpjsKesehatan.actual,
      expected: all.bpjsKesehatan.expected,
      diff: all.bpjsKesehatan.diff,
      isCorrect: all.bpjsKesehatan.verdict === "WAJAR",
      isIllegal: all.bpjsKesehatan.actual > BPJS_KESEHATAN.employee_max,
      note: `${(BPJS_KESEHATAN.employee_rate * 100).toFixed(0)}% x min(gaji, ${fmt(BPJS_KESEHATAN.wage_cap)})`,
    },
    bpjsJht: {
      label: "BPJS JHT",
      charged: all.bpjsJHT.actual,
      expected: all.bpjsJHT.expected,
      diff: all.bpjsJHT.diff,
      isCorrect: all.bpjsJHT.verdict === "WAJAR",
      note: `${(BPJS_JHT.employee_rate * 100).toFixed(0)}% dari upah bulanan`,
    },
    bpjsJp: {
      label: "BPJS JP",
      charged: all.bpjsJP.actual,
      expected: all.bpjsJP.expected,
      diff: all.bpjsJP.diff,
      isCorrect: all.bpjsJP.verdict === "WAJAR",
      isIllegal: all.bpjsJP.verdict === "TIDAK_WAJAR" && all.flags.some((f) => f.includes("JP")),
      note: all.bpjsJP.explanation_id,
    },
    bpjsJkk: {
      label: "BPJS JKK",
      charged: all.jkk.actual,
      expected: 0,
      diff: all.jkk.actual,
      isCorrect: all.jkk.verdict === "WAJAR",
      isIllegal: all.jkk.verdict === "TIDAK_WAJAR",
      note: all.jkk.explanation_id,
    },
    bpjsJkm: {
      label: "BPJS JKM",
      charged: all.jkm.actual,
      expected: 0,
      diff: all.jkm.actual,
      isCorrect: all.jkm.verdict === "WAJAR",
      isIllegal: all.jkm.verdict === "TIDAK_WAJAR",
      note: all.jkm.explanation_id,
    },
    totalCharged,
    totalExpected,
    totalOvercharge: all.totalOvercharge,
    annual_overcharge_estimate: all.annualImpact,
    annual_overcharge_with_interest: all.annualImpactWithInterest,
    jp_cap_unverified: false,
    explanation: buildExplanation(all),
    legalBasis,
    isDecember: all.isDecember,
    pph21DataIncomplete: all.pph21.expected === null,
  }
}

export function estimateAnnualOvercharge(monthlyOvercharge: number): number {
  return monthlyOvercharge * 12
}

export function formatRupiah(value: number): string {
  return "Rp " + new Intl.NumberFormat("id-ID").format(Math.round(value))
}
