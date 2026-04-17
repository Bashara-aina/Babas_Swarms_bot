'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Upgrade Success Page
// Confetti + feature checklist after successful payment
// ══════════════════════════════════════════════════════════════════════════════

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { CheckCircle2, Sparkles, ArrowRight, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { ConfettiEffect } from '@/components/ConfettiEffect'
import { UPGRADE_COPY } from '@/lib/copy'

const PLAN_LABELS: Record<string, string> = {
  basic: 'Basic',
  pro: 'Pro',
}

const NEW_ACCESS: Record<string, { label: string; desc: string }[]> = {
  basic: [
    { label: 'Detail selisih IDR per komponen', desc: 'PPh21, BPJS, JHT — semua dalam angka' },
    { label: 'Riwayat audit lengkap', desc: 'Cek slip sebelumnya tanpa batas' },
    { label: 'Benchmark P25–P75 per kota', desc: 'etahui posisi gaji kamu dikotamu' },
    { label: 'Wajar Kabur — 20 negara', desc: 'Bandingkan daya beli luar negeri' },
  ],
  pro: [
    { label: 'Semua fitur Basic', desc: '' },
    { label: 'Analisis tanah & properti', desc: 'Cek harga wajar tanah di area pilihan' },
    { label: 'COL Index per negara', desc: 'Cost of living index 50+ negara' },
    { label: 'PPP purchasing power parity', desc: 'Bandingkan daya beli riil' },
  ],
}

function SuccessContent() {
  const searchParams = useSearchParams()
  const plan = searchParams.get('plan') ?? 'basic'
  const isPending = searchParams.get('payment') === 'pending'
  const tier = plan as 'basic' | 'pro'
  const accesses = NEW_ACCESS[tier] ?? NEW_ACCESS.basic
  const [showConfetti, setShowConfetti] = useState(false)

  useEffect(() => {
    if (isPending) return
    const t = setTimeout(() => setShowConfetti(true), 300)
    return () => clearTimeout(t)
  }, [isPending])

  if (isPending) {
    return (
      <div className="min-h-screen bg-muted flex items-center justify-center px-4">
        <Card className="max-w-md w-full text-center">
          <CardContent className="pt-6">
            <div className="text-5xl mb-4">⏳</div>
            <h1 className="text-2xl font-bold mb-2">Pembayaran Pending</h1>
            <p className="text-muted-foreground mb-6">
              Pembayaranmu sedang diproses. Biasanya memakan waktu 1–5 menit.
              Kami akan mengirimi email setelah terkonfirmasi.
            </p>
            <Link href="/dashboard">
              <Button className="bg-emerald-600 hover:bg-emerald-700 gap-2">
                <Home className="h-4 w-4" />
                Kembali ke Dashboard
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-muted flex items-center justify-center px-4 py-12">
      <ConfettiEffect fire={showConfetti} />
      <div className="max-w-md w-full text-center space-y-6">
        {/* Success icon */}
        <div className="relative mx-auto w-fit">
          <div className="absolute inset-0 bg-emerald-100 rounded-full scale-150 opacity-50 animate-ping" />
          <div className="relative bg-emerald-100 rounded-full p-5">
            <CheckCircle2 className="h-12 w-12 text-emerald-600" />
          </div>
        </div>

        {/* Headline */}
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-50 rounded-full text-emerald-700 text-sm font-medium mb-3">
            <Sparkles className="h-3.5 w-3.5" />
            Pembayaran berhasil!
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            Kamu sekarang di paket {PLAN_LABELS[plan] ?? plan}
          </h1>
          <p className="text-muted-foreground text-sm">
            {plan === 'pro' ? 'Rp 79K' : 'Rp 29K'}/bulan · {UPGRADE_COPY.cancelAnytime}
          </p>
        </div>

        {/* Feature checklist */}
        <Card>
          <CardContent className="pt-4 pb-4">
            <p className="text-left text-sm font-semibold text-foreground mb-3">
              Yang baru bisa kamu akses:
            </p>
            <ul className="space-y-3 text-left">
              {accesses.map((item, i) => (
                <li key={i} className="flex items-start gap-2.5">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-foreground">{item.label}</p>
                    {item.desc && (
                      <p className="text-xs text-muted-foreground">{item.desc}</p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        {/* CTA */}
        <div className="space-y-2">
          <Link href="/wajar-slip" className="block">
            <Button size="lg" className="w-full bg-emerald-600 hover:bg-emerald-700 gap-2">
              Cek Slip Gaji Sekarang
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <Link href="/dashboard" className="block">
            <Button variant="outline" size="lg" className="w-full gap-2">
              <Home className="h-4 w-4" />
              Kembali ke Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default function SuccessPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-muted flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Mengambil data...</div>
      </div>
    }>
      <SuccessContent />
    </Suspense>
  )
}
