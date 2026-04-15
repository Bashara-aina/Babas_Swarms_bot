// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Subscription Badge
// Small colored badge showing user subscription tier
// ══════════════════════════════════════════════════════════════════════════════

import type { SubscriptionTier } from '@/types'

interface SubscriptionBadgeProps {
  tier: SubscriptionTier
  showLabel?: boolean
}

const TIER_CONFIG: Record<SubscriptionTier, { label: string; className: string }> = {
  free: {
    label: 'Gratis',
    className: 'bg-slate-100 text-slate-600',
  },
  basic: {
    label: 'Basic',
    className: 'bg-blue-100 text-blue-700',
  },
  pro: {
    label: 'Pro',
    className: 'bg-purple-100 text-purple-700',
  },
}

export function SubscriptionBadge({ tier, showLabel = true }: SubscriptionBadgeProps) {
  const config = TIER_CONFIG[tier]

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${config.className}`}
    >
      {showLabel ? config.label : null}
    </span>
  )
}
