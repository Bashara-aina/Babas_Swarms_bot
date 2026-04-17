// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — SampleResultTeaser Component
// Collapsible example violations preview for wajar-slip page
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react'

export function SampleResultTeaser() {
  const [open, setOpen] = useState(false)

  return (
    <div className="mb-8 border border-dashed border-border rounded-xl overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm text-muted-foreground hover:bg-muted/30 transition-colors"
      >
        <span className="font-medium">Lihat contoh hasil audit →</span>
        {open ? (
          <ChevronUp className="w-4 h-4" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
      </button>

      {open && (
        <div className="px-4 pb-4 animate-fade-in-up">
          <p className="text-xs text-muted-foreground mb-3 italic">
            Contoh — bukan data nyata
          </p>

          {/* Sample verdict badge */}
          <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-3">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <span className="font-bold text-red-700 dark:text-red-400">
                2 Pelanggaran Ditemukan
              </span>
            </div>

            {/* Sample violation 1 */}
            <div className="bg-card rounded-lg p-3 mb-2 border border-red-100 dark:border-red-900">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 px-2 py-0.5 rounded font-mono">
                  V02
                </span>
                <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded font-semibold">
                  TINGGI
                </span>
              </div>
              <p className="text-sm font-semibold">PPh21 Tidak Dipotong</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                HRD tidak memotong PPh21 bulan ini.
              </p>
              <div className="mt-2 text-xs text-muted-foreground">
                Selisih: <span className="blur-sm select-none">Rp 185.000</span>
                <span className="ml-2 text-emerald-600 text-xs">
                  🔒 Upgrade untuk lihat angka
                </span>
              </div>
            </div>

            {/* Sample violation 2 */}
            <div className="bg-card rounded-lg p-3 border border-yellow-100 dark:border-yellow-900">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300 px-2 py-0.5 rounded font-mono">
                  V04
                </span>
                <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded font-semibold">
                  SEDANG
                </span>
              </div>
              <p className="text-sm font-semibold">JP Karyawan Kurang Dipotong</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Jaminan Pensiun yang dipotong lebih kecil dari seharusnya.
              </p>
            </div>
          </div>

          <p className="text-xs text-center text-muted-foreground">
            Hasil nyata bergantung pada data slip gaji kamu
          </p>
        </div>
      )}
    </div>
  )
}
