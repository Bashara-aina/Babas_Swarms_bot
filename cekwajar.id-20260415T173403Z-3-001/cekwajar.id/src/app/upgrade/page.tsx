'use client'

// ==============================================================================
// cekwajar.id — Upgrade Page
// Client component with Midtrans Snap integration
// ==============================================================================

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Check, X, Loader2, ArrowRight, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { cn } from '@/lib/utils'

// --- Types --------------------------------------------------------------------

type BillingPeriod = 'monthly' | 'annual'
type PlanType = 'basic' | 'pro'

interface PricingTier {
  id: PlanType
  name: string
  monthlyPrice: number
  annualPrice: number
  description: string
  color: 'blue' | 'purple'
  badge?: string
  features: { label: string; included: boolean }[]
  cta: string
  disabled: boolean
}

// --- Pricing Data ------------------------------------------------------------

const PRICING: Record<PlanType, PricingTier> = {
  basic: {
    id: 'basic',
    name: 'Basic',
    monthlyPrice: 29_000,
    annualPrice: 278_400, // 29k × 12 × 0.80
    description: 'Untuk pekerja yang ingin audit slip gaji secara mendalam',
    color: 'blue',
    badge: 'Paling Populer',
    features: [
      { label: '3 audit slip gaji/hari', included: true },
      { label: 'Benchmark provinsi', included: true },
      { label: 'Detail pelanggaran IDR', included: true },
      { label: 'P25–P75 per kota', included: true },
      { label: 'Wajar Kabur (20 negara)', included: true },
      { label: 'Analisis tanah & properti', included: false },
    ],
    cta: 'Pilih Basic',
    disabled: false,
  },
  pro: {
    id: 'pro',
    name: 'Pro',
    monthlyPrice: 79_000,
    annualPrice: 758_400, // 79k × 12 × 0.80
    description: 'Untuk konsultan HR dan profesional yang butuh fitur lengkap',
    color: 'purple',
    features: [
      { label: '3 audit slip gaji/hari', included: true },
      { label: 'Benchmark provinsi', included: true },
      { label: 'Detail pelanggaran IDR', included: true },
      { label: 'P25–P75 per kota', included: true },
      { label: 'Wajar Kabur (20 negara)', included: true },
      { label: 'Analisis tanah & properti', included: true },
    ],
    cta: 'Pilih Pro',
    disabled: false,
  },
}

const COLOR_CONFIG: Record<string, { border: string; header: string; button: string; badge: string; badgeText: string }> = {
  blue: {
    border: 'border-blue-300',
    header: 'bg-blue-50',
    button: 'bg-blue-600 hover:bg-blue-700',
    badge: 'bg-blue-600 text-white',
    badgeText: 'text-blue-700',
  },
  purple: {
    border: 'border-purple-300',
    header: 'bg-purple-50',
    button: 'bg-purple-600 hover:bg-purple-700',
    badge: 'bg-purple-600 text-white',
    badgeText: 'text-purple-700',
  },
}

// --- Helpers -----------------------------------------------------------------

function formatIDR(amount: number): string {
  return `Rp ${amount.toLocaleString('id-ID')}`
}

// --- Main Component -----------------------------------------------------------

