# Stage 5 — Wajar Slip: OCR Pipeline (Google Vision + Tesseract)
**cekwajar.id Vibe Coding Playbook**  
**Estimated time:** 3–4 hours  
**Prerequisites:** Stage 4 complete. Google Vision API key in .env.local.  
**Goal:** Full OCR upload flow — drag & drop → Google Vision → field extraction → confirm screen → auto-calculate.

---

## New Dependencies This Stage

```bash
# Tesseract.js for client-side OCR fallback
pnpm add tesseract.js

# File upload handling
pnpm add react-dropzone

# Image processing utilities  
pnpm add sharp

# Dev
pnpm add -D @types/sharp
```

---

## ═══════════════════════════════════════════════
## MASTER PROMPT — SEND THIS TO CLAUDE CODE
## (Stage 5 — OCR Pipeline)
## ═══════════════════════════════════════════════

```
===START===
cekwajar.id — Stage 5: OCR Pipeline

Context: Stage 4 complete. Wajar Slip manual form works end-to-end.
Now adding OCR: user uploads payslip image/PDF → Google Vision extracts fields → 
auto-fills the manual form.

YOUR TASK FOR STAGE 5:
Build the complete OCR pipeline. This includes server-side Vision API call,
client-side Tesseract.js fallback, quota management, file upload UI, and
field extraction with Indonesian payslip-specific regex patterns.

════════════════════════════════════════════════════
PART A: FILE UPLOAD API
════════════════════════════════════════════════════

Create src/app/api/ocr/upload/route.ts

This route:
1. Accepts multipart/form-data with 'file' field
2. Validates: file type (image/jpeg, image/png, application/pdf), max 5MB
3. Uploads to Supabase Storage bucket 'payslips'
4. Checks OCR quota counter in DB
5. Calls Google Vision or Tesseract based on quota
6. Returns extracted fields

Important: For PDF files, convert first page to image using the @vercel/og image approach
or return extracted text directly from Vision (Vision can handle PDFs directly).

File path in storage: `{userId || 'anon-' + sessionId}/{uuid}.{ext}`

Validation:
  const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
  const MAX_SIZE = 5 * 1024 * 1024  // 5MB

Route handler:
export async function POST(request: Request) {
  const formData = await request.formData()
  const file = formData.get('file') as File
  const sessionId = formData.get('sessionId') as string
  
  // 1. Validate
  if (!ALLOWED_TYPES.includes(file.type)) {
    return Response.json({ error: { code: 'INVALID_FILE_TYPE', message: 'Format tidak didukung. Gunakan JPEG, PNG, atau PDF.' } }, { status: 400 })
  }
  if (file.size > MAX_SIZE) {
    return Response.json({ error: { code: 'FILE_TOO_LARGE', message: 'File terlalu besar (maks 5MB). Kompres foto atau gunakan JPEG.' } }, { status: 400 })
  }
  
  // 2. Get user context
  const { user, tier } = await getCurrentUser()
  
  // 3. Upload to Supabase Storage
  const userId = user?.id ?? `anon-${sessionId}`
  const fileExt = file.name.split('.').pop() ?? 'jpg'
  const filePath = `${userId}/${crypto.randomUUID()}.${fileExt}`
  
  const fileBuffer = await file.arrayBuffer()
  const serviceClient = getServiceClient()
  const { error: uploadError } = await serviceClient.storage
    .from('payslips')
    .upload(filePath, fileBuffer, {
      contentType: file.type,
      upsert: false
    })
  
  if (uploadError) {
    return Response.json({ error: { code: 'UPLOAD_FAILED', message: 'Gagal mengupload file.' } }, { status: 500 })
  }
  
  // 4. Check Vision quota
  const currentMonthCount = await checkOCRQuota(serviceClient)
  const useVision = currentMonthCount < 950
  
  let ocrResult: OCRExtractionResult
  
  if (useVision) {
    await incrementOCRCounter(serviceClient)
    ocrResult = await extractWithGoogleVision(fileBuffer, file.type)
  } else {
    // Return file path and instruct client to use Tesseract
    ocrResult = { 
      source: 'tesseract_client',
      requiresClientOCR: true,
      filePath,
      message: 'Quota Google Vision habis bulan ini. OCR lokal akan digunakan.'
    }
  }
  
  return Response.json({
    success: true,
    data: {
      filePath,
      ...ocrResult
    }
  })
}

════════════════════════════════════════════════════
PART B: GOOGLE VISION INTEGRATION
════════════════════════════════════════════════════

Create src/lib/ocr/google-vision.ts

CONSTANTS for Indonesian payslip field extraction:
  const IDR_PATTERNS = [
    /(?:Rp\.?\s*)([\d.,]+)/gi,           // "Rp 1.234.567" or "Rp. 1.234.567"
    /(?:IDR\s*)([\d.,]+)/gi,              // "IDR 1234567"
    /(?:Rupiah\s*)([\d.,]+)/gi,           // "Rupiah 1.234.567"
  ]
  
  const FIELD_PATTERNS = {
    grossSalary: [
      /gaji\s*(?:bruto|pokok|dasar|kotor)[:\s]+([\d.,]+)/i,
      /total\s*(?:gaji|penghasilan)[:\s]+([\d.,]+)/i,
      /basic\s*salary[:\s]+([\d.,]+)/i,
      /upah\s*(?:bruto|kotor)[:\s]+([\d.,]+)/i,
    ],
    pph21: [
      /(?:pph\s*21|pph21|pajak\s*penghasilan\s*pasal\s*21)[:\s]+([\d.,]+)/i,
      /(?:income\s*tax|withholding\s*tax)[:\s]+([\d.,]+)/i,
    ],
    jhtEmployee: [
      /jht\s*(?:karyawan|pekerja|peserta)[:\s]+([\d.,]+)/i,
      /jaminan\s*hari\s*tua[:\s]+([\d.,]+)/i,
      /jht\s*2%[:\s]+([\d.,]+)/i,
    ],
    jpEmployee: [
      /jp\s*(?:karyawan|pekerja|peserta)[:\s]+([\d.,]+)/i,
      /jaminan\s*pensiun[:\s]+([\d.,]+)/i,
      /jp\s*1%[:\s]+([\d.,]+)/i,
      /jaminan\s*pensiun\s*karyawan[:\s]+([\d.,]+)/i,
    ],
    kesehatanEmployee: [
      /(?:jkn|kesehatan|bpjs\s*kes(?:ehatan)?)\s*(?:karyawan|peserta|1%)[:\s]+([\d.,]+)/i,
      /potongan\s*kesehatan[:\s]+([\d.,]+)/i,
    ],
    takeHome: [
      /(?:take\s*home\s*pay|thp)[:\s]+([\d.,]+)/i,
      /(?:gaji|penghasilan)\s*(?:diterima|bersih|nett?)[:\s]+([\d.,]+)/i,
      /(?:jumlah\s*diterima|total\s*diterima)[:\s]+([\d.,]+)/i,
    ],
  }

Helper to parse IDR string to number:
  function parseIDR(raw: string): number {
    // Handle "1.234.567" (Indonesian format) and "1,234,567" (Western format)
    const cleaned = raw.replace(/\./g, '').replace(/,/g, '').replace(/\s/g, '')
    return parseInt(cleaned, 10) || 0
  }

Main Vision API call:
  export async function extractWithGoogleVision(
    fileBuffer: ArrayBuffer,
    mimeType: string
  ): Promise<OCRExtractionResult> {
    const base64 = Buffer.from(fileBuffer).toString('base64')
    
    const requestBody = {
      requests: [{
        image: { content: base64 },
        features: [{ type: 'DOCUMENT_TEXT_DETECTION', maxResults: 1 }],
        imageContext: { languageHints: ['id', 'en'] }
      }]
    }
    
    const response = await fetch(
      `https://vision.googleapis.com/v1/images:annotate?key=${process.env.GOOGLE_VISION_API_KEY}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      }
    )
    
    if (!response.ok) {
      throw new Error(`Vision API error: ${response.status}`)
    }
    
    const data = await response.json()
    const fullText = data.responses[0]?.fullTextAnnotation?.text ?? ''
    const confidence = data.responses[0]?.fullTextAnnotation?.pages?.[0]?.confidence ?? 0
    
    // Extract fields using patterns
    const extracted = extractFieldsFromText(fullText)
    
    // Calculate per-field confidence
    const fieldConfidences = calculateFieldConfidences(extracted, fullText)
    
    // Overall routing decision
    const routingDecision = confidence >= 0.92 ? 'AUTO_ACCEPT' 
      : confidence >= 0.80 ? 'SOFT_CHECK' 
      : 'MANUAL_REQUIRED'
    
    return {
      source: 'google_vision',
      confidence,
      routingDecision,
      extractedFields: extracted,
      fieldConfidences,
      rawText: fullText,  // useful for debugging
      requiresClientOCR: false,
      requiresConfirmation: Object.entries(fieldConfidences)
        .filter(([_, conf]) => conf < 0.80)
        .map(([field, _]) => field)
    }
  }

