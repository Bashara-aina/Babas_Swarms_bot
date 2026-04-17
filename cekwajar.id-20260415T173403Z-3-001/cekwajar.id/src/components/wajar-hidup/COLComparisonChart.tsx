// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — COLComparisonChart
// Side-by-side bar chart comparing cost-of-living categories between cities
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { Card, CardContent } from '@/components/ui/card'
import { TrendingDown, TrendingUp } from 'lucide-react'

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

function formatIDR(amount: number): string {
  if (amount >= 1_000_000) {
    return `Rp ${(amount / 1_000_000).toFixed(1)}jt`
  }
  return `Rp ${amount.toLocaleString('id-ID')}`
}

const CATEGORY_LABELS: Record<string, string> = {
  MAKANAN: 'Makanan',
  TRANSPORTASI: 'Transportasi',
  PERUMAHAN: 'Perumahan',
  KESEHATAN: 'Kesehatan',
  PENDIDIKAN: 'Pendidikan',
  REKREASI: 'Rekreasi',
  SANDANG: 'Sandang',
  DLL: 'Lainnya',
}

export function COLComparisonChart({ categories, fromCity, toCity, className }: COLComparisonChartProps) {
  if (!categories || categories.length === 0) return null

  const maxValue = Math.max(...categories.map((c) => Math.max(c.fromAmount, c.toAmount)))

  return (
    <Card className={className}>
      <CardContent className="p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-foreground">Breakdown per Kategori</h3>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-3 rounded bg-blue-400" />
              {fromCity}
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-3 rounded bg-emerald-400" />
              {toCity}
            </span>
          </div>
        </div>

        <div className="space-y-3">
          {categories.map((cat) => {
            const fromPct = maxValue > 0 ? (cat.fromAmount / maxValue) * 100 : 0
            const toPct = maxValue > 0 ? (cat.toAmount / maxValue) * 100 : 0
            const isHigherInTarget = cat.difference > 0

            return (
              <div key={cat.category}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-foreground">
                    {CATEGORY_LABELS[cat.category] ?? cat.category}
                  </span>
                  <div className="flex items-center gap-1">
                    {isHigherInTarget ? (
                      <TrendingUp className="h-3 w-3 text-rose-500" />
                    ) : (
                      <TrendingDown className="h-3 w-3 text-emerald-500" />
                    )}
                    <span className={`text-xs font-medium ${isHigherInTarget ? 'text-rose-600' : 'text-emerald-600'}`}>
                      {isHigherInTarget ? '+' : ''}{formatIDR(Math.abs(cat.difference))}
                    </span>
                  </div>
                </div>

                {/* Bar chart */}
                <div className="relative h-6 rounded-sm bg-muted overflow-hidden">
                  {/* From city bar (blue) */}
                  <div
                    className="absolute left-0 top-0 h-full rounded-sm bg-blue-400 transition-all"
                    style={{ width: `${fromPct}%` }}
                    title={`${fromCity}: ${formatIDR(cat.fromAmount)}`}
                  />
                  {/* To city bar (emerald) — overlaid to the right */}
                  <div
                    className="absolute left-0 top-0 h-full rounded-sm bg-emerald-400/80 transition-all"
                    style={{ width: `${toPct}%`, left: 0 }}
                    title={`${toCity}: ${formatIDR(cat.toAmount)}`}
                  />
                </div>

                <div className="flex justify-between mt-0.5">
                  <span className="text-[10px] text-muted-foreground">{formatIDR(cat.fromAmount)}</span>
                  <span className="text-[10px] text-muted-foreground">{formatIDR(cat.toAmount)}</span>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
