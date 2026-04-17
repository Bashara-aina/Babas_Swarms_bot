'use client'

// ==============================================================================
// cekwajar.id — Wajar Kabur (PPP Abroad Comparison)
// Full implementation with World Bank PPP + Frankfurter exchange rates
// ==============================================================================

import { useState } from 'react'
import Link from 'next/link'
import { Plane, Lock, Info, ArrowRight, ChevronDown, ChevronLeft, Globe, TrendingUp, TrendingDown, XCircle, DollarSign, Calculator } from 'lucide-react'
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
import { CrossToolSuggestion } from '@/components/CrossToolSuggestion'
import { HowItWorks } from '@/components/HowItWorks'
import { TrustBadges } from '@/components/shared/TrustBadges'
import { PPPBasketComparison } from '@/components/wajar-kabur/PPPBasketComparison'
import { PageHeader } from '@/components/shared/PageHeader/PageHeader'
import { COPY } from '@/lib/copy'
import { ResultSkeleton } from '@/components/ResultSkeleton'
import { DisclaimerBanner } from '@/components/shared/DisclaimerBanner'

// --- Types --------------------------------------------------------------------

type PageState = 'IDLE' | 'LOADING' | 'RESULT' | 'GATED' | 'ERROR'

interface Country {
  country_code: string
  country_name: string
  currency_code: string
  flag_emoji: string
  is_free_tier: boolean
}

interface CompareResponse {
  success: boolean
  data?: {
    isGated: boolean
    countryName: string
    currencyCode: string
    idSalary: number
    nominalEquivalent: number
    nominalCurrency: string
    userPowerIntlUSD: number
    idPPPFactor: number
    foreignPPPFactor: number
    pppYear: number
    exchangeRate: number
    offerSalary: number | null
    offerPowerIntlUSD: number | null
    realRatio: number | null
    isPPPBetter: boolean | null
    disclaimer: string
  }
  error?: {
    code: string
    message: string
  }
}

function formatIDR(amount: number): string {
  return `Rp ${amount.toLocaleString('id-ID')}`
}

