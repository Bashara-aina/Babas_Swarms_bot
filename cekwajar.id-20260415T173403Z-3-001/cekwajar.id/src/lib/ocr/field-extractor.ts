// ==============================================================================
// cekwajar.id ? OCR Field Extractor (Shared)
// Indonesian payslip regex patterns + field extraction + confidence scoring
// Used by both Google Vision (server) and Tesseract.js (client)
// ==============================================================================

// --- IDR Parsing -------------------------------------------------------------

/**
 * Parse Indonesian IDR string to number.
 * Handles "1.234.567" (Indonesian dots) and "1234567" (plain).
 */
export function parseIDR(raw: string): number {
  if (!raw) return 0
  // Remove all dots (thousands separator) and replace comma decimal with nothing
  const cleaned = raw.replace(/\./g, '').replace(/,/g, '').replace(/\s/g, '')
  return parseInt(cleaned, 10) || 0
}

// --- Field Patterns for Indonesian Payslips -----------------------------------

const IDR_PATTERNS = [
  /(?:Rp\.?\s*)([\d.,]+)/gi,       // "Rp 1.234.567" or "Rp. 1.234.567"
  /(?:IDR\s*)([\d.,]+)/gi,          // "IDR 1234567"
  /(?:Rupiah\s*)([\d.,]+)/gi,       // "Rupiah 1.234.567"
]

const FIELD_PATTERNS: Record<string, RegExp[]> = {
  grossSalary: [
    /gaji\s*(?:bruto|pokok|dasar|kotor)[:\s]+([\d.,]+)/i,
    /total\s*(?:gaji|penghasilan)[:\s]+([\d.,]+)/i,
    /basic\s*salary[:\s]+([\d.,]+)/i,
    /upah\s*(?:bruto|kotor)[:\s]+([\d.,]+)/i,
    /bruto[:\s]*([\d.,]+)/i,
    /(?:salary|gaji)[:\s]+([\d.,]+)/i,
  ],
  pph21: [
    /(?:pph\s*21|pph21|pajak\s*penghasilan\s*pasal\s*21)[:\s]+([\d.,]+)/i,
    /(?:income\s*tax|withholding\s*tax)[:\s]+([\d.,]+)/i,
    /pph\s*21[:\s]*([\d.,]+)/i,
  ],
  jhtEmployee: [
    /jht\s*(?:karyawan|pekerja|peserta)[:\s]+([\d.,]+)/i,
    /jaminan\s*hari\s*tua[:\s]+([\d.,]+)/i,
    /jht\s*2%[:\s]+([\d.,]+)/i,
    /jht[:\s]*([\d.,]+)/i,
  ],
  jpEmployee: [
    /jp\s*(?:karyawan|pekerja|peserta)[:\s]+([\d.,]+)/i,
    /jaminan\s*pensiun[:\s]+([\d.,]+)/i,
    /jp\s*1%[:\s]+([\d.,]+)/i,
    /jaminan\s*pensiun\s*karyawan[:\s]+([\d.,]+)/i,
    /jp[:\s]*([\d.,]+)/i,
  ],
  kesehatanEmployee: [
    /(?:jkn|kesehatan|bpjs\s*kes(?:ehatan)?)\s*(?:karyawan|peserta|1%)[:\s]+([\d.,]+)/i,
    /potongan\s*kesehatan[:\s]+([\d.,]+)/i,
    /bpjs\s*kesehatan[:\s]*([\d.,]+)/i,
    /kesehatan[:\s]*([\d.,]+)/i,
  ],
  takeHome: [
    /(?:take\s*home\s*pay|thp)[:\s]+([\d.,]+)/i,
    /(?:gaji|penghasilan)\s*(?:diterima|bersih|nett?)[:\s]+([\d.,]+)/i,
    /(?:jumlah\s*diterima|total\s*diterima)[:\s]+([\d.,]+)/i,
    /net(?:t)?\s*(?:salary|pay)[:\s]*([\d.,]+)/i,
    /diterima[:\s]*([\d.,]+)/i,
  ],
}

