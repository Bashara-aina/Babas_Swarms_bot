'use client'

// ==============================================================================
// cekwajar.id — COL Comparison Chart (Spec 10)
// Recharts grouped bar chart with summary headline
// ==============================================================================

import { useEffect, useState, useRef } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, Cell
} from 'recharts'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

// --- Types --------------------------------------------------------------------

interface CategoryBreakdown {
  category: string
  fromAmount: number
  toAmount: number
  difference: number
}

interface COLComparisonChartProps {
  categories: CategoryBreakdown[]
  fromCity: string
  toCity: string
  className?: string
}

// --- Formatters ---------------------------------------------------------------

function formatIDR(amount: number): string {
  return `Rp ${amount.toLocaleString('id-ID')}`
}

// --- Custom Tooltip -----------------------------------------------------------

function CustomTooltip({ active, payload, label }: {
  active?: boolean
  payload?: Array<{ value: number; name: string; color: string }>
  label?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-border rounded-lg shadow-lg p-3 text-sm">
      <p className="font-semibold text-foreground mb-2">{label}</p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex justify-between gap-4 text-xs">
          <span style={{ color: entry.color }}>{entry.name}</span>
          <span className="font-medium">{formatIDR(entry.value)}</span>
        </div>
      ))}
    </div>
  )
}

// --- Category label mapping ---------------------------------------------------

const CATEGORY_LABELS: Record<string, string> = {
  SEWA: 'Sewa',
  MAKANAN: 'Makanan',
  TRANSPORT: 'Transport',
  UTILITAS: 'Utilitas',
  KESEHATAN: 'Kesehatan',
  PENDIDIKAN: 'Pendidikan',
  HIBURAN: 'Hiburan',
  PAKAIAN: 'Pakaian',
  LAINNYA: 'Lainnya',
}

// --- Main Component -----------------------------------------------------------

export function COLComparisonChart({
  categories,
  fromCity,
  toCity,
  className,
}: COLComparisonChartProps) {
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

  // Compute summary
  const totalFrom = categories.reduce((s, c) => s + c.fromAmount, 0)
  const totalTo = categories.reduce((s, c) => s + c.toAmount, 0)
  const totalDiff = totalTo - totalFrom
  const absTotalDiff = Math.abs(totalDiff)
  const diffPct = totalFrom > 0 ? Math.round((absTotalDiff / totalFrom) * 100) : 0
  const isMoreExpensive = totalDiff > 0

  const chartData = categories.map((c) => ({
    name: CATEGORY_LABELS[c.category] ?? c.category,
    [fromCity]: c.fromAmount,
    [toCity]: c.toAmount,
    diff: c.difference,
  }))

  return (
    <figure
      role="img"
      aria-label={`Perbandingan biaya hidup antara ${fromCity} dan ${toCity}. Total di ${fromCity} ${formatIDR(totalFrom)}, Total di ${toCity} ${formatIDR(totalTo)}`}
      className={className}
    >
      <figcaption className="sr-only">
        Grafik batang perbandingan biaya hidup bulanan antara {fromCity} dan {toCity}.
        {categories.map((c) => `${CATEGORY_LABELS[c.category] ?? c.category}: ${fromCity} ${formatIDR(c.fromAmount)}, ${toCity} ${formatIDR(c.toAmount)}.`).join(' ')}
        Total bulanan: {fromCity} {formatIDR(totalFrom)}, {toCity} {formatIDR(totalTo)}.
        {isMoreExpensive
          ? `${toCity} lebih mahal ${diffPct}% atau ${formatIDR(absTotalDiff)}/bulan.`
          : `${toCity} lebih murah ${diffPct}% atau ${formatIDR(absTotalDiff)}/bulan.`}
      </figcaption>

      <Card>
        <CardContent className="p-4">
          {/* Summary headline */}
          <div
            className="mb-4 text-center"
            style={{
              opacity: animate ? 1 : 0,
              transition: 'opacity 0.5s ease',
            }}
          >
            <p className="text-sm text-muted-foreground">
              {fromCity}
            </p>
            <p className="text-2xl font-bold text-foreground">
              {formatIDR(totalFrom)}
            </p>
            <div
              className={cn(
                'inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-semibold mt-2',
                isMoreExpensive
                  ? 'bg-red-50 text-red-700 border border-red-200'
                  : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              )}
            >
              <span>
                {isMoreExpensive ? '↑' : '↓'} {diffPct}% ({isMoreExpensive ? '+' : '-'}{formatIDR(absTotalDiff)})
              </span>
              <span className="text-xs text-muted-foreground font-normal">
                vs {toCity}
              </span>
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              {toCity}: <span className="font-semibold text-foreground">{formatIDR(totalTo)}</span>
            </p>
          </div>

          {/* Chart */}
          <div
            style={{
              opacity: animate ? 1 : 0,
              transform: animate ? 'translateY(0)' : 'translateY(12px)',
              transition: 'opacity 0.6s ease 0.3s, transform 0.6s ease 0.3s',
            }}
          >
            <ResponsiveContainer width="100%" height={220}>
              <BarChart
                data={chartData}
                margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
                barCategoryGap="20%"
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: '#6b7280' }}
                  tickFormatter={(v) => `Rp${(v / 1000000).toFixed(1)}jt`}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  wrapperStyle={{ fontSize: '12px' }}
                  formatter={(value) => (
                    <span className="text-xs text-muted-foreground">{value}</span>
                  )}
                />
                <Bar
                  dataKey={fromCity}
                  fill="#3B82F6"
                  radius={[4, 4, 0, 0]}
                  isAnimationActive={!prefersReducedMotion.current}
                  animationDuration={800}
                  animationBegin={200}
                />
                <Bar
                  dataKey={toCity}
                  fill={isMoreExpensive ? '#EF4444' : '#10B981'}
                  radius={[4, 4, 0, 0]}
                  isAnimationActive={!prefersReducedMotion.current}
                  animationDuration={800}
                  animationBegin={400}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Per-category diff pills */}
          <div className="mt-3 space-y-1">
            {chartData.map((d) => (
              <div key={d.name} className="flex justify-between items-center text-xs px-1">
                <span className="text-muted-foreground">{d.name}</span>
                <span
                  className={cn(
                    'font-medium',
                    d.diff > 0 ? 'text-red-600' : d.diff < 0 ? 'text-emerald-600' : 'text-muted-foreground'
                  )}
                >
                  {d.diff > 0 ? '+' : ''}{formatIDR(d.diff)}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </figure>
  )
}