Field extraction function:
  function extractFieldsFromText(text: string): ExtractedPayslipFields {
    const result: Partial<ExtractedPayslipFields> = {}
    
    for (const [fieldName, patterns] of Object.entries(FIELD_PATTERNS)) {
      for (const pattern of patterns) {
        const match = text.match(pattern)
        if (match) {
          result[fieldName] = parseIDR(match[1])
          break  // first match wins
        }
      }
    }
    
    return result as ExtractedPayslipFields
  }

Field confidence function:
  function calculateFieldConfidences(
    extracted: ExtractedPayslipFields,
    rawText: string
  ): Record<string, number> {
    const confidences: Record<string, number> = {}
    
    for (const [field, value] of Object.entries(extracted)) {
      if (!value) {
        confidences[field] = 0
        continue
      }
      
      // Sanity checks — if value passes sanity check, confidence is high
      if (field === 'grossSalary' && value >= 500000 && value <= 1_000_000_000) {
        confidences[field] = 0.90
      } else if (field === 'pph21' && value >= 0 && value < 100_000_000) {
        confidences[field] = 0.85
      } else {
        confidences[field] = 0.75
      }
    }
    
    return confidences
  }

════════════════════════════════════════════════════
PART C: CLIENT-SIDE TESSERACT FALLBACK
════════════════════════════════════════════════════

