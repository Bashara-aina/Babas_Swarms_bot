// ==============================================================================
// cekwajar.id — VerdictBadge component
// Large colored badge for property verdict
// ==============================================================================

import { PropertyVerdict } from '@/app/api/property/benchmark/route'

interface VerdictBadgeProps {
  verdict: PropertyVerdict
}

const VERDICT_CONFIG = {
  MURAH: {
    label: 'MURAH',
    bgColor: 'bg-emerald-100',
    textColor: 'text-emerald-700',
    icon: '↓',
    description: 'Harga di bawah rata-rata pasar',
  },
  WAJAR: {
    label: 'WAJAR',
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-700',
    icon: '✓',
    description: 'Harga sesuai pasaran',
  },
  MAHAL: {
    label: 'MAHAL',
    bgColor: 'bg-amber-100',
    textColor: 'text-amber-700',
    icon: '↑',
    description: 'Harga di atas median pasar',
  },
  SANGAT_MAHAL: {
    label: 'SANGAT MAHAL',
    bgColor: 'bg-red-100',
    textColor: 'text-red-700',
    icon: '⚠️',
    description: 'Harga jauh di atas pasar',
  },
} as const

export function VerdictBadge({ verdict }: VerdictBadgeProps) {
  const config = VERDICT_CONFIG[verdict]

  return (
    <div className={`${config.bgColor} ${config.textColor} rounded-2xl p-6 text-center`}>
      <div className="text-4xl mb-2">{config.icon}</div>
      <div className="text-2xl font-bold">{config.label}</div>
      <div className="text-sm mt-1 opacity-80">{config.description}</div>
    </div>
  )
}

export type { PropertyVerdict }