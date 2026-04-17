'use client'

// ==============================================================================
// cekwajar.id — Wajar Hidup (COL City Comparison)
// Full implementation with COL index adjustment
// ==============================================================================

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Home, Info, ArrowRight, ChevronDown, ChevronLeft, Building2, MapPin, XCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CrossToolSuggestion } from '@/components/CrossToolSuggestion'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { PremiumGate } from '@/components/shared/PremiumGate'
import { COLComparisonChart } from '@/components/wajar-hidup/COLComparisonChart'
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

const LIFESTYLE_OPTIONS: { value: LifestyleTier; label: string; desc: string }[] = [
  { value: 'HEMAT', label: 'Hemat', desc: 'Prioritas tabungan, masak sendiri, transportasi umum' },
  { value: 'STANDAR', label: 'Standar', desc: 'Sesekali makan di luar, kendaraan pribadi' },
  { value: 'NYAMAN', label: 'Nyaman', desc: 'Restoran, hiburan rutin, tabungan lebih banyak' },
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
  const [userTier] = useState<'free' | 'basic' | 'pro'>('free')

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
      <div data-tool="wajar-hidup" className="min-h-screen bg-teal-50">
        <div className="mx-auto max-w-2xl px-4 py-12">
          <div className="mb-8 text-center">
            <div className="mb-4"><Building2 className="h-12 w-12 text-emerald-600 mx-auto" /></div>
            <Skeleton shimmer className="mx-auto h-8 w-40 mb-2" />
            <Skeleton shimmer className="mx-auto h-4 w-64" />
          </div>

          <Card>
            <CardContent className="p-6">
              <div className="space-y-5">
                {/* Two City Dropdowns */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Skeleton shimmer className="h-4 w-20 mb-2" />
                    <Skeleton shimmer className="h-10 w-full" />
                  </div>
                  <div>
                    <Skeleton shimmer className="h-4 w-16 mb-2" />
                    <Skeleton shimmer className="h-10 w-full" />
                  </div>
                </div>

                {/* Salary Input */}
                <div>
                  <Skeleton shimmer className="h-4 w-32 mb-2" />
                  <Skeleton shimmer className="h-10 w-full" />
                </div>

                {/* Lifestyle Tier */}
                <div>
                  <Skeleton shimmer className="h-4 w-24 mb-2" />
                  <div className="grid grid-cols-3 gap-2 mt-2">
                    {[1, 2, 3].map((i) => (
                      <Skeleton key={i} shimmer className="h-16 rounded-lg" />
                    ))}
                  </div>
                </div>

                {/* Submit Button */}
                <Skeleton shimmer className="h-10 w-full rounded-lg" />
              </div>
            </CardContent>
          </Card>

          {/* Info Skeleton */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-start gap-3">
              <Skeleton shimmer className="h-5 w-5 rounded" />
              <div className="flex-1 space-y-2">
                <Skeleton shimmer className="h-4 w-32" />
                <Skeleton shimmer className="h-3 w-full" />
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
      <div data-tool="wajar-hidup" className="min-h-screen bg-teal-50">
        <div className="mx-auto max-w-2xl px-4 py-12 text-center">
          <div className="mb-4"><XCircle className="h-12 w-12 text-red-500 mx-auto" /></div>
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
      result.verdict === 'LEBIH_MURAH' ? 'LEBIH_MURAH' :
      result.verdict === 'LEBIH_MAHAL' ? 'LEBIH_MAHAL' : 'SAMA'

    return (
      <div data-tool="wajar-hidup" className="min-h-screen bg-teal-50">
        <div className="mx-auto max-w-2xl px-4 py-8">
          <button
            onClick={resetState}
            className="flex items-center text-sm text-muted-foreground hover:text-emerald-600 mb-4"
          >
            <ChevronLeft className="h-4 w-4" />
            Hitung lagi
          </button>

          {/* Verdict Card */}
          <Card className="mb-6">
            <CardContent className="p-6">
              <div className="text-center mb-6">
                <div className="mb-2 mx-auto w-12 h-12 rounded-full flex items-center justify-center">
                  {result.verdict === 'LEBIH_MURAH' && (
                    <div className="h-10 w-10 rounded-full bg-emerald-100 flex items-center justify-center">
                      <TrendingDown className="h-5 w-5 text-emerald-600" />
                    </div>
                  )}
                  {result.verdict === 'LEBIH_MAHAL' && (
                    <div className="h-10 w-10 rounded-full bg-red-100 flex items-center justify-center">
                      <TrendingUp className="h-5 w-5 text-red-600" />
                    </div>
                  )}
                  {result.verdict === 'SAMA' && (
                    <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                      <Minus className="h-5 w-5 text-blue-600" />
                    </div>
                  )}
                </div>
                <div className="text-xl font-bold text-foreground">
                  {result.verdict === 'LEBIH_MURAH'
                    ? `Lebih Murah di ${result.toCity}!`
                    : result.verdict === 'LEBIH_MAHAL'
                    ? `Lebih Mahal di ${result.toCity}!`
                    : 'Biaya Hidup Setara'}
                </div>
                {result.verdict !== 'SAMA' && (
                  <div className="text-lg font-medium text-muted-foreground mt-1">
                    {result.verdict === 'LEBIH_MURAH'
                      ? `Dengan gaji ${formatIDR(result.requiredSalary)}, kamu hemat ${formatIDR(Math.abs(result.salaryDifference))}/bulan`
                      : `Kamu butuh ${absPct}% lebih banyak untuk gaya hidup yang sama di ${result.toCity}`}
                  </div>
                )}
              </div>

              {/* COL Index Display */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="text-center p-4 bg-muted rounded-lg">
                  <div className="text-xs text-muted-foreground">📍 {result.fromCity}</div>
                  <div className="text-2xl font-bold text-foreground">
                    {result.fromCOLIndex.toFixed(1)}
                  </div>
                  <div className="text-xs text-muted-foreground">COL Index</div>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-xs text-muted-foreground">📍 {result.toCity}</div>
                  <div className="text-2xl font-bold text-blue-700">
                    {result.toCOLIndex.toFixed(1)}
                  </div>
                  <div className="text-xs text-muted-foreground">COL Index</div>
                </div>
              </div>

              {/* Required Salary */}
              <div className="text-center p-4 bg-emerald-50 rounded-xl mb-4">
                <div className="text-xs text-muted-foreground">Gaji Setara di {result.toCity}</div>
                <div className="text-2xl font-bold text-emerald-700">
                  {formatIDR(result.requiredSalary)}
                  <span className="text-sm font-normal text-muted-foreground">/bulan</span>
                </div>
                {result.salaryDifference !== 0 && (
                  <div className="text-sm text-muted-foreground mt-1">
                    {result.salaryDifference < 0
                      ? `Hemat ${formatIDR(Math.abs(result.salaryDifference))}/bulan`
                      : `Butuh lebih ${formatIDR(result.salaryDifference)}/bulan`}
                  </div>
                )}
              </div>

              {/* Category Breakdown — Basic+ Gate */}
              {result.categoryBreakdown && result.categoryBreakdown.length > 0 ? (
                <PremiumGate
                  userTier={userTier}
                  requiredTier="basic"
                  featureLabel="Detail breakdown per kategori"
                  benefit="Bandingkan biaya hidup per kategori"
                >
                  <COLComparisonChart
                    categories={result.categoryBreakdown}
                    fromCity={result.fromCity}
                    toCity={result.toCity}
                    className="mt-4"
                  />
                </PremiumGate>
              ) : (
                <div className="mt-4 p-4 border border-dashed border-border rounded-lg text-center">
                  <div className="text-sm font-medium text-muted-foreground">
                    Detail breakdown per kategori (Basic+)
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Upgrade untuk lihat distribusi biaya di setiap kategori
                  </div>
                  <Button
                    size="sm"
                    className="mt-3 bg-emerald-600 hover:bg-emerald-700"
                    onClick={() => { window.location.href = '/upgrade' }}
                  >
                    Upgrade Sekarang
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* COL Baseline Note */}
          <div className="text-center text-xs text-muted-foreground mb-4">
            COL Index: Jakarta = 100 sebagai baseline
          </div>

          <div className="text-center">
            <Link href="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              <ChevronLeft className="inline h-4 w-4" /> Kembali
            </Link>
          </div>

          <CrossToolSuggestion fromTool="wajar-hidup" className="mt-6" />
        </div>
      </div>
    )
  }

  return null
}