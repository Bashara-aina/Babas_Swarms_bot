// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — FirstVisitBanner Component
// Bottom-right emerald banner for first-time visitors
// Uses localStorage to show only once per visitor
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useEffect, useState } from 'react'
import { X, Zap } from 'lucide-react'
import Link from 'next/link'

export function FirstVisitBanner() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    try {
      const hasSeen = localStorage.getItem('cw_has_visited')
      if (!hasSeen) {
        setVisible(true)
        localStorage.setItem('cw_has_visited', '1')
      }
    } catch {
      // localStorage unavailable — don't show banner
    }
  }, [])

  if (!visible) return null

  return (
    <div className="fixed bottom-20 left-4 right-4 md:left-auto md:right-6 md:max-w-sm z-50 animate-slide-in-bottom">
      <div className="bg-emerald-600 dark:bg-emerald-700 text-white rounded-xl shadow-xl p-4 flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
          <Zap className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm">Baru di cekwajar.id? 👋</p>
          <p className="text-xs text-emerald-100 mt-0.5">
            Cek slip gaji butuh 30 detik. Gratis, tanpa daftar.
          </p>
          <Link
            href="/wajar-slip"
            className="inline-block mt-2 text-xs font-semibold bg-white text-emerald-700 px-3 py-1 rounded-full hover:bg-emerald-50 transition-colors"
            onClick={() => setVisible(false)}
          >
            Coba sekarang →
          </Link>
        </div>
        <button
          type="button"
          onClick={() => setVisible(false)}
          className="flex-shrink-0 text-white/70 hover:text-white transition-colors"
          aria-label="Tutup"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
