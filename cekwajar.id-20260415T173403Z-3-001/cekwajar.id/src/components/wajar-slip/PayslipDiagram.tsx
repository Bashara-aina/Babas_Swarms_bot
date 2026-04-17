'use client'

// ==============================================================================
// cekwajar.id — Payslip Diagram (Spec 10)
// Payslip audit diagram with red-highlighted violation rows
// ==============================================================================

import { useEffect, useState, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'
import { CheckCircle2, XCircle, AlertTriangle, TrendingUp } from 'lucide-react'

// --- Types --------------------------------------------------------------------

interface PayslipItem {
  label: string
  amount: number
  type: 'earning' | 'deduction' | 'contribution'
  status: 'ok' | 'violation' | 'warning'
  expected?: number
  violationDetail?: string
}

interface PayslipDiagramProps {
  items: PayslipItem[]
  employerName?: string
  period?: string
  totalEarnings: number
  totalDeductions: number
  totalTakeHome: number
  violations: { count: number; amount: number }
  className?: string
}

// --- Formatters ---------------------------------------------------------------

function formatIDR(amount: number): string {
  return `Rp ${amount.toLocaleString('id-ID')}`
}

// --- Category config -----------------------------------------------------------

const CATEGORY_COLORS: Record<string, { bg: string; text: string; icon: string }> = {
  earning: { bg: 'bg-emerald-50', text: 'text-emerald-700', icon: '💰' },
  deduction: { bg: 'bg-amber-50', text: 'text-amber-700', icon: '✂️' },
  contribution: { bg: 'bg-blue-50', text: 'text-blue-700', icon: '🏛️' },
}

// --- Main Component -----------------------------------------------------------

export function PayslipDiagram({
  items,
  employerName,
  period,
  totalEarnings,
  totalDeductions,
  totalTakeHome,
  violations,
  className,
}: PayslipDiagramProps) {
  const [animate, setAnimate] = useState(false)
  const prefersReducedMotion = useRef(false)

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    prefersReducedMotion.current = mq.matches
    if (!mq.matches) {
      const t = setTimeout(() => setAnimate(true), 400)
      return () => clearTimeout(t)
    } else {
      setAnimate(true)
    }
  }, [])

  const violationItems = items.filter((i) => i.status === 'violation')
  const warningItems = items.filter((i) => i.status === 'warning')

  return (
    <figure
      role="img"
      aria-label={`Diagram audit slip gaji${employerName ? ` dari ${employerName}` : ''}${period ? ` periode ${period}` : ''}. ${violations.count} pelanggaran ditemukan dengan total estimasi ${formatIDR(violations.amount)}`}
      className={className}
    >
      <figcaption className="sr-only">
        Diagram audit slip gaji{employerName ? ` dari ${employerName}` : ''}.
        Total pendapatan: {formatIDR(totalEarnings)}.
        Total potongan: {formatIDR(totalDeductions)}.
        Total take-home: {formatIDR(totalTakeHome)}.
        {violationItems.map((item) =>
          `${item.label}: dibayar ${formatIDR(item.amount)}, seharusnya ${item.expected ? formatIDR(item.expected) : 'lebih tinggi'}.`
        ).join(' ')}
        Total estimasi pelanggaran: {violations.count} komponen, {formatIDR(violations.amount)}.
      </figcaption>

      <Card>
        <CardContent className="p-4">
          {/* Header */}
          {(employerName || period) && (
            <div className="mb-4 pb-3 border-b border-border">
              <div className="flex justify-between items-center">
                <div>
                  {employerName && (
                    <p className="text-sm font-semibold text-foreground">{employerName}</p>
                  )}
                  {period && (
                    <p className="text-xs text-muted-foreground">{period}</p>
                  )}
                </div>
                {violations.count > 0 && (
                  <div className="flex items-center gap-1.5 px-2.5 py-1 bg-red-50 border border-red-200 rounded-full">
                    <XCircle className="h-3.5 w-3.5 text-red-500" />
                    <span className="text-xs font-semibold text-red-700">
                      {violations.count} pelanggaran
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Summary totals */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className={cn('text-center p-3 rounded-lg', CATEGORY_COLORS.earning.bg)}>
              <div className="text-xs text-muted-foreground mb-1">Total Pendapatan</div>
              <div className={cn('font-bold', CATEGORY_COLORS.earning.text)}>
                {formatIDR(totalEarnings)}
              </div>
            </div>
            <div className={cn('text-center p-3 rounded-lg', CATEGORY_COLORS.deduction.bg)}>
              <div className="text-xs text-muted-foreground mb-1">Total Potongan</div>
              <div className={cn('font-bold', CATEGORY_COLORS.deduction.text)}>
                {formatIDR(totalDeductions)}
              </div>
            </div>
            <div className="text-center p-3 rounded-lg bg-muted">
              <div className="text-xs text-muted-foreground mb-1">Take Home Pay</div>
              <div className="font-bold text-foreground">
                {formatIDR(totalTakeHome)}
              </div>
            </div>
          </div>

          {/* Violation summary banner */}
          {violations.count > 0 && (
            <div
              className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg"
              style={{
                opacity: animate ? 1 : 0,
                transition: 'opacity 0.5s ease 0.2s',
              }}
            >
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-red-800">
                    {violations.count} komponen tidak sesuai regulasi
                  </p>
                  <p className="text-xs text-red-600 mt-0.5">
                    Estimasi underpayment:{' '}
                    <span className="font-bold">{formatIDR(violations.amount)}</span>
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Item rows */}
          <div className="space-y-2">
            {items.map((item, i) => {
              const colors = CATEGORY_COLORS[item.type]
              const isViolation = item.status === 'violation'
              const isWarning = item.status === 'warning'

              return (
                <div
                  key={item.label}
                  className={cn(
                    'flex items-center justify-between p-3 rounded-lg border transition-all',
                    isViolation && 'bg-red-50 border-red-200',
                    isWarning && 'bg-amber-50 border-amber-200',
                    !isViolation && !isWarning && 'bg-white border-border'
                  )}
                  style={{
                    opacity: animate ? 1 : 0,
                    transform: animate ? 'translateX(0)' : 'translateX(-8px)',
                    transition: `opacity 0.4s ease ${0.3 + i * 0.06}s, transform 0.4s ease ${0.3 + i * 0.06}s`,
                  }}
                >
                  {/* Left: icon + label */}
                  <div className="flex items-center gap-2">
                    <span className="text-base">{colors.icon}</span>
                    <div>
                      <p
                        className={cn(
                          'text-sm font-medium',
                          isViolation ? 'text-red-800' : isWarning ? 'text-amber-800' : 'text-foreground'
                        )}
                      >
                        {item.label}
                      </p>
                      {isViolation && item.violationDetail && (
                        <p className="text-xs text-red-600 mt-0.5">{item.violationDetail}</p>
                      )}
                      {isWarning && item.violationDetail && (
                        <p className="text-xs text-amber-600 mt-0.5">{item.violationDetail}</p>
                      )}
                    </div>
                  </div>

                  {/* Right: amount + status */}
                  <div className="flex items-center gap-2">
                    {item.expected && item.expected !== item.amount && (
                      <span className="text-xs text-muted-foreground line-through">
                        {formatIDR(item.expected)}
                      </span>
                    )}
                    <span
                      className={cn(
                        'text-sm font-bold',
                        isViolation ? 'text-red-700' : isWarning ? 'text-amber-700' : colors.text
                      )}
                    >
                      {formatIDR(item.amount)}
                    </span>
                    {isViolation ? (
                      <XCircle className="h-4 w-4 text-red-500 shrink-0" />
                    ) : isWarning ? (
                      <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Take home row */}
          <div
            className="mt-4 pt-3 border-t-2 border-emerald-300 flex justify-between items-center p-3 bg-emerald-50 rounded-lg"
            style={{
              opacity: animate ? 1 : 0,
              transition: 'opacity 0.4s ease 1s',
            }}
          >
            <span className="flex items-center gap-2 text-sm font-bold text-emerald-800">
              <TrendingUp className="h-4 w-4" />
              Take Home Pay
            </span>
            <span className="text-lg font-bold text-emerald-700">
              {formatIDR(totalTakeHome)}
            </span>
          </div>
        </CardContent>
      </Card>
    </figure>
  )
}
