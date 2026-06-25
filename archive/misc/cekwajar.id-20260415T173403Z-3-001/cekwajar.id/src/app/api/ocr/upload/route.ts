// ==============================================================================
// cekwajar.id ? POST /api/ocr/upload
// Accepts file upload, stores to Supabase Storage, runs OCR, returns extracted fields
// ==============================================================================

import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { getCurrentUser } from '@/lib/auth/getCurrentUser'
import { extractWithGoogleVision } from '@/lib/ocr/google-vision'
import type { OCRExtractionResult } from '@/lib/ocr/field-extractor'

export const runtime = 'nodejs'

// --- Validation Constants ----------------------------------------------------

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
const MAX_SIZE = 5 * 1024 * 1024 // 5MB

// --- Quota Helpers -----------------------------------------------------------

const VISION_MONTHLY_LIMIT = 950

function getCurrentMonthKey(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

async function getMonthlyCount(supabase: Awaited<ReturnType<typeof createClient>>): Promise<number> {
  const { data } = await supabase
    .from('ocr_quota_counter')
    .select('month_count')
    .eq('month_key', getCurrentMonthKey())
    .single()
  return data?.month_count ?? 0
}

async function incrementQuota(supabase: Awaited<ReturnType<typeof createClient>>): Promise<void> {
  const monthKey = getCurrentMonthKey()
  const { data: existing } = await supabase
    .from('ocr_quota_counter')
    .select('month_count')
    .eq('month_key', monthKey)
    .single()

  if (existing) {
    await supabase
      .from('ocr_quota_counter')
      .update({
        month_count: existing.month_count + 1,
        updated_at: new Date().toISOString(),
      })
      .eq('month_key', monthKey)
  } else {
    await supabase
      .from('ocr_quota_counter')
      .insert({
        month_key: monthKey,
        month_count: 1,
        updated_at: new Date().toISOString(),
      })
  }
}

// --- POST Handler ------------------------------------------------------------

export async function POST(request: NextRequest) {
  // 1. Parse form data
  let file: File | null = null
  let sessionId: string | null = null

  try {
    const formData = await request.formData()
    file = formData.get('file') as File | null
    sessionId = formData.get('sessionId') as string | null
  } catch {
    return NextResponse.json(
      { error: { code: 'INVALID_FORM', message: 'Form data tidak valid.' } },
      { status: 400 }
    )
  }

  // 2. Validate file presence
  if (!file) {
    return NextResponse.json(
      { error: { code: 'NO_FILE', message: 'File tidak ditemukan.' } },
      { status: 400 }
    )
  }

  // 3. Validate file type
  if (!ALLOWED_TYPES.includes(file.type)) {
    return NextResponse.json(
      { error: { code: 'INVALID_FILE_TYPE', message: 'Format tidak didukung. Gunakan JPEG, PNG, atau PDF.' } },
      { status: 400 }
    )
  }

  // 4. Validate file size
  if (file.size > MAX_SIZE) {
    return NextResponse.json(
      { error: { code: 'FILE_TOO_LARGE', message: 'File terlalu besar (maks 5MB). Kompres foto atau gunakan JPEG.' } },
      { status: 400 }
    )
  }

  // 5. Get user context
  let userId = `anon-${sessionId ?? crypto.randomUUID()}`
  let tier = 'free'

  const supabase = await createClient()

  try {
    const { user } = await getCurrentUser()
    if (user) {
      userId = user.id
      const { data: profile } = await supabase
        .from('profiles')
        .select('subscription_tier')
        .eq('id', user.id)
        .single()
      tier = (profile?.subscription_tier as string) ?? 'free'
    }
  } catch {
    // Anonymous session ? continue
  }

  // 6. Upload to Supabase Storage
  const fileExt = file.name.split('.').pop()?.toLowerCase() ?? 'jpg'
  const storagePath = `${userId}/${crypto.randomUUID()}.${fileExt}`

  const fileBuffer = await file.arrayBuffer()

  const { error: uploadError } = await supabase.storage
    .from('payslips')
    .upload(storagePath, fileBuffer, {
      contentType: file.type,
      upsert: false,
    })

  if (uploadError) {
    console.error('[ocr/upload] storage error:', uploadError)
    return NextResponse.json(
      { error: { code: 'UPLOAD_FAILED', message: 'Gagal mengupload file.' } },
      { status: 500 }
    )
  }

  // 7. Check Vision quota
  const currentMonthCount = await getMonthlyCount(supabase)
  const useVision = currentMonthCount < VISION_MONTHLY_LIMIT

  let ocrResult: OCRExtractionResult

  if (useVision) {
    // 8a. Use Google Vision
    await incrementQuota(supabase)

    try {
      ocrResult = await extractWithGoogleVision(fileBuffer, file.type)
    } catch (visionErr) {
      console.error('[ocr/upload] Vision API error:', visionErr)
      // Fall back to requiring client-side OCR
      ocrResult = {
        source: 'google_vision',
        confidence: 0,
        routingDecision: 'MANUAL_REQUIRED',
        extractedFields: {},
        fieldConfidences: {},
        requiresClientOCR: true,
        filePath: storagePath,
        message: 'Gagal membaca slip gaji. Silakan isi manual.',
        requiresConfirmation: [],
      }
    }
  } else {
    // 8b. Quota exceeded ? instruct client to use Tesseract
    ocrResult = {
      source: 'tesseract',
      confidence: 0,
      routingDecision: 'MANUAL_REQUIRED',
      extractedFields: {},
      fieldConfidences: {},
      requiresClientOCR: true,
      filePath: storagePath,
      message: 'Kuota Google Vision bulan ini sudah habis. Silakan gunakan OCR lokal.',
      requiresConfirmation: [],
    }
  }

  // 9. Return result
  return NextResponse.json({
    success: true,
    data: {
      filePath: storagePath,
      ...ocrResult,
    },
  })
}