export default function UpgradePage() {
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>('monthly')
  const [loadingPlan, setLoadingPlan] = useState<PlanType | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Load Midtrans Snap script
  useEffect(() => {
    const clientKey = process.env.NEXT_PUBLIC_MIDTRANS_CLIENT_KEY
    if (!clientKey) return

    const isProduction = process.env.NEXT_PUBLIC_MIDTRANS_IS_PRODUCTION === 'true'
    const baseUrl = isProduction
      ? 'https://app.midtrans.com/snap/snap.js'
      : 'https://app.sandbox.midtrans.com/snap/snap.js'

    const script = document.createElement('script')
    script.src = baseUrl
    script.setAttribute('data-client-key', clientKey)
    document.head.appendChild(script)

    return () => {
      document.head.removeChild(script)
    }
  }, [])

  const handleUpgrade = async (plan: PlanType) => {
    setError(null)
    setLoadingPlan(plan)

    try {
      const response = await fetch('/api/payment/create-transaction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan, billingPeriod }),
      })

      if (!response.ok) {
        const err = await response.json()
        setError(err.error?.message ?? 'Gagal membuat transaksi.')
        setLoadingPlan(null)
        return
      }

      const { data } = await response.json()

      // Open Midtrans Snap
      if (typeof window !== 'undefined' && (window as Window & { snap?: { pay: (token: string, opts: object) => void } }).snap) {
        ;(window as Window & { snap?: { pay: (token: string, opts: object) => void } }).snap!.pay(data.snapToken, {
          onSuccess: () => {
            setLoadingPlan(null)
            window.location.href = '/dashboard?upgraded=true'
          },
          onPending: () => {
            setLoadingPlan(null)
            window.location.href = '/dashboard?payment=pending'
          },
          onError: () => {
            setLoadingPlan(null)
            setError('Pembayaran gagal. Coba metode lain.')
          },
          onClose: () => {
            setLoadingPlan(null)
          },
        })
      } else {
        setError('Midtrans tidak tersedia. Silakan刷新页面后重试。')
        setLoadingPlan(null)
      }
    } catch {
      setError('Tidak dapat terhubung ke server.')
      setLoadingPlan(null)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-5xl px-4 py-12">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-50 rounded-full text-emerald-700 text-sm font-medium mb-4">
            <Sparkles className="h-4 w-4" />
            Tingkatkan paket kamu
          </div>
          <h1 className="text-3xl font-bold text-slate-900 mb-3">
            Paket Berlangganan
          </h1>
          <p className="text-slate-500 max-w-md mx-auto">
            Dapatkan akses ke fitur lengkap untuk audit slip gaji, benchmark,
            dan analisis properti.
          </p>
        </div>

        {/* Billing Period Toggle */}
        <div className="flex justify-center mb-8">
          <div className="inline-flex items-center bg-slate-100 rounded-lg p-1 gap-1">
            <button
              onClick={() => setBillingPeriod('monthly')}
              className={cn(
                'px-5 py-2 rounded-md text-sm font-medium transition-all',
                billingPeriod === 'monthly'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              Bulanan
            </button>
            <button
              onClick={() => setBillingPeriod('annual')}
              className={cn(
                'px-5 py-2 rounded-md text-sm font-medium transition-all',
                billingPeriod === 'annual'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              Tahunan
              <span className="ml-2 text-xs text-emerald-600 font-semibold">HEMAT 20%</span>
            </button>
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="max-w-md mx-auto mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700 text-center">{error}</p>
          </div>
        )}

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Free Tier */}
          <Card className="border-2 border-slate-200 relative overflow-hidden">
            <CardHeader className="bg-slate-50 pb-4">
              <CardTitle className="text-xl">Gratis</CardTitle>
              <CardDescription className="mt-1">
                Untuk coba fitur dasar cekwajar.id
              </CardDescription>
              <div className="mt-4">
                <span className="text-3xl font-bold text-slate-900">Rp 0</span>
                <span className="text-slate-500 text-sm ml-1">selamanya</span>
              </div>
            </CardHeader>
            <CardContent className="pb-4">
              <ul className="space-y-2">
                {[
                  { label: '3 audit slip gaji/hari', included: true },
                  { label: 'Benchmark provinsi', included: true },
                  { label: 'Detail pelanggaran IDR', included: false },
                  { label: 'P25–P75 per kota', included: false },
                  { label: 'Wajar Kabur (20 negara)', included: false },
                  { label: 'Analisis tanah & properti', included: false },
                ].map((f, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm">
                    {f.included ? (
                      <Check className="h-4 w-4 text-emerald-500 shrink-0" />
                    ) : (
                      <X className="h-4 w-4 text-slate-300 shrink-0" />
                    )}
                    <span className={f.included ? 'text-slate-700' : 'text-slate-400'}>
                      {f.label}
                    </span>
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button variant="outline" className="w-full" disabled>
                Paket Saat Ini
              </Button>
            </CardFooter>
          </Card>

          {/* Paid Tiers */}
          {(Object.values(PRICING)).map((tier) => {
            const colors = COLOR_CONFIG[tier.color]
            const price = billingPeriod === 'monthly' ? tier.monthlyPrice : Math.round(tier.annualPrice / 12)
            const isLoading = loadingPlan === tier.id

            return (
              <Card
                key={tier.id}
                className={cn(
                  'border-2 relative overflow-hidden transition-all',
                  colors.border,
                  isLoading && 'scale-[1.02] shadow-lg'
                )}
              >
                {tier.badge && (
                  <div className={cn(
                    'absolute top-0 right-0 text-xs font-medium px-3 py-1 rounded-bl-lg',
                    colors.badge
                  )}>
                    {tier.badge}
                  </div>
                )}
                <CardHeader className={cn(colors.header, 'pb-4')}>
                  <CardTitle className="text-xl">{tier.name}</CardTitle>
                  <CardDescription className="mt-1">{tier.description}</CardDescription>
                  <div className="mt-4">
                    <span className="text-3xl font-bold text-slate-900">
                      {formatIDR(price)}
                    </span>
                    <span className="text-slate-500 text-sm ml-1">
                      /bulan
                    </span>
                    {billingPeriod === 'annual' && (
                      <div className="text-xs text-emerald-600 mt-1 font-medium">
                        {formatIDR(tier.annualPrice)} / tahun
                      </div>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="pb-4">
                  <ul className="space-y-2">
                    {tier.features.map((f, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm">
                        {f.included ? (
                          <Check className="h-4 w-4 text-emerald-500 shrink-0" />
                        ) : (
                          <X className="h-4 w-4 text-slate-300 shrink-0" />
                        )}
                        <span className={f.included ? 'text-slate-700' : 'text-slate-400'}>
                          {f.label}
                        </span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
                <CardFooter>
                  <Button
                    onClick={() => handleUpgrade(tier.id)}
                    disabled={tier.disabled || isLoading}
                    className={cn('w-full', colors.button)}
                  >
                    {isLoading ? (
                      <div className="flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span>Memproses...</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        {tier.cta}
                        <ArrowRight className="h-4 w-4" />
                      </div>
                    )}
                  </Button>
                </CardFooter>
              </Card>
            )
          })}
        </div>

        {/* Trust Footer */}
        <p className="text-center text-sm text-slate-400 mt-8">
          Pembayaran aman melalui Midtrans. Batalkan kapan saja.
        </p>

        {/* Login prompt for unauthenticated users */}
        <div className="text-center mt-6">
          <p className="text-sm text-slate-400">
            Sudah punya akun?{' '}
            <Link href="/auth/login" className="text-emerald-600 hover:text-emerald-700 font-medium">
              Login di sini
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
