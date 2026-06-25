'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — NumberTicker Component
// Animates a number from 0 (or previous value) to the target value
// Used for: KPI cards, dashboard stats, financial totals
// ══════════════════════════════════════════════════════════════════════════════

import { useEffect, useRef, useState } from 'react'

interface NumberTickerProps {
  value: number
  /** Default: '' — prepended to the number (e.g. 'Rp ' for IDR) */
  prefix?: string
  /** Default: '' — appended to the number (e.g. '%', 'jt') */
  suffix?: string
  /** Animation duration in ms. Default: 1200 */
  duration?: number
  /** Locale for number formatting. Default: 'id-ID' (Indonesian) */
  locale?: string
  /** Decimal places. Default: 0 */
  decimals?: number
  /** Extra className */
  className?: string
}

export function NumberTicker({
  value,
  prefix = '',
  suffix = '',
  duration = 1200,
  locale = 'id-ID',
  decimals = 0,
  className,
}: NumberTickerProps) {
  const [display, setDisplay] = useState(0)
  const startRef = useRef(0)
  const rafRef = useRef<number | null>(null)
  const startTimeRef = useRef<number | null>(null)

  useEffect(() => {
    // Easing: ease-out cubic
    const easeOut = (t: number) => 1 - Math.pow(1 - t, 3)

    const animate = (currentTime: number) => {
      if (startTimeRef.current === null) {
        startTimeRef.current = currentTime
      }

      const elapsed = currentTime - startTimeRef.current
      const progress = Math.min(elapsed / duration, 1)
      const easedProgress = easeOut(progress)

      setDisplay(Math.floor(startRef.current + (value - startRef.current) * easedProgress))

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate)
      }
    }

    // Start from the last displayed value for smooth transition on re-render
    startRef.current = display
    startTimeRef.current = null

    rafRef.current = requestAnimationFrame(animate)

    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current)
      }
    }
  }, [value, duration, display])

  const formatted = display.toLocaleString(locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })

  return (
    <span className={className}>
      {prefix}
      {formatted}
      {suffix}
    </span>
  )
}
