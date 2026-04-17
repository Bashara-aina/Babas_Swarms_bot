// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — TrustBadges Component
// Social proof badges shown on homepage
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useEffect, useState } from 'react'
import { Shield, Clock, Users } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TrustBadgesProps {
  auditCount?: number
  className?: string
}

export function TrustBadges({ auditCount, className }: TrustBadgesProps) {
  const [count, setCount] = useState(auditCount ?? 0)
  const [loading, setLoading] = useState(!auditCount)

  useEffect(() => {
    if (auditCount !== undefined) return
    fetch('/api/stats/audit-count')
      .then((r) => r.json())
      .then((d) => setCount(d.count ?? 0))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [auditCount])

  return (
    <div className={cn('flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground', className)}>
      {/* Audit count */}
      <div className="flex items-center gap-1.5">
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100">
          <Users className="h-3.5 w-3.5 text-emerald-700" />
        </div>
        <span>
          {loading ? (
            <span className="inline-block h-4 w-12 animate-pulse rounded bg-muted" />
          ) : (
            <>
              <span className="font-semibold text-foreground">{count.toLocaleString('id-ID')}</span>
              {' '}audit slip gaji
            </>
          )}
        </span>
      </div>

      {/* No login needed */}
      <div className="flex items-center gap-1.5">
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100">
          <Shield className="h-3.5 w-3.5 text-blue-700" />
        </div>
        <span>Tidak perlu login</span>
      </div>

      {/* Fast */}
      <div className="flex items-center gap-1.5">
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-amber-100">
          <Clock className="h-3.5 w-3.5 text-amber-700" />
        </div>
        <span>Hasil dalam 30 detik</span>
      </div>
    </div>
  )
}