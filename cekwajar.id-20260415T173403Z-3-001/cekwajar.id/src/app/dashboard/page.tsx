// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — User Dashboard
// Server Component — reads session + subscription tier server-side
// ══════════════════════════════════════════════════════════════════════════════

import { redirect } from 'next/navigation'
import Link from 'next/link'
import type { Metadata } from 'next'
import { getCurrentUser } from '@/lib/auth/getCurrentUser'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CheckCircle, XCircle, ArrowRight, Calculator, TrendingUp, MapPin, Globe } from 'lucide-react'
import { SubscriptionBadge } from '@/components/shared/SubscriptionBadge'
import { PaymentToast } from '@/components/shared/PaymentToast'
import { TOOLS } from '@/lib/constants'
import { ToastProvider } from '@/components/ui/toast'

const TIER_FEATURES = {
  free: {
    name: 'Paket Gratis',
    color: 'text-slate-700',
    border: 'border-slate-200',
    bg: 'bg-slate-50',
    badge: 'free',
    features: [
      { label: '3 audit slip gaji/hari', included: true },
      { label: 'Benchmark provinsi', included: true },
      { label: 'Detail pelanggaran IDR', included: false },
      { label: 'P25–P75 per kota', included: false },
      { label: 'Wajar Kabur (20 negara)', included: false },
      { label: 'Analisis tanah & properti', included: false },
    ],
    cta: { label: 'Upgrade ke Basic', href: '/upgrade', price: 'Rp 29.000/bulan' },
  },
  basic: {
    name: 'Paket Basic ✓',
    color: 'text-blue-700',
    border: 'border-blue-200',
    bg: 'bg-blue-50',
    badge: 'basic',
    features: [
      { label: '3 audit slip gaji/hari', included: true },
      { label: 'Benchmark provinsi', included: true },
      { label: 'Detail pelanggaran IDR', included: true },
      { label: 'P25–P75 per kota', included: true },
      { label: 'Wajar Kabur (20 negara)', included: true },
      { label: 'Analisis tanah & properti', included: false },
    ],
    cta: { label: 'Upgrade ke Pro', href: '/upgrade', price: 'Rp 79.000/bulan' },
  },
  pro: {
    name: 'Paket Pro ✓',
    color: 'text-purple-700',
    border: 'border-purple-200',
    bg: 'bg-purple-50',
    badge: 'pro',
    features: [
      { label: '3 audit slip gaji/hari', included: true },
      { label: 'Benchmark provinsi', included: true },
      { label: 'Detail pelanggaran IDR', included: true },
      { label: 'P25–P75 per kota', included: true },
      { label: 'Wajar Kabur (20 negara)', included: true },
      { label: 'Analisis tanah & properti', included: true },
    ],
    cta: null,
  },
} as const

export default async function DashboardPage() {
  const { user, tier, profile } = await getCurrentUser()

  if (!user) {
    redirect('/auth/login')
  }

  const displayName = profile?.full_name ?? user.user_metadata?.full_name ?? user.email?.split('@')[0] ?? 'User'
  const tierConfig = TIER_FEATURES[tier]

  return (
    <ToastProvider>
      <PaymentToast />
      <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-5xl px-4 py-8 space-y-8">
        {/* Welcome header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              Halo, {displayName}! 👋
            </h1>
            <p className="text-slate-500">
              Berikut ringkasan akun cekwajar.id kamu.
            </p>
          </div>
          <SubscriptionBadge tier={tier} />
        </div>

        {/* Subscription card */}
        <Card className={`border ${tierConfig.border} ${tierConfig.bg}`}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className={`text-xl ${tierConfig.color}`}>
                {tierConfig.name}
              </CardTitle>
              <SubscriptionBadge tier={tier} />
            </div>
            <CardDescription>
              {tier === 'pro'
                ? 'Kamu memiliki akses ke semua fitur.'
                : tier === 'basic'
                ? 'Kamu memiliki akses ke fitur menengah.'
                : 'Kamu menggunakan paket gratis.'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <ul className="space-y-2">
              {tierConfig.features.map((f, i) => (
                <li key={i} className="flex items-center gap-2 text-sm">
                  {f.included ? (
                    <CheckCircle className="h-4 w-4 text-emerald-500 shrink-0" />
                  ) : (
                    <XCircle className="h-4 w-4 text-slate-300 shrink-0" />
                  )}
                  <span className={f.included ? 'text-slate-700' : 'text-slate-400'}>
                    {f.label}
                  </span>
                </li>
              ))}
            </ul>

            {tierConfig.cta && (
              <div className="border-t pt-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-700">{tierConfig.cta.label}</p>
                  <p className="text-xs text-slate-500">{tierConfig.cta.price}</p>
                </div>
                <Button asChild className="bg-emerald-600 hover:bg-emerald-700">
                  <Link href={tierConfig.cta!.href}>
                    Upgrade <ArrowRight className="ml-1 h-4 w-4" />
                  </Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick access cards */}
        <div>
          <h2 className="mb-4 text-lg font-semibold text-slate-900">Akses Cepat</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {TOOLS.map((tool) => {
              const Icon = tool.id === 'wajar-slip' ? Calculator
                : tool.id === 'wajar-gaji' ? TrendingUp
                : tool.id === 'wajar-tanah' ? MapPin
                : Globe

              return (
                <Link key={tool.id} href={tool.href}>
                  <Card className="hover:border-emerald-300 hover:shadow-md transition-all cursor-pointer group">
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-3">
                        <div className="rounded-lg bg-emerald-100 p-2.5">
                          <Icon className="h-5 w-5 text-emerald-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-slate-900 text-sm">
                            {tool.emoji} {tool.name}
                          </p>
                          <p className="text-xs text-slate-500 line-clamp-1">{tool.description}</p>
                        </div>
                        <ArrowRight className="h-4 w-4 text-slate-300 group-hover:text-emerald-500 transition-colors" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              )
            })}
          </div>
        </div>

        {/* Recent audits placeholder */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Riwayat Audit</CardTitle>
            <CardDescription>Analisis slip gaji terbaru kamu.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Calculator className="h-10 w-10 text-slate-200 mb-3" />
              <p className="text-sm text-slate-500">Belum ada audit slip gaji.</p>
              <p className="text-xs text-slate-400 mb-4">Mulai analisis pertama kamu sekarang.</p>
              <Button asChild size="sm" className="bg-emerald-600 hover:bg-emerald-700">
                <Link href="/wajar-slip">
                  <Calculator className="mr-1 h-4 w-4" />
                  Cek Slip Gaji
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
      </div>
    </ToastProvider>
  )
}
