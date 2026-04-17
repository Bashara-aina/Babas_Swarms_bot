// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — AuditCounterBadge Component
// Live audit count for the past 7 days from Supabase
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useEffect, useState } from 'react'
import { TrendingUp } from 'lucide-react'

export function AuditCounterBadge() {
  const [count, setCount] = useState<number | null>(null)

  useEffect(() => {
    fetch('/api/stats/audit-count')
      .then((r) => r.json())
      .then((d) => setCount(d.count ?? 0))
      .catch(() => setCount(null))
  }, [])

  if (count === null) return null

  const formatted = new Intl.NumberFormat('id-ID').format(count)

  return (
    <div className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
      <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
      <span>
        <strong className="text-foreground">{formatted}</strong> pengecekan minggu ini
      </span>
    </div>
  )
}
