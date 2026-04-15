'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Wajar Slip Page (Full Client Component)
// Stage 4: Manual form + PPh21 TER + BPJS + violation detectors
// ══════════════════════════════════════════════════════════════════════════════

import { useReducer, useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { AlertCircle, CheckCircle2, X, Loader2, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { PremiumGate } from '@/components/shared/PremiumGate'
import { ViolationItem } from '@/components/wajar-slip/ViolationItem'
import { UMKBadge } from '@/components/wajar-slip/UMKBadge'
import type { SubscriptionTier, Violation } from '@/types'

// ─── Types ────────────────────────────────────────────────────────────────────

type SlipState =
  | { status: 'IDLE' }
  | { status: 'MANUAL_FORM' }
  | { status: 'CALCULATING' }
  | { status: 'VERDICT'; data: AuditResult }
  | { status: 'ERROR'; message: string }

interface AuditResult {
  auditId: string | null
  verdict: 'SESUAI' | 'ADA_PELANGGARAN'
  violationCount: number
  violationCodes: string[]
  violations: GatedViolation[]
  calculations?: {
    correctPph21: number
    correctJht: number
    correctJp: number
    correctKesehatan: number
    cityUMK: number
  }
  isGated: boolean
  gateMessage?: string
  subscriptionRequired?: 'basic' | 'pro'
  cityUMK: number
  city: string
  grossSalary: number
  monthNumber: number
  year: number
}

interface GatedViolation extends Omit<Violation, 'differenceIDR'> {
  differenceIDR: number | null
}

type SlipAction =
  | { type: 'SHOW_FORM' }
  | { type: 'SUBMIT' }
  | { type: 'SUCCESS'; data: AuditResult }
  | { type: 'ERROR'; message: string }
  | { type: 'RESET' }

// ─── Form Schema (input type — strings, parsed in onSubmit) ───────────────────

const PTKP_LABELS: Record<string, string> = {
  'TK/0': 'Tidak Kawin, 0 tanggungan',
  'TK/1': 'Tidak Kawin, 1 tanggungan',
  'TK/2': 'Tidak Kawin, 2 tanggungan',
  'TK/3': 'Tidak Kawin, 3 tanggungan',
  'K/0':  'Kawin, 0 tanggungan',
  'K/1':  'Kawin, 1 tanggungan',
  'K/2':  'Kawin, 2 tanggungan',
  'K/3':  'Kawin, 3 tanggungan',
  'K/I/0': 'Kawin + Istri/Suami, 0 tanggungan',
  'K/I/1': 'Kawin + Istri/Suami, 1 tanggungan',
  'K/I/2': 'Kawin + Istri/Suami, 2 tanggungan',
  'K/I/3': 'Kawin + Istri/Suami, 3 tanggungan',
}

const MONTHS = [
  { value: 1, label: 'Januari' },
  { value: 2, label: 'Februari' },
  { value: 3, label: 'Maret' },
  { value: 4, label: 'April' },
  { value: 5, label: 'Mei' },
  { value: 6, label: 'Juni' },
  { value: 7, label: 'Juli' },
  { value: 8, label: 'Agustus' },
  { value: 9, label: 'September' },
  { value: 10, label: 'Oktober' },
  { value: 11, label: 'November' },
  { value: 12, label: 'Desember' },
]

// Schema for API submission (numbers)
const apiSchema = z.object({
  grossSalary: z.number().min(500_000).max(1_000_000_000),
  ptkpStatus: z.enum([
    'TK/0','TK/1','TK/2','TK/3',
    'K/0','K/1','K/2','K/3',
    'K/I/0','K/I/1','K/I/2','K/I/3',
  ]),
  city: z.string().min(1),
  monthNumber: z.number().int().min(1).max(12),
  year: z.number().int().min(2024).max(2030),
  hasNPWP: z.boolean(),
  reportedPph21: z.number().min(0),
  reportedJht: z.number().min(0),
  reportedJp: z.number().min(0),
  reportedKesehatan: z.number().min(0),
  takeHome: z.number().min(0),
})

type ApiPayload = z.infer<typeof apiSchema>

// Helper: parse IDR string to number
function parseIDR(v: string): number {
  return parseInt(v.replace(/\D/g, '') || '0', 10)
}

// Schema for form (all strings — react-hook-form compatible)
const formSchema = z.object({
  grossSalary: z.string().min(1, 'Wajib diisi'),
  ptkpStatus: z.enum([
    'TK/0','TK/1','TK/2','TK/3',
    'K/0','K/1','K/2','K/3',
    'K/I/0','K/I/1','K/I/2','K/I/3',
  ]),
  city: z.string().min(1, 'Pilih kota'),
  monthNumber: z.string(),
  year: z.string(),
  hasNPWP: z.boolean(),
  reportedPph21: z.string(),
  reportedJht: z.string(),
  reportedJp: z.string(),
  reportedKesehatan: z.string(),
  takeHome: z.string(),
})

type FormValues = z.infer<typeof formSchema>

// ─── Reducer ─────────────────────────────────────────────────────────────────

function slipReducer(state: SlipState, action: SlipAction): SlipState {
  switch (action.type) {
    case 'SHOW_FORM':
      return { status: 'MANUAL_FORM' }
    case 'SUBMIT':
      return { status: 'CALCULATING' }
    case 'SUCCESS':
      return { status: 'VERDICT', data: action.data }
    case 'ERROR':
      return { status: 'ERROR', message: action.message }
    case 'RESET':
      return { status: 'IDLE' }
    default:
      return state
  }
}

// ─── City type ───────────────────────────────────────────────────────────────

interface CityOption {
  city: string
  province: string
  umk: number
}

// ─── Page Component ───────────────────────────────────────────────────────────

export default function WajarSlipPage() {
  const [state, dispatch] = useReducer(slipReducer, { status: 'IDLE' })
  const [cities, setCities] = useState<CityOption[]>([])
  const [userTier, setUserTier] = useState<SubscriptionTier>('free')
  const currentMonth = new Date().getMonth() + 1
  const currentYear = new Date().getFullYear()

  // Load cities + user tier on mount
  useEffect(() => {
    fetch('/api/cities')
      .then((r) => r.json())
      .then((d) => setCities(d.cities ?? []))
      .catch(() => setCities([]))

    fetch('/api/auth/me')
      .then((r) => r.ok ? r.json() : null)
      .then((d) => { if (d?.tier) setUserTier(d.tier) })
      .catch(() => {})
  }, [])

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      grossSalary: '',
      ptkpStatus: 'TK/0',
      city: '',
      monthNumber: String(currentMonth),
      year: String(currentYear),
      hasNPWP: true,
      reportedPph21: '',
      reportedJht: '',
      reportedJp: '',
      reportedKesehatan: '',
      takeHome: '',
    },
  })

  async function onSubmit(values: FormValues) {
    dispatch({ type: 'SUBMIT' })

    // Parse string form values to numbers for API
    const parsed: ApiPayload = {
      grossSalary: parseIDR(values.grossSalary),
      ptkpStatus: values.ptkpStatus,
      city: values.city,
      monthNumber: parseInt(values.monthNumber, 10),
      year: parseInt(values.year, 10),
      hasNPWP: values.hasNPWP,
      reportedPph21: parseIDR(values.reportedPph21),
      reportedJht: parseIDR(values.reportedJht),
      reportedJp: parseIDR(values.reportedJp),
      reportedKesehatan: parseIDR(values.reportedKesehatan),
      takeHome: parseIDR(values.takeHome),
    }

    // Validate against API schema
    const safe = apiSchema.safeParse(parsed)
    if (!safe.success) {
      dispatch({ type: 'ERROR', message: safe.error.issues[0]?.message ?? 'Validasi gagal' })
      return
    }

    try {
      const res = await fetch('/api/audit-payslip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grossSalary: safe.data.grossSalary,
          ptkpStatus: safe.data.ptkpStatus,
          city: safe.data.city,
          monthNumber: safe.data.monthNumber,
          year: safe.data.year,
          hasNPWP: safe.data.hasNPWP,
          reportedDeductions: {
            pph21: safe.data.reportedPph21,
            jhtEmployee: safe.data.reportedJht,
            jpEmployee: safe.data.reportedJp,
            jkkEmployee: 0,
            jkmEmployee: 0,
            kesehatanEmployee: safe.data.reportedKesehatan,
            takeHome: safe.data.takeHome,
          },
          ocrSource: 'manual',
        }),
      })

      const json = await res.json()

      if (!res.ok) {
        dispatch({ type: 'ERROR', message: json.message ?? 'Terjadi kesalahan' })
        return
      }

      const result: AuditResult = {
        ...json.data,
        cityUMK: json.data?.calculations?.cityUMK ?? 0,
        city: values.city,
        grossSalary: values.grossSalary,
        monthNumber: values.monthNumber,
        year: values.year,
      }

      dispatch({ type: 'SUCCESS', data: result })
    } catch {
      dispatch({ type: 'ERROR', message: 'Tidak dapat terhubung ke server' })
    }
  }

  // ─── IDLE state ─────────────────────────────────────────────────────────────
  if (state.status === 'IDLE') {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-2xl px-4 py-16 text-center">
          <div className="mb-6 text-6xl">📋</div>
          <h1 className="text-3xl font-bold text-slate-900">Cek Slip Gaji Kamu — Gratis</h1>
          <p className="mt-3 text-slate-500 max-w-md mx-auto">
            Pastikan PPh21 dan BPJS sudah dipotong dengan benar. Hanya butuh 30 detik.
          </p>
          <p className="mt-2 text-sm text-slate-400">
            OCR upload tersedia di Stage 5 — untuk saat ini gunakan form manual.
          </p>
          <button
            onClick={() => dispatch({ type: 'SHOW_FORM' })}
            className="mt-8 inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors"
          >
            Isi Data Manual →
          </button>
        </div>
      </div>
    )
  }

  // ─── VERDICT state ─────────────────────────────────────────────────────────
  if (state.status === 'VERDICT') {
    const { data } = state
    const isPaid = !data.isGated
    const hasV06 = data.violations.some((v) => v.code === 'V06')
    const monthLabel = MONTHS.find((m) => m.value === data.monthNumber)?.label ?? ''

    return (
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-2xl px-4 py-8">

          {/* Verdict header */}
          <Card className={`mb-6 ${data.verdict === 'SESUAI' ? 'border-emerald-300 bg-emerald-50' : 'border-red-300 bg-red-50'}`}>
            <CardContent className="flex items-start gap-4 p-6">
              {data.verdict === 'SESUAI' ? (
                <CheckCircle2 className="h-10 w-10 shrink-0 text-emerald-600" />
              ) : (
                <AlertTriangle className="h-10 w-10 shrink-0 text-red-600" />
              )}
              <div>
                <h2 className={`text-xl font-bold ${data.verdict === 'SESUAI' ? 'text-emerald-800' : 'text-red-800'}`}>
                  {data.verdict === 'SESUAI'
                    ? 'Slip Gaji Sesuai Regulasi'
                    : 'Ada Pelanggaran pada Slip Gaji'}
                </h2>
                <p className="mt-1 text-sm text-slate-600">
                  {data.verdict === 'SESUAI'
                    ? `Tidak ada pelanggaran ditemukan. Gaji bruto Rp ${data.grossSalary.toLocaleString('id-ID')}/bulan, ${monthLabel} ${data.year}.`
                    : `Ditemukan ${data.violationCount} pelanggaran pada slip gaji kamu.`}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* UMK Badge */}
          {data.cityUMK > 0 && (
            <div className="mb-6">
              <UMKBadge
                city={data.city}
                umk={data.cityUMK}
                grossSalary={data.grossSalary}
              />
            </div>
          )}

          {/* Violations */}
          {data.violations.length > 0 && (
            <div className="mb-6 space-y-3">
              {data.violations.map((violation) => (
                <ViolationItem
                  key={violation.code}
                  violation={violation}
                  showAmount={isPaid}
                  reportedValue={
                    violation.code === 'V01' || violation.code === 'V05'
                      ? 0
                      : violation.code === 'V03'
                      ? 0
                      : violation.code === 'V06'
                      ? data.grossSalary
                      : violation.code === 'V04' || violation.code === 'V02'
                      ? data.calculations
                        ? violation.code === 'V04'
                          ? data.calculations.correctPph21 - (violation.differenceIDR ?? 0)
                          : data.calculations.correctJp - (violation.differenceIDR ?? 0)
                        : 0
                      : 0
                  }
                  calculatedValue={
                    violation.code === 'V01'
                      ? data.calculations?.correctJht ?? 0
                      : violation.code === 'V05'
                      ? data.calculations?.correctKesehatan ?? 0
                      : violation.code === 'V03'
                      ? data.calculations?.correctPph21 ?? 0
                      : violation.code === 'V06'
                      ? data.cityUMK
                      : violation.code === 'V04'
                      ? data.calculations?.correctPph21 ?? 0
                      : violation.code === 'V02'
                      ? data.calculations?.correctJp ?? 0
                      : violation.code === 'V07'
                      ? data.calculations?.correctJp ?? 0
                      : 0
                  }
                />
              ))}
            </div>
          )}

          {/* Calculations table — paid tier only */}
          {isPaid && data.calculations && (
            <PremiumGate
              userTier={userTier}
              requiredTier="basic"
              featureLabel="Detail selisih IDR dan panduan tindakan"
            >
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle className="text-base">Rincian Kalkulasi</CardTitle>
                </CardHeader>
                <CardContent className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-slate-500">
                        <th className="text-left py-2 pr-4">Komponen</th>
                        <th className="text-right py-2 px-2">Di Slip</th>
                        <th className="text-right py-2 px-2">Seharusnya</th>
                        <th className="text-right py-2 pl-2">Selisih</th>
                      </tr>
                    </thead>
                    <tbody className="text-slate-700">
                      {[
                        {
                          label: 'PPh21',
                          slip: data.calculations.correctPph21 - (data.violations.find((v) => v.code === 'V04')?.differenceIDR ?? 0),
                          correct: data.calculations.correctPph21,
                        },
                        {
                          label: 'JHT (2%)',
                          slip: data.violations.find((v) => v.code === 'V01') ? 0 : data.calculations.correctJht,
                          correct: data.calculations.correctJht,
                        },
                        {
                          label: 'JP (1%)',
                          slip: data.violations.find((v) => v.code === 'V07' || v.code === 'V02') ? 0 : data.calculations.correctJp,
                          correct: data.calculations.correctJp,
                        },
                        {
                          label: 'BPJS Kesehatan (1%)',
                          slip: data.violations.find((v) => v.code === 'V05') ? 0 : data.calculations.correctKesehatan,
                          correct: data.calculations.correctKesehatan,
                        },
                      ].map((row) => {
                        const diff = row.correct - row.slip
                        return (
                          <tr key={row.label} className="border-b border-slate-100">
                            <td className="py-2 pr-4 font-medium">{row.label}</td>
                            <td className="py-2 px-2 text-right text-slate-500">
                              Rp {row.slip.toLocaleString('id-ID')}
                            </td>
                            <td className="py-2 px-2 text-right">
                              Rp {row.correct.toLocaleString('id-ID')}
                            </td>
                            <td className={`py-2 pl-2 text-right font-semibold ${diff > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                              {diff > 0 ? '+' : ''}Rp {Math.abs(diff).toLocaleString('id-ID')}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            </PremiumGate>
          )}

          {/* Premium gate message for free users */}
          {data.isGated && (
            <Card className="mb-6 border-amber-200 bg-amber-50">
              <CardContent className="flex items-center gap-4 p-4">
                <AlertCircle className="h-6 w-6 shrink-0 text-amber-600" />
                <p className="text-sm text-amber-800">
                  {data.gateMessage}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Caveats */}
          <p className="mb-6 text-xs text-slate-400">
            Kalkulasi berdasarkan PMK 168/2023 (TER) dan peraturan BPJS yang berlaku.
            Alat ini tidak menggantikan konsultasi dengan konsultan pajak.
          </p>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={() => dispatch({ type: 'RESET' })}
              className="flex-1 rounded-lg border border-slate-200 bg-white py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
            >
              Cek Slip Lain
            </button>
            <button
              onClick={() => dispatch({ type: 'SHOW_FORM' })}
              className="flex-1 rounded-lg bg-emerald-600 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 transition-colors"
            >
              Hitung Ulang
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ─── ERROR state ────────────────────────────────────────────────────────────
  if (state.status === 'ERROR') {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Card className="mx-4 max-w-md border-red-200 bg-red-50">
          <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
            <AlertCircle className="h-10 w-10 text-red-500" />
            <div>
              <p className="font-semibold text-red-800">Terjadi Kesalahan</p>
              <p className="mt-1 text-sm text-red-600">{state.message}</p>
            </div>
            <button
              onClick={() => dispatch({ type: 'RESET' })}
              className="mt-2 rounded-lg border border-red-200 bg-white px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
            >
              Coba Lagi
            </button>
          </CardContent>
        </Card>
      </div>
    )
  }

  // ─── MANUAL FORM ────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-xl px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-900">Cek Slip Gaji</h1>
            <p className="text-sm text-slate-500">Input data manual</p>
          </div>
          <button
            onClick={() => dispatch({ type: 'RESET' })}
            className="flex items-center gap-1 text-sm text-slate-400 hover:text-slate-600"
          >
            <X className="h-4 w-4" />
            Batal
          </button>
        </div>

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">

          {/* Gross Salary */}
          <div>
            <Label htmlFor="grossSalary">Gaji Bruto /bulan *</Label>
            <Input
              id="grossSalary"
              placeholder="7.500.000"
              {...form.register('grossSalary')}
              className="mt-1"
            />
            {form.formState.errors.grossSalary && (
              <p className="mt-1 text-xs text-red-500">{form.formState.errors.grossSalary.message}</p>
            )}
          </div>

          {/* PTKP + Kota row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Status PTKP *</Label>
              <Select
                onValueChange={(v) => form.setValue('ptkpStatus', v as FormValues['ptkpStatus'])}
                defaultValue={form.getValues('ptkpStatus')}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(PTKP_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {value} — {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {form.formState.errors.ptkpStatus && (
                <p className="mt-1 text-xs text-red-500">{form.formState.errors.ptkpStatus.message}</p>
              )}
            </div>

            <div>
              <Label>Kota *</Label>
              <Select onValueChange={(v) => form.setValue('city', v)} defaultValue={form.getValues('city')}>
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Pilih kota..." />
                </SelectTrigger>
                <SelectContent>
                  {cities.length === 0 ? (
                    <SelectItem value="loading" disabled>Memuat kota...</SelectItem>
                  ) : (
                    cities.map((c) => (
                      <SelectItem key={`${c.city}-${c.province}`} value={c.city}>
                        {c.city} ({c.province})
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {form.formState.errors.city && (
                <p className="mt-1 text-xs text-red-500">{form.formState.errors.city.message}</p>
              )}
            </div>
          </div>

          {/* Month + Year + NPWP */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label>Bulan *</Label>
              <Select
                onValueChange={(v) => form.setValue('monthNumber', v)}
                defaultValue={String(form.getValues('monthNumber'))}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MONTHS.map((m) => (
                    <SelectItem key={m.value} value={String(m.value)}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Tahun *</Label>
              <Input
                type="number"
                className="mt-1"
                {...form.register('year', { valueAsNumber: true })}
              />
            </div>
            <div>
              <Label>Punya NPWP?</Label>
              <div className="mt-1 flex items-center gap-3">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    checked={form.watch('hasNPWP') === true}
                    onChange={() => form.setValue('hasNPWP', true)}
                    className="accent-emerald-600"
                  />
                  Ya
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    checked={form.watch('hasNPWP') === false}
                    onChange={() => form.setValue('hasNPWP', false)}
                    className="accent-emerald-600"
                  />
                  Tidak
                </label>
              </div>
            </div>
          </div>

          <Separator />

          {/* Reported deductions */}
          <div>
            <p className="text-sm font-medium text-slate-700">Isian dari Slip Gaji</p>
            <p className="text-xs text-slate-400 mb-3">Masukkan angka yang ada di slip gaji kamu</p>

            <div className="space-y-3">
              <div>
                <Label htmlFor="reportedPph21">PPh21 Dipotong</Label>
                <Input
                  id="reportedPph21"
                  placeholder="112.500"
                  {...form.register('reportedPph21')}
                  className="mt-1"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="reportedJht">JHT Karyawan</Label>
                  <Input
                    id="reportedJht"
                    placeholder="150.000"
                    {...form.register('reportedJht')}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="reportedJp">JP Karyawan</Label>
                  <Input
                    id="reportedJp"
                    placeholder="75.000"
                    {...form.register('reportedJp')}
                    className="mt-1"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="reportedKesehatan">BPJS Kesehatan Karyawan</Label>
                <Input
                  id="reportedKesehatan"
                  placeholder="75.000"
                  {...form.register('reportedKesehatan')}
                  className="mt-1"
                />
              </div>

              <div>
                <Label htmlFor="takeHome">Take Home Pay</Label>
                <Input
                  id="takeHome"
                  placeholder="7.000.000"
                  {...form.register('takeHome')}
                  className="mt-1"
                />
              </div>
            </div>
          </div>

          {/* Submit */}
          <Button
            type="submit"
            disabled={state.status === 'CALCULATING'}
            className="w-full bg-emerald-600 hover:bg-emerald-700"
          >
            {state.status === 'CALCULATING' ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Menghitung... ⚡
              </>
            ) : (
              'Cek Slip Gaji →'
            )}
          </Button>
        </form>

        {/* Disclaimer */}
        <p className="mt-4 text-center text-xs text-slate-400">
          Kalkulasi berdasarkan PMK 168/2023 (TER). Hasil bukan pengganti konsultasi pajak resmi.
        </p>
      </div>
    </div>
  )
}