// --- Extracted Fields Type ---------------------------------------------------

export interface ExtractedPayslipFields {
  grossSalary?: number
  pph21?: number
  jhtEmployee?: number
  jpEmployee?: number
  kesehatanEmployee?: number
  takeHome?: number
}

// --- Field Extraction -------------------------------------------------------

/**
 * Extract payslip fields from raw OCR text using regex patterns.
 * First match per field wins.
 */
export function extractFieldsFromText(text: string): ExtractedPayslipFields {
  const result: Partial<ExtractedPayslipFields> = {}

  for (const [fieldName, patterns] of Object.entries(FIELD_PATTERNS)) {
    for (const pattern of patterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const value = parseIDR(match[1])
        if (value > 0) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          ;(result as any)[fieldName] = value
          break // first match wins
        }
      }
    }
  }

  return result as ExtractedPayslipFields
}

// --- Confidence Scoring -----------------------------------------------------

export type FieldConfidences = Record<string, number>

/**
 * Calculate per-field confidence scores based on sanity checks.
 * Returns 0-1 confidence per field.
 */
export function calculateFieldConfidences(
  extracted: ExtractedPayslipFields,
  _rawText: string
): FieldConfidences {
  const confidences: FieldConfidences = {}

  for (const [field, value] of Object.entries(extracted)) {
    if (!value || value === 0) {
      confidences[field] = 0
      continue
    }

    if (field === 'grossSalary') {
      // Valid range: Rp 500K ? Rp 1B
      confidences[field] = value >= 500_000 && value <= 1_000_000_000 ? 0.90 : 0.40
    } else if (field === 'pph21') {
      // PPh21 should be non-negative and reasonable (< Rp 500M/year -> < ~42M/month)
      confidences[field] = value >= 0 && value < 500_000_000 ? 0.85 : 0.40
    } else if (field === 'jhtEmployee' || field === 'jpEmployee' || field === 'kesehatanEmployee') {
      // Deduction should be non-negative
      confidences[field] = value >= 0 ? 0.80 : 0.40
    } else if (field === 'takeHome') {
      // Take-home should be reasonable relative to gross
      confidences[field] = value > 0 ? 0.75 : 0.40
    } else {
      confidences[field] = 0.70
    }
  }

  return confidences
}

// --- Routing Decision -------------------------------------------------------

export type OCRRoutingDecision = 'AUTO_ACCEPT' | 'SOFT_CHECK' | 'MANUAL_REQUIRED'

/**
 * Determine routing based on overall OCR confidence.
 * AUTO_ACCEPT: auto-submit without confirmation
 * SOFT_CHECK: show confirmation screen
 * MANUAL_REQUIRED: force manual entry
 */
export function getRoutingDecision(
  overallConfidence: number,
  fieldConfidences: FieldConfidences,
  source: 'google_vision' | 'tesseract'
): OCRRoutingDecision {
  // Google Vision: more reliable
  if (source === 'google_vision') {
    if (overallConfidence >= 0.92) return 'AUTO_ACCEPT'
    if (overallConfidence >= 0.80) return 'SOFT_CHECK'
    return 'MANUAL_REQUIRED'
  }

  // Tesseract: less reliable, always be more conservative
  const lowConfidenceFields = Object.values(fieldConfidences).filter((c) => c < 0.80).length
  if (lowConfidenceFields === 0 && overallConfidence >= 0.70) return 'SOFT_CHECK'
  return 'MANUAL_REQUIRED'
}

// --- Combined Extraction Result ---------------------------------------------

export interface OCRExtractionResult {
  source: 'google_vision' | 'tesseract' | 'tesseract_client'
  confidence: number
  routingDecision: OCRRoutingDecision
  extractedFields: ExtractedPayslipFields
  fieldConfidences: FieldConfidences
  rawText?: string
  requiresClientOCR?: boolean
  filePath?: string
  message?: string
  requiresConfirmation: string[] // field names with low confidence
}