// ==============================================================================
// cekwajar.id — POST /api/salary/submit
// Submit salary data to crowdsource database
// ==============================================================================

import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { createHash } from 'crypto'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

// --- Zod Schema ---------------------------------------------------------------

const SubmitSchema = z.object({
  jobTitle: z.string().min(1, 'Job title is required'),
  city: z.string().min(1, 'City is required'),
  province: z.string().min(1, 'Province is required'),
  grossSalary: z.number().positive('Salary must be positive'),
  experienceBucket: z.enum(['0-2', '3-5', '6-10', '10+']),
  industry: z.string().optional(),
})

// --- Fingerprint Generation ---------------------------------------------------

function createFingerprint(
  ip: string,
  jobTitle: string,
  city: string,
  salary: number
): string {
  const salaryBucket = Math.round(salary / 1_000_000)
  const input = `${ip}:${jobTitle.toLowerCase()}:${city.toLowerCase()}:${salaryBucket}`

  return createHash('sha256')
    .update(input)
    .digest('hex')
    .slice(0, 16)
}

// --- Job Title Normalization --------------------------------------------------

async function normalizeJobTitle(
  input: string,
  supabase: Awaited<ReturnType<typeof createClient>>
): Promise<string | null> {
  const trimmed = input.trim()

  // Exact match first
  const { data: exactMatch } = await supabase
    .from('job_categories')
    .select('id, title')
    .ilike('title', trimmed)
    .single()

  if (exactMatch) return exactMatch.id

  // Fuzzy match
  const { data: fuzzyMatches } = await supabase.rpc('search_job_categories_fuzzy', {
    search_term: trimmed,
    threshold: 0.3,
  })

  if (fuzzyMatches && fuzzyMatches.length > 0 && fuzzyMatches[0].similarity_score >= 0.5) {
    return fuzzyMatches[0].id
  }

  return null
}

// --- UMK Validation -----------------------------------------------------------

async function validateSalaryAgainstUMK(
  salary: number,
  city: string,
  supabase: Awaited<ReturnType<typeof createClient>>
): Promise<{ valid: boolean; umk: number | null }> {
  const { data: umkRecord } = await supabase
    .from('umk_2026')
    .select('monthly_minimum_idr')
    .ilike('city', city)
    .order('effective_date', { ascending: false })
    .limit(1)
    .single()

  if (!umkRecord) {
    return { valid: true, umk: null } // Can't validate without UMK
  }

  const umk = umkRecord.monthly_minimum_idr

  // Outlier check: < 0.5x UMK or > 30x UMK
  if (salary < umk * 0.5 || salary > umk * 30) {
    return { valid: false, umk }
  }

  return { valid: true, umk }
}

// --- Duplicate Check ----------------------------------------------------------

async function checkDuplicate(
  fingerprint: string,
  supabase: Awaited<ReturnType<typeof createClient>>
): Promise<boolean> {
  const { data: existing } = await supabase
    .from('salary_submissions')
    .select('id')
    .eq('submission_fingerprint', fingerprint)
    .gte('created_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()) // Within 24h
    .limit(1)
    .single()

  return !!existing
}

// --- Handler ------------------------------------------------------------------

export async function POST(request: NextRequest) {
  let body: unknown

  try {
    body = await request.json()
  } catch {
    return NextResponse.json(
      { error: { code: 'INVALID_JSON', message: 'JSON body tidak valid.' } },
      { status: 400 }
    )
  }

  const parsed = SubmitSchema.safeParse(body)

  if (!parsed.success) {
    return NextResponse.json(
      { error: { code: 'VALIDATION_ERROR', message: parsed.error.issues[0].message } },
      { status: 400 }
    )
  }

  const { jobTitle, city, province, grossSalary, experienceBucket, industry } = parsed.data

  const supabase = await createClient()

  // Step 1: Normalize job title to category ID
  const jobCategoryId = await normalizeJobTitle(jobTitle, supabase)

  if (!jobCategoryId) {
    return NextResponse.json({
      data: {
        accepted: false,
        isDuplicate: false,
        violatesOutlierRule: false,
        message: 'Judul pekerjaan tidak dikenali. Silakan pilih dari daftar.',
      },
    })
  }

  // Step 2: Create fingerprint
  const ip = request.headers.get('x-forwarded-for')?.split(',')[0] ?? 'unknown'
  const fingerprint = createFingerprint(ip, jobTitle, city, grossSalary)

  // Step 3: Check for duplicate submission
  const isDuplicate = await checkDuplicate(fingerprint, supabase)

  if (isDuplicate) {
    return NextResponse.json({
      data: {
        accepted: false,
        isDuplicate: true,
        violatesOutlierRule: false,
        message: 'Laporan dengan data serupa sudah ada dalam 24 jam terakhir.',
      },
    })
  }

  // Step 4: Validate against UMK
  const umkValidation = await validateSalaryAgainstUMK(grossSalary, city, supabase)

  if (!umkValidation.valid) {
    return NextResponse.json({
      data: {
        accepted: false,
        isDuplicate: false,
        violatesOutlierRule: true,
        message: `Gaji terlalu ekstrem. UMK kota ini adalah Rp ${umkValidation.umk?.toLocaleString('id-ID')}. Gaji yang wajar adalah 0.5x - 30x UMK.`,
      },
    })
  }

  // Step 5: Get job category title for raw record
  const { data: category } = await supabase
    .from('job_categories')
    .select('title, industry')
    .eq('id', jobCategoryId)
    .single()

  // Step 6: Insert submission
  const { error: insertError } = await supabase.from('salary_submissions').insert({
    job_category_id: jobCategoryId,
    job_title_raw: jobTitle,
    city,
    province,
    gross_salary: grossSalary,
    experience_bucket: experienceBucket,
    industry: industry ?? category?.industry ?? null,
    submission_fingerprint: fingerprint,
    is_validated: false,
    is_outlier: false,
    submission_date: new Date().toISOString().split('T')[0],
  })

  if (insertError) {
    console.error('[salary/submit] Insert error:', insertError)
    return NextResponse.json(
      { error: { code: 'INSERT_FAILED', message: 'Gagal menyimpan laporan gaji.' } },
      { status: 500 }
    )
  }

  return NextResponse.json({
    data: {
      accepted: true,
      isDuplicate: false,
      violatesOutlierRule: false,
      message: 'Laporan gaji berhasil disimpan. Terima kasih atas kontribusimu!',
    },
  })
}
