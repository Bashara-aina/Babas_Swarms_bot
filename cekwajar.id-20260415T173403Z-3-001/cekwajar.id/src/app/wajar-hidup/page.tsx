'use client'

// ==============================================================================
// cekwajar.id — Wajar Hidup (COL City Comparison)
// Full implementation with COL index adjustment
// ==============================================================================

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Home, Loader2, Info, ArrowRight, ChevronDown } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

// --- Types --------------------------------------------------------------------

type PageState = 'IDLE' | 'LOADING' | 'RESULT' | 'ERROR'
type COLVerdict = 'LEBIH_MURAH' | 'SAMA' | 'LEBIH_MAHAL'
type LifestyleTier = 'HEMAT' | 'STANDAR' | 'NYAMAN'

interface City {
  city_code: string
  city_name: string
  province: string
  col_index: number
}

interface CompareResponse {
  success: boolean
  data?: {
    fromCity: string
    toCity: string
    fromCOLIndex: number
    toCOLIndex: number
    adjustmentRatio: number
    requiredSalary: number
    salaryDifference: number
    percentChange: number
    verdict: COLVerdict
    verdictMessage: string
    categoryBreakdown: {
      category: string
      fromAmount: number
      toAmount: number
      difference: number
    }[]
  }
  error?: {
    code: string
    message: string
  }
}

function formatIDR(amount: number): string {
  return `Rp ${amount.toLocaleString('id-ID')}`
}

// --- Lifestyle Options --------------------------------------------------------

const LIFESTYLE_OPTIONS: { value: LifestyleTier; label: string; emoji: string; desc: string }[] = [
  { value: 'HEMAT', label: 'Hemat', emoji: '🪙', desc: 'Prioritas tabungan, masak sendiri, transportasi umum' },
  { value: 'STANDAR', label: 'Standar', emoji: '🏠', desc: 'Sesekali makan di luar, kendaraan pribadi' },
  { value: 'NYAMAN', label: 'Nyaman', emoji: '✨', desc: 'Restoran, hiburan rutin, tabungan lebih banyak' },
]

// --- Main Component ----------------------------------------------------------

