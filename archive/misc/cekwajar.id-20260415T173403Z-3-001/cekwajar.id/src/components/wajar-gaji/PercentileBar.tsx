'use client'

// ==============================================================================
// cekwajar.id — Percentile Bar (Spec 10)
// Animated percentile distribution bar with red/green/blue zones
// ==============================================================================

import { useState, useEffect, useRef } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

// --- Types --------------------------------------------------------------------

interface PercentileBarProps {
  p25: number | null
  p50: number | null
  p75: number | null
  userSalary: number | null
  city: string
  jobTitle: string
}

// --- Formatters ---------------------------------------------------------------

function formatIDR(amount: number): string {
  return `Rp ${amount.toLocaleString('id-ID')}`
}

// --- Threshold markers (relative positions on the bar) ----------------------
// P25 = 25% from left, P50 = 50%, P75 = 75%

// --- Main Component -----------------------------------------------------------

export function PercentileBar({
  p25,
  p50,
  p75,
  userSalary,
  city,
  jobTitle,
}: PercentileBarProps) {
  const [animateUser, setAnimateUser] = useState(false)
  const [animateP50, setAnimateP50] = useState(false)
  const prefersReducedMotion = useRef(false)

  // Check reduced motion preference
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    prefersReducedMotion.current = mq.matches
    if (!mq.matches) {
      // Animate markers in sequence
      const t1 = setTimeout(() => setAnimateP50(true), 200)
      const t2 = setTimeout(() => setAnimateUser(true), 500)
      return () => { clearTimeout(t1); clearTimeout(t2) }
    } else {
      setAnimateP50(true)
      setAnimateUser(true)
    }
  }, [])

  if (!p50) return null

  const p25Val = p25 ?? Math.round(p50 * 0.78)
  const p75Val = p75 ?? Math.round(p50 * 1.28)
  const range = p75Val - p25Val

  // Positions as percentages on the 0-100 scale
  const p25Pos = 25
  const p50Pos = 50
  const p75Pos = 75

  const userPos = userSalary
    ? Math.min(97, Math.max(3, ((userSalary - p25Val) / range) * 100))
    : null

  const markerTransition = prefersReducedMotion.current
    ? 'none'
    : 'left 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)'

  return (
    <div>
      {/* Accessible figcaption */}
      <figure role="img" aria-label={`Distribusi gaji untuk ${jobTitle} di ${city}. P25 ${formatIDR(p25Val)}, Median ${formatIDR(p50)}, P75 ${formatIDR(p75Val)}`}>
        <figcaption className="sr-only">
          Grafik distribusi gaji untuk {jobTitle} di {city}. Quartil pertama (P25) adalah {formatIDR(p25Val)},
          median (P50) adalah {formatIDR(p50)}, dan quartil ketiga (P75) adalah {formatIDR(p75Val)}.
          {userSalary != null && ` Posisi gaji kamu di ${userSalary > p50 ? 'atas' : 'bawah'} median.`}
        </figcaption>

        {/* Label row */}
        <div className="flex justify-between text-xs text-muted-foreground mb-2">
          <div className="text-left">
            <span className="font-medium text-red-600">P25</span>
            <br />
            <span>{formatIDR(p25Val)}</span>
          </div>
          <div className="text-center">
            <span className="font-medium text-emerald-600">Median</span>
            <br />
            <span className="text-foreground font-semibold">{formatIDR(p50)}</span>
          </div>
          <div className="text-right">
            <span className="font-medium text-blue-600">P75</span>
            <br />
            <span>{formatIDR(p75Val)}</span>
          </div>
        </div>

        {/* Bar with zones */}
        <div className="relative h-8 rounded-full overflow-hidden flex">
          {/* Red zone — bottom quartile */}
          <div
            className="h-full bg-gradient-to-r from-red-200 to-red-300 flex items-center justify-center"
            style={{ width: '25%' }}
            aria-hidden="true"
          />
          {/* Green zone — middle half */}
          <div
            className="h-full bg-gradient-to-r from-emerald-300 to-emerald-400 flex items-center justify-center"
            style={{ width: '50%' }}
            aria-hidden="true"
          />
          {/* Blue zone — top quartile */}
          <div
            className="h-full bg-gradient-to-r from-blue-300 to-blue-400 flex items-center justify-center"
            style={{ width: '25%' }}
            aria-hidden="true"
          />

          {/* P50 vertical marker */}
          <div
            className="absolute top-0 bottom-0 w-1 bg-emerald-700 z-20 shadow-[0_0_6px_rgba(16,185,129,0.8)]"
            style={{
              left: `${p50Pos}%`,
              transform: 'translateX(-50%)',
              transition: markerTransition,
              opacity: animateP50 ? 1 : 0,
            }}
            aria-hidden="true"
          />

          {/* User salary triangle marker */}
          {userPos !== null && (
            <div
              className="absolute z-30"
              style={{
                left: `${userPos}%`,
                top: '-2px',
                transform: 'translateX(-50%)',
                transition: markerTransition,
                opacity: animateUser ? 1 : 0,
              }}
              aria-hidden="true"
            >
              <svg
                width="16"
                height="36"
                viewBox="0 0 16 36"
                fill="none"
                className="drop-shadow-md"
              >
                <polygon
                  points="8,8 2,0 14,0"
                  fill="#2563EB"
                />
                <rect
                  x="6"
                  y="8"
                  width="4"
                  height="20"
                  rx="2"
                  fill="#2563EB"
                />
              </svg>
            </div>
          )}
        </div>

        {/* Zone legend */}
        <div className="flex justify-between mt-2 text-xs text-muted-foreground px-1">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-sm bg-red-300" aria-hidden="true" />
            <span>25% bawah</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-sm bg-emerald-300" aria-hidden="true" />
            <span>Median</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-sm bg-blue-300" aria-hidden="true" />
            <span>25% atas</span>
          </div>
        </div>

        {/* User position callout */}
        {userSalary && (
          <div
            className="mt-3 text-center text-sm"
            style={{
              opacity: animateUser ? 1 : 0,
              transition: 'opacity 0.4s ease 0.8s',
            }}
          >
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
              {userSalary > p50
                ? `+${formatIDR(userSalary - p50)} di atas median`
                : userSalary < p50 * 0.95
                ? `${formatIDR(p50 - userSalary)} di bawah median`
                : 'Di sekitar median'}
            </span>
          </div>
        )}
      </figure>
    </div>
  )
}
