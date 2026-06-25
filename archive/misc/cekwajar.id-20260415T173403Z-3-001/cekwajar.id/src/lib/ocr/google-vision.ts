// ==============================================================================
// cekwajar.id ? Google Vision OCR Integration (Server-side)
// Calls Google Cloud Vision API for document text extraction
// ==============================================================================

import {
  extractFieldsFromText,
  calculateFieldConfidences,
  getRoutingDecision,
  type OCRExtractionResult,
  type ExtractedPayslipFields,
} from './field-extractor'

const VISION_API_URL = 'https://vision.googleapis.com/v1/images:annotate'

// --- Google Vision API Call --------------------------------------------------

export async function extractWithGoogleVision(
  fileBuffer: ArrayBuffer,
  mimeType: string
): Promise<OCRExtractionResult> {
  const apiKey = process.env.GOOGLE_VISION_API_KEY

  if (!apiKey) {
    throw new Error('GOOGLE_VISION_API_KEY is not set')
  }

  const base64 = Buffer.from(fileBuffer).toString('base64')

  const requestBody = {
    requests: [
      {
        image: { content: base64 },
        features: [{ type: 'DOCUMENT_TEXT_DETECTION', maxResults: 1 }],
        imageContext: { languageHints: ['id', 'en'] },
      },
    ],
  }

  const response = await fetch(`${VISION_API_URL}?key=${apiKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Vision API error ${response.status}: ${errorText}`)
  }

  const data = (await response.json()) as {
    responses?: Array<{
      fullTextAnnotation?: {
        text: string
        pages?: Array<{ confidence?: number }>
      }
      error?: { message: string }
    }>
  }

  const annotation = data.responses?.[0]

  if (!annotation || annotation.error) {
    throw new Error(annotation?.error?.message ?? 'Vision API returned no response')
  }

  const fullText = annotation.fullTextAnnotation?.text ?? ''
  const pageConfidence = annotation.fullTextAnnotation?.pages?.[0]?.confidence ?? 0

  // Normalize confidence to 0-1
  const confidence = Math.min(1, Math.max(0, pageConfidence))

  // Extract fields using shared patterns
  const extractedFields: ExtractedPayslipFields = extractFieldsFromText(fullText)

  // Calculate per-field confidence
  const fieldConfidences = calculateFieldConfidences(extractedFields, fullText)

  // Determine routing decision
  const routingDecision = getRoutingDecision(confidence, fieldConfidences, 'google_vision')

  // Fields that need user confirmation (confidence < 0.80)
  const requiresConfirmation = Object.entries(fieldConfidences)
    .filter(([, conf]) => conf < 0.80)
    .map(([field]) => field)

  return {
    source: 'google_vision',
    confidence,
    routingDecision,
    extractedFields,
    fieldConfidences,
    rawText: fullText,
    requiresClientOCR: false,
    requiresConfirmation,
  }
}