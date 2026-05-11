---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/architecture/cekwajar-ocr-pipeline.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-10T01:00:00.605771"
}
---

---
title: cekwajar-ocr-pipeline
type: architecture
status: active
tags: [cekwajar, ocr, google-vision, tesseract, payslip, document-processing, confidence-threshold]
created: 2026-04-13
updated: 2026-04-13
summary: "The cekwajar.id OCR pipeline routes payslip images through Google Cloud Vision API (primary) with confidence threshold routing: AUTO_ACCEPT at 0.92 confidence (proceed directly), SOFT_CHECK at 0.80 (show to user for confirmation), and MANUAL_REQUIRED at 0.70 (block verdict, require manual entry). Tesseract.js provides fallback. Before launch, 200 real payslip samples across 5 categories must validate ≥92% per-field accuracy on digital PDFs and ≥75% on photos."
wikilinks:
  - [[projects/cekwajar-id]]
  - [[architecture/cekwajar-verdict-engine]]
  - [[entities/supabase]]
confidence: high
source: implementation
---

# cekwajar OCR Pipeline Architecture

## TL;DR

The cekwajar.id OCR pipeline processes payslip uploads through a confidence-gated routing system: Google Cloud Vision API handles initial OCR, Tesseract.js provides fallback, and confidence scores determine whether to auto-accept results, prompt user verification, or require full manual entry. Three thresholds govern routing: AUTO_ACCEPT (0.92), SOFT_CHECK (0.80), MANUAL_REQUIRED (0.70). Pre-launch validation requires testing on 200 real Indonesian payslips across 5 categories — digital PDFs must achieve ≥92% per-field accuracy, photos ≥75% — before OCR path can be enabled for public use.

---

## 1. Pipeline Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        OCR PIPELINE                                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────┐     ┌──────────────────┐     ┌──────────────────┐    │
│  │  PDF/Image │────▶│  Google Cloud    │────▶│  Confidence      │    │
│  │  Upload    │     │  Vision API      │     │  Scoring         │    │
│  └────────────┘     │  (Document AI)   │     │                  │    │
│                    └──────────────────┘     └──────────────────┘    │
│                            │                        │              │
│                            │                        ▼              │
│                            │              ┌──────────────────┐     │
│                            │              │  Threshold Check │     │
│                            │              └──────────────────┘     │
│                            │                        │              │
│              ┌─────────────┼────────────┬───────────┘              │
│              ▼             ▼            ▼                          │
│     ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│     │ AUTO       │  │ SOFT       │  │ MANUAL     │                │
│     │ ACCEPT     │  │ CHECK      │  │ REQUIRED   │                │
│     │ ≥0.92      │  │ 0.80-0.91  │  │ <0.70      │                │
│     └────────────┘  └────────────┘  └────────────┘                │
│           │               │              │                         │
│           ▼               ▼              ▼                         │
│     ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│     │ Proceed to │  │ Show to    │  │ Block      │                │
│     │ Verdict    │  │ user with │  │ verdict,   │                │
│     │ Engine     │  │ editable   │  │ require    │                │
│     │            │  │ fields     │  │ manual     │                │
│     └────────────┘  └────────────┘  │ entry      │                │
│                                     └────────────┘                │
│                                           │                        │
│                                     ┌────────────┐                │
│                                     │ Tesseract  │                │
│                                     │ fallback   │                │
│                                     │ (if Vision │                │
│                                     │  <0.80)    │                │
│                                     └────────────┘                │
│                                           │                        │
└───────────────────────────────────────────┼────────────────────────┘
                                            ▼
                                     ┌────────────┐
                                     │ Verdict    │
                                     │ Engine     │
                                     │ (Stage 2+) │
                                     └────────────┘
```

---

## 2. OCR Engine Selection

### 2.1 Primary: Google Cloud Vision Document AI

Google Cloud Vision Document AI (formerly Textract) is the primary OCR engine for its superior performance on:
- Structured tables and forms
- Mixed-language documents (Indonesian + English payslips)
- PDF documents (not just images)

**Configuration for Indonesian payslips**:
```python
from google.cloud import documentai_v1 as documentai

