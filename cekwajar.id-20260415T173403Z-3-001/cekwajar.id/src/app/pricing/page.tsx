// cekwajar.id — Pricing Page
// Outcome-led copy, value framing, sample result modal
// spec 08

'use client'

import { useState } from 'react'
import Link from 'next/link'
import { CheckCircle2, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { SamplePaidResultModal } from '@/components/shared/SamplePaidResultModal'
import { UPGRADE_COPY } from '@/lib/copy'

function formatIDR(n: number) {
  return `Rp ${n.toLocaleString('id-ID')}`
}

const PLANS = [
  {
    id: 'basic',
    name: 'Basic',
    badge: 'PALING POPULER',
    badgeColor: 'bg-emerald-500 text-white',
    price: 29_000,
    description: 'Untuk pekerja yang ingin audit slip gaji secara mendalam',
    color: 'emerald',
    colorClasses: 'border-emerald-400',
    features: [
      { label: 'Lihat selisih IDR per komponen (PPh21, JHT, JP, BPJS)' },
      { label: 'Tabel kalkulasi lengkap dengan metode TER' },
      { label: 'Rekomendasi tindak lanjut per pelanggaran' },
      { label: 'Riwayat semua audit tersimpan' },
      { label: 'Audit slip gaji tanpa batas' },
    ],
    cta: 'Mulai Paket Basic →',
    ctaHref: '/upgrade',
  },
  {
    id: 'pro',
    name: 'Pro',
    badge: null,
    price: 79_000,
    description: 'Untuk HRD dan profesional yang butuh fitur lengkap',
    color: 'indigo',
    colorClasses: 'border-indigo-200 dark:border-indigo-800',
    features: [
      { label: 'Semua fitur Basic' },
      { label: 'Export PDF laporan audit' },
      { label: 'Benchmark gaji unlimited (Wajar Gaji)' },
      { label: 'API akses untuk integrasi' },
      { label: 'Priority support' },
    ],
    cta: 'Mulai Paket Pro →',
    ctaHref: '/upgrade',
  },
]

export default function PricingPage() {
  const [showSampleModal, setShowSampleModal] = useState(false)

  return (
    <div className="min-h-screen bg-muted">
      {/* Outcome headline */}
      <section className="text-center py-16 px-4 max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-full px-4 py-1.5 text-sm text-emerald-700 mb-6">
          <Sparkles className="h-3.5 w-3.5" />
          <span>Berbasis PMK 168/2023 · Kalkulasi akurat</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-4 text-foreground">
          Cari tahu persis<br />
          <span className="text-emerald-600">berapa yang kurang dibayar perusahaanmu</span>
        </h1>
        <p className="text-muted-foreground text-lg">
          Upgrade untuk akses angka lengkap — bukan estimasi, tapi kalkulasi PMK 168/2023 yang akurat.
        </p>
      </section>

      {/* Pricing cards */}
      <section className="px-4 max-w-4xl mx-auto pb-16">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl mx-auto">

          {PLANS.map((plan) => (
            <div
              key={plan.id}
              className={`border-2 ${plan.colorClasses} rounded-2xl p-6 relative bg-white dark:bg-slate-900`}
            >
              {/* Badge */}
              {plan.badge && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className={`${plan.badgeColor} text-xs font-bold px-3 py-1 rounded-full`}>
                    {plan.badge}
                  </span>
                </div>
              )}

              {/* Plan header */}
              <div className="mb-4">
                <p className="text-sm font-medium text-muted-foreground mb-1">Paket {plan.name}</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold">{formatIDR(plan.price)}</span>
                  <span className="text-muted-foreground">/bulan</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">{UPGRADE_COPY.valueFrame}</p>
              </div>

              {/* Feature list — outcome focused */}
              <ul className="space-y-3 mb-6 text-sm">
                {plan.features.map((f) => (
                  <li key={f.label} className="flex items-start gap-2">
                    <CheckCircle2
                      className={`w-4 h-4 flex-shrink-0 mt-0.5 ${
                        plan.color === 'emerald' ? 'text-emerald-500' : 'text-indigo-500'
                      }`}
                    />
                    <span>{f.label}</span>
                  </li>
                ))}
              </ul>

              {/* ROI framing for Basic plan */}
              {plan.id === 'basic' && (
                <div className="bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 rounded-lg p-3 mb-4 text-xs text-emerald-700 dark:text-emerald-400">
                  💡 {UPGRADE_COPY.roiFrame}
                </div>
              )}

              <Button
                asChild
                className={`w-full h-12 ${
                  plan.color === 'emerald'
                    ? 'bg-emerald-600 hover:bg-emerald-700'
                    : 'bg-indigo-600 hover:bg-indigo-700'
                }`}
              >
                <Link href={plan.ctaHref}>
                  {plan.cta}
                </Link>
              </Button>
            </div>
          ))}
        </div>

        {/* Value framing footer */}
        <p className="text-center text-sm text-muted-foreground mt-8">
          {UPGRADE_COPY.trialNote} · {UPGRADE_COPY.cancelAnytime}
        </p>

        {/* Sample result link */}
        <p className="text-center text-sm text-muted-foreground mt-4">
          Belum yakin?{' '}
          <button
            type="button"
            className="text-emerald-600 underline hover:no-underline"
            onClick={() => setShowSampleModal(true)}
          >
            Lihat dulu contoh hasil lengkapnya →
          </button>
        </p>

        <SamplePaidResultModal open={showSampleModal} onClose={() => setShowSampleModal(false)} />
      </section>

      {/* Trust badges */}
      <section className="px-4 pb-16 max-w-md mx-auto">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-center text-xs">
          {[
            { icon: '🔒', label: 'Data terenkripsi' },
            { icon: '🚫', label: 'Auto-delete 24 jam' },
            { icon: '🏛️', label: 'PMK 168/2023' },
          ].map((t) => (
            <div key={t.label} className="bg-white dark:bg-slate-800 rounded-lg px-3 py-2 border">
              <span>{t.icon}</span>
              <span className="ml-1">{t.label}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

