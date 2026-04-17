// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — SampleResultTeaser Component
// Animated mock result card shown on homepage to demonstrate tool output
// ══════════════════════════════════════════════════════════════════════════════

import Link from 'next/link'
import { CheckCircle, AlertTriangle, ArrowRight, Eye } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface SampleResultTeaserProps {
  className?: string
  onViewPremiumSample?: () => void
}

export function SampleResultTeaser({ className, onViewPremiumSample }: SampleResultTeaserProps) {
  return (
    <div className={className}>
      <div className="rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-white p-6 shadow-sm overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-emerald-600" />
            <span className="text-sm font-semibold text-emerald-700">3 Pelanggaran Terdeteksi</span>
          </div>
          <span className="text-xs text-muted-foreground">Contoh hasil</span>
        </div>

        {/* Mock violations */}
        <div className="space-y-2.5 mb-4">
          {/* Violation 1 */}
          <div className="flex items-center justify-between rounded-lg border border-red-100 bg-red-50/50 p-3">
            <div className="flex items-center gap-2">
              <div className="h-5 w-5 rounded-full bg-red-600 flex items-center justify-center">
                <span className="text-white text-xs font-bold">!</span>
              </div>
              <span className="text-sm font-medium text-foreground">PPh21 tidak dipotong</span>
            </div>
            <span className="text-sm font-bold text-red-600">Rp 1.240.000</span>
          </div>

          {/* Violation 2 */}
          <div className="flex items-center justify-between rounded-lg border border-orange-100 bg-orange-50/50 p-3">
            <div className="flex items-center gap-2">
              <div className="h-5 w-5 rounded-full bg-orange-500 flex items-center justify-center">
                <span className="text-white text-xs font-bold">!</span>
              </div>
              <span className="text-sm font-medium text-foreground">BPJS Kesehatan tidak dihitung</span>
            </div>
            <span className="text-sm font-bold text-orange-600">Rp 480.000</span>
          </div>

          {/* Violation 3 */}
          <div className="flex items-center justify-between rounded-lg border border-amber-100 bg-amber-50/50 p-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <span className="text-sm font-medium text-foreground">THT tidak dibayar</span>
            </div>
            <span className="text-sm font-bold text-amber-600">Rp 320.000</span>
          </div>
        </div>

        {/* Total */}
        <div className="flex items-center justify-between rounded-lg border border-emerald-200 bg-emerald-50 p-3 mb-4">
          <span className="text-sm font-semibold text-foreground">Total Potensi Kerugian</span>
          <span className="text-base font-bold text-emerald-700">Rp 2.040.000</span>
        </div>

        {/* CTA */}
        <div className="space-y-2">
          {onViewPremiumSample && (
            <button
              type="button"
              onClick={onViewPremiumSample}
              className="w-full flex items-center justify-center gap-2 rounded-lg border border-border bg-white py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            >
              <Eye className="h-4 w-4" />
              Lihat Contoh Hasil Premium
            </button>
          )}
          <Link href="/wajar-slip">
            <Button className="w-full bg-emerald-600 hover:bg-emerald-700 gap-2">
              Cek Slip Gaji Kamu
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
