// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — POST /api/audit-payslip
// Core payslip audit engine: validates, calculates, detects, stores
// ══════════════════════════════════════════════════════════════════════════════

import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { createClient } from '@/lib/supabase/server'
import { getCurrentUser } from '@/lib/auth/getCurrentUser'
import { calculateBPJS } from '@/lib/calculations/bpjs'
import { calculatePPh21 } from '@/lib/calculations/pph21'
import { detectViolations } from '@/lib/calculations/violations'
import type { SubscriptionTier } from '@/types'

export const runtime = 'nodejs'

// ─── Rate Limiting (in-memory — replace with KV in Stage 10) ─────────────────

const rateLimitMap = new Map<string, { count: number; resetAt: number }>()
const RATE_LIMIT = 5
const RATE_WINDOW_MS = 60 * 60 * 1000 // 1 hour

function checkRateLimit(ip: string): boolean {
  const now = Date.now()
  const entry = rateLimitMap.get(ip)

  if (!entry || now > entry.resetAt) {
    rateLimitMap.set(ip, { count: 1, resetAt: now + RATE_WINDOW_MS })
    return true
  }

  if (entry.count >= RATE_LIMIT) return false
  entry.count++
  return true
}

// ─── Request Schema ────────────────────────────────────────────────────────────

const AuditPayslipSchema = z.object({
  grossSalary: z.number().min(500_000).max(1_000_000_000),
  ptkpStatus: z.enum([
    'TK/0', 'TK/1', 'TK/2', 'TK/3',
    'K/0', 'K/1', 'K/2', 'K/3',
    'K/I/0', 'K/I/1', 'K/I/2', 'K/I/3',
  ]),
  city: z.string().min(1).max(100),
  monthNumber: z.number().int().min(1).max(12),
  year: z.number().int().min(2024).max(2030).optional(),
  hasNPWP: z.boolean(),
  reportedDeductions: z.object({
    pph21: z.number().min(0),
    jhtEmployee: z.number().min(0),
    jpEmployee: z.number().min(0),
    jkkEmployee: z.number().min(0),
    jkmEmployee: z.number().min(0),
    kesehatanEmployee: z.number().min(0),
    takeHome: z.number().min(0),
  }),
  sessionId: z.string().uuid().optional(),
  ocrSource: z.enum(['google_vision', 'tesseract', 'manual']).optional(),
  payslipFilePath: z.string().optional(),
})

type AuditPayslipInput = z.infer<typeof AuditPayslipSchema>

// ─── GET (not supported) ──────────────────────────────────────────────────────

export async function GET() {
  return NextResponse.json({ error: 'Method not allowed' }, { status: 405 })
}

// ─── POST Handler ────────────────────────────────────────────────────────────

