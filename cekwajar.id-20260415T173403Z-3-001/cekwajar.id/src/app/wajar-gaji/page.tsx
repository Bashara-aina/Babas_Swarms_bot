'use client'

// ==============================================================================
// cekwajar.id — Wajar Gaji (Salary Benchmark)
// Full implementation with autocomplete, Bayesian blending, crowdsource
// ==============================================================================

import { useState, useCallback, useEffect, useRef } from 'react'
import Link from 'next/link'
import {
  Search, MapPin, Briefcase, Wallet, ChevronDown,
  ChevronLeft,
  CheckCircle2, AlertCircle, TrendingUp, TrendingDown,
  Minus, Star, Lock, Info, Banknote, XCircle
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { CrossToolSuggestion } from '@/components/CrossToolSuggestion'
import { HowItWorks } from '@/components/HowItWorks'
import { TrustBadges } from '@/components/shared/TrustBadges'
import { CityCommandSelect } from '@/components/shared/CityCommandSelect'
import { FormProgress } from '@/components/shared/FormProgress'
import { PageHeader } from '@/components/shared/PageHeader/PageHeader'
import { ResultSkeleton } from '@/components/ResultSkeleton'
import { DisclaimerBanner } from '@/components/shared/DisclaimerBanner'
import { PercentileBar } from '@/components/wajar-gaji/PercentileBar'
import { COPY } from '@/lib/copy'

// --- Types --------------------------------------------------------------------

type PageState = 'IDLE' | 'SEARCHING' | 'RESULT' | 'NO_DATA' | 'ERROR' | 'CANDIDATES'

interface SearchResult {
  matchedTitle: string
  matchType: 'EXACT' | 'FUZZY'
  matchConfidence: number
  benchmark: {
    cityP25: number | null
    cityP50: number | null
    cityP75: number | null
    provinceP50: number | null
    bpsPriorP50: number | null
    sampleCount: number
    dataTier: 'CITY_LEVEL' | 'CITY_LEVEL_LIMITED' | 'PROVINCE_LEVEL' | 'BPS_PRIOR' | 'NO_DATA'
    isBlended: boolean
    blendWeight: number | null
    umk: number | null
    experienceBucket: string
  }
  userSalary: {
    value: number
    position: 'above' | 'below' | 'within'
    comparison: { diff: number; percentage: number }
  } | null
}

interface Candidate {
  id: string
  title: string
  similarity: number
}

interface SearchResponse {
  success: boolean
  data: {
    matchType: 'EXACT' | 'FUZZY' | 'CANDIDATES' | 'NO_MATCH'
    matchedTitle?: string
    matchConfidence?: number
    candidates?: Candidate[]
    benchmark?: SearchResult['benchmark']
    userSalary?: SearchResult['userSalary']
    message?: string
  }
}

interface City {
  city: string
  province: string
}

interface SubmitResponse {
  success: boolean
  data: {
    accepted: boolean
    isDuplicate: boolean
    violatesOutlierRule: boolean
    message: string
  }
}

// --- Constants ----------------------------------------------------------------

const EXPERIENCE_BUCKETS = [
  { value: '0-2', label: '0-2 tahun' },
  { value: '3-5', label: '3-5 tahun' },
  { value: '6-10', label: '6-10 tahun' },
  { value: '10+', label: '10+ tahun' },
]

// Indonesian cities with UMK
const CITIES: City[] = [
  { city: 'Jakarta', province: 'DKI Jakarta' },
  { city: 'Jakarta Pusat', province: 'DKI Jakarta' },
  { city: 'Jakarta Utara', province: 'DKI Jakarta' },
  { city: 'Jakarta Selatan', province: 'DKI Jakarta' },
  { city: 'Jakarta Timur', province: 'DKI Jakarta' },
  { city: 'Jakarta Barat', province: 'DKI Jakarta' },
  { city: 'Bekasi', province: 'Jawa Barat' },
  { city: 'Depok', province: 'Jawa Barat' },
  { city: 'Bogor', province: 'Jawa Barat' },
  { city: 'Bandung', province: 'Jawa Barat' },
  { city: 'Bandung', province: 'Jawa Barat' },
  { city: 'Surabaya', province: 'Jawa Timur' },
  { city: 'Sidoarjo', province: 'Jawa Timur' },
  { city: 'Malang', province: 'Jawa Timur' },
  { city: 'Semarang', province: 'Jawa Tengah' },
  { city: 'Tangerang', province: 'Banten' },
  { city: 'Tangerang Selatan', province: 'Banten' },
  { city: 'Serang', province: 'Banten' },
  { city: 'Medan', province: 'Sumatera Utara' },
  { city: 'Palembang', province: 'Sumatera Selatan' },
  { city: 'Makassar', province: 'Sulawesi Selatan' },
  { city: 'Yogyakarta', province: 'DI Yogyakarta' },
  { city: 'Denpasar', province: 'Bali' },
  { city: 'Manado', province: 'Sulawesi Utara' },
  { city: 'Balikpapan', province: 'Kalimantan Timur' },
  { city: 'Samarinda', province: 'Kalimantan Timur' },
  { city: 'Pontianak', province: 'Kalimantan Barat' },
]

// Dedupe cities by name
const UNIQUE_CITIES = Array.from(new Map(CITIES.map(c => [c.city, c])).values())

// --- Formatters ---------------------------------------------------------------

function formatIDR(amount: number | null): string {
  if (amount == null) return '-'
  return `Rp ${amount.toLocaleString('id-ID')}`
}

function getProvince(cityName: string): string {
  return CITIES.find(c => c.city === cityName)?.province ?? ''
}

// --- Components ---------------------------------------------------------------

function ConfidenceBadge({ tier, sampleCount }: { tier: string; sampleCount: number }) {
  if (tier === 'CITY_LEVEL' && sampleCount >= 30) {
    return (
      <Badge variant="success" className="bg-emerald-100 text-emerald-700">
        <CheckCircle2 className="mr-1 h-3 w-3" />
        Terverifikasi (n={sampleCount})
      </Badge>
    )
  }
  if (tier === 'CITY_LEVEL_LIMITED' || tier === 'PROVINCE_LEVEL') {
    return (
      <Badge variant="warning" className="bg-amber-100 text-amber-700">
        <Info className="mr-1 h-3 w-3" />
        Estimasi (n={sampleCount})
      </Badge>
    )
  }
  if (tier === 'BPS_PRIOR') {
    return (
      <Badge variant="secondary" className="bg-muted text-muted-foreground">
        <Star className="mr-1 h-3 w-3" />
        Prior BPS
      </Badge>
    )
  }
  return null
}


function UserSalaryComparison({
  position,
  percentage
}: {
  position: 'above' | 'below' | 'within'
  percentage: number
}) {
  const isAbove = position === 'above'
  const isBelow = position === 'below'

  return (
    <div className={`flex items-center gap-2 p-3 rounded-lg ${
      isAbove ? 'bg-emerald-50 text-emerald-700' :
      isBelow ? 'bg-red-50 text-red-700' :
      'bg-amber-50 text-amber-700'
    }`}>
      {isAbove && <TrendingUp className="h-5 w-5" />}
      {isBelow && <TrendingDown className="h-5 w-5" />}
      {position === 'within' && <Minus className="h-5 w-5" />}
      <div className="text-sm">
        {isAbove && `Gaji kamu ${percentage}% di atas median`}
        {isBelow && `Gaji kamu ${Math.abs(percentage)}% di bawah median`}
        {position === 'within' && `Gaji kamu within 5% median`}
      </div>
    </div>
  )
}

// --- Main Component -----------------------------------------------------------

export default function WajarGajiPage() {
  const [state, setState] = useState<PageState>('IDLE')
  const [jobTitleInput, setJobTitleInput] = useState('')
  const [selectedCity, setSelectedCity] = useState('')
  const [selectedExperience, setSelectedExperience] = useState('3-5')
  const [userSalaryInput, setUserSalaryInput] = useState('')
  const [cities, setCities] = useState<string[]>([])

  // Load cities on mount
  useEffect(() => {
    fetch('/api/cities')
      .then((r) => r.json())
      .then((d) =>
        setCities(
          (d.cities ?? [])
            .map((c: { city?: string; label?: string } | string) =>
              typeof c === 'string' ? c : (c.city ?? c.label ?? '')
            )
            .filter(Boolean)
        )
      )
  }, [])

  const [searchResults, setSearchResults] = useState<SearchResult | null>(null)
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [selectedCandidate, setSelectedCandidate] = useState<string | null>(null)

  const [autocompleteResults, setAutocompleteResults] = useState<Array<{id: string; title: string; industry: string | null}>>([])
  const [showAutocomplete, setShowAutocomplete] = useState(false)
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null)

  const [errorMessage, setErrorMessage] = useState('')

  // Crowdsource form state
  const [showCrowdsourceForm, setShowCrowdsourceForm] = useState(false)
  const [submitState, setSubmitState] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle')
  const [submitMessage, setSubmitMessage] = useState('')

  const [salaryInput, setSalaryInput] = useState('')

  const debounceRef = useRef<NodeJS.Timeout | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Autocomplete search
  const searchCategories = useCallback(async (query: string) => {
    if (!query || query.length < 2) {
      setAutocompleteResults([])
      return
    }

    try {
      const res = await fetch(`/api/salary/benchmark-search?q=${encodeURIComponent(query)}`)
      const json = await res.json()
      if (json.success) {
        setAutocompleteResults(json.data.results)
        setShowAutocomplete(true)
      }
    } catch {
      setAutocompleteResults([])
    }
  }, [])

  const handleJobTitleChange = (value: string) => {
    setJobTitleInput(value)
    setSelectedCategoryId(null)
    setSearchResults(null)
    setCandidates([])

    if (debounceRef.current) clearTimeout(debounceRef.current)

    debounceRef.current = setTimeout(() => {
      searchCategories(value)
    }, 300)
  }

  const selectAutocompleteItem = (item: { id: string; title: string }) => {
    setJobTitleInput(item.title)
    setSelectedCategoryId(item.id)
    setShowAutocomplete(false)
    setAutocompleteResults([])
  }

  const handleSearch = async () => {
    if (!selectedCategoryId || !selectedCity) {
      setErrorMessage('Silakan pilih judul pekerjaan dan kota')
      return
    }

    setState('SEARCHING')
    setErrorMessage('')

    try {
      const province = getProvince(selectedCity)
      const params = new URLSearchParams({
        jobTitle: jobTitleInput,
        city: selectedCity,
        province,
        experienceBucket: selectedExperience,
        ...(userSalaryInput && { userSalary: userSalaryInput }),
      })

      const res = await fetch(`/api/salary/benchmark?${params}`)
      const json: SearchResponse = await res.json()

      if (!json.success) {
        setState('ERROR')
        setErrorMessage(json.data?.message ?? COPY.error.genericError)
        return
      }

      if (json.data.matchType === 'CANDIDATES') {
        setState('CANDIDATES')
        setCandidates(json.data.candidates ?? [])
        return
      }

      if (json.data.matchType === 'NO_MATCH') {
        setState('NO_DATA')
        setErrorMessage(json.data.message ?? 'Judul tidak ditemukan')
        return
      }

      setState('RESULT')
      setSearchResults(json.data as SearchResult)
    } catch (err) {
      setState('ERROR')
      setErrorMessage(COPY.error.networkError)
    }
  }

  const selectCandidate = async (candidateId: string) => {
    setSelectedCandidate(candidateId)
    const candidate = candidates.find(c => c.id === candidateId)
    if (candidate) {
      setJobTitleInput(candidate.title)
      setSelectedCategoryId(candidateId)
    }
  }

  const handleSubmitSalary = async () => {
    if (!selectedCategoryId || !selectedCity || !salaryInput) {
      setSubmitMessage('Silakan isi semua field')
      setSubmitState('error')
      return
    }

    const salary = parseInt(salaryInput.replace(/\D/g, ''), 10)
    if (isNaN(salary) || salary <= 0) {
      setSubmitMessage('Gaji tidak valid')
      setSubmitState('error')
      return
    }

    setSubmitState('submitting')

    try {
      const province = getProvince(selectedCity)
      const res = await fetch('/api/salary/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jobTitle: jobTitleInput,
          city: selectedCity,
          province,
          grossSalary: salary,
          experienceBucket: selectedExperience,
        }),
      })

      const json: SubmitResponse = await res.json()

      if (json.data.accepted) {
        setSubmitState('success')
        setSubmitMessage('Laporan gaji berhasil disimpan! Terima kasih.')
        setSalaryInput('')
      } else {
        setSubmitState('error')
        setSubmitMessage(json.data.message)
      }
    } catch {
      setSubmitState('error')
      setSubmitMessage(COPY.error.networkError)
    }
  }

  // Close autocomplete on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (inputRef.current && !inputRef.current.contains(e.target as Node)) {
        setShowAutocomplete(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // --- Render SEARCHING (loading) ---
  if (state === 'SEARCHING') {
    return (
      <div data-tool="wajar-gaji" className="min-h-screen bg-blue-50">
        <div className="mx-auto max-w-2xl px-4 py-12">
          <PageHeader
            icon={<Banknote className="h-5 w-5" />}
            title="Cek Wajar Gaji"
            description={`Mengecek benchmark untuk ${selectedCity}...`}
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

  // --- Render IDLE (form) ---
  if (state === 'IDLE') {
    return (
      <div data-tool="wajar-gaji" className="min-h-screen bg-blue-50">
        <div className="mx-auto max-w-2xl px-4 py-12">
          <PageHeader
            icon={<Banknote className="h-5 w-5" />}
            title="Cek Wajar Gaji"
            description="Benchmark gaji dengan 12.000+ data karyawan"
            className="text-center"
          />

          <HowItWorks
            steps={[
              {
                icon: Search,
                title: 'Masukkan posisi & kota',
                description: 'Ketik jabatan dan pilih kota tempat kamu bekerja',
              },
              {
                icon: TrendingUp,
                title: 'AI bandingkan data pasar',
                description: 'Blending data crowdsourced + scraping job portal',
              },
              {
                icon: Wallet,
                title: 'Lihat posisi gajimu',
                description: 'P25–P75 range dan di mana gajimu berdiri',
              },
            ]}
          />

          <TrustBadges variant="grid" className="mb-6" />
          <DisclaimerBanner type="tax" />

          <Card>
            <CardContent className="p-6">
              <div className="space-y-4">
                {/* Job Title with Autocomplete */}
                <div>
                  <Label htmlFor="jobTitle">Judul Pekerjaan</Label>
                  <div className="relative" ref={inputRef}>
                    <Input
                      id="jobTitle"
                      value={jobTitleInput}
                      onChange={(e) => handleJobTitleChange(e.target.value)}
                      onFocus={() => jobTitleInput.length >= 2 && setShowAutocomplete(true)}
                      placeholder="Contoh: Software Engineer"
                      className="pr-10"
                    />
                    {showAutocomplete && autocompleteResults.length > 0 && (
                      <div className="absolute z-50 mt-1 w-full rounded-xl border bg-popover shadow-lg overflow-hidden">
                        <div className="max-h-48 overflow-y-auto py-1">
                          {autocompleteResults.map((item) => (
                            <button
                              key={item.id}
                              type="button"
                              onClick={() => selectAutocompleteItem(item)}
                              className="flex w-full items-center px-3 py-2 text-sm text-left hover:bg-muted transition-colors"
                            >
                              <span className="truncate">{item.title}</span>
                              {item.industry && (
                                <span className="ml-2 text-xs text-muted-foreground truncate">{item.industry}</span>
                              )}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* City */}
                <div>
                  <Label htmlFor="city">Kota</Label>
                  <div className="mt-1.5">
                    <CityCommandSelect
                      value={selectedCity}
                      onChange={(city) => {
                        setSelectedCity(city)
                        setSearchResults(null)
                      }}
                      cities={cities}
                      placeholder="Pilih kota..."
                    />
                  </div>
                </div>

                {/* Experience */}
                <div>
                  <Label htmlFor="experience">Pengalaman Kerja</Label>
                  <select
                    id="experience"
                    value={selectedExperience}
                    onChange={(e) => setSelectedExperience(e.target.value)}
                    className="flex h-10 w-full rounded-lg border bg-white px-3 py-2 text-sm mt-1.5"
                  >
                    {EXPERIENCE_BUCKETS.map((bucket) => (
                      <option key={bucket.value} value={bucket.value}>{bucket.label}</option>
                    ))}
                  </select>
                </div>

                {/* User Salary (optional) */}
                <div>
                  <Label htmlFor="userSalary">Gaji Kamu (opsional)</Label>
                  <Input
                    id="userSalary"
                    type="text"
                    value={userSalaryInput}
                    onChange={(e) => {
                      const raw = e.target.value.replace(/\D/g, '')
                      setUserSalaryInput(raw ? parseInt(raw, 10).toLocaleString('id-ID') : '')
                    }}
                    placeholder="Contoh: 12.000.000"
                    className="mt-1.5"
                  />
                  <p className="mt-1 text-xs text-muted-foreground">
                    Kosongkan jika hanya ingin lihat benchmark
                  </p>
                </div>

                {/* Submit */}
                {errorMessage && (
                  <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                    <AlertCircle className="h-4 w-4 flex-shrink-0" />
                    {errorMessage}
                  </div>
                )}
                <Button
                  onClick={handleSearch}
                  disabled={!selectedCategoryId || !selectedCity}
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                >
                  <Search className="mr-2 h-4 w-4" />
                  Cek Wajar Gaji
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Info */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-blue-500 shrink-0 mt-0.5" />
              <div className="text-sm text-blue-700">
                <p className="font-medium">Data benchmark dari siapa?</p>
                <p className="mt-0.5 text-blue-600">200+ title pekerjaan, 50+ kota di Indonesia. Data digabung dari BPS dan laporan anonim.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // --- Render CANDIDATES ---

  if (state === 'CANDIDATES') {
    return (
      <div data-tool="wajar-gaji" className="min-h-screen bg-blue-50">
        <div className="mx-auto max-w-2xl px-4 py-12">
          <Card>
            <CardContent className="p-6">
              <h2 className="text-lg font-semibold text-foreground mb-4">
                Pilih Judul Pekerjaan yang Sesuai
              </h2>
              <p className="text-sm text-muted-foreground mb-4">
                Apakah maksudmu salah satu dari ini?
              </p>
              <div className="space-y-2">
                {candidates.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => selectCandidate(c.id)}
                    className={`w-full p-3 text-left rounded-lg border transition-colors ${
                      selectedCandidate === c.id
                        ? 'border-emerald-500 bg-emerald-50'
                        : 'border-border hover:border-emerald-300 hover:bg-muted'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-foreground">{c.title}</span>
                      {selectedCandidate === c.id && (
                        <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Kemiripan: {Math.round(c.similarity * 100)}%
                    </div>
                  </button>
                ))}
              </div>
              <div className="flex gap-3 mt-6">
                <Button
                  variant="outline"
                  onClick={() => {
                    setState('IDLE')
                    setCandidates([])
                    setSelectedCandidate(null)
                  }}
                  className="flex-1"
                >
                  <ChevronLeft className="mr-1 h-4 w-4" />
                  Cek lagi
                </Button>
                <Button
                  onClick={() => {
                    if (selectedCandidate) {
                      setState('SEARCHING')
                      handleSearch()
                    }
                  }}
                  disabled={!selectedCandidate}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                >
                  Lanjutkan
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
      <div data-tool="wajar-gaji" className="min-h-screen bg-blue-50">
        <div className="mx-auto max-w-2xl px-4 py-12 text-center">
          <div className="text-center py-10 px-4 bg-blue-50 rounded-xl">
            <Search className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
            <h3 className="font-semibold mb-1">Data belum tersedia</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Belum ada data gaji untuk posisi ini di kota tersebut. Coba kota terdekat atau jabatan yang lebih umum.
            </p>
            <p className="text-xs text-muted-foreground">
              💡 Kontribusi data gajimu:{' '}
              <Link href="/wajar-gaji/kontribusi" className="text-emerald-600 underline">
                Isi survey gaji anonim →
              </Link>
            </p>
          </div>
          <Button
            onClick={() => {
              setState('IDLE')
              setSearchResults(null)
              setErrorMessage('')
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
      <div data-tool="wajar-gaji" className="min-h-screen bg-blue-50">
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

  if (state === 'RESULT' && searchResults) {
    const { benchmark, matchedTitle, matchType, userSalary } = searchResults

    const STEPS = [
      { label: 'Cari' },
      { label: 'Benchmark' },
      { label: 'Hasil' },
    ]

    return (
      <div data-tool="wajar-gaji" className="min-h-screen bg-blue-50">
        <div className="mx-auto max-w-2xl px-4 py-8">
          {/* Back button */}
          <button
            onClick={() => {
              setState('IDLE')
              setSearchResults(null)
            }}
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4"
          >
            <ChevronLeft className="h-4 w-4" />
            Cek lagi
          </button>

          {/* Form Progress */}
          <FormProgress steps={STEPS} currentStep={2} className="mb-6" />

          {/* Result Card */}
          <Card className="mb-6">
            <CardContent className="p-6">
              {/* Title and Match Badge */}
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold text-foreground">{matchedTitle}</h2>
                  <div className="flex items-center gap-2 mt-1">
                    {matchType === 'EXACT' ? (
                      <Badge className="bg-emerald-100 text-emerald-700">
                        <CheckCircle2 className="mr-1 h-3 w-3" /> Exact Match
                      </Badge>
                    ) : (
                      <Badge className="bg-amber-100 text-amber-700">
                        <Info className="mr-1 h-3 w-3" /> Fuzzy Match
                      </Badge>
                    )}
                    <ConfidenceBadge tier={benchmark.dataTier} sampleCount={benchmark.sampleCount} />
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-muted-foreground">{selectedCity}</div>
                  <div className="text-sm text-muted-foreground">{selectedExperience} tahun</div>
                </div>
              </div>

              {/* UMK Reference */}
              {benchmark.umk && (
                <div className="mb-4 p-3 bg-muted rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">UMK {selectedCity} 2026</span>
                    <span className="font-semibold text-foreground">
                      {formatIDR(benchmark.umk)}
                    </span>
                  </div>
                </div>
              )}

              {/* City-Level Data (Premium) */}
              {benchmark.cityP50 ? (
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-foreground mb-3">
                    Rentang Gaji di {selectedCity}
                  </h3>
                  <PercentileBar
                    p25={benchmark.cityP25}
                    p50={benchmark.cityP50}
                    p75={benchmark.cityP75}
                    userSalary={userSalary?.value ?? null}
                    city={selectedCity}
                    jobTitle={matchedTitle}
                  />

                  {/* User Salary Comparison */}
                  {userSalary && userSalary.position && (
                    <div className="mt-4">
                      <UserSalaryComparison
                        position={userSalary.position}
                        percentage={userSalary.comparison.percentage}
                      />
                    </div>
                  )}
                </div>
              ) : (
                /* Province-Level Data (Free) */
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-foreground mb-2">
                    Median Gaji Provinsi
                  </h3>
                  <div className="p-4 bg-muted rounded-lg text-center">
                    <div className="text-3xl font-bold text-emerald-600">
                      {formatIDR(benchmark.provinceP50 ?? benchmark.bpsPriorP50)}
                    </div>
                    <div className="text-sm text-muted-foreground mt-1">
                      Median provinsi
                    </div>
                  </div>

                  {/* User Salary Comparison */}
                  {userSalary && userSalary.position && (
                    <div className="mt-4">
                      <UserSalaryComparison
                        position={userSalary.position}
                        percentage={userSalary.comparison.percentage}
                      />
                    </div>
                  )}

                  {/* Premium Gate */}
                  <div className="mt-4 p-4 border border-dashed border-border rounded-lg text-center">
                    <Lock className="h-5 w-5 text-muted-foreground mx-auto mb-2" />
                    <p className="text-sm text-muted-foreground font-medium">
                      Upgrade ke Basic+ untuk data P25-P75 kota
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Termasuk analisis gaji personal dan prediksi bonus
                    </p>
                    <Button size="sm" className="mt-3 bg-emerald-600 hover:bg-emerald-700">
                      Upgrade Sekarang
                    </Button>
                  </div>
                </div>
              )}

              {/* Blending Explanation */}
              {benchmark.isBlended && benchmark.blendWeight && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
                  <Info className="h-4 w-4 inline mr-1" />
                  Data digabung dengan prior BPS (bobot {benchmark.blendWeight}%) karena
                  sampel kota terbatas.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Crowdsource Form */}
          {!showCrowdsourceForm ? (
            <Button
              variant="outline"
              onClick={() => setShowCrowdsourceForm(true)}
              className="w-full"
            >
              <Star className="mr-2 h-4 w-4" />
              Tambahkan Laporan Gaji Anonim
            </Button>
          ) : (
            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold text-foreground mb-4">
                  Laporan Gaji Anonim
                </h3>

                {submitState === 'success' ? (
                  <div className="animate-fade-in-up text-center py-4">
                    <CheckCircle2 className="h-12 w-12 text-emerald-500 mx-auto mb-2" />
                    <p className="text-emerald-700 font-medium">{submitMessage}</p>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowCrowdsourceForm(false)
                        setSubmitState('idle')
                      }}
                      className="mt-4"
                    >
                      Tutup
                    </Button>
                  </div>
                ) : (
                  <>
                    <div className="space-y-3">
                      <div className="p-3 bg-muted rounded-lg text-sm">
                        <div className="text-muted-foreground">
                          <strong>{jobTitleInput}</strong> di <strong>{selectedCity}</strong>
                        </div>
                      </div>

                      <div>
                        <Label htmlFor="submitSalary">Gaji Kotor per Bulan</Label>
                        <Input
                          id="submitSalary"
                          type="text"
                          value={salaryInput}
                          onChange={(e) => {
                            const raw = e.target.value.replace(/\D/g, '')
                            setSalaryInput(raw ? parseInt(raw, 10).toLocaleString('id-ID') : '')
                          }}
                          placeholder="Contoh: 10.000.000"
                        />
                      </div>

                      <p className="text-xs text-muted-foreground">
                        Data dikirim anonim. Tidak ada nama/email disimpan. Hanya IP hash
                        untuk deduplikasi.
                      </p>

                      {submitState === 'error' && (
                        <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                          <AlertCircle className="h-4 w-4 flex-shrink-0" />
                          {submitMessage}
                        </div>
                      )}

                      <Button
                        onClick={handleSubmitSalary}
                        disabled={submitState === 'submitting' || !salaryInput}
                        className="w-full bg-emerald-600 hover:bg-emerald-700"
                      >
                        {submitState === 'submitting' ? (
                          <div className="flex items-center gap-2">
                            <Skeleton shimmer className="h-4 w-4 rounded-full" />
                            Menyimpan...
                          </div>
                        ) : (
                          <div>
                            <span>Kirim Laporan</span>
                          </div>
                        )}
                      </Button>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          )}

          {/* Back to Home */}
          <div className="mt-6 text-center">
            <Link
              href="/"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <ChevronLeft className="inline h-4 w-4" /> Kembali
            </Link>
          </div>

          <CrossToolSuggestion fromTool="wajar-gaji" className="mt-6" />
        </div>
      </div>
    )
  }

  return null
}
