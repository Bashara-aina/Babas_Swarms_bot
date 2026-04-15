'use client'

// ==============================================================================
// cekwajar.id — Wajar Tanah (Property Price Benchmark)
// Full implementation with cascading dropdowns, IQR verdict, crowdsource
// ==============================================================================

import { useState, useCallback, useEffect } from 'react'
import Link from 'next/link'
import {
  Home, Trees, Building, Store, Loader2, AlertCircle,
  ChevronDown, Info, Lock, MapPin
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
        setErrorMessage(json.data?.message ?? 'Terjadi kesalahan')
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
      setErrorMessage('Tidak dapat terhubung ke server')
    }
  }

  // --- Render IDLE / FORM ---

  if (state === 'IDLE' || state === 'LOADING') {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-2xl px-4 py-12">
          <div className="mb-8 text-center">
            <div className="mb-4 text-5xl">🏠</div>
            <h1 className="text-2xl font-bold text-slate-900">Wajar Tanah</h1>
            <p className="mt-2 text-slate-500">
              Cek apakah harga properti yang kamu incar sudah wajar
            </p>
          </div>

          <Card>
            <CardContent className="p-6">
              <div className="space-y-5">
                {/* Province */}
                <div>
                  <Label>Provinsi</Label>
                  <Select value={selectedProvince} onValueChange={handleProvinceChange}>
                    <SelectTrigger>
                      <SelectValue placeholder="Pilih provinsi" />
                    </SelectTrigger>
                    <SelectContent>
                      {INDONESIA_PROVINCES.map((p) => (
                        <SelectItem key={p} value={p}>{p}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* City */}
                <div>
                  <Label>Kota</Label>
                  <Select
                    value={selectedCity}
                    onValueChange={handleCityChange}
                    disabled={!selectedProvince}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={selectedProvince ? 'Pilih kota' : 'Pilih provinsi dulu'} />
                    </SelectTrigger>
                    <SelectContent>
                      {cities.map((c) => (
                        <SelectItem key={c} value={c}>{c}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* District */}
                <div>
                  <Label>Kecamatan</Label>
                  <Select
                    value={selectedDistrict}
                    onValueChange={handleDistrictChange}
                    disabled={!selectedCity}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={selectedCity ? 'Pilih kecamatan' : 'Pilih kota dulu'} />
                    </SelectTrigger>
                    <SelectContent>
                      {districts.map((d) => (
                        <SelectItem key={d} value={d}>{d}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {districts.length === 0 && selectedCity && (
                    <p className="mt-1 text-xs text-slate-400">
                      Memuat kecamatan...
                    </p>
                  )}
                </div>

                {/* Property Type */}
                <div>
                  <Label>Tipe Properti</Label>
                  <div className="grid grid-cols-4 gap-2 mt-2">
                    {PROPERTY_TYPES.map(({ value, label, icon: Icon }) => (
                      <button
                        key={value}
                        onClick={() => setSelectedPropertyType(value)}
                        className={`flex flex-col items-center gap-1 p-3 rounded-lg border-2 transition-colors ${
                          selectedPropertyType === value
                            ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                            : 'border-slate-200 hover:border-emerald-300 text-slate-600'
                        }`}
                      >
                        <Icon className="h-6 w-6" />
                        <span className="text-xs font-medium">{label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Land Area + Price */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="landArea">Luas Tanah (m²)</Label>
                    <Input
                      id="landArea"
                      type="number"
                      value={landAreaInput}
                      onChange={(e) => setLandAreaInput(e.target.value)}
                      placeholder="Contoh: 120"
                    />
                  </div>
                  <div>
                    <Label htmlFor="price">Harga Ditawarkan (IDR)</Label>
                    <Input
                      id="price"
                      type="text"
                      value={priceInput}
                      onChange={(e) => {
                        const raw = e.target.value.replace(/\D/g, '')
                        setPriceInput(raw ? parseInt(raw, 10).toLocaleString('id-ID') : '')
                      }}
                      placeholder="Contoh: 2.500.000.000"
                    />
                  </div>
                </div>

                {/* Price per sqm preview */}
                {pricePerSqm && (
                  <div className="text-center p-3 bg-emerald-50 rounded-lg">
                    <span className="text-sm text-slate-600">Harga per m²: </span>
                    <span className="text-sm font-bold text-emerald-700">{formatIDR(pricePerSqm)}/m²</span>
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
                  disabled={state === 'LOADING' || !selectedDistrict || !landAreaInput || !priceInput}
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                >
                  {state === 'LOADING' ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Menghitung...
                    </>
                  ) : (
                    <>
                      <MapPin className="mr-2 h-4 w-4" />
                      Cek Harga
                    </>
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
                  Masukkan lokasi dan harga properti. Kami akan membandingkan dengan
                  data listing publik untuk memberikan verdict harga: MURAH, WAJAR,
                  MAHAL, atau SANGAT MAHAL.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // --- Render NO_DATA ---

  if (state === 'NO_DATA') {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-2xl px-4 py-12 text-center">
          <div className="text-5xl mb-4">📍</div>
          <h2 className="text-xl font-bold text-slate-900">Belum Ada Data</h2>
          <p className="mt-2 text-slate-500">{benchmarkData?.message}</p>
          <p className="mt-1 text-sm text-slate-400">{benchmarkData?.suggestion}</p>
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
            <Link href="/" className="text-sm text-slate-500 hover:text-emerald-600">
              ← Kembali ke Homepage
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // --- Render ERROR ---

  if (state === 'ERROR') {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-2xl px-4 py-12 text-center">
          <div className="text-5xl mb-4">❌</div>
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
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-2xl px-4 py-8">
          {/* Back button */}
          <button
            onClick={() => {
              setState('IDLE')
              setBenchmarkData(null)
            }}
            className="flex items-center text-sm text-slate-500 hover:text-emerald-600 mb-4"
          >
            ← Cek Lagi
          </button>

          <Card className="mb-6">
            <CardContent className="p-6">
              {/* Verdict Badge */}
              {verdict && <VerdictBadge verdict={verdict} />}

              {/* Price Comparison */}
              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-slate-50 rounded-lg">
                  <div className="text-xs text-slate-500">Harga kamu</div>
                  <div className="text-lg font-bold text-slate-700">
                    {askingPricePerSqm ? formatIDR(askingPricePerSqm) : '-'}
                    <span className="text-xs font-normal text-slate-400">/m²</span>
                  </div>
                </div>
                <div className="text-center p-4 bg-emerald-50 rounded-lg">
                  <div className="text-xs text-slate-500">Median Pasar</div>
                  <div className="text-lg font-bold text-emerald-700">
                    {benchmark?.p50 ? formatIDR(benchmark.p50) : '-'}
                    <span className="text-xs font-normal text-slate-400">/m²</span>
                  </div>
                </div>
              </div>

              {/* Position */}
              <div className="mt-4 text-center">
                <div className="text-sm text-slate-500">Posisi estimasi</div>
                <div className="text-2xl font-bold text-slate-700">
                  P{percentileEstimate ?? '?'}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {benchmark?.sampleCount ? `Berdasarkan ${benchmark.sampleCount} listing` : ''}
                  {benchmark?.freshness ? ` · ${benchmark.freshness} lalu` : ''}
                </div>
              </div>

              {/* Verdict Message */}
              <div className="mt-4 p-3 bg-slate-50 rounded-lg text-sm text-slate-600">
                {message}
              </div>

              {/* Premium Gate: P25-P75 range */}
              {benchmark?.p25 && benchmark?.p75 ? (
                <div className="mt-6">
                  <div className="p-4 border border-dashed border-slate-300 rounded-lg text-center">
                    <Lock className="h-5 w-5 text-slate-400 mx-auto mb-2" />
                    <p className="text-sm font-medium text-slate-600">
                      Upgrade ke Basic+ untuk rentang harga P25-P75
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
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
                      userPricePerSqm={askingPricePerSqm ?? 0}
                      p25={benchmark.p25 ?? benchmark.p50 * 0.85}
                      p50={benchmark.p50}
                      p75={benchmark.p75 ?? benchmark.p50 * 1.2}
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