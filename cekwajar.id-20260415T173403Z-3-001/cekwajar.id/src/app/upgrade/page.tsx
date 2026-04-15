// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Upgrade Page
// Shows pricing tiers with upgrade CTAs
// ══════════════════════════════════════════════════════════════════════════════

import { Check, X } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

const TIERS = [
  {
    id: 'free',
    name: 'Gratis',
    price: 'Rp 0',
    period: 'selamanya',
    description: 'Untuk coba fitur dasar cekwajar.id',
    color: 'slate',
    features: [
      { label: '3 audit slip gaji/hari', included: true },
      { label: 'Benchmark provinsi', included: true },
      { label: 'Detail pelanggaran IDR', included: false },
      { label: 'P25–P75 per kota', included: false },
      { label: 'Wajar Kabur (20 negara)', included: false },
      { label: 'Analisis tanah & properti', included: false },
    ],
    cta: 'Paket Saat Ini',
    ctaDisabled: true,
    href: '#',
  },
  {
    id: 'basic',
    name: 'Basic',
    price: 'Rp 29.000',
    period: 'per bulan',
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
    ctaDisabled: false,
    href: '/upgrade#basic',
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 'Rp 79.000',
    period: 'per bulan',
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
    ctaDisabled: false,
    href: '/upgrade#pro',
  },
]

const COLOR_MAP: Record<string, { border: string; header: string; button: string; badge: string }> = {
  slate: {
    border: 'border-slate-200',
    header: 'bg-slate-50',
    button: 'bg-slate-600 hover:bg-slate-700',
    badge: 'bg-slate-100 text-slate-600',
  },
  blue: {
    border: 'border-blue-300',
    header: 'bg-blue-50',
    button: 'bg-blue-600 hover:bg-blue-700',
    badge: 'bg-blue-600 text-white',
  },
  purple: {
    border: 'border-purple-300',
    header: 'bg-purple-50',
    button: 'bg-purple-600 hover:bg-purple-700',
    badge: 'bg-purple-600 text-white',
  },
}

export default function UpgradePage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-5xl px-4 py-12">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-slate-900 mb-3">
            Tingkatkan Paket kamu
          </h1>
          <p className="text-slate-500 max-w-md mx-auto">
            Dapatkan akses ke fitur lengkap untuk audit slip gaji, benchmark,
            dan analisis properti.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {TIERS.map((tier) => {
            const colors = COLOR_MAP[tier.color]
            return (
              <Card
                key={tier.id}
                id={tier.id}
                className={`border-2 ${colors.border} relative overflow-hidden`}
              >
                {tier.badge && (
                  <div className={`absolute top-0 right-0 ${colors.badge} text-xs font-medium px-3 py-1 rounded-bl-lg`}>
                    {tier.badge}
                  </div>
                )}
                <CardHeader className={`${colors.header} pb-4`}>
                  <CardTitle className="text-xl">{tier.name}</CardTitle>
                  <CardDescription className="mt-1">{tier.description}</CardDescription>
                  <div className="mt-4">
                    <span className="text-3xl font-bold text-slate-900">{tier.price}</span>
                    <span className="text-slate-500 text-sm ml-1">{tier.period}</span>
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
                  {tier.ctaDisabled ? (
                    <Button variant="outline" className="w-full" disabled>
                      {tier.cta}
                    </Button>
                  ) : (
                    <Button asChild className={`w-full ${colors.button}`}>
                      <Link href={tier.href}>{tier.cta}</Link>
                    </Button>
                  )}
                </CardFooter>
              </Card>
            )
          })}
        </div>

        <p className="text-center text-sm text-slate-400 mt-8">
          Pembayaran aman melalui Midtrans. Batalkan kapan saja.
        </p>
      </div>
    </div>
  )
}
