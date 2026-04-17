'use client'

// ==============================================================================
// cekwajar.id — Wajar Tanah (Property Price Benchmark)
// Full implementation with cascading dropdowns, IQR verdict, crowdsource
// ==============================================================================

import { useState, useCallback, useEffect } from 'react'
import Link from 'next/link'
import {
  Home, Trees, Building, Store, AlertCircle,
  ChevronDown, ChevronLeft, Info, Lock, MapPin, XCircle, TrendingUp, Trash2, FileCheck, ShieldCheck
} from 'lucide-react'
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
import { VerdictBadge } from '@/components/wajar-tanah/VerdictBadge'
import { PropertyPriceBar } from '@/components/wajar-tanah/PropertyPriceBar'
import { PropertyVerdict } from '@/app/api/property/benchmark/route'
import { COPY } from '@/lib/copy'
import { CrossToolSuggestion } from '@/components/CrossToolSuggestion'
import { HowItWorks } from '@/components/HowItWorks'
import { TrustBadges } from '@/components/shared/TrustBadges'
import { PageHeader } from '@/components/shared/PageHeader/PageHeader'
import { ResultSkeleton } from '@/components/ResultSkeleton'
import { DisclaimerBanner } from '@/components/shared/DisclaimerBanner'

// --- Provinces & Cities --------------------------------------------------------

const INDONESIA_PROVINCES = [
  'DKI Jakarta', 'Jawa Barat', 'Jawa Tengah', 'Jawa Timur', 'Banten',
  'Sumatera Utara', 'Sumatera Selatan', 'Sumatera Barat', 'Riau', 'Lampung',
  'Kalimantan Timur', 'Kalimantan Barat', 'Kalimantan Selatan', 'Kalimantan Tengah',
  'Sulawesi Selatan', 'Sulawesi Utara', 'Sulawesi Tengah',
  'Bali', 'Nusa Tenggara Barat', 'Nusa Tenggara Timur',
  'Maluku', 'Papua', 'West Papua',
]

const PROVINCE_CITIES: Record<string, string[]> = {
  'DKI Jakarta': ['Jakarta Selatan', 'Jakarta Pusat', 'Jakarta Utara', 'Jakarta Timur', 'Jakarta Barat'],
  'Jawa Barat': ['Bandung', 'Kota Bekasi', 'Kota Depok', 'Bogor', 'Sukabumi', 'Cirebon', 'Bekasi', 'Depok', 'Bandung Barat'],
  'Jawa Tengah': ['Semarang', 'Solo', 'Salatiga', 'Kudus', 'Magelang', 'Tegal', 'Pekalongan'],
  'Jawa Timur': ['Surabaya', 'Malang', 'Sidoarjo', 'Kediri', 'Mojokerto', 'Pasuruan', 'Probolinggo'],
  'Banten': ['Tangerang', 'Tangerang Selatan', 'Serang', 'Cilegon', 'Rangkas'],
  'Sumatera Utara': ['Medan', 'Pematangsiantar', 'Sibolangit', 'Deli Serdang'],
  'Sumatera Selatan': ['Palembang', 'Plaju', 'Banyuasin'],
  'Riau': ['Pekanbaru', 'Dumai'],
  'Lampung': ['Bandar Lampung', 'Metro'],
  'Kalimantan Timur': ['Balikpapan', 'Samarinda', 'Bontang'],
  'Kalimantan Barat': ['Pontianak', 'Singkawang', 'Kubu Raya'],
  'Kalimantan Selatan': ['Banjarmasin', 'Banjarbaru'],
  'Sulawesi Selatan': ['Makassar', 'Parepare', 'Maros'],
  'Sulawesi Utara': ['Manado', 'Bitung', 'Tomohon'],
  'Bali': ['Denpasar', 'Badung', 'Gianyar', 'Tabanan'],
  'Nusa Tenggara Barat': ['Mataram', 'Lombok Barat'],
  'Nusa Tenggara Timur': ['Kupang'],
}

// --- Types --------------------------------------------------------------------

