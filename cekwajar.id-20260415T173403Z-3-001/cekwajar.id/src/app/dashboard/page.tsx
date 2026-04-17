// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — User Dashboard
// Server Component — reads session + subscription tier server-side
// P3: Bento Grid Layout with animated tool cards
// ══════════════════════════════════════════════════════════════════════════════

import { redirect } from 'next/navigation'
import Link from 'next/link'
import { getCurrentUser } from '@/lib/auth/getCurrentUser'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  CheckCircle,
  XCircle,
  Calculator,
  TrendingUp,
  MapPin,
  Globe,
  BarChart3,
  Sparkles,
  Shield,
  ChevronRight,
} from 'lucide-react'
import { SubscriptionBadge } from '@/components/shared/SubscriptionBadge'
import { PaymentToast } from '@/components/shared/PaymentToast'
import { ToastProvider } from '@/components/ui/toast'
import { StaggerContainer, StaggerItem } from '@/components/transitions'
import { BentoCard } from '@/components/dashboard/BentoCard'
import { DashboardStats } from '@/components/dashboard/DashboardStats'
import { cn } from '@/lib/utils'

const TIER_FEATURES = {
  free: {
    name: 'Paket Gratis',
    color: 'text-foreground dark:text-muted-foreground',
    border: 'border-border dark:border-muted-foreground',
    bg: 'bg-muted dark:bg-muted/50',
    badge: 'free',
    accentBg: 'bg-muted-foreground/80 dark:bg-muted-foreground',
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
    name: 'Paket Basic',
    color: 'text-blue-700 dark:text-blue-400',
    border: 'border-blue-200 dark:border-blue-800',
    bg: 'bg-blue-50 dark:bg-blue-950/30',
    badge: 'basic',
    accentBg: 'bg-blue-600 dark:bg-blue-700',
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
    name: 'Paket Pro',
    color: 'text-purple-700 dark:text-purple-400',
    border: 'border-purple-200 dark:border-purple-800',
    bg: 'bg-purple-50 dark:bg-purple-950/30',
    badge: 'pro',
    accentBg: 'bg-purple-600 dark:bg-purple-700',
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

// Bento card definitions — maps tool id to grid position and visual config
const BENTO_TOOLS = [
  {
    id: 'wajar-slip',
    name: 'Wajar Slip',
    href: '/wajar-slip',
    description: 'Audit PPh21 & BPJS dalam 30 detik. Deteksi 7 jenis pelanggaran umum.',
    icon: <Calculator className="h-6 w-6" />,
    iconBgClass: 'bg-emerald-100 dark:bg-emerald-900/40',
    borderClass: 'hover:border-emerald-300 dark:hover:border-emerald-600',
    span: 'col-span-1 row-span-1 sm:col-span-2 lg:col-span-2 lg:row-span-2',
    featured: true,
  },
  {
    id: 'wajar-gaji',
    name: 'Wajar Gaji',
    href: '/wajar-gaji',
    description: 'Benchmark gaji dengan data 12.000+ karyawan. Tau apakah gajimu sudah wajar.',
    icon: <TrendingUp className="h-6 w-6" />,
    iconBgClass: 'bg-blue-100 dark:bg-blue-900/40',
    borderClass: 'hover:border-blue-300 dark:hover:border-blue-600',
    span: 'col-span-1 row-span-1 lg:col-span-2 lg:row-span-1',
    featured: false,
  },
  {
    id: 'wajar-tanah',
    name: 'Wajar Tanah',
    href: '/wajar-tanah',
    description: 'Cek harga properti vs pasar. Deteksi harga tidak wajar dalam detik.',
    icon: <MapPin className="h-6 w-6" />,
    iconBgClass: 'bg-amber-100 dark:bg-amber-900/40',
    borderClass: 'hover:border-amber-300 dark:hover:border-amber-600',
    span: 'col-span-1 row-span-1 lg:col-span-1 lg:row-span-2',
    featured: false,
  },
  {
    id: 'wajar-kabur',
    name: 'Wajar Kabur',
    href: '/wajar-kabur',
    description: 'Kerja di luar negeri — perbandingan PPP 20 negara.',
    icon: <Globe className="h-6 w-6" />,
    iconBgClass: 'bg-indigo-100 dark:bg-indigo-900/40',
    borderClass: 'hover:border-indigo-300 dark:hover:border-indigo-600',
    span: 'col-span-1 row-span-1',
    featured: false,
  },
  {
    id: 'wajar-hidup',
    name: 'Wajar Hidup',
    href: '/wajar-hidup',
    description: 'Pindah kota? Hitung gaji setara berdasarkan biaya hidup.',
    icon: <BarChart3 className="h-6 w-6" />,
    iconBgClass: 'bg-rose-100 dark:bg-rose-900/40',
    borderClass: 'hover:border-rose-300 dark:hover:border-rose-600',
    span: 'col-span-1 row-span-1',
    featured: false,
  },
]

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
      <div data-tool="dashboard" className="min-h-screen bg-background">
        <div className="mx-auto max-w-6xl px-4 py-8 space-y-8">
          {/* Welcome header */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-foreground">
                Halo, {displayName}!
              </h1>
              <p className="text-muted-foreground">
                Berikut ringkasan akun cekwajar.id kamu.
              </p>
            </div>
            <SubscriptionBadge tier={tier} />
          </div>

          {/* Bento Grid */}
          <StaggerContainer
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 auto-rows-min"
            delay={0.08}
          >
            {/* Subscription status — wide card */}
            <StaggerItem className="col-span-1 sm:col-span-2 lg:col-span-4">
              <Link href="/upgrade" className="block h-full">
                <Card
                  className={cn(
                    'h-full border-2 transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5',
                    tierConfig.border,
                    tierConfig.bg
                  )}
                >
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={cn('rounded-lg p-2', tierConfig.accentBg)}>
                          <Shield className="h-4 w-4 text-white" />
                        </div>
                        <CardTitle className={cn('text-lg', tierConfig.color)}>
                          {tierConfig.name}
                        </CardTitle>
                      </div>
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
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {tierConfig.features.slice(0, 4).map((f, i) => (
                        <div
                          key={i}
                          className={cn(
                            'flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
                            f.included
                              ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                              : 'bg-muted text-muted-foreground'
                          )}
                        >
                          {f.included ? (
                            <CheckCircle className="h-3 w-3" />
                          ) : (
                            <XCircle className="h-3 w-3" />
                          )}
                          {f.label}
                        </div>
                      ))}
                    </div>
                    {tierConfig.cta && (
                      <div className="mt-3 flex items-center gap-1 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                        {tierConfig.cta.label}
                        <ChevronRight className="h-3 w-3" />
                      </div>
                    )}
                  </CardContent>
                </Card>
              </Link>
            </StaggerItem>

            {/* Feature cards — bento tool cards */}
            {BENTO_TOOLS.map((tool) => (
              <StaggerItem key={tool.id} className={tool.span}>
                <Link href={tool.href} className="block h-full">
                  <BentoCard
                    title={tool.name}
                    description={tool.description}
                    icon={tool.icon}
                    iconBgClass={tool.iconBgClass}
                    borderClass={tool.borderClass}
                    featured={tool.featured}
                    className="h-full"
                  />
                </Link>
              </StaggerItem>
            ))}

            {/* Quick stats row */}
            <StaggerItem className="col-span-1 sm:col-span-2 lg:col-span-4">
              <DashboardStats userId={user.id} />
            </StaggerItem>

            {/* Recent audits — full width card */}
            <StaggerItem className="col-span-1 sm:col-span-2 lg:col-span-4">
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="rounded-lg bg-amber-100 p-2 dark:bg-amber-900/30">
                        <Sparkles className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                      </div>
                      <CardTitle className="text-base">Riwayat Audit</CardTitle>
                    </div>
                    <Button asChild size="sm" className="bg-emerald-600 hover:bg-emerald-700">
                      <Link href="/wajar-slip">
                        <Calculator className="mr-1 h-3.5 w-3.5" />
                        Baru
                      </Link>
                    </Button>
                  </div>
                  <CardDescription>Analisis slip gaji terbaru kamu.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col items-center justify-center py-6 text-center">
                    <div className="rounded-full bg-muted p-4 mb-3">
                      <Calculator className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Belum ada audit slip gaji.
                    </p>
                    <p className="text-xs text-muted-foreground mb-4">
                      Mulai analisis pertama kamu sekarang.
                    </p>
                    <Button asChild size="sm" className="bg-emerald-600 hover:bg-emerald-700">
                      <Link href="/wajar-slip">
                        <Calculator className="mr-1 h-3.5 w-3.5" />
                        Cek Slip Gaji
                      </Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </StaggerItem>
          </StaggerContainer>
        </div>
      </div>
    </ToastProvider>
  )
}
