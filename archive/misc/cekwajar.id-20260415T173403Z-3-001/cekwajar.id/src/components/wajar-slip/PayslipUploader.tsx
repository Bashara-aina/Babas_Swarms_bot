'use client'

// ==============================================================================
// cekwajar.id ? Payslip Uploader Component
// Drag & drop -> upload -> OCR -> confirm -> auto-fill
// States: IDLE | UPLOADING | PROCESSING | OCR_CONFIRM | ERROR
// ==============================================================================

import { useState, useCallback, useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import {
  Upload, FileText, Camera, AlertCircle, CheckCircle2,
  Loader2, RefreshCw, X, AlertTriangle, Eye
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { extractWithTesseract } from '@/lib/ocr/tesseract-client'
import { COPY } from '@/lib/copy'
import type { ExtractedPayslipFields, FieldConfidences } from '@/lib/ocr/field-extractor'

// --- Types -------------------------------------------------------------------

type OCRSource = 'google_vision' | 'tesseract' | 'tesseract_client'

type RoutingDecision = 'AUTO_ACCEPT' | 'SOFT_CHECK' | 'MANUAL_REQUIRED'

interface OCRResult {
  source: OCRSource
  confidence: number
  routingDecision: RoutingDecision
  extractedFields: ExtractedPayslipFields
  fieldConfidences: FieldConfidences
  requiresClientOCR: boolean
  filePath?: string
  message?: string
  requiresConfirmation: string[]
}

type UploaderState =
  | { phase: 'IDLE' }
  | { phase: 'UPLOADING'; fileName: string }
  | { phase: 'VISION_PROCESSING' }
  | { phase: 'TESSERACT_PROCESSING'; progress: number }
  | { phase: 'OCR_CONFIRM'; result: OCRResult; filePath: string }
  | { phase: 'AUTO_SUBMIT'; result: OCRResult }
  | { phase: 'MANUAL_REQUIRED'; result: OCRResult }
  | { phase: 'ERROR'; message: string }

// --- Props -------------------------------------------------------------------

interface PayslipUploaderProps {
  onFieldsExtracted: (
    fields: ExtractedPayslipFields,
    filePath: string,
    source: string
  ) => void
  onManualMode: () => void
}

// --- Component ---------------------------------------------------------------

export function PayslipUploader({ onFieldsExtracted, onManualMode }: PayslipUploaderProps) {
  const [state, setState] = useState<UploaderState>({ phase: 'IDLE' })
  const tesseractStarted = useRef(false)

  // --- Upload + OCR flow ---------------------------------------------------

  const uploadAndOCR = useCallback(async (file: File, sessionId: string) => {
    setState({ phase: 'UPLOADING', fileName: file.name })

    const formData = new FormData()
    formData.append('file', file)
    formData.append('sessionId', sessionId)

    let res: Response
    try {
      res = await fetch('/api/ocr/upload', {
        method: 'POST',
        body: formData,
      })
    } catch {
      setState({ phase: 'ERROR', message: COPY.error.networkError })
      return
    }

    const json = await res.json()

    if (!res.ok || !json.success) {
      setState({ phase: 'ERROR', message: COPY.error.ocrFailed })
      return
    }

    const result: OCRResult = {
      source: json.data.source,
      confidence: json.data.confidence,
      routingDecision: json.data.routingDecision,
      extractedFields: json.data.extractedFields,
      fieldConfidences: json.data.fieldConfidences,
      requiresClientOCR: json.data.requiresClientOCR ?? false,
      filePath: json.data.filePath,
      message: json.data.message,
      requiresConfirmation: json.data.requiresConfirmation ?? [],
    }

    const filePath = json.data.filePath ?? ''

    // Route based on result
    if (result.requiresClientOCR) {
      // Quota exceeded -> use Tesseract client-side
      setState({ phase: 'TESSERACT_PROCESSING', progress: 0 })
      tesseractStarted.current = true

      try {
        const tessResult = await extractWithTesseract(file, (p) => {
          setState({ phase: 'TESSERACT_PROCESSING', progress: p })
        })
        const mergedResult: OCRResult = {
          ...tessResult,
          filePath,
          requiresClientOCR: false,
        }
        handleOCRResult(mergedResult, filePath)
      } catch {
        setState({ phase: 'ERROR', message: 'OCR lokal gagal. Silakan isi manual.' })
      }
    } else if (result.routingDecision === 'AUTO_ACCEPT') {
      // High confidence -> auto-submit
      setState({ phase: 'AUTO_SUBMIT', result })
      onFieldsExtracted(result.extractedFields, filePath, result.source)
    } else if (result.routingDecision === 'SOFT_CHECK') {
      setState({ phase: 'OCR_CONFIRM', result, filePath })
    } else {
      // MANUAL_REQUIRED -> pre-fill what we can, let user complete manually
      setState({ phase: 'MANUAL_REQUIRED', result })
      onFieldsExtracted(result.extractedFields, filePath, result.source)
    }
  }, [onFieldsExtracted])

  // --- Handle OCR result after any source completes ----------------------

  const handleOCRResult = (result: OCRResult, filePath: string) => {
    if (result.routingDecision === 'AUTO_ACCEPT') {
      setState({ phase: 'AUTO_SUBMIT', result })
      onFieldsExtracted(result.extractedFields, filePath, result.source)
    } else if (result.routingDecision === 'SOFT_CHECK') {
      setState({ phase: 'OCR_CONFIRM', result, filePath })
    } else {
      setState({ phase: 'MANUAL_REQUIRED', result })
      onFieldsExtracted(result.extractedFields, filePath, result.source)
    }
  }

  // --- Confirm extracted fields --------------------------------------------

  const handleConfirm = (result: OCRResult, filePath: string) => {
    setState({ phase: 'AUTO_SUBMIT', result })
    onFieldsExtracted(result.extractedFields, filePath, result.source)
  }

  // --- Reset -------------------------------------------------------------

  const handleReset = () => {
    setState({ phase: 'IDLE' })
    tesseractStarted.current = false
  }

  // --- Drop handler ------------------------------------------------------

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return
    const sessionId = crypto.randomUUID()
    uploadAndOCR(file, sessionId)
  }, [uploadAndOCR])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': [],
      'image/png': [],
      'image/webp': [],
      'application/pdf': [],
    },
    maxSize: 5 * 1024 * 1024,
    multiple: false,
  })

  // --- Render IDLE -------------------------------------------------------

  if (state.phase === 'IDLE') {
    return (
      <Card className="border-dashed border-2 border-border bg-muted">
        <CardContent className="flex flex-col items-center justify-center py-12 px-6">
          <div
            {...getRootProps()}
            className={`
              flex w-full cursor-pointer flex-col items-center justify-center
              rounded-lg border-2 border-dashed p-8 text-center transition-colors
              ${isDragActive
                ? 'border-emerald-400 bg-emerald-50'
                : 'border-border hover:border-emerald-400 hover:bg-emerald-50'
              }
            `}
          >
            <input {...getInputProps()} />
            <div className="mb-4 rounded-full bg-emerald-100 p-4">
              <Upload className="h-8 w-8 text-emerald-600" />
            </div>
            <p className="mb-1 text-base font-semibold text-foreground">
              Upload Foto atau PDF Slip Gaji
            </p>
            <p className="mb-4 text-sm text-muted-foreground">
              JPEG ? PNG ? PDF ? Maks 5MB
            </p>
            <Button size="sm" variant="outline" className="border-emerald-300 text-emerald-700">
              <Camera className="mr-2 h-4 w-4" />
              Pilih File
            </Button>
            <div className="mt-5 flex w-full items-center gap-3 text-xs text-muted-foreground">
              <div className="h-px flex-1 bg-border" />
              <span>atau</span>
              <div className="h-px flex-1 bg-border" />
            </div>
          </div>

          <button
            onClick={onManualMode}
            className="mt-4 text-sm text-muted-foreground underline hover:text-emerald-600"
          >
            Isi Manual Instead →
          </button>
        </CardContent>
      </Card>
    )
  }

  // --- Render UPLOADING ---------------------------------------------------

  if (state.phase === 'UPLOADING') {
    return (
      <Card className="border-dashed border-2 border-border bg-muted">
        <CardContent className="flex flex-col items-center justify-center py-12 px-6">
          <Loader2 className="mb-3 h-8 w-8 animate-spin text-emerald-600" />
          <p className="font-medium text-foreground">Mengupload {state.fileName}...</p>
          <p className="mt-1 text-sm text-muted-foreground">Menyimpan ke storage...</p>
        </CardContent>
      </Card>
    )
  }

  // --- Render VISION PROCESSING -------------------------------------------

  if (state.phase === 'VISION_PROCESSING') {
    return (
      <Card className="border-dashed border-2 border-emerald-300 bg-emerald-50">
        <CardContent className="flex flex-col items-center justify-center py-12 px-6">
          <div className="mb-3 flex items-center gap-2">
            <Eye className="h-6 w-6 text-emerald-600" />
            <span className="text-2xl"></span>
          </div>
          <p className="font-medium text-emerald-700">Membaca slip gaji dengan Google Vision...</p>
          <div className="mt-3 h-2 w-48 overflow-hidden rounded-full bg-emerald-200">
            <div className="h-full animate-pulse rounded-full bg-emerald-500" style={{ width: '70%' }} />
          </div>
          <p className="mt-2 text-xs text-emerald-600">Menganalisis teks dan angka...</p>
        </CardContent>
      </Card>
    )
  }

  // --- Render TESSERACT PROCESSING ----------------------------------------

  if (state.phase === 'TESSERACT_PROCESSING') {
    return (
      <Card className="border-dashed border-2 border-amber-300 bg-amber-50">
        <CardContent className="flex flex-col items-center justify-center py-12 px-6">
          <Loader2 className="mb-3 h-8 w-8 animate-spin text-amber-600" />
          <p className="font-medium text-amber-700">Membaca dengan OCR lokal...</p>
          <div className="mt-3 w-64">
            <div className="flex justify-between text-xs text-amber-600 mb-1">
              <span>Memproses...</span>
              <span>{state.progress}%</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-amber-200">
              <div
                className="h-full rounded-full bg-amber-500 transition-all duration-300"
                style={{ width: `${state.progress}%` }}
              />
            </div>
          </div>
          <p className="mt-2 text-xs text-amber-600">
            {state.progress < 50
              ? 'Menganalisis teks...'
              : state.progress < 80
              ? 'Mengekstrak angka...'
              : 'Menyempurnakan hasil...'}
          </p>
        </CardContent>
      </Card>
    )
  }

  // --- Render OCR CONFIRM -------------------------------------------------

  if (state.phase === 'OCR_CONFIRM') {
    return (
      <Card className="border-emerald-300 bg-emerald-50">
        <CardContent className="p-6">
          <div className="mb-4 flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
            <h3 className="font-semibold text-emerald-800">Konfirmasi Hasil Scan</h3>
          </div>
          <p className="mb-5 text-sm text-emerald-700">
            OCR mengekstrak data berikut dari slip gaji. Periksa dan koreksi jika perlu.
          </p>

          <div className="mb-5 space-y-3">
            {Object.entries(state.result.extractedFields).map(([field, value]) => {
              const confidence = state.result.fieldConfidences[field]
              const needsCheck = confidence < 0.80
              return (
                <div key={field}>
                  <div className="mb-1 flex items-center justify-between">
                    <Label className="text-xs font-medium text-muted-foreground capitalize">
                      {field.replace(/([A-Z])/g, ' $1').trim()}
                    </Label>
                    {needsCheck && (
                      <span className="flex items-center gap-1 text-xs text-amber-600">
                        <AlertTriangle className="h-3 w-3" />
                        Harap periksa
                      </span>
                    )}
                  </div>
                  <Input
                    key={`${field}-${value}`}
                    type="text"
                    defaultValue={value != null ? String(value) : ''}
                    className={`${needsCheck ? 'border-amber-400 bg-white' : 'border-emerald-300 bg-white'}`}
                    onChange={(e) => {
                      const parsed = parseInt(e.target.value.replace(/\D/g, '') || '0', 10)
                      // Update extracted fields in result
                      setState({
                        phase: 'OCR_CONFIRM',
                        result: {
                          ...state.result,
                          extractedFields: {
                            ...state.result.extractedFields,
                            [field]: parsed,
                          },
                        },
                        filePath: state.filePath,
                      })
                    }}
                  />
                </div>
              )
            })}
          </div>

          <div className="flex gap-3">
            <Button
              onClick={() => handleConfirm(state.result, state.filePath)}
              className="flex-1 bg-emerald-600 hover:bg-emerald-700"
            >
              Konfirmasi & Hitung →
            </Button>
          </div>

          <button
            onClick={onManualMode}
            className="mt-3 w-full text-center text-sm text-muted-foreground underline hover:text-emerald-600"
          >
            Isi Ulang Manual
          </button>

          <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
            <span>
              Confidence: {Math.round(state.result.confidence * 100)}%
              {state.result.source === 'google_vision' ? ' ? Google Vision' : ' ? OCR Lokal'}
            </span>
            <button onClick={handleReset} className="flex items-center gap-1 hover:text-foreground">
              <RefreshCw className="h-3 w-3" />
              Upload Ulang
            </button>
          </div>
        </CardContent>
      </Card>
    )
  }

  // --- Render MANUAL REQUIRED ---------------------------------------------

  if (state.phase === 'MANUAL_REQUIRED') {
    return (
      <Card className="border-amber-300 bg-amber-50">
        <CardContent className="flex flex-col items-center py-8 px-6 text-center">
          <AlertTriangle className="mb-3 h-8 w-8 text-amber-600" />
          <p className="font-semibold text-amber-800">OCR Tidak Dapat Membaca Slip</p>
          <p className="mt-1 text-sm text-amber-700">
            {state.result.message ?? 'Hasil scan tidak cukup akurat. Silakan isi manual.'}
          </p>
          <p className="mt-2 text-xs text-amber-600">
            Data yang berhasil dibaca telah diisi ke form.
          </p>
          <Button
            onClick={onManualMode}
            className="mt-4 bg-emerald-600 hover:bg-emerald-700"
          >
            Lanjut Isi Manual →
          </Button>
        </CardContent>
      </Card>
    )
  }

  // --- Render AUTO SUBMIT -------------------------------------------------

  if (state.phase === 'AUTO_SUBMIT') {
    return (
      <Card className="border-emerald-300 bg-emerald-50">
        <CardContent className="flex flex-col items-center py-8 px-6 text-center">
          <Loader2 className="mb-3 h-8 w-8 animate-spin text-emerald-600" />
          <p className="font-semibold text-emerald-800">AI menganalisis slip gaji...</p>
          <p className="mt-1 text-sm text-emerald-600">
            Confidence tinggi ({Math.round(state.result.confidence * 100)}%) ? langsung proses.
          </p>
        </CardContent>
      </Card>
    )
  }

  // --- Render ERROR -------------------------------------------------------

  if (state.phase === 'ERROR') {
    return (
      <Card className="border-red-300 bg-red-50">
        <CardContent className="flex flex-col items-center py-8 px-6 text-center">
          <AlertCircle className="mb-3 h-8 w-8 text-red-500" />
          <p className="font-semibold text-red-800">Upload Gagal</p>
          <p className="mt-1 text-sm text-red-600">{state.message}</p>
          <Button
            onClick={handleReset}
            variant="outline"
            className="mt-4 border-red-300 text-red-600 hover:bg-red-50"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Coba Lagi
          </Button>
        </CardContent>
      </Card>
    )
  }

  return null
}