type PageState = 'IDLE' | 'LOADING' | 'RESULT' | 'NO_DATA' | 'ERROR'

interface BenchmarkResponse {
  success: boolean
  data: {
    hasData: boolean
    verdict?: PropertyVerdict
    percentileEstimate?: number
    message?: string
    askingPricePerSqm?: number
    askingPriceTotal?: number
    landAreaSqm?: number
    benchmark?: {
      p25: number | null
      p50: number | null
      p75: number | null
      sampleCount: number
      freshness: string | null
      dataTier: string
    }
    location?: { province: string; city: string; district: string }
    propertyType?: string
    disclaimer?: string
    suggestion?: string
  }
}

// --- Formatters ----------------------------------------------------------------

function formatIDR(amount: number): string {
  return `Rp ${amount.toLocaleString('id-ID')}`
}

// --- Property Type Icons ------------------------------------------------------

const PROPERTY_TYPES = [
  { value: 'RUMAH', label: 'Rumah', icon: Home },
  { value: 'TANAH', label: 'Tanah', icon: Trees },
  { value: 'APARTEMEN', label: 'Apartemen', icon: Building },
  { value: 'RUKO', label: 'Ruko', icon: Store },
]

// --- Main Component -----------------------------------------------------------

export default function WajarTanahPage() {
  const [state, setState] = useState<PageState>('IDLE')
  const [selectedProvince, setSelectedProvince] = useState('')
  const [selectedCity, setSelectedCity] = useState('')
  const [selectedDistrict, setSelectedDistrict] = useState('')
  const [districts, setDistricts] = useState<string[]>([])
  const [selectedPropertyType, setSelectedPropertyType] = useState('RUMAH')
  const [landAreaInput, setLandAreaInput] = useState('')
  const [priceInput, setPriceInput] = useState('')
  const [pricePerSqm, setPricePerSqm] = useState<number | null>(null)
  const [errorMessage, setErrorMessage] = useState('')

  const [benchmarkData, setBenchmarkData] = useState<BenchmarkResponse['data'] | null>(null)

  // --- Cascading: Province → City → District ---

  const cities = selectedProvince ? (PROVINCE_CITIES[selectedProvince] ?? []) : []

  // Load districts when city changes
  useEffect(() => {
    if (!selectedProvince || !selectedCity) {
      setDistricts([])
      return
    }

    const loadDistricts = async () => {
      try {
        const res = await fetch(
          `/api/property/districts?province=${encodeURIComponent(selectedProvince)}&city=${encodeURIComponent(selectedCity)}`
        )
        const json = await res.json()
        if (json.success) {
          setDistricts(json.data.districts)
        }
      } catch {
        setDistricts([])
      }
    }

    loadDistricts()
  }, [selectedProvince, selectedCity])

  // Auto-calculate price per sqm
  useEffect(() => {
    const land = parseInt(landAreaInput, 10)
    const price = parseInt(priceInput.replace(/\D/g, ''), 10)

    if (land && price && land > 0) {
      setPricePerSqm(Math.round(price / land))
    } else {
      setPricePerSqm(null)
    }
  }, [landAreaInput, priceInput])

  // Reset dependent fields when parent changes
  const handleProvinceChange = (province: string) => {
    setSelectedProvince(province)
    setSelectedCity('')
    setSelectedDistrict('')
    setDistricts([])
    setBenchmarkData(null)
    setState('IDLE')
  }

  const handleCityChange = (city: string) => {
    setSelectedCity(city)
    setSelectedDistrict('')
    setBenchmarkData(null)
    setState('IDLE')
  }

  const handleDistrictChange = (district: string) => {
    setSelectedDistrict(district)
    setBenchmarkData(null)
    setState('IDLE')
  }

  // --- Calculate Benchmark ---

  const handleCheckPrice = async () => {
    if (!selectedProvince || !selectedCity || !selectedDistrict || !selectedPropertyType) {
      setErrorMessage('Silakan isi semua field')
      return
    }

    const land = parseInt(landAreaInput, 10)
    const price = parseInt(priceInput.replace(/\D/g, ''), 10)

    if (!land || land <= 0) {
      setErrorMessage('Luas tanah harus diisi dengan angka positif')
      return
    }
    if (!price || price <= 0) {
      setErrorMessage('Harga harus diisi dengan angka positif')
      return
    }

    setState('LOADING')
    setErrorMessage('')

    try {
      const params = new URLSearchParams({
        province: selectedProvince,
        city: selectedCity,
        district: selectedDistrict,
        propertyType: selectedPropertyType,
        landAreaSqm: land.toString(),
        askingPriceTotal: price.toString(),
      })

      const res = await fetch(`/api/property/benchmark?${params}`)
      const json: BenchmarkResponse = await res.json()

      if (!json.success) {
        setState('ERROR')
        setErrorMessage(json.data?.message ?? COPY.error.genericError)
        return
      }

      if (!json.data.hasData) {
        setState('NO_DATA')
        setBenchmarkData(json.data)
        return
      }

      setState('RESULT')
      setBenchmarkData(json.data)
    } catch {
      setState('ERROR')
      setErrorMessage(COPY.error.networkError)
    }
  }

  // --- Render LOADING ---
  if (state === 'LOADING') {
    return (
      <div data-tool="wajar-tanah" className="min-h-screen bg-stone-50">
        <div className="mx-auto max-w-2xl px-4 py-12">
          <PageHeader
            icon={<Home className="h-5 w-5" />}
            title="Wajar Tanah"
            description="Bandingkan harga properti dengan benchmark pasar lokal."
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

  // --- Render IDLE / FORM ---
  if (state === 'IDLE') {
    return (
      <div data-tool="wajar-tanah" className="min-h-screen bg-stone-50">
        <div className="mx-auto max-w-2xl px-4 py-12">
          <PageHeader
            icon={<Home className="h-5 w-5" />}
            title="Wajar Tanah"
            description="Bandingkan harga properti dengan benchmark pasar lokal."
            className="text-center"
          />

          <HowItWorks
            steps={[
              {
                icon: MapPin,
                title: 'Pilih lokasi & tipe',
                description: 'Provinsi, kota, kecamatan, dan tipe properti',
              },
              {
                icon: TrendingUp,
                title: 'AI analisis harga pasar',
                description: 'IQR dari data listing 99.co dan Rumah123',
              },
              {
                icon: Building,
                title: 'Dapat verdict harga',
                description: 'MURAH / WAJAR / MAHAL / SANGAT MAHAL berdasarkan data lokal',
              },
            ]}
          />

          <TrustBadges
            variant="grid"
            className="mb-6"
            badges={[
              { icon: Lock, label: 'Enkripsi TLS 1.3', sublabel: 'Data aman saat transfer' },
              { icon: Trash2, label: 'Hapus Otomatis', sublabel: '30 hari setelah audit' },
              { icon: FileCheck, label: 'Data dari Listing Publik', sublabel: '99.co & Rumah123' },
              { icon: ShieldCheck, label: 'IQR Statistical Method', sublabel: 'Outlier otomatis dibuang' },
            ]}
          />
          <DisclaimerBanner type="property" />

          <Card>
            <CardContent className="p-6">
              <div className="space-y-5">
                <div>
                  <Label htmlFor="province">Provinsi</Label>
                  <Select value={selectedProvince} onValueChange={handleProvinceChange}>
                    <SelectTrigger id="province" className="mt-1.5">
                      <SelectValue placeholder="Pilih provinsi" />
                    </SelectTrigger>
                    <SelectContent>
                      {INDONESIA_PROVINCES.map((province) => (
                        <SelectItem key={province} value={province}>
                          {province}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="city">Kota/Kabupaten</Label>
                  <Select value={selectedCity} onValueChange={handleCityChange} disabled={!selectedProvince}>
                    <SelectTrigger id="city" className="mt-1.5">
                      <SelectValue placeholder="Pilih kota/kabupaten" />
                    </SelectTrigger>
                    <SelectContent>
                      {cities.map((city) => (
                        <SelectItem key={city} value={city}>
                          {city}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="district">Kecamatan</Label>
                  <Select value={selectedDistrict} onValueChange={handleDistrictChange} disabled={!selectedCity}>
                    <SelectTrigger id="district" className="mt-1.5">
                      <SelectValue placeholder="Pilih kecamatan" />
                    </SelectTrigger>
                    <SelectContent>
                      {districts.map((district) => (
                        <SelectItem key={district} value={district}>
                          {district}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Tipe Properti</Label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2">
                    {PROPERTY_TYPES.map((property) => {
                      const Icon = property.icon
                      const isActive = selectedPropertyType === property.value
                      return (
                        <button
                          key={property.value}
                          type="button"
                          onClick={() => setSelectedPropertyType(property.value)}
                          className={`rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                            isActive
                              ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                              : 'border-border bg-white text-foreground hover:border-emerald-300'
                          }`}
                        >
                          <span className="inline-flex items-center gap-1">
                            <Icon className="h-4 w-4" />
                            {property.label}
                          </span>
                        </button>
                      )
                    })}
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="landArea">Luas Tanah (m²)</Label>
                    <Input
                      id="landArea"
                      type="number"
                      min="1"
                      value={landAreaInput}
                      onChange={(e) => setLandAreaInput(e.target.value)}
                      placeholder="Contoh: 120"
                      className="mt-1.5"
                    />
                  </div>
                  <div>
                    <Label htmlFor="totalPrice">Harga Total</Label>
                    <Input
                      id="totalPrice"
                      type="text"
                      value={priceInput}
                      onChange={(e) => {
                        const raw = e.target.value.replace(/\D/g, '')
                        setPriceInput(raw ? parseInt(raw, 10).toLocaleString('id-ID') : '')
                      }}
                      placeholder="Contoh: 850.000.000"
                      className="mt-1.5"
                    />
                  </div>
                </div>

                {pricePerSqm && (
                  <div className="rounded-lg bg-muted p-3 text-sm">
                    <span className="text-muted-foreground">Harga per m²:</span>{' '}
                    <span className="font-semibold text-foreground">{formatIDR(pricePerSqm)}</span>
                  </div>
                )}

                {errorMessage && (
                  <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                    <AlertCircle className="h-4 w-4 flex-shrink-0" />
                    {errorMessage}
                  </div>
                )}

                <Button
                  onClick={handleCheckPrice}
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                  disabled={!selectedProvince || !selectedCity || !selectedDistrict || !landAreaInput || !priceInput}
                >
                  Cek Wajar Harga Properti
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // --- Render NO_DATA ---

  if (state === 'NO_DATA') {
    return (
      <div data-tool="wajar-tanah" className="min-h-screen bg-stone-50">
        <div className="mx-auto max-w-2xl px-4 py-12 text-center">
          <div className="mb-4"><MapPin className="h-12 w-12 text-emerald-600 mx-auto" /></div>
          <h2 className="text-xl font-bold text-foreground">Belum Ada Data</h2>
          <p className="mt-2 text-muted-foreground">{benchmarkData?.message}</p>
          <p className="mt-1 text-sm text-muted-foreground">{benchmarkData?.suggestion}</p>
          <Button
            onClick={() => {
              setSelectedDistrict('')
              setBenchmarkData(null)
              setState('IDLE')
            }}
            className="mt-6 bg-emerald-600 hover:bg-emerald-700"
          >
            Coba Lagi
          </Button>
          <div className="mt-6">
            <Link href="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              <ChevronLeft className="inline h-4 w-4" /> Kembali
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // --- Render ERROR ---

  if (state === 'ERROR') {
    return (
      <div data-tool="wajar-tanah" className="min-h-screen bg-stone-50">
        <div className="mx-auto max-w-2xl px-4 py-12 text-center">
          <div className="mb-4"><XCircle className="h-12 w-12 text-red-500 mx-auto" /></div>
          <h2 className="text-xl font-bold text-red-900">Terjadi Kesalahan</h2>
          <p className="mt-2 text-red-600">{errorMessage}</p>
          <Button
            onClick={() => {
              setState('IDLE')
              setErrorMessage('')
            }}
            className="mt-6 bg-emerald-600 hover:bg-emerald-700"
          >
            Kembali
          </Button>
        </div>
      </div>
    )
  }

  // --- Render RESULT ---

  if (state === 'RESULT' && benchmarkData) {
    const { verdict, percentileEstimate, message, askingPricePerSqm, benchmark, disclaimer } = benchmarkData

    return (
      <div data-tool="wajar-tanah" className="min-h-screen bg-stone-50">
        <div className="mx-auto max-w-2xl px-4 py-8">
          {/* Back button */}
          <button
            onClick={() => {
              setState('IDLE')
              setBenchmarkData(null)
            }}
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4"
          >
            <ChevronLeft className="h-4 w-4" />
            Cek lagi
          </button>

          <Card className="mb-6">
            <CardContent className="p-6">
              {/* Verdict Badge */}
              {verdict && <VerdictBadge verdict={verdict} />}

              {/* Price Comparison */}
              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-muted rounded-lg">
                  <div className="text-xs text-muted-foreground">Harga kamu</div>
                  <div className="text-lg font-bold text-foreground">
                    {askingPricePerSqm ? formatIDR(askingPricePerSqm) : '-'}
                    <span className="text-xs font-normal text-muted-foreground">/m²</span>
                  </div>
                </div>
                <div className="text-center p-4 bg-emerald-50 rounded-lg">
                  <div className="text-xs text-muted-foreground">Median Pasar</div>
                  <div className="text-lg font-bold text-emerald-700">
                    {benchmark?.p50 ? formatIDR(benchmark.p50) : '-'}
                    <span className="text-xs font-normal text-muted-foreground">/m²</span>
                  </div>
                </div>
              </div>

              {/* Position */}
              <div className="mt-4 text-center">
                <div className="text-sm text-muted-foreground">Posisi estimasi</div>
                <div className="text-2xl font-bold text-foreground">
                  P{percentileEstimate ?? '?'}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {benchmark?.sampleCount ? `Berdasarkan ${benchmark.sampleCount} listing` : ''}
                  {benchmark?.freshness ? ` · ${benchmark.freshness} lalu` : ''}
                </div>
              </div>

              {/* Verdict Message */}
              <div className="mt-4 p-3 bg-muted rounded-lg text-sm text-muted-foreground">
                {message}
              </div>

              {/* Premium Gate: P25-P75 range */}
              {benchmark?.p25 && benchmark?.p75 ? (
                <div className="mt-6">
                  <div className="p-4 border border-dashed border-border rounded-lg text-center">
                    <Lock className="h-5 w-5 text-muted-foreground mx-auto mb-2" />
                    <p className="text-sm font-medium text-muted-foreground">
                      Upgrade ke Basic+ untuk rentang harga P25-P75
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Lihat distribusi lengkap harga di area ini
                    </p>
                    <Button size="sm" className="mt-3 bg-emerald-600 hover:bg-emerald-700">
                      Upgrade Sekarang
                    </Button>
                  </div>
                </div>
              ) : (
                benchmark?.p50 && (
                  <div className="mt-6">
                    <PropertyPriceBar
                      userPrice={askingPricePerSqm ?? 0}
                      fairPrice={benchmark.p50}
                      lowerBound={benchmark.p25 ?? benchmark.p50 * 0.85}
                      upperBound={benchmark.p75 ?? benchmark.p50 * 1.2}
                      city={selectedCity}
                      propertyType={selectedPropertyType}
                    />
                  </div>
                )
              )}
            </CardContent>
          </Card>

          {/* KJPP Disclaimer */}
          {disclaimer && (
            <div className="mt-4 p-3 bg-amber-50 rounded-lg">
              <p className="text-xs text-amber-700">{disclaimer}</p>
            </div>
          )}

          {/* Back to Home */}
          <div className="mt-6 text-center">
            <Link href="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              <ChevronLeft className="inline h-4 w-4" /> Kembali
            </Link>
          </div>

          <CrossToolSuggestion fromTool="wajar-tanah" className="mt-6" />
        </div>
      </div>
    )
  }

  return null
}
