// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Homepage
// Hero + 5 tool cards
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import Link from 'next/link'
import { ArrowRight, ShieldCheck, TrendingUp, MapPin, Plane, BarChart3 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { BalanceScaleSVG } from '@/components/BalanceScaleSVG'
import { HowItWorks } from '@/components/HowItWorks'
import { SampleResultTeaser } from '@/components/SampleResultTeaser'
import { FirstVisitBanner } from '@/components/FirstVisitBanner'
import { TrustBadges } from '@/components/shared/TrustBadges'
import { SamplePaidResultModal } from '@/components/shared/SamplePaidResultModal'
import { FounderSection } from '@/components/FounderSection'
import { TestimonialsSection } from '@/components/TestimonialsSection'
import { AuditCounter } from '@/components/AuditCounter'
import { useState } from 'react'

export default function HomePage() {
  const [showSampleModal, setShowSampleModal] = useState(false)

  return (
    <div className="flex flex-col">
      <FirstVisitBanner className="mx-4 mt-4 lg:mx-auto lg:max-w-3xl" />

      {/* Trust badges */}
      <div className="mt-6 px-4">
        <TrustBadges className="py-3" />
      </div>

      {/* Hero — gradient from emerald-50 to white */}
      <section className="relative overflow-hidden bg-gradient-to-b from-emerald-50 to-white dark:from-emerald-950/20 dark:to-background px-4 py-16 lg:py-24">
        <BalanceScaleSVG className="absolute right-4 top-0 w-64 h-64 md:w-96 md:h-96 pointer-events-none" opacity={0.05} />
        <div className="mx-auto max-w-3xl text-center relative z-10">
          {/* Trust pill */}
          <div className="inline-flex items-center gap-2 bg-white dark:bg-slate-800 border border-emerald-200 dark:border-emerald-800 rounded-full px-4 py-1.5 text-sm text-emerald-700 dark:text-emerald-400 mb-6 shadow-sm">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Gratis · Berbasis PMK 168/2023 · Data Terenkripsi</span>
          </div>

          {/* Main headline */}
          <h1 className="text-3xl font-bold leading-tight text-foreground sm:text-4xl lg:text-5xl">
            Slip Gaji Kamu Dipotong
            <span className="mt-2 block text-emerald-600">Sesuai Aturan Nggak?</span>
          </h1>

          <p className="mt-4 text-base text-muted-foreground sm:text-lg">
            AI audit PPh21, BPJS, dan UMK slip gajimu dalam 30 detik.
            Gratis, tanpa daftar.
          </p>

          {/* Primary CTA */}
          <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Link href="/wajar-slip">
              <Button size="lg" className="bg-emerald-600 hover:bg-emerald-700 text-white text-base h-12 px-8">
                Cek Slip Gaji Sekarang
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link href="/wajar-gaji">
              <Button size="lg" variant="outline" className="text-base h-12">
                Cek Standar Gaji
              </Button>
            </Link>
          </div>

          {/* Social proof line */}
          <p className="mt-4 text-sm text-muted-foreground">
            Sudah{' '}
            <AuditCounter />{' '}
            slip gaji dicek minggu ini
          </p>
        </div>
      </section>

      {/* "Mulai dari mana?" decision helper */}
      <section className="py-8 px-4 max-w-2xl mx-auto">
        <p className="text-center text-sm font-medium text-muted-foreground mb-4">Mulai dari mana?</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            {
              href: '/wajar-slip',
              question: 'Punya slip gaji?',
              action: 'Audit sekarang →',
              bg: 'bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/20 dark:hover:bg-amber-950/30 border-amber-200',
              icon: '📋',
              ariaLabel: 'Audit slip gaji — cek PPh21 dan BPJS',
            },
            {
              href: '/wajar-gaji',
              question: 'Mau tahu gaji standar?',
              action: 'Benchmark gaji →',
              bg: 'bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/20 dark:hover:bg-blue-950/30 border-blue-200',
              icon: '💰',
              ariaLabel: 'Benchmark gaji — cari tahu gaji standar untuk posisi kamu',
            },
            {
              href: '/wajar-kabur',
              question: 'Berminat kerja di LN?',
              action: 'Hitung daya beli →',
              bg: 'bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/20 dark:hover:bg-indigo-950/30 border-indigo-200',
              icon: '✈️',
              ariaLabel: 'Wajar Kabur — bandingkan daya beli di luar negeri',
            },
          ].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-label={item.ariaLabel}
              className={`rounded-xl border p-4 transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 ${item.bg}`}
            >
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {item.icon} {item.question}
              </p>
              <p className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold">{item.action}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Tool Cards — Wajar Slip featured, others secondary */}
      <section id="alat" className="px-4 py-12 lg:py-16">
        <div className="mx-auto max-w-5xl">

          {/* Secondary tools — 2x2 grid below hero */}
          <h2 className="text-center text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-8">
            Juga tersedia
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              {
                href: '/wajar-gaji',
                icon: <TrendingUp className="w-5 h-5 text-blue-500" />,
                label: 'Wajar Gaji',
                desc: 'Benchmark gaji posisimu',
                badge: 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400',
                ariaLabel: 'Wajar Gaji — benchmark gaji berdasarkan posisi dan kota',
              },
              {
                href: '/wajar-tanah',
                icon: <MapPin className="w-5 h-5 text-stone-500" />,
                label: 'Wajar Tanah',
                desc: 'Harga tanah & properti',
                badge: 'bg-stone-50 text-stone-700 dark:bg-stone-950/40 dark:text-stone-400',
                ariaLabel: 'Wajar Tanah — cek harga wajar tanah dan properti',
              },
              {
                href: '/wajar-kabur',
                icon: <Plane className="w-5 h-5 text-indigo-500" />,
                label: 'Wajar Kabur',
                desc: 'Bandingkan daya beli luar negeri',
                badge: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-400',
                ariaLabel: 'Wajar Kabur — bandingkan daya beli di 20 negara',
              },
              {
                href: '/wajar-hidup',
                icon: <BarChart3 className="w-5 h-5 text-teal-500" />,
                label: 'Wajar Hidup',
                desc: 'Biaya hidup antar kota',
                badge: 'bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-400',
                ariaLabel: 'Wajar Hidup — bandingkan biaya hidup antar kota di Indonesia',
              },
            ].map((tool) => (
              <Link
                key={tool.href}
                href={tool.href}
                aria-label={tool.ariaLabel}
                className={`group rounded-xl border p-4 hover:shadow-md hover:bg-emerald-50/50 dark:hover:bg-emerald-950/20 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 ${tool.badge}`}
              >
                <div className="flex items-center gap-2 mb-2">
                  {tool.icon}
                  <span className="font-semibold text-sm">{tool.label}</span>
                </div>
                <p className="text-xs opacity-80">{tool.desc}</p>
                <ArrowRight className="w-3 h-3 mt-2 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
              </Link>
            ))}
          </div>

          {/* Wajar Slip — featured full-width card */}
          <Link
            href="/wajar-slip"
            aria-label="Wajar Slip — audit slip gaji PPh21 dan BPJS"
            className="group flex flex-col gap-3 rounded-2xl border-2 border-emerald-200 bg-emerald-50 p-6 transition-all hover:border-emerald-300 hover:bg-emerald-100/50 dark:hover:bg-emerald-950/20 hover:shadow-lg dark:border-emerald-800 dark:bg-emerald-950/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-emerald-100 p-3 dark:bg-emerald-900/40">
                <ArrowRight className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">Alat Utama</span>
                <h3 className="text-lg font-bold text-foreground">Cek Slip Gaji</h3>
              </div>
            </div>
            <p className="text-sm text-muted-foreground">
              Audit PPh21, BPJS, dan UMK slip gaji dalam 30 detik. Deteksi 7 jenis pelanggaran umum.
            </p>
            <div className="mt-auto flex items-center text-sm font-semibold text-emerald-600 group-hover:gap-2">
              Mulai Audit Gratis
              <ArrowRight className="ml-1 h-4 w-4 transition-all group-hover:ml-2" />
            </div>
          </Link>
        </div>
      </section>

      {/* How it works */}
      <FounderSection className="bg-background" />
      <TestimonialsSection className="bg-background" />
      <HowItWorks />

      {/* Sample result teaser */}
      <section className="px-4 py-12 lg:py-16 bg-muted/50">
        <div className="mx-auto max-w-md">
          <h2 className="text-center text-xl font-bold text-foreground sm:text-2xl mb-6">
            Contoh Hasil
          </h2>
          <SampleResultTeaser onViewPremiumSample={() => setShowSampleModal(true)} />
        </div>
      </section>

      <SamplePaidResultModal open={showSampleModal} onClose={() => setShowSampleModal(false)} />
    </div>
  )
}