def process_payslip_document(
    project_id: str,
    location: str,
    processor_id: str,
    file_content: bytes,
    mime_type: str
) -> documentai.Document:
    """
    Process payslip using Google Cloud Document AI.
    
    Args:
        project_id: GCP project ID
        location: Processor location (e.g., 'us')
        processor_id: Document AI processor ID
        file_content: Raw file bytes (PDF or image)
        mime_type: 'application/pdf', 'image/png', 'image/jpeg'
    
    Returns:
        Extracted document with confidence scores per field
    """
    client = documentai.DocumentProcessorServiceClient()
    
    raw_document = documentai.RawDocument(
        content=file_content,
        mime_type=mime_type
    )
    
    request = documentai.ProcessDocumentRequest(
        name=f"projects/{project_id}/locations/{location}/processors/{processor_id}",
        raw_document=raw_document,
        # Enable table extraction
        process_options=documentai.ProcessOptions(
            layout_config=documentai.ProcessOptions.LayoutConfig(
                trigger_page_orientation_detection=True
            )
        )
    )
    
    result = client.process_document(request=request)
    return result.document
```

### 2.2 Fallback: Tesseract.js

For environments where Google Vision is unavailable or cost-prohibitive:

```javascript
import Tesseract from 'tesseract.js';

async function extractWithTesseract(imageBuffer: Buffer): Promise<{
  text: string;
  confidence: number;
}> {
  const result = await Tesseract.recognize(imageBuffer, 'ind+eng', {
    logger: (m) => console.log(m),
  });
  
  return {
    text: result.data.text,
    confidence: result.data.confidence / 100,  // Tesseract returns 0-100
  };
}
```

### 2.3 Engine Selection Decision Tree

```
Input: Payslip file (PDF or image)
│
├─▶ Google Cloud Vision API (Document AI)
│   │
│   ├─▶ Confidence ≥ 0.92: AUTO_ACCEPT
│   │
│   ├─▶ Confidence 0.80-0.91: SOFT_CHECK
│   │   └─▶ Show extracted fields to user for verification
│   │
│   ├─▶ Confidence 0.70-0.79: 
│   │   └─▶ Tesseract.js fallback
│   │       ├─▶ Tesseract ≥ 0.80: SOFT_CHECK with Tesseract data
│   │       └─▶ Tesseract < 0.80: MANUAL_REQUIRED
│   │
│   └─▶ Confidence < 0.70: MANUAL_REQUIRED
│       └─▶ Block verdict, show manual entry form
```

---

## 3. Confidence Threshold Routing

### 3.1 Threshold Definitions

```typescript
const OCR_CONFIDENCE_THRESHOLDS = {
  AUTO_ACCEPT: 0.92,    // Proceed to verdict without user input
  SOFT_CHECK: 0.80,     // Show extracted values, require confirmation
  MANUAL_REQUIRED: 0.70, // Block verdict, require manual entry
} as const;

type ThresholdLevel = 'AUTO_ACCEPT' | 'SOFT_CHECK' | 'MANUAL_REQUIRED';

function routeByConfidence(confidence: number): ThresholdLevel {
  if (confidence >= OCR_CONFIDENCE_THRESHOLDS.AUTO_ACCEPT) {
    return 'AUTO_ACCEPT';
  } else if (confidence >= OCR_CONFIDENCE_THRESHOLDS.SOFT_CHECK) {
    return 'SOFT_CHECK';
  }
  return 'MANUAL_REQUIRED';
}
```

### 3.2 Per-Field Confidence Routing

Not all fields have equal importance. Route on a per-field basis:

| Field | P0/P1/P2 | Min Confidence | Action if Below |
|-------|----------|---------------|-----------------|
| Gaji Pokok | P0 | 0.92 | MANUAL_REQUIRED |
| Total Tunjangan | P0 | 0.90 | MANUAL_REQUIRED |
| BPJS JHT (EE) | P0 | 0.92 | MANUAL_REQUIRED |
| BPJS JP (EE) | P0 | 0.92 | MANUAL_REQUIRED |
| BPJS Kesehatan (EE) | P0 | 0.92 | MANUAL_REQUIRED |
| PPh21 amount | P0 | 0.90 | MANUAL_REQUIRED |
| Gaji Bersih | P0 | 0.92 | MANUAL_REQUIRED |
| Period (month/year) | P1 | 0.80 | SOFT_CHECK |
| Company name | P2 | 0.70 | MANUAL_ENTRY_ALLOWED |

**Rule**: If any P0 field is below threshold, trigger MANUAL_REQUIRED regardless of overall confidence.

---

## 4. Field Extraction Patterns

### 4.1 Indonesian Payslip Field Patterns

Indonesian payslips follow inconsistent formats. Extract using regex patterns:

```python
import re

