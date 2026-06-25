'use client'

// ==============================================================================
// cekwajar.id — PPP Basket Comparison (Spec 10)
// Purchasing power comparison with PPP indicator bars
// ==============================================================================

import { useEffect, useState, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'

// --- Types --------------------------------------------------------------------

interface PPPBasketComparisonProps {
  countryName: string
  currencyCode: string
  exchangeRate: number
  idSalary: number
  nominalEquivalent: number
  userPowerIntlUSD: number
  offerSalary: number | null
  offerPowerIntlUSD: number | null
  realRatio: number | null
  isPPPBetter: boolean | null
  pppYear: number
  className?: string
}

// --- Formatters ---------------------------------------------------------------

function formatIDR(amount: number): string {
  return `Rp ${amount.toLocaleString('id-ID')}`
}

function formatUSD(amount: number): string {
  return `$${amount.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}

function formatPct(amount: number): string {
  return `${(amount * 100).toFixed(0)}%`
}

// --- Static basket proxy items (derived from PPP factors) --------------------
// We use representative goods to show PPP effect visually

interface BasketRow {
  label: string
  icon: string
  priceIndo: number
  priceForeign: number
  pppRatio: number
}

function buildBasketRows(
  idSalary: number,
  nominalEquivalent: number,
  exchangeRate: number,
  idPPPFactor: number,
  foreignPPPFactor: number,
  currencyCode: string
): BasketRow[] {
  // Representative basket items (illustrative)
  // Each shows the PPP-adjusted price comparison
  const rawItems: Array<{
    label: string
    icon: string
    baseIndoPrice: number
  }> = [
    { label: 'Nasi + Lauk', icon: '🍚', baseIndoPrice: 45000 },
    { label: 'Kopi', icon: '☕', baseIndoPrice: 15000 },
    { label: 'Transport Harian', icon: '🚌', baseIndoPrice: 22000 },
    { label: 'Listrik + Utilitas', icon: '💡', baseIndoPrice: 180000 },
    { label: 'Sewa 1 kamar', icon: '🏠', baseIndoPrice: 2500000 },
    { label: 'Internet Bulanan', icon: '📶', baseIndoPrice: 280000 },
  ]

  const netRatio = foreignPPPFactor / idPPPFactor

  return rawItems.map((item) => {
    // PPP-adjusted foreign price
    const priceForeign = Math.round(item.baseIndoPrice * netRatio)
    // How many of these can you buy in each country with same wage
    const unitsIndo = Math.round(idSalary / item.baseIndoPrice)
    const unitsForeign = Math.round(nominalEquivalent / priceForeign)

    return {
      label: item.label,
      icon: item.icon,
      priceIndo: item.baseIndoPrice,
      priceForeign,
      pppRatio: unitsForeign / (unitsIndo || 1),
    }
  })
}

// --- Main Component -----------------------------------------------------------

export function PPPBasketComparison({
  countryName,
  currencyCode,
  exchangeRate,
  idSalary,
  nominalEquivalent,
  userPowerIntlUSD,
  offerSalary,
  offerPowerIntlUSD,
  realRatio,
  isPPPBetter,
  pppYear,
  className,
}: PPPBasketComparisonProps) {
  const [animate, setAnimate] = useState(false)
  const prefersReducedMotion = useRef(false)

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    prefersReducedMotion.current = mq.matches
    if (!mq.matches) {
      const t = setTimeout(() => setAnimate(true), 300)
      return () => clearTimeout(t)
    } else {
      setAnimate(true)
    }
  }, [])

  // Derive PPP ratio from nominal vs PPP
  const pppRatio = exchangeRate > 0 && nominalEquivalent > 0
    ? idSalary / nominalEquivalent
    : 1

  const isPPPLower = pppRatio < 1

  const basketRows = buildBasketRows(
    idSalary,
    nominalEquivalent,
    exchangeRate,
    1.0,    // idPPPFactor
    pppRatio, // foreignPPPFactor
    currencyCode
  )

  return (
    <figure
      role="img"
      aria-label={`Perbandingan purchasing power antara Indonesia dan ${countryName}. Gaji ${formatIDR(idSalary)} di Indonesia setara dengan ${formatIDR(nominalEquivalent)} di ${countryName} berdasarkan PPP ${pppYear}`}
      className={className}
    >
      <figcaption className="sr-only">
        Perbandingan purchasing power antara Indonesia dan {countryName}.
        Gaji Indonesia {formatIDR(idSalary)} per bulan setara dengan {formatIDR(nominalEquivalent)} di {countryName}
        berdasarkan PPP factor {pppYear}.
        Daya beli internasional: {formatUSD(userPowerIntlUSD)} USD PPP.
        {offerSalary != null && ` Penawaran {formatCurrency(offerSalary, currencyCode)} di {countryName} = {formatUSD(offerPowerIntlUSD ?? 0)} USD PPP.`}
        {realRatio != null && `Ratio riil: {formatPct(realRatio)}.`}
        {isPPPBetter ? `Kerja di {countryName} memberikan daya beli lebih tinggi.` : `Indonesia memberikan purchasing power lebih tinggi untuk kebutuhan lokal.`}
      </figcaption>

      <Card>
        <CardContent className="p-4">
          {/* PPP Headline */}
          <div
            className="mb-4 p-4 rounded-xl text-center"
            style={{
              background: isPPPLower
                ? 'linear-gradient(135deg, #d1fae5, #ecfdf5)'
                : 'linear-gradient(135deg, #fee2e2, #fef2f2)',
              opacity: animate ? 1 : 0,
              transition: 'opacity 0.5s ease',
            }}
          >
            <div className="text-xs text-muted-foreground mb-1">Indonesia vs {countryName}</div>
            <div
              className="text-3xl font-bold mb-1"
              style={{ color: isPPPLower ? '#065f46' : '#991b1b' }}
            >
              {pppRatio.toFixed(2)}x
            </div>
            <p className="text-sm font-medium" style={{ color: isPPPLower ? '#065f46' : '#991b1b' }}>
              {isPPPLower
                ? `IDR lebih kuat — ${formatIDR(idSalary)} ≈ ${formatIDR(Math.round(idSalary / pppRatio))}当地货币`
                : `${countryName} memiliki daya beli lebih tinggi`}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              PPP {pppYear} · 1 USD PPP
            </p>
          </div>

          {/* Two-column key stats */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-xs text-blue-600 mb-1">Gaji di IDR</div>
              <div className="font-bold text-blue-700">{formatIDR(idSalary)}</div>
            </div>
            <div className="text-center p-3 bg-emerald-50 rounded-lg">
              <div className="text-xs text-emerald-600 mb-1">Ekuivalen {countryName}</div>
              <div className="font-bold text-emerald-700">
                {currencyCode} {Math.round(nominalEquivalent / exchangeRate).toLocaleString()}
              </div>
            </div>
          </div>

          {/* PPP basket comparison bars */}
          <div className="space-y-3">
            {basketRows.map((row, i) => {
              const maxPrice = Math.max(row.priceIndo, row.priceForeign)
              const indoPct = maxPrice > 0 ? (row.priceIndo / maxPrice) * 100 : 50
              const foreignPct = maxPrice > 0 ? (row.priceForeign / maxPrice) * 100 : 50
              const isIndoMore = row.priceIndo > row.priceForeign

              return (
                <div
                  key={row.label}
                  className="space-y-1"
                  style={{
                    opacity: animate ? 1 : 0,
                    transition: `opacity 0.4s ease ${0.3 + i * 0.08}s`,
                  }}
                >
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-foreground">
                      {row.icon} {row.label}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {isIndoMore ? '🇮🇩' : `🇺🇳`}
                    </span>
                  </div>
                  <div className="flex gap-1 items-center h-5">
                    <div className="w-10 text-xs text-right text-blue-600 shrink-0 font-medium">
                      {formatIDR(row.priceIndo)}
                    </div>
                    <div className="flex-1 h-3 rounded-full overflow-hidden flex" aria-hidden="true">
                      <div
                        className={cn(
                          'h-full rounded-l-full',
                          isIndoMore ? 'bg-blue-400' : 'bg-emerald-400'
                        )}
                        style={{
                          width: `${indoPct}%`,
                          transition: prefersReducedMotion.current ? 'none' : `width 0.7s ease ${0.5 + i * 0.08}s`,
                        }}
                      />
                      <div
                        className={cn(
                          'h-full rounded-r-full',
                          isIndoMore ? 'bg-red-200' : 'bg-amber-300'
                        )}
                        style={{
                          width: `${foreignPct}%`,
                          transition: prefersReducedMotion.current ? 'none' : `width 0.7s ease ${0.5 + i * 0.08}s`,
                        }}
                      />
                    </div>
                    <div className="w-10 text-xs text-left text-emerald-600 shrink-0 font-medium">
                      {Math.round(row.priceForeign).toLocaleString()}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Legend */}
          <div className="flex justify-center gap-5 mt-4 pt-3 border-t border-border">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <div className="w-3 h-3 rounded-full bg-blue-400" />
              <span>🇮🇩 Indonesia</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <div className="w-3 h-3 rounded-full bg-amber-400" />
              <span>🌍 {countryName}</span>
            </div>
          </div>

          {/* Purchasing power note */}
          <p className="text-xs text-center text-muted-foreground mt-3">
            Perbandingan berdasarkan PPP {pppYear} dan kurs {formatIDR(exchangeRate)}/USD.
            Prices shown in local currency equivalents.
          </p>
        </CardContent>
      </Card>
    </figure>
  )
}
