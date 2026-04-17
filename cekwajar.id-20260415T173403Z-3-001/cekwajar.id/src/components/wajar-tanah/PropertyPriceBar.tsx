'use client'

// ==============================================================================
// cekwajar.id — Property Price Bar (Spec 10)
// Zone-colored property price bar with animated price marker
// ==============================================================================

import { useState, useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'

// --- Types --------------------------------------------------------------------

interface PropertyPriceBarProps {
  userPrice: number
  fairPrice: number
  lowerBound: number
  upperBound: number
  city: string
  propertyType: string
}

// --- Formatters ---------------------------------------------------------------

function formatIDR(amount: number): string {
  return `Rp ${amount.toLocaleString('id-ID')}`
}

// --- Main Component -----------------------------------------------------------

export function PropertyPriceBar({
  userPrice,
  fairPrice,
  lowerBound,
  upperBound,
  city,
  propertyType,
}: PropertyPriceBarProps) {
  const [animateMarker, setAnimateMarker] = useState(false)
  const [animatePrice, setAnimatePrice] = useState(false)
  const prefersReducedMotion = useRef(false)

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    prefersReducedMotion.current = mq.matches
    if (!mq.matches) {
      const t1 = setTimeout(() => setAnimateMarker(true), 300)
      const t2 = setTimeout(() => setAnimatePrice(true), 600)
      return () => { clearTimeout(t1); clearTimeout(t2) }
    } else {
      setAnimateMarker(true)
      setAnimatePrice(true)
    }
  }, [])

  const range = upperBound - lowerBound
  // Position user price on bar
  const userPos = Math.min(97, Math.max(3, ((userPrice - lowerBound) / range) * 100))
  // Fair price marker position
  const fairPos = ((fairPrice - lowerBound) / range) * 100

  // Zone widths (relative)
  const underValPct = Math.min(50, Math.max(10, ((fairPrice - lowerBound) / range) * 100))
  const fairPct = Math.min(40, Math.max(15, ((upperBound - fairPrice) / range) * 100))
  const overPct = 100 - underValPct - fairPct

  const markerTransition = prefersReducedMotion.current
    ? 'none'
    : 'left 0.7s cubic-bezier(0.34, 1.56, 0.64, 1)'

  const verdict = userPrice < lowerBound
    ? 'DI BAWAH_WAJAR'
    : userPrice > upperBound
    ? 'LEBIH_MAHAL'
    : 'WAJAR'

  const verdictColor =
    verdict === 'DI BAWAH_WAJAR' ? 'emerald'
    : verdict === 'LEBIH_MAHAL' ? 'red'
    : 'blue'

  return (
    <figure
      role="img"
      aria-label={`Perbandingan harga ${propertyType} di ${city}. Harga kamu ${formatIDR(userPrice)}, estimasi wajar ${formatIDR(fairPrice)}`}
    >
      <figcaption className="sr-only">
        Grafik perbandingan harga {propertyType} di {city}. Harga yang kamu input adalah {formatIDR(userPrice)}.
        Estimasi harga wajar berdasarkan data pasar adalah {formatIDR(fairPrice)}.
        {verdict === 'DI BAWAH_WAJAR' && ` Harga kamu di bawah estimasi wajar — ini adalah harga yang bagus.`}
        {verdict === 'LEBIH_MAHAL' && ` Harga kamu di atas estimasi wajar — hati-hati, harga可能过高。`}
        {verdict === 'WAJAR' && ` Harga kamu dalam range wajar.`}
      </figcaption>

      {/* Price labels */}
      <div className="flex justify-between text-xs text-muted-foreground mb-2">
        <div className="text-left">
          <span className="font-medium text-emerald-600">Terjangkau</span>
          <br />
          <span className="text-emerald-700 font-semibold">{formatIDR(lowerBound)}</span>
        </div>
        <div className="text-center">
          <span className="font-medium text-amber-600">Estimasi</span>
          <br />
          <span className="text-amber-700 font-bold">{formatIDR(fairPrice)}</span>
        </div>
        <div className="text-right">
          <span className="font-medium text-red-600">Mahal</span>
          <br />
          <span className="text-red-700 font-semibold">{formatIDR(upperBound)}</span>
        </div>
      </div>

      {/* Bar */}
      <div className="relative h-10 rounded-xl overflow-hidden flex">
        {/* Green zone */}
        <div
          className="h-full bg-gradient-to-r from-emerald-200 to-emerald-300 flex items-center justify-center"
          style={{ width: `${underValPct}%` }}
          aria-hidden="true"
        >
          {underValPct > 15 && (
            <span className="text-xs font-medium text-emerald-700">Terjangkau</span>
          )}
        </div>
        {/* Amber zone */}
        <div
          className="h-full bg-gradient-to-r from-amber-200 to-amber-300 flex items-center justify-center"
          style={{ width: `${fairPct}%` }}
          aria-hidden="true"
        >
          {fairPct > 15 && (
            <span className="text-xs font-medium text-amber-700">Wajar</span>
          )}
        </div>
        {/* Red zone */}
        <div
          className="h-full bg-gradient-to-r from-red-300 to-red-400 flex items-center justify-center"
          style={{ width: `${overPct}%` }}
          aria-hidden="true"
        >
          {overPct > 15 && (
            <span className="text-xs font-medium text-red-700">Kemahalan</span>
          )}
        </div>

        {/* Fair price dashed line */}
        <div
          className="absolute top-0 bottom-0 border-l-2 border-dashed border-amber-600 z-10"
          style={{ left: `${fairPos}%` }}
          aria-hidden="true"
        />

        {/* User price pin */}
        <div
          className="absolute z-20"
          style={{
            left: `${userPos}%`,
            top: '-2px',
            transform: 'translateX(-50%)',
            transition: markerTransition,
            opacity: animateMarker ? 1 : 0,
          }}
          aria-hidden="true"
        >
          <svg width="20" height="44" viewBox="0 0 20 44" fill="none">
            <circle cx="10" cy="22" r="9" fill="#7C3AED" stroke="white" strokeWidth="2" />
            <path d="M10 14 L10 8 M10 30 L10 36" stroke="white" strokeWidth="2" strokeLinecap="round" />
            <path d="M6 22 L14 22" stroke="white" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>
      </div>

      {/* Zone legend */}
      <div className="flex justify-between mt-2 text-xs text-muted-foreground px-1">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-emerald-200" aria-hidden="true" />
          <span>Terjangkau</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-amber-200" aria-hidden="true" />
          <span>Wajar</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-red-300" aria-hidden="true" />
          <span>Kemahalan</span>
        </div>
      </div>

      {/* Price callout */}
      <div
        className="mt-3 text-center"
        style={{
          opacity: animatePrice ? 1 : 0,
          transition: 'opacity 0.4s ease 0.9s',
        }}
      >
        <span
          className={cn(
            'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold border',
            verdictColor === 'emerald' && 'bg-emerald-50 border-emerald-200 text-emerald-700',
            verdictColor === 'red' && 'bg-red-50 border-red-200 text-red-700',
            verdictColor === 'blue' && 'bg-blue-50 border-blue-200 text-blue-700'
          )}
        >
          <span
            className={cn(
              'w-2.5 h-2.5 rounded-full',
              verdictColor === 'emerald' && 'bg-emerald-500',
              verdictColor === 'red' && 'bg-red-500',
              verdictColor === 'blue' && 'bg-blue-500'
            )}
          />
          {verdict === 'DI BAWAH_WAJAR' && `${formatIDR(fairPrice - userPrice)} lebih murah dari estimasi`}
          {verdict === 'LEBIH_MAHAL' && `${formatIDR(userPrice - fairPrice)} lebih mahal dari estimasi`}
          {verdict === 'WAJAR' && 'Harga dalam range wajar'}
        </span>
      </div>
    </figure>
  )
}