export default function WajarHidupPage() {
  const [pageState, setPageState] = useState<PageState>('IDLE')
  const [cities, setCities] = useState<City[]>([])
  const [fromCity, setFromCity] = useState('')
  const [toCity, setToCity] = useState('')
  const [salaryInput, setSalaryInput] = useState('')
  const [lifestyleTier, setLifestyleTier] = useState<LifestyleTier>('STANDAR')
  const [result, setResult] = useState<CompareResponse['data'] | null>(null)
  const [errorMessage, setErrorMessage] = useState('')

  // Load cities on mount
  useEffect(() => {
    fetch('/api/col/cities')
      .then((r) => r.json())
      .then((json) => {
        if (json.success) setCities(json.data.cities)
      })
      .catch(() => null)
  }, [])

  const handleCompare = async () => {
    const salary = parseInt(salaryInput.replace(/\D/g, ''), 10)

    if (!fromCity) {
      setErrorMessage('Pilih kota asal')
      return
    }
    if (!toCity) {
      setErrorMessage('Pilih kota tujuan')
      return
    }
    if (!salary || salary < 500000) {
      setErrorMessage('Gaji minimal Rp 500.000')
      return
    }
    if (fromCity === toCity) {
      setErrorMessage('Kota asal dan tujuan tidak boleh sama')
      return
    }

    setPageState('LOADING')
    setErrorMessage('')

    try {
      const params = new URLSearchParams({
        fromCity,
        toCity,
        currentSalary: salary.toString(),
        lifestyleTier,
      })

      const res = await fetch(`/api/col/compare?${params}`)
      const json: CompareResponse = await res.json()

      if (!json.success && json.error?.code === 'SAME_CITY_ERROR') {
        setErrorMessage('Kota asal dan tujuan tidak boleh sama')
        setPageState('IDLE')
        return
      }

      if (!json.success) {
        setPageState('ERROR')
        setErrorMessage(json.error?.message ?? 'Terjadi kesalahan')
        return
      }

      setPageState('RESULT')
      setResult(json.data!)
    } catch {
      setPageState('ERROR')
      setErrorMessage('Tidak dapat terhubung ke server')
    }
  }

  const resetState = () => {
    setPageState('IDLE')
    setResult(null)
    setErrorMessage('')
  }

  // === IDLE / LOADING ==========================================================

  if (pageState === 'IDLE' || pageState === 'LOADING') {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-2xl px-4 py-12">
          <div className="mb-8 text-center">
            <div className="mb-4 text-5xl">🏙️</div>
            <h1 className="text-2xl font-bold text-slate-900">Wajar Hidup</h1>
            <p className="mt-2 text-slate-500">
              Mau pindah kota? Hitung gaji setara berdasarkan biaya hidup
            </p>
          </div>

          <Card>
            <CardContent className="p-6">
              <div className="space-y-5">
                {/* Two City Dropdowns */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Dari Kota</Label>
                    <Select value={fromCity} onValueChange={setFromCity}>
                      <SelectTrigger>
                        <SelectValue placeholder="Pilih kota" />
                      </SelectTrigger>
                      <SelectContent>
                        {cities.map((c) => (
                          <SelectItem key={c.city_code} value={c.city_code}>
                            {c.city_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Ke Kota</Label>
                    <Select value={toCity} onValueChange={setToCity}>
                      <SelectTrigger>
                        <SelectValue placeholder="Pilih kota" />
                      </SelectTrigger>
                      <SelectContent>
                        {cities.map((c) => (
                          <SelectItem key={c.city_code} value={c.city_code}>
                            {c.city_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Salary Input */}
                <div>
                  <Label htmlFor="salary">Gaji Sekarang (IDR)</Label>
                  <Input
                    id="salary"
                    type="text"
                    value={salaryInput}
                    onChange={(e) => {
                      const raw = e.target.value.replace(/\D/g, '')
                      setSalaryInput(raw ? parseInt(raw, 10).toLocaleString('id-ID') : '')
                    }}
                    placeholder="Contoh: 12.000.000"
                  />
                </div>

                {/* Lifestyle Tier */}
                <div>
                  <Label>Gaya Hidup</Label>
                  <div className="grid grid-cols-3 gap-2 mt-2">
                    {LIFESTYLE_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => setLifestyleTier(opt.value)}
                        className={`flex flex-col items-center gap-1 p-3 rounded-lg border-2 transition-colors ${
                          lifestyleTier === opt.value
                            ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                            : 'border-slate-200 hover:border-emerald-300 text-slate-600'
                        }`}
                      >
                        <span className="text-xl">{opt.emoji}</span>
                        <span className="text-xs font-medium">{opt.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {errorMessage && (
                  <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                    <Info className="h-4 w-4 flex-shrink-0" />
                    {errorMessage}
                  </div>
                )}

                <Button
                  onClick={handleCompare}
                  disabled={pageState === 'LOADING' || !fromCity || !toCity || !salaryInput}
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                >
                  {pageState === 'LOADING' ? (
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Menghitung...</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <Home className="h-4 w-4" />
                      <span>Hitung</span>
                    </div>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Info */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-blue-500 mt-0.5" />
              <div className="text-sm text-blue-700">
                <p className="font-medium">Bagaimana ini bekerja?</p>
                <p className="mt-1">
                  COL Index (Cost of Living) mengukur perbedaan biaya hidup antar kota
                  relatif terhadap Jakarta (baseline = 100). Gaya hidup menentukan
                  sensitivitas adjustment — Hemat kurang sensitif, Nyaman lebih sensitif.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // === ERROR ==================================================================

  if (pageState === 'ERROR') {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-2xl px-4 py-12 text-center">
          <div className="text-5xl mb-4">❌</div>
          <h2 className="text-xl font-bold text-red-900">Terjadi Kesalahan</h2>
          <p className="mt-2 text-red-600">{errorMessage}</p>
          <Button onClick={resetState} className="mt-6 bg-emerald-600 hover:bg-emerald-700">
            Kembali
          </Button>
        </div>
      </div>
    )
  }

  // === RESULT =================================================================

  if (pageState === 'RESULT' && result) {
    const absPct = Math.abs(result.percentChange)
    const verdictIcon =
      result.verdict === 'LEBIH_MURAH' ? '🟢' :
      result.verdict === 'LEBIH_MAHAL' ? '🔴' : '🔵'

    return (
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-2xl px-4 py-8">
          <button
            onClick={resetState}
            className="flex items-center text-sm text-slate-500 hover:text-emerald-600 mb-4"
          >
            ← Hitung Lagi
          </button>

          {/* Verdict Card */}
          <Card className="mb-6">
            <CardContent className="p-6">
              <div className="text-center mb-6">
                <div className="text-4xl mb-2">{verdictIcon}</div>
                <div className="text-xl font-bold text-slate-800">
                  {result.verdict === 'LEBIH_MURAH'
                    ? `Lebih Murah di ${result.toCity}!`
                    : result.verdict === 'LEBIH_MAHAL'
                    ? `Lebih Mahal di ${result.toCity}!`
                    : 'Biaya Hidup Setara'}
                </div>
                {result.verdict !== 'SAMA' && (
                  <div className="text-lg font-medium text-slate-600 mt-1">
                    {result.verdict === 'LEBIH_MURAH'
                      ? `Dengan gaji ${formatIDR(result.requiredSalary)}, kamu hemat ${formatIDR(Math.abs(result.salaryDifference))}/bulan`
                      : `Kamu butuh ${absPct}% lebih banyak untuk gaya hidup yang sama di ${result.toCity}`}
                  </div>
                )}
              </div>

              {/* COL Index Display */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="text-center p-4 bg-slate-50 rounded-lg">
                  <div className="text-xs text-slate-500">📍 {result.fromCity}</div>
                  <div className="text-2xl font-bold text-slate-700">
                    {result.fromCOLIndex.toFixed(1)}
                  </div>
                  <div className="text-xs text-slate-400">COL Index</div>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-xs text-slate-500">📍 {result.toCity}</div>
                  <div className="text-2xl font-bold text-blue-700">
                    {result.toCOLIndex.toFixed(1)}
                  </div>
                  <div className="text-xs text-slate-400">COL Index</div>
                </div>
              </div>

              {/* Required Salary */}
              <div className="text-center p-4 bg-emerald-50 rounded-xl mb-4">
                <div className="text-xs text-slate-500">Gaji Setara di {result.toCity}</div>
                <div className="text-2xl font-bold text-emerald-700">
                  {formatIDR(result.requiredSalary)}
                  <span className="text-sm font-normal text-slate-400">/bulan</span>
                </div>
                {result.salaryDifference !== 0 && (
                  <div className="text-sm text-slate-500 mt-1">
                    {result.salaryDifference < 0
                      ? `Hemat ${formatIDR(Math.abs(result.salaryDifference))}/bulan`
                      : `Butuh lebih ${formatIDR(result.salaryDifference)}/bulan`}
                  </div>
                )}
              </div>

              {/* Category Breakdown — Basic+ Gate */}
              <div className="mt-4">
                <div className="p-4 border border-dashed border-slate-300 rounded-lg text-center">
                  <div className="text-sm font-medium text-slate-600">
                    Detail breakdown per kategori (Basic+)
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    Upgrade untuk lihat distribusi biaya di setiap kategori
                  </div>
                  <Button size="sm" className="mt-3 bg-emerald-600 hover:bg-emerald-700">
                    Upgrade Sekarang
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* COL Baseline Note */}
          <div className="text-center text-xs text-slate-400 mb-4">
            COL Index: Jakarta = 100 sebagai baseline
          </div>

          <div className="text-center">
            <Link href="/" className="text-sm text-slate-500 hover:text-emerald-600">
              ← Kembali ke Homepage
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return null
}