// cekwajar.id — ViolationSummaryBanner (spec 07)
// Quick-glance violation summary at top of verdict screen
// Shows total count + critical count in a prominent banner

import { AlertTriangle, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ViolationSummaryBannerProps {
  verdict: 'SESUAI' | 'ADA_PELANGGARAN'
  violationCount: number
  criticalCount?: number
  className?: string
}

export function ViolationSummaryBanner({
  verdict,
  violationCount,
  criticalCount = 0,
  className,
}: ViolationSummaryBannerProps) {
  if (verdict === 'SESUAI') return null

  const isCritical = criticalCount > 0

  return (
    <div
      className={cn(
        'rounded-xl p-5 mb-4 animate-scale-in',
        isCritical
          ? 'bg-red-50 dark:bg-red-950/30 border-2 border-red-300 dark:border-red-800'
          : 'bg-amber-50 dark:bg-amber-950/30 border-2 border-amber-300 dark:border-amber-800',
        className
      )}
    >
      <div className="flex items-center gap-3">
        <div
          className={cn(
            'w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0',
            isCritical ? 'bg-red-100 dark:bg-red-900' : 'bg-amber-100 dark:bg-amber-900'
          )}
        >
          <AlertTriangle
            className={cn(
              'w-6 h-6',
              isCritical ? 'text-red-600 dark:text-red-400' : 'text-amber-600 dark:text-amber-400'
            )}
          />
        </div>
        <div>
          <p
            className={cn(
              'text-2xl font-bold leading-none',
              isCritical ? 'text-red-700 dark:text-red-400' : 'text-amber-700 dark:text-amber-400'
            )}
          >
            {violationCount} Pelanggaran Ditemukan
          </p>
          <p className={cn('text-sm mt-1', isCritical ? 'text-red-600 dark:text-red-300' : 'text-amber-600 dark:text-amber-300')}>
            {criticalCount > 0
              ? `${criticalCount} bersifat KRITIS — perlu segera ditindaklanjuti`
              : 'Cek detail di bawah untuk penjelasan dan saran'}
          </p>
        </div>
      </div>
    </div>
  )
}
