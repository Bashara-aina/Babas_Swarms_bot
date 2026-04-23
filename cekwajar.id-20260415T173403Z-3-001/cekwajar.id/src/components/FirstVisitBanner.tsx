// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — FirstVisitBanner Component
// Dismissible banner for new visitors using localStorage gate
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

const STORAGE_KEY = 'cekwajar_first_visit_seen'
const DISMISS_COOKIE = 'cekwajar_banner_dismissed'

export function FirstVisitBanner({ className }: { className?: string }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    try {
      const dismissed = localStorage.getItem(DISMISS_COOKIE)
      if (dismissed) return

      const seen = localStorage.getItem(STORAGE_KEY)
      if (!seen) {
        setVisible(true)
      }
    } catch {
      // localStorage not available (SSR, private browsing, etc.)
      setVisible(false)
    }
  }, [])

  if (!visible) return null

  const handleDismiss = () => {
    setVisible(false)
    try {
      localStorage.setItem(DISMISS_COOKIE, '1')
    } catch {
      // localStorage not available
    }
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className={`rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 ${className}`}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="shrink-0 mt-0.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-100">
            <span className="text-base">🎁</span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-amber-900">
            Audite slip gaji pertama — gratis!
          </p>
          <p className="mt-0.5 text-xs text-amber-700">
            Deteksi PPh21, BPJS, dan 5 jenis pelanggaran lain dalam 30 detik.
          </p>
          <div className="mt-2 flex items-center gap-2">
            <Link href="/wajar-slip">
              <Button size="sm" className="h-7 bg-amber-600 hover:bg-amber-700 text-xs">
                Mulai Gratis
              </Button>
            </Link>
          </div>
        </div>

        {/* Dismiss */}
        <button
          onClick={handleDismiss}
          aria-label="Dismiss banner"
          className="shrink-0 text-amber-400 hover:text-amber-600 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