Create src/lib/ocr/tesseract-client.ts

This runs in the BROWSER (not Node.js).
Tesseract.js is loaded lazily only when needed.

export async function extractWithTesseract(
  imageFile: File,
  onProgress?: (progress: number) => void
): Promise<OCRExtractionResult> {
  
  const { createWorker } = await import('tesseract.js')
  
  const worker = await createWorker(['ind', 'eng'], 1, {
    logger: (m) => {
      if (m.status === 'recognizing text' && onProgress) {
        onProgress(Math.round(m.progress * 100))
      }
    },
  })
  
  const { data } = await worker.recognize(imageFile)
  await worker.terminate()
  
  // Apply 15% confidence penalty (Tesseract less accurate than Vision)
  const adjustedConfidence = (data.confidence / 100) * 0.85
  
  // Use same field extraction patterns
  const extracted = extractFieldsFromText(data.text)
  const fieldConfidences = calculateFieldConfidences(extracted, data.text)
  
  // Tesseract always goes to SOFT_CHECK (never AUTO_ACCEPT)
  const routingDecision = adjustedConfidence >= 0.70 ? 'SOFT_CHECK' : 'MANUAL_REQUIRED'
  
  return {
    source: 'tesseract',
    confidence: adjustedConfidence,
    routingDecision,
    extractedFields: extracted,
    fieldConfidences,
    requiresClientOCR: false,
    requiresConfirmation: Object.keys(extracted),  // always confirm all for Tesseract
  }
}

Note: Share extractFieldsFromText and calculateFieldConfidences in a shared utils file
since the same logic runs in both Vision and Tesseract pipelines.

Create src/lib/ocr/field-extractor.ts (shared between Vision + Tesseract):
  - All FIELD_PATTERNS constants
  - extractFieldsFromText()
  - calculateFieldConfidences()
  - parseIDR()
  - Export all

════════════════════════════════════════════════════
PART D: UPLOAD UI COMPONENT
════════════════════════════════════════════════════

Create src/components/wajar-slip/PayslipUploader.tsx

This is a CLIENT COMPONENT with states:
  IDLE → UPLOADING → PROCESSING (Vision/Tesseract) → CONFIRM_FIELDS | MANUAL_REQUIRED | AUTO_ACCEPT

Props:
  onComplete: (extracted: ExtractedPayslipFields, filePath: string, source: string) => void
  onManualMode: () => void

UI:

IDLE state:
  Dashed border dropzone, full width, min-height 200px
  Center content:
    📷 icon
    "Upload Foto atau PDF Slip Gaji"
    "JPEG · PNG · PDF · Maks 5MB"
    "Pilih File" button OR drag & drop text
    Divider "—— atau ——"
    "Isi Manual" link button → onManualMode()

  Use react-dropzone:
    const { getRootProps, getInputProps, isDragActive } = useDropzone({
      accept: { 'image/jpeg': [], 'image/png': [], 'image/webp': [], 'application/pdf': [] },
      maxSize: 5 * 1024 * 1024,
      onDrop: handleFileDrop,
    })

UPLOADING state:
  Show file name + progress indicator
  "Mengupload..."

PROCESSING (Vision) state:
  "Membaca slip gaji dengan Google Vision... ⚡"
  Show confidence building up (fake animation OK)

PROCESSING (Tesseract) state:
  Progress bar 0-100%
  "Membaca dengan OCR lokal... [X%]"
  Note: "Proses ini membutuhkan 15-30 detik di pertama kali"

