// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — SamplePaidResultModal
// Shows what a paid result looks like — drives upgrade conversion
// Triggered by clicking "Lihat Contoh Hasil" on homepage
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { X, AlertTriangle, CheckCircle2, ArrowRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface SamplePaidResultModalProps {
  open: boolean
  onClose: () => void
}

function formatIDR(n: number) {
  return `Rp ${n.toLocaleString('id-ID')}`
}

export function SamplePaidResultModal({ open, onClose }: SamplePaidResultModalProps) {
  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Contoh hasil premium"
    >
      <div
        className="w-full max-w-lg rounded-2xl border bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div>
            <h2 className="text-lg font-bold text-foreground">Contoh Hasil Premium</h2>
            <p className="text-xs text-muted-foreground">Ini yang kamu dapat dengan paket Pro</p>
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-muted"
            aria-label="Tutup"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Verdict */}
        <div className="px-5 py-4">
          <Card className="border-red-200 bg-red-50">
            <CardContent className="flex items-start gap-3 p-4">
              <AlertTriangle className="h-8 w-8 shrink-0 text-red-600" />
              <div>
                <p className="font-bold text-red-800">Ada 3 Pelanggaran pada Slip Gaji</p>
                <p className="mt-0.5 text-sm text-red-600">
                  Total potensi kerugian: Rp 3.850.000/tahun
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Violations */}
        <div className="px-5 pb-4 space-y-2">
          <p className="text-xs font-medium text-muted-foreground mb-2">Pelanggaran yang ditemukan:</p>
          {[
            { code: 'V04', label: 'PPh21 kurang bayar', slip: 'Rp 0', should: 'Rp 425.000', diff: '+Rp 425.000' },
            { code: 'V01', label: 'JHT tidak dibayar', slip: 'Rp 0', should: 'Rp 170.000', diff: '+Rp 170.000' },
            { code: 'V05', label: 'BPJS Kesehatan tidak dipotong', slip: 'Rp 0', should: 'Rp 150.000', diff: '+Rp 150.000' },
          ].map((v) => (
            <div key={v.code} className="flex items-center justify-between rounded-lg border bg-white px-3 py-2">
              <div className="flex items-center gap-2">
                <span className="rounded bg-red-100 px-1.5 py-0.5 text-xs font-semibold text-red-700">{v.code}</span>
                <span className="text-sm text-foreground">{v.label}</span>
              </div>
              <span className="text-xs font-semibold text-red-600">{v.diff}</span>
            </div>
          ))}
        </div>

        {/* Calculations table */}
        <div className="px-5 pb-4">
          <div className="rounded-lg border bg-muted overflow-hidden">
            <div className="border-b bg-muted/80 px-3 py-2">
              <p className="text-xs font-semibold text-muted-foreground">Rincian Kalkulasi (Lihat di paket Pro)</p>
            </div>
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left py-1.5 px-3 font-medium text-muted-foreground">Komponen</th>
                  <th className="text-right py-1.5 px-3 font-medium text-muted-foreground">Di Slip</th>
                  <th className="text-right py-1.5 px-3 font-medium text-muted-foreground">Seharusnya</th>
                </tr>
              </thead>
              <tbody className="text-muted-foreground">
                <tr className="border-b">
                  <td className="py-1.5 px-3">PPh21</td>
                  <td className="text-right">Rp 0</td>
                  <td className="text-right">Rp 425.000</td>
                </tr>
                <tr className="border-b">
                  <td className="py-1.5 px-3">JHT (2%)</td>
                  <td className="text-right">Rp 0</td>
                  <td className="text-right">Rp 170.000</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-3">JP (1%)</td>
                  <td className="text-right">Rp 75.000</td>
                  <td className="text-right">Rp 85.000</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* CTA */}
        <div className="border-t px-5 py-4">
          <Button
            onClick={() => { onClose(); window.location.href = '/upgrade' }}
            className="w-full bg-emerald-600 hover:bg-emerald-700"
          >
            Lihat Semua Fitur Premium
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
          <p className="mt-2 text-center text-xs text-muted-foreground">
            Mulai dari Rp 29.900/bulan · Tidak perlu kartu kredit
          </p>
        </div>
      </div>
    </div>
  )
}