// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — ViolationSummaryBanner
// Quick-glance violation summary at top of verdict screen
// Shows verdict type + violation count in a single line
// ══════════════════════════════════════════════════════════════════════════════

import { CheckCircle2, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ViolationSummaryBannerProps {
  verdict: 'SESUAI' | 'ADA_PELANGGARAN'
  violationCount: number
  className?: string
}

export function ViolationSummaryBanner({
  verdict,
  violationCount,
  className,
}: ViolationSummaryBannerProps) {
  const isSesuai = verdict === 'SESUAI'

  return (
    <div
      className={cn(
        'flex items-center gap-2 rounded-xl border px-4 py-2.5',
        isSesuai
          ? 'border-emerald-200 bg-emerald-50'
          : 'border-red-200 bg-red-50',
        className
      )}
      role="status"
      aria-live="polite"
    >
      {isSesuai ? (
        <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" />
      ) : (
        <AlertTriangle className="h-5 w-5 shrink-0 text-red-600" />
      )}
      <span className={cn('text-sm font-semibold', isSesuai ? 'text-emerald-800' : 'text-red-800')}>
        {isSesuai
          ? 'Slip sesuai regulasi — tidak ada pelanggaran'
          : `${violationCount} pelanggaran ditemukan`}
      </span>
    </div>
  )
}