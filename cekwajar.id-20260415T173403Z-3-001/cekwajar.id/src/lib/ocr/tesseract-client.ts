// cekwajar.id -- Tesseract.js Client-side OCR
// Browser-based fallback when Google Vision quota is exceeded
// ==========================================================================

import {
  extractFieldsFromText,
  calculateFieldConfidences,
  getRoutingDecision,
  type OCRExtractionResult,
  type ExtractedPayslipFields,
} from './field-extractor'

// Tesseract.js -- lazy loaded only when needed

// ==========================================================================
// Client-side Tesseract OCR
// ==========================================================================

/**
 * Run Tesseract.js OCR in the browser.
 * Must be called client-side only (uses window/tesseract.js browser APIs).
 *
 * @param imageFile - The image/PDF file to process
 * @param onProgress - Optional callback for progress updates (0-100)
 */
export async function extractWithTesseract(
  imageFile: File,
  onProgress?: (progress: number) => void
): Promise<OCRExtractionResult> {
  // Dynamic import -- only loaded when actually needed (browser only)
  const { createWorker } = await import('tesseract.js')

  const worker = await createWorker(['ind', 'eng'], 1, {
    logger: (m: { status: string; progress: number }) => {
      if (m.status === 'recognizing text' && onProgress) {
        onProgress(Math.round(m.progress * 100))
      }
    },
  })

  const { data } = await worker.recognize(imageFile)
  await worker.terminate()

  // Apply 15% penalty -- Tesseract is less accurate than Google Vision
  const adjustedConfidence = (data.confidence / 100) * 0.85

  // Extract fields using same patterns as Vision
  const extractedFields: ExtractedPayslipFields = extractFieldsFromText(data.text)
  const fieldConfidences = calculateFieldConfidences(extractedFields, data.text)

  // Routing -- Tesseract always requires more caution
  const routingDecision = getRoutingDecision(adjustedConfidence, fieldConfidences, 'tesseract')

  // For Tesseract, always require confirmation of all extracted fields
  // since confidence is lower
  const requiresConfirmation = Object.keys(extractedFields)

  return {
    source: 'tesseract_client',
    confidence: adjustedConfidence,
    routingDecision,
    extractedFields,
    fieldConfidences,
    rawText: data.text,
    requiresClientOCR: false,
    requiresConfirmation,
  }
}