function formatNumber(num: number, decimals = 0): string {
  return num.toLocaleString('id-ID', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

// --- Main Component ----------------------------------------------------------

export default function WajarKaburPage() {
  const [pageState, setPageState] = useState<PageState>('IDLE')
  const [salaryInput, setSalaryInput] = useState('')
  const [offerInput, setOfferInput] = useState('')
  const [countries, setCountries] = useState<Country[]>([])
  const [selectedCountry, setSelectedCountry] = useState('')
  const [result, setResult] = useState<CompareResponse['data'] | null>(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [gatedCountryName, setGatedCountryName] = useState('')

  // Load countries on mount
  useState(() => {
    fetch('/api/abroad/countries')
      .then((r) => r.json())
      .then((json) => {
        if (json.success) setCountries(json.data.countries)
      })
      .catch(() => null)
  })

  const selectedCountryData = countries.find((c) => c.country_code === selectedCountry)
  const isSelectedGated =
    selectedCountryData && !selectedCountryData.is_free_tier

  const handleCompare = async () => {
    const salary = parseInt(salaryInput.replace(/\D/g, ''), 10)
    if (!salary || salary < 100000) {
      setErrorMessage('Masukkan gaji minimal Rp 100.000')
      return
    }
    if (!selectedCountry) {
      setErrorMessage('Pilih negara tujuan')
      return
    }

    setPageState('LOADING')
    setErrorMessage('')

    try {
      const params = new URLSearchParams({
        currentIDRSalary: salary.toString(),
        targetCountry: selectedCountry,
      })

      const offer = parseInt(offerInput.replace(/\D/g, ''), 10)
      if (offer && offer > 0) params.set('offerSalary', offer.toString())

      const res = await fetch(`/api/abroad/compare?${params}`)
      const json: CompareResponse = await res.json()

      if (!json.success) {
        setPageState('ERROR')
        setErrorMessage(json.error?.message ?? COPY.error.genericError)
        return
      }

      const data = json.data!
      if (data.isGated) {
        setPageState('GATED')
        setGatedCountryName(data.countryName)
        return
      }

      setPageState('RESULT')
      setResult(data)
    } catch {
      setPageState('ERROR')
      setErrorMessage(COPY.error.networkError)
    }
  }

  const resetState = () => {
    setPageState('IDLE')
    setResult(null)
    setSelectedCountry('')
    setErrorMessage('')
  }

  // === LOADING ================================================================
  if (pageState === 'LOADING') {
    return (
      <div data-tool="wajar-kabur" className="min-h-screen bg-indigo-50">
        <div className="mx-auto max-w-2xl px-4 py-12">
          <PageHeader
            icon={<Plane className="h-5 w-5" />}
            title="Wajar Kabur"
            description="Bandingkan daya beli riil gaji Indonesia vs negara tujuan."
            className="text-center"
          />
          <Card>
            <CardContent className="p-6">
              <ResultSkeleton />
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // === IDLE ===================================================================
  if (pageState === 'IDLE') {
    return (
      <div data-tool="wajar-kabur" className="min-h-screen bg-indigo-50">
        <div className="mx-auto max-w-2xl px-4 py-12">
          <PageHeader
            icon={<Plane className="h-5 w-5" />}
            title="Wajar Kabur"
            description="Bandingkan daya beli riil gaji Indonesia vs negara tujuan."
            className="text-center"
          />

          <HowItWorks
            steps={[
              {
                icon: DollarSign,
                title: 'Masukkan gaji & negara',
                description: 'Gaji IDR kamu dan negara/kota tujuan',
              },
              {
                icon: Calculator,
                title: 'Hitung PPP adjustment',
                description: 'World Bank PPP data + kurs real-time Frankfurter',
              },
              {
                icon: Globe,
                title: 'Lihat daya beli riil',
                description: 'Perbandingan nilai riil gaji setelah penyesuaian biaya hidup',
              },
            ]}
          />

          <TrustBadges variant="grid" className="mb-6" />
          <DisclaimerBanner type="ppp" />

          <Card>
            <CardContent className="p-6">
              <div className="space-y-5">
                <div>
                  <Label htmlFor="salaryIDR">Gaji di Indonesia (IDR/bulan)</Label>
                  <Input
                    id="salaryIDR"
                    type="text"
                    value={salaryInput}
                    onChange={(e) => {
                      const raw = e.target.value.replace(/\D/g, '')
                      setSalaryInput(raw ? parseInt(raw, 10).toLocaleString('id-ID') : '')
                    }}
                    placeholder="Contoh: 12.000.000"
                    className="mt-1.5"
                  />
                </div>

                <div>
                  <Label htmlFor="offerSalary">Offer di negara tujuan (opsional)</Label>
                  <Input
                    id="offerSalary"
                    type="text"
                    value={offerInput}
                    onChange={(e) => {
                      const raw = e.target.value.replace(/\D/g, '')
                      setOfferInput(raw ? parseInt(raw, 10).toLocaleString('id-ID') : '')
                    }}
                    placeholder="Contoh: 3.500"
                    className="mt-1.5"
                  />
                </div>

                <div>
                  <Label htmlFor="targetCountry">Negara Tujuan</Label>
                  <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                    <SelectTrigger id="targetCountry" className="mt-1.5">
                      <SelectValue placeholder="Pilih negara tujuan" />
                    </SelectTrigger>
                    <SelectContent>
                      {countries.map((country) => (
                        <SelectItem key={country.country_code} value={country.country_code}>
                          <span className="inline-flex items-center gap-2">
                            <span>{country.flag_emoji}</span>
                            <span>{country.country_name}</span>
                            {!country.is_free_tier && <Lock className="h-3 w-3 text-amber-600" />}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {isSelectedGated && (
                  <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 text-sm text-amber-700">
                    Negara ini tersedia untuk paket Basic+.
                  </div>
                )}

                {errorMessage && (
                  <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                    <XCircle className="h-4 w-4 flex-shrink-0" />
                    {errorMessage}
                  </div>
                )}

                <Button
                  onClick={handleCompare}
                  disabled={!salaryInput || !selectedCountry}
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                >
                  Hitung Daya Beli Riil
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // === GATED ==================================================================

  if (pageState === 'GATED') {
    return (
      <div data-tool="wajar-kabur" className="min-h-screen bg-indigo-50">
        <div className="mx-auto max-w-2xl px-4 py-12 text-center">
          <div className="mb-4"><Lock className="h-12 w-12 text-muted-foreground mx-auto" /></div>
          <h2 className="text-xl font-bold text-foreground">Negara Ini Untuk Basic+</h2>
          <p className="mt-2 text-muted-foreground">
            Data PPP untuk <strong>{gatedCountryName}</strong> tersedia untuk langganan
            Basic+ ke atas.
          </p>
          <Button
            onClick={resetState}
            className="mt-6 bg-emerald-600 hover:bg-emerald-700"
          >
            Pilih Negara Lain
          </Button>
          <div className="mt-6">
            <Link href="/upgrade" className="text-sm text-emerald-600 hover:text-emerald-700">
              Lihat Paket Berlangganan →
            </Link>
          </div>
          <div className="mt-4">
            <Link href="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              <ChevronLeft className="inline h-4 w-4" /> Kembali
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // === ERROR ==================================================================

  if (pageState === 'ERROR') {
    return (
      <div data-tool="wajar-kabur" className="min-h-screen bg-indigo-50">
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
    const flag = selectedCountryData?.flag_emoji ?? ''
    const ratioDisplay = result.realRatio
      ? result.realRatio.toFixed(2)
      : null

    return (
      <div data-tool="wajar-kabur" className="min-h-screen bg-indigo-50">
        <div className="mx-auto max-w-2xl px-4 py-8">
          <button
            onClick={resetState}
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4"
          >
            <ChevronLeft className="h-4 w-4" />
            Cek lagi
          </button>

          <Card className="mb-6">
            <CardContent className="p-6">
              {/* Country Header */}
              <div className="text-center mb-6">
                <div className="mb-2"><Globe className="h-10 w-10 text-emerald-600 mx-auto" /></div>
                <div className="text-xl font-bold text-foreground">{result.countryName}</div>
                <div className="text-sm text-muted-foreground">
                  1 {result.currencyCode} = {formatNumber(result.exchangeRate, 2)} IDR
                </div>
              </div>

              {/* PPP Basket Comparison */}
              <PPPBasketComparison
                countryName={result.countryName}
                currencyCode={result.currencyCode}
                exchangeRate={result.exchangeRate}
                idSalary={result.idSalary}
                nominalEquivalent={result.nominalEquivalent}
                userPowerIntlUSD={result.userPowerIntlUSD}
                offerSalary={result.offerSalary}
                offerPowerIntlUSD={result.offerPowerIntlUSD}
                realRatio={result.realRatio}
                isPPPBetter={result.isPPPBetter}
                pppYear={result.pppYear}
                className="mb-4"
              />

              {/* Disclaimer */}
              <div className="p-3 bg-amber-50 rounded-lg">
                <p className="text-xs text-amber-700">{result.disclaimer}</p>
              </div>
            </CardContent>
          </Card>

          <div className="text-center">
            <Link href="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              <ChevronLeft className="inline h-4 w-4" /> Kembali
            </Link>
          </div>

          <CrossToolSuggestion fromTool="wajar-kabur" className="mt-6" />
        </div>
      </div>
    )
  }

  return null
}