OCR_CONFIRM state (routingDecision = SOFT_CHECK):
  Show filled form with extracted values, each field showing:
    - Pre-filled input
    - If fieldConfidence < 0.80: yellow border + "Harap periksa nilai ini"
    - If fieldConfidence >= 0.80: green border

  Title: "Konfirmasi Hasil Scan"
  Subtitle: "OCR mengekstrak data berikut. Periksa dan koreksi jika perlu."
  
  [Konfirmasi & Hitung →] button → passes to onComplete()
  [Isi Ulang Manual] link → onManualMode()

Handle "requiresClientOCR: true" (quota exceeded):
  Show message about Tesseract being used
  Load Tesseract lazily and start processing client-side
  Update progress bar

════════════════════════════════════════════════════
PART E: INTEGRATE INTO WAJAR SLIP PAGE
════════════════════════════════════════════════════

Update src/app/wajar-slip/page.tsx to add PayslipUploader above the form.

Flow:
1. User sees PayslipUploader at top
2. User can upload OR click "Isi Manual" to skip to form
3. If OCR completes with AUTO_ACCEPT: auto-fill form, immediately calculate
4. If OCR completes with SOFT_CHECK: show confirmation screen, then form
5. If OCR fails (MANUAL_REQUIRED): pre-fill what was extracted, show warning
6. Manual mode: show form directly

State additions to existing page state machine:
  | { status: 'UPLOADING' }
  | { status: 'OCR_PROCESSING'; progress?: number; source: 'vision'|'tesseract' }
  | { status: 'OCR_CONFIRM'; extracted: ExtractedPayslipFields; filePath: string }

New transitions:
  IDLE → UPLOADING (file dropped)
  UPLOADING → OCR_PROCESSING (file uploaded successfully)
  OCR_PROCESSING → OCR_CONFIRM (routingDecision = SOFT_CHECK)
  OCR_PROCESSING → CALCULATING (routingDecision = AUTO_ACCEPT → auto-submit)
  OCR_PROCESSING → MANUAL_FORM (routingDecision = MANUAL_REQUIRED)
  OCR_CONFIRM → CALCULATING (user confirms fields)
  
When auto-submitting (AUTO_ACCEPT):
  Auto-populate form values and call API immediately
  Show "Otomatis menghitung hasil..." to user

════════════════════════════════════════════════════
PART F: QUOTA CHECK API
════════════════════════════════════════════════════

Create src/app/api/ocr/quota/route.ts:
  GET → return { monthlyCount: number, isQuotaAvailable: boolean, source: 'google_vision'|'tesseract' }
  Used by frontend to determine which OCR path to show user

════════════════════════════════════════════════════
PART G: DISCLAIMER BANNER COMPONENT
════════════════════════════════════════════════════

Create src/components/shared/DisclaimerBanner.tsx:
Props: { text: string, type: 'warning' | 'info' | 'danger', collapsible?: boolean }

For Wajar Slip, show this banner:
  type='warning'
  text='Alat ini bukan nasihat pajak. Hasil bersifat indikatif berdasarkan regulasi PMK 168/2023 dan peraturan BPJS yang berlaku. Konsultasikan dengan konsultan pajak untuk keputusan penting.'

For Wajar Tanah (add for later): KJPP disclaimer
For Wajar Kabur (add for later): PPP accuracy disclaimer

════════════════════════════════════════════════════
VERIFICATION:
════════════════════════════════════════════════════

Test 1 — Upload + Google Vision (requires real image):
  Take a photo of any payslip (real or printed test payslip)
  Upload to /wajar-slip
  Verify: file appears in Supabase Storage payslips bucket
  Verify: OCR result shows in confirm screen
  Check: extracted IDR values are reasonable

Test 2 — Quota exceeded → Tesseract fallback:
  Manually set ocr_quota_counter for current month to 960
  Upload another image
  Verify: response includes requiresClientOCR=true OR tesseract runs client-side

Test 3 — Invalid file type:
  Try uploading a .docx file
  Expected: error "Format tidak didukung"

Test 4 — File too large:
  Try uploading a >5MB file
  Expected: error "File terlalu besar"

Test 5 — Full OCR → Confirm → Calculate:
  Upload → confirm values → submit → get verdict
  Verify audit saved in payslip_audits with ocrSource set

pnpm tsc --noEmit → zero errors
===END===
```

---

## Verification Checklist for Stage 5

```bash
# Storage bucket exists
# Check in Supabase Studio: Storage → Buckets → payslips (private)

# OCR API works
curl -X POST localhost:3000/api/ocr/upload \
  -F "file=@test-payslip.jpg" \
  -F "sessionId=$(uuidgen)"

# Quota check
curl localhost:3000/api/ocr/quota
# Expected: { monthlyCount: N, isQuotaAvailable: true|false }

pnpm tsc --noEmit
```

**Next:** Stage 6 — Wajar Gaji (Salary Benchmark)
