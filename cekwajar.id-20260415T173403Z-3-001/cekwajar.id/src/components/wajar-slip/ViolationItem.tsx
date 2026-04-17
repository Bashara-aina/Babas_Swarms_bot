'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — ViolationItem Component
// Displays a single violation with severity badge, optional IDR amounts
// Copy sourced from COPY.violations, with Violation type fields as fallback
// ══════════════════════════════════════════════════════════════════════════════

import type { Violation } from '@/types'
import { COPY } from '@/lib/copy'

interface ViolationItemProps {
  violation: Violation
  showAmount: boolean
  reportedValue: number
  calculatedValue: number
}

const SEVERITY_STYLES = {
  CRITICAL: {
    badge: 'bg-red-600 text-white',
    label: 'CRITICAL',
  },
  HIGH: {
    badge: 'bg-orange-500 text-white',
    label: 'HIGH',
  },
  MEDIUM: {
    badge: 'bg-yellow-500 text-white',
    label: 'MEDIUM',
  },
  LOW: {
    badge: 'bg-blue-400 text-white',
    label: 'LOW',
  },
} as const

export function ViolationItem({ violation, showAmount, reportedValue, calculatedValue }: ViolationItemProps) {
  const severity = SEVERITY_STYLES[violation.severity]
  const difference = calculatedValue - reportedValue
  const isUnderpaid = difference > 0

  // Prefer COPY.violations; fall back to violation type fields
  const copy = COPY.violations[violation.code as keyof typeof COPY.violations]
  const title = copy?.title ?? violation.titleID
  const description = copy?.description ?? violation.descriptionID
  const recommendation = copy?.recommendation ?? violation.actionID

  return (
    <div className={cn(
      'rounded-lg border p-4',
      violation.code === 'V06'
        ? 'border-red-300 bg-red-50/50'
        : 'border-border bg-white'
    )}>
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className={cn(
            'mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-xs font-bold',
            severity.badge,
            violation.code === 'V06' && 'bg-red-600 text-white animate-pulse'
          )}>
            {violation.code}
          </span>
          <div>
            <p className="font-semibold text-foreground">
              {violation.code === 'V06' && (
                <span className="text-red-600 mr-1">PELANGGARAN HUKUM —</span>
              )}
              {title}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">{description}</p>
          </div>
        </div>
        <span className={cn(
          'shrink-0 rounded-full px-2 py-0.5 text-xs font-medium',
          severity.badge
        )}>
          {severity.label}
        </span>
      </div>

      {/* IDR breakdown (paid tier only) */}
      {showAmount && (
        <div className="mt-3 grid grid-cols-3 gap-2 rounded bg-muted p-3 text-sm">
          <div>
            <p className="text-muted-foreground">Di Slip</p>
            <p className="font-medium text-foreground">
              Rp {reportedValue.toLocaleString('id-ID')}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Seharusnya</p>
            <p className="font-medium text-foreground">
              Rp {calculatedValue.toLocaleString('id-ID')}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Selisih</p>
            <p className={cn('font-semibold', isUnderpaid ? 'text-red-600' : 'text-emerald-600')}>
              {isUnderpaid ? '+' : ''}Rp {Math.abs(difference).toLocaleString('id-ID')}
            </p>
          </div>
        </div>
      )}

      {/* Action recommendation */}
      {recommendation && (
        <p className="mt-3 text-sm text-muted-foreground">
          <span className="font-medium text-foreground">Langkah:</span> {recommendation}
        </p>
      )}
    </div>
  )
}

function cn(...classes: (string | undefined | false)[]) {
  return classes.filter(Boolean).join(' ')
}