export async function POST(request: NextRequest) {
  // 1. Parse & validate body
  let body: AuditPayslipInput
  try {
    const json = await request.json()
    body = AuditPayslipSchema.parse(json)
  } catch (err) {
    if (err instanceof z.ZodError) {
      return NextResponse.json(
        { code: 'VALIDATION_ERROR', message: err.issues[0]?.message ?? 'Invalid input' },
        { status: 400 }
      )
    }
    return NextResponse.json({ code: 'INVALID_JSON', message: 'Malformed JSON body' }, { status: 400 })
  }

  // 2. Rate limiting
  const ip = request.headers.get('x-forwarded-for')?.split(',')[0].trim()
    ?? request.headers.get('x-real-ip') ?? 'unknown'
  if (!checkRateLimit(ip)) {
    return NextResponse.json(
      { code: 'RATE_LIMITED', message: `Terlalu banyak request. Coba lagi dalam 1 jam.` },
      { status: 429 }
    )
  }

  // 3. Get current user + tier
  const { tier } = await getCurrentUser()

  const supabase = await createClient()

  // 4. Get UMK for city
  const { data: umkRow } = await supabase
    .from('umk_2026')
    .select('monthly_minimum_idr')
    .ilike('city', `%${body.city}%`)
    .order('effective_date', { ascending: false })
    .limit(1)
    .maybeSingle()

  const cityUMK = (umkRow as { monthly_minimum_idr: number } | null)?.monthly_minimum_idr ?? null

  if (cityUMK === null) {
    return NextResponse.json(
      { code: 'INVALID_CITY', message: `Kota "${body.city}" tidak ditemukan dalam database UMK kami.` },
      { status: 400 }
    )
  }

  // 5. Calculate PPh21 (TER method)
  const pph21Result = await calculatePPh21(
    {
      grossSalary: body.grossSalary,
      ptkpStatus: body.ptkpStatus,
      monthNumber: body.monthNumber,
      year: body.year ?? new Date().getFullYear(),
      hasNPWP: body.hasNPWP,
    },
    supabase
  )

  // 6. Calculate BPJS
  const bpjsResult = calculateBPJS({ grossSalary: body.grossSalary })

  // 7. Detect violations
  const violations = detectViolations({
    grossSalary: body.grossSalary,
    cityUMK,
    reported: {
      pph21: body.reportedDeductions.pph21,
      jhtEmployee: body.reportedDeductions.jhtEmployee,
      jpEmployee: body.reportedDeductions.jpEmployee,
      kesehatan: body.reportedDeductions.kesehatanEmployee,
    },
    calculated: {
      pph21: pph21Result.pph21Amount,
      jhtEmployee: bpjsResult.jhtEmployee,
      jpEmployee: bpjsResult.jpEmployee,
      kesehatan: bpjsResult.kesehatanEmployee,
    },
  })

  // 8. Apply freemium gate — hide IDR amounts for free users
  const isPaidResult = tier !== 'free'
  const gatedViolations = violations.map((v) => ({
    ...v,
    differenceIDR: isPaidResult ? v.differenceIDR : null,
  }))

  const verdict = violations.length > 0 ? 'ADA_PELANGGARAN' : 'SESUAI'

  // 9. Save audit to DB
  const { data: insertedRow, error: insertError } = await supabase
    .from('payslip_audits')
    .insert({
      user_id: (await getCurrentUser()).user?.id ?? null,
      session_id: body.sessionId ?? null,
      gross_salary: body.grossSalary,
      ptkp_status: body.ptkpStatus,
      city: body.city,
      month_number: body.monthNumber,
      year: body.year ?? new Date().getFullYear(),
      has_npwp: body.hasNPWP,
      reported_pph21: body.reportedDeductions.pph21,
      reported_jht_employee: body.reportedDeductions.jhtEmployee,
      reported_jp_employee: body.reportedDeductions.jpEmployee,
      reported_jkk: body.reportedDeductions.jkkEmployee,
      reported_jkm: body.reportedDeductions.jkmEmployee,
      reported_kesehatan_employee: body.reportedDeductions.kesehatanEmployee,
      reported_take_home: body.reportedDeductions.takeHome,
      ocr_source: body.ocrSource ?? 'manual',
      payslip_file_path: body.payslipFilePath ?? null,
      calculated_pph21: pph21Result.pph21Amount,
      calculated_jht: bpjsResult.jhtEmployee,
      calculated_jp: bpjsResult.jpEmployee,
      calculated_kesehatan: bpjsResult.kesehatanEmployee,
      city_umk: cityUMK,
      violations: violations,
      verdict,
      is_paid_result: isPaidResult,
      subscription_tier_at_time: tier,
    })
    .select('id')
    .single()

  if (insertError) {
    console.error('[audit-payslip] insert error:', insertError)
  }

  const auditId = (insertedRow as { id: string } | null)?.id ?? null

  // 10. Return response
  return NextResponse.json({
    success: true,
    data: {
      auditId,
      verdict,
      violationCount: violations.length,
      violationCodes: violations.map((v) => v.code),
      violations: gatedViolations,
      calculations: isPaidResult
        ? {
            correctPph21: pph21Result.pph21Amount,
            correctJht: bpjsResult.jhtEmployee,
            correctJp: bpjsResult.jpEmployee,
            correctKesehatan: bpjsResult.kesehatanEmployee,
            cityUMK,
          }
        : undefined,
      isGated: !isPaidResult && violations.length > 0,
      subscriptionRequired: !isPaidResult ? 'basic' : null,
      gateMessage:
        !isPaidResult && violations.length > 0
          ? 'Upgrade ke Basic untuk melihat selisih IDR dan detail tindakan'
          : undefined,
    },
  })
}