PAYSLIP_PATTERNS = {
    # Gaji Pokok patterns
    'gaji_pokok': [
        r'Gaji Pokok[:\s]*Rp\.?\s*([\d\.]+)',
        r'Upah Pokok[:\s]*Rp\.?\s*([\d\.]+)',
        r'Basic Salary[:\s]*Rp\.?\s*([\d\.]+)',
    ],
    
    # BPJS patterns
    'bpjs_jht': [
        r'JHT[:\s]*Rp\.?\s*([\d\.]+)',
        r'Jaminan Hari Tua[:\s]*Rp\.?\s*([\d\.]+)',
    ],
    'bpjs_jp': [
        r'JP[:\s]*Rp\.?\s*([\d\.]+)',
        r'Jaminan Pensiun[:\s]*Rp\.?\s*([\d\.]+)',
    ],
    'bpjs_kesehatan': [
        r'BPJS Kesehatan[:\s]*Rp\.?\s*([\d\.]+)',
        r'Kesehatan[:\s]*Rp\.?\s*([\d\.]+)',
    ],
    
    # PPh21 patterns
    'pph21': [
        r'PPh\s*21[:\s]*Rp\.?\s*([\d\.]+)',
        r'Pajak Penghasilan[:\s]*Rp\.?\s*([\d\.]+)',
    ],
    
    # Net salary
    'gaji_bersih': [
        r'Gaji Bersih[:\s]*Rp\.?\s*([\d\.]+)',
        r'Take Home Pay[:\s]*Rp\.?\s*([\d\.]+)',
        r'Netto[:\s]*Rp\.?\s*([\d\.]+)',
    ],
    
    # Period
    'period': [
        r'Periode[:\s]*(\w+\s+\d{4})',
        r'Bulan[:\s]*(\w+\s+\d{4})',
        r'(\w+\s+\d{4})',
    ]
}

def extract_field(text: str, field: str) -> tuple[Optional[str], float]:
    """
    Extract field value using regex patterns.
    Returns (value, confidence) tuple.
    """
    patterns = PAYSLIP_PATTERNS.get(field, [])
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Confidence is based on which pattern matched (earlier = more common)
            confidence = 1.0 - (patterns.index(pattern) * 0.05)
            return match.group(1), confidence
    return None, 0.0
```

### 4.2 Validation: Cross-Field Consistency

After extraction, validate consistency:

```python
def validate_extraction(extracted: dict) -> dict:
    """
    Cross-validate extracted fields.
    
    Rule: gross - deductions should equal net
    If variance > 5%, flag for review.
    """
    gross = extracted.get('gaji_pokok', 0) + extracted.get('tunjangan_total', 0)
    deductions = sum(extracted.get(d, 0) for d in ['bpjs_jht', 'bpjs_jp', 'bpjs_kesehatan', 'pph21', 'other'])
    net_calculated = gross - deductions
    
    variance = abs(net_calculated - extracted.get('gaji_bersih', 0))
    variance_pct = variance / net_calculated if net_calculated > 0 else 1.0
    
    if variance_pct > 0.05:
        return {
            **extracted,
            '_validation_warnings': [f'Net salary variance: {variance_pct:.1%}']
        }
    return extracted
