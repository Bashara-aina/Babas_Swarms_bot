// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — PostPaymentSuccess
// Shown after successful Midtrans payment
// Confirms subscription upgrade and shows next steps
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useState } from 'react'
import Link from 'next/link'
import { CheckCircle2, Zap } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

type Tier = 'basic' | 'pro'

function PaymentContent() {
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [tier, setTier] = useState<Tier>('basic')

  useEffect(() => {
    const orderId = searchParams.get('order_id')
    if (!orderId) {
      setStatus('error')
      return
    }

    // In production, verify with your backend that the payment succeeded
    // For now, assume any return with order_id = success
    fetch(`/api/payment/verify?order_id=${encodeURIComponent(orderId)}`)
      .then((r) => r.json())
      .then((d) => {
        if (d.success) {
          setTier(d.tier ?? 'basic')
          setStatus('success')
        } else {
          setStatus('error')
        }
      })
      .catch(() => setStatus('error'))
  }, [searchParams])

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center gap-4 p-8 text-center">
            <div className="h-12 w-12 rounded-full border-4 border-emerald-200 border-t-emerald-600 animate-spin" />
            <div>
              <p className="font-semibold">Memverifikasi pembayaran...</p>
              <p className="mt-1 text-sm text-muted-foreground">Halaman ini akan otomatis teralihkan</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
        <Card className="w-full max-w-md border-red-200 bg-red-50">
          <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
            <p className="text-lg font-bold text-red-800">Terjadi Kesalahan</p>
            <p className="text-sm text-red-600">Tidak dapat memverifikasi pembayaran. Hubungi support.</p>
            <Link href="/dashboard">
              <Button variant="outline" className="mt-2">Kembali ke Dashboard</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  const tierLabel = tier === 'pro' ? 'Pro' : 'Basic'

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md border-emerald-200 bg-emerald-50">
        <CardContent className="flex flex-col items-center gap-4 p-8 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100">
            <CheckCircle2 className="h-8 w-8 text-emerald-600" />
          </div>

          <div>
            <p className="text-2xl font-bold text-emerald-800">Pembayaran Berhasil!</p>
            <p className="mt-1 text-sm text-emerald-700">
              Kamu sekarang menggunakan paket {tierLabel}
            </p>
          </div>

          <div className="w-full space-y-2 rounded-lg bg-white/80 p-4 text-left text-sm text-muted-foreground">
            <p className="font-semibold text-foreground">Yang bisa kamu akses sekarang:</p>
            <ul className="space-y-1.5">
              {tier === 'pro' ? (
                <>
                  <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-600" /> Detail selisih IDR semua pelanggaran</li>
                  <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-600" /> Perbandingan gaji dengan 12.000+ data</li>
                  <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-600" /> Perbandingan biaya hidup antar kota</li>
                  <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-600" /> Harga properti vs NJOP</li>
                  <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-600" /> Tanpa batas audit slip gaji</li>
                </>
              ) : (
                <>
                  <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-600" /> Detail selisih PPh21 & BPJS</li>
                  <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-600" /> Tanpa batas audit slip gaji</li>
                  <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-600" /> Langsung tahu pelanggaran mana</li>
                </>
              )}
            </ul>
          </div>

          <div className="flex w-full gap-3">
            <Link href="/dashboard" className="flex-1">
              <Button variant="outline" className="w-full gap-2">
                ke Dashboard
              </Button>
            </Link>
            <Link href="/wajar-slip" className="flex-1">
              <Button className="w-full gap-2 bg-emerald-600 hover:bg-emerald-700">
                <Zap className="h-4 w-4" />
                Cek Slip Gaji
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Wrap in Suspense since useSearchParams requires it in Next.js App Router
export default function PostPaymentSuccessPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center gap-4 p-8 text-center">
            <div className="h-12 w-12 rounded-full border-4 border-emerald-200 border-t-emerald-600 animate-spin" />
            <div>
              <p className="font-semibold">Memuat...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    }>
      <PaymentContent />
    </Suspense>
  )
}