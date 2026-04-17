// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — StatsGrid
// Bento-grid KPI card layout with NumberTicker animation and trend badges
// ══════════════════════════════════════════════════════════════════════════════

import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { NumberTicker } from '@/components/ui/number-ticker'
import { cn } from '@/lib/utils'

export interface StatItem {
  /** Primary label */
  title: string
  /** Animated number value */
  value: number
  /** Trend: percentage change from last period */
  trend: number // e.g. 12.5 for 12.5%
  /** Trend direction label */
  trendLabel?: string
  /** Prefix (e.g. 'Rp ') */
  prefix?: string
  /** Suffix (e.g. 'jt', '%') */
  suffix?: string
  /** Color theme for the card accent */
  accent?: 'emerald' | 'amber' | 'violet' | 'slate'
  /** Decimal places for the value */
  decimals?: number
}

interface StatsGridProps {
  stats: StatItem[]
  /** Gap between cards. Default: 'gap-4' */
  gap?: string
  className?: string
}

const accentStyles = {
  emerald: 'border-l-4 border-l-emerald-500',
  amber: 'border-l-4 border-l-amber-500',
  violet: 'border-l-4 border-l-violet-500',
  slate: 'border-l-4 border-l-slate-400',
}

function TrendBadge({ trend }: { trend: number }) {
  if (trend === 0) {
    return (
      <Badge variant="secondary" className="gap-1 text-xs">
        <Minus className="h-3 w-3" />
        0%
      </Badge>
    )
  }

  const isPositive = trend > 0
  return (
    <Badge
      variant={isPositive ? 'success' : 'destructive'}
      className="gap-1 text-xs"
    >
      {isPositive ? (
        <TrendingUp className="h-3 w-3" />
      ) : (
        <TrendingDown className="h-3 w-3" />
      )}
      {isPositive ? '+' : ''}
      {trend.toFixed(1)}%
    </Badge>
  )
}

function StatCard({ stat, index }: { stat: StatItem; index: number }) {
  return (
    <Card
      className={cn(
        'relative overflow-hidden transition-all duration-200',
        'hover:shadow-md hover:-translate-y-px',
        stat.accent ? accentStyles[stat.accent] : '',
        'animate-fade-in-up'
      )}
      style={{ animationDelay: `${index * 80}ms`, animationFillMode: 'both' } as React.CSSProperties}
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {stat.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-between">
          <div>
            <NumberTicker
              value={stat.value}
              prefix={stat.prefix}
              suffix={stat.suffix}
              decimals={stat.decimals ?? 0}
              className="text-3xl font-bold tracking-tight text-foreground"
            />
            {stat.trendLabel && (
              <p className="mt-1 text-xs text-muted-foreground">{stat.trendLabel}</p>
            )}
          </div>
          <TrendBadge trend={stat.trend} />
        </div>
      </CardContent>
    </Card>
  )
}

export function StatsGrid({ stats, gap = 'gap-4', className }: StatsGridProps) {
  return (
    <div className={cn('grid', gap, 'md:grid-cols-2 xl:grid-cols-4', className)}>
      {stats.map((stat, index) => (
        <StatCard key={stat.title} stat={stat} index={index} />
      ))}
    </div>
  )
}