```

---

## 5. Pre-Launch Validation Requirements

### 5.1 Test Corpus (200 Payslips)

Before enabling OCR for public launch, validate on this corpus:

| Category | Sample Size | Description | Required Accuracy |
|----------|------------|-------------|-------------------|
| Large corp PDF (digital-native) | 60 | SAP/Oracle HR systems, consistent layout | ≥ 97% per-field |
| SME Excel-to-PDF | 50 | Variable layout, converted from Excel | ≥ 92% per-field |
| Startup HTML payslip | 30 | Mekari/Gadjian-generated digital | ≥ 95% per-field |
| Government payslip (ASN) | 20 | Fixed format, often printed+scanned | ≥ 88% per-field |
| Mobile photo of paper | 40 | Variable lighting, rotation, blur | ≥ 75% per-field |

**Total: 200 payslips**

### 5.2 Required Accuracy by Field

| Priority | Field | Digital PDF | Photo |
|----------|-------|-------------|-------|
| P0 | Gaji Pokok | ≥ 92% | ≥ 75% |
| P0 | Total Tunjangan | ≥ 92% | ≥ 75% |
| P0 | BPJS JHT (EE) | ≥ 92% | ≥ 75% |
| P0 | BPJS JP (EE) | ≥ 92% | ≥ 75% |
| P0 | BPJS Kesehatan (EE) | ≥ 92% | ≥ 75% |
| P0 | PPh21 | ≥ 90% | ≥ 70% |
| P0 | Gaji Bersih | ≥ 92% | ≥ 75% |
| P1 | Period | ≥ 85% | ≥ 70% |
| P2 | Company Name | ≥ 80% | ≥ 60% |

### 5.3 Launch Gate

```
IF overall per-field accuracy on digital PDFs < 90%:
    → DELAY LAUNCH
    → Fix extraction logic
    
IF overall per-field accuracy on photos < 70%:
    → DISABLE PHOTO UPLOAD
    → PDF-only launch
```

---

## 6. Error Handling

### 6.1 API Failure Handling

```python
async def process_with_fallback(file_content: bytes, mime_type: str) -> dict:
    """
    Process payslip with fallback chain:
    1. Google Vision Document AI
    2. Tesseract.js (via subprocess)
    3. Manual entry form (last resort)
    """
    try:
        # Attempt 1: Google Vision
        result = await call_google_vision(file_content, mime_type)
        if result.confidence >= OCR_CONFIDENCE_THRESHOLDS.SOFT_CHECK:
            return result
    except GoogleVisionError as e:
        logger.warning(f"Google Vision failed: {e}")
    
    try:
        # Attempt 2: Tesseract
        result = await call_tesseract(file_content)
        if result.confidence >= OCR_CONFIDENCE_THRESHOLDS.SOFT_CHECK:
            return result
    except TesseractError as e:
        logger.warning(f"Tesseract failed: {e}")
    
    # Fallback 3: Manual entry
    return {
        'status': 'MANUAL_REQUIRED',
        'message': 'Could not extract payslip data automatically. Please enter manually.',
        'redirect_to_form': True
    }
```

### 6.2 File Upload Validation

```python
ALLOWED_MIME_TYPES = ['application/pdf', 'image/png', 'image/jpeg']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_file(file_content: bytes, mime_type: str) -> tuple[bool, str]:
    """
    Validate uploaded file before OCR processing.
    """
    if mime_type not in ALLOWED_MIME_TYPES:
        return False, f'File type {mime_type} not supported. Upload PDF, PNG, or JPEG.'
    
    if len(file_content) > MAX_FILE_SIZE:
        return False, f'File too large. Maximum size is 5MB.'
    
    # Malware scan (optional, recommended before production)
    # if scan_for_malware(file_content):
    #     return False, 'File rejected: potential malware detected'
    
    return True, 'OK'
```

---

## 7. Security and Privacy

### 7.1 Data Flow

```
User Upload → HTTPS → Supabase Storage (encrypted at rest, ap-southeast-1)
                                    ↓
                    Edge Function: validate_file (type, size)
                                    ↓
                    OCR API call (Vision API) — no raw image stored with PII
                                    ↓
                    Structured fields → payslip_submissions table
                                    ↓
                    Raw file → deleted after 30 days (pg_cron)
```

### 7.2 Never Stored Permanently

- Raw payslip file after 30 days (automated deletion)
- Full company name in linkable form (anonymized to industry after 90 days)
- NIK if visible on payslip (redacted before storing)

---

## Related Articles

- [[projects/cekwajar-id]] — Project using this pipeline
- [[architecture/cekwajar-verdict-engine]] — Verdict engine that consumes OCR output
- [[entities/supabase]] — Storage and database
