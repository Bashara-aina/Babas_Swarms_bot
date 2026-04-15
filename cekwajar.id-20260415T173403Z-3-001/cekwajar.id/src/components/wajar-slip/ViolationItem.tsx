'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — ViolationItem Component
// Displays a single violation with severity badge, optional IDR amounts
// ══════════════════════════════════════════════════════════════════════════════

import type { Violation } from '@/types'

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
    dot: 'bg-red-500',
  },
  HIGH: {
    badge: 'bg-orange-500 text-white',
    label: 'HIGH',
    dot: 'bg-orange-500',
  },
  MEDIUM: {
    badge: 'bg-yellow-500 text-white',
    label: 'MEDIUM',
    dot: 'bg-yellow-500',
  },
  LOW: {
    badge: 'bg-blue-400 text-white',
    label: 'LOW',
    dot: 'bg-blue-400',
  },
} as const

export function ViolationItem({ violation, showAmount, reportedValue, calculatedValue }: ViolationItemProps) {
  const severity = SEVERITY_STYLES[violation.severity]
  const difference = calculatedValue - reportedValue
  const isUnderpaid = difference > 0

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-xs font-bold ${severity.badge}`}>
            {violation.code}
          </span>
          <div>
            <p className="font-semibold text-slate-800">{violation.titleID}</p>
            <p className="mt-1 text-sm text-slate-500">{violation.descriptionID}</p>
          </div>
        </div>
        <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${severity.badge}`}>
          {severity.label}
        </span>
      </div>

      {/* IDR breakdown (paid tier only) */}
      {showAmount && (
        <div className="mt-3 grid grid-cols-3 gap-2 rounded bg-slate-50 p-3 text-sm">
          <div>
            <p className="text-slate-400">Di Slip</p>
            <p className="font-medium text-slate-700">
              Rp {reportedValue.toLocaleString('id-ID')}
            </p>
          </div>
          <div>
            <p className="text-slate-400">Seharusnya</p>
            <p className="font-medium text-slate-700">
              Rp {calculatedValue.toLocaleString('id-ID')}
            </p>
          </div>
          <div>
            <p className="text-slate-400">Selisih</p>
            <p className={`font-semibold ${isUnderpaid ? 'text-red-600' : 'text-emerald-600'}`}>
              {isUnderpaid ? '+' : ''}Rp {Math.abs(difference).toLocaleString('id-ID')}
            </p>
          </div>
        </div>
      )}

      {/* Action recommendation */}
      {showAmount && violation.actionID && (
        <p className="mt-3 text-sm text-slate-600">
          <span className="font-medium">Langkah:</span> {violation.actionID}
        </p>
      )}
    </div>
  )
}
