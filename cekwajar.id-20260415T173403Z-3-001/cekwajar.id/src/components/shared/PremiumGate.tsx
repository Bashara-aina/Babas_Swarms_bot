'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — PremiumGate
// Partial-reveal paywall: blurred masked amounts + personalized upgrade CTA
// ══════════════════════════════════════════════════════════════════════════════

import { Lock, ArrowRight, TrendingUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { SubscriptionTier } from '@/types'
import { COPY, UPGRADE_COPY } from '@/lib/copy'

interface PremiumGateProps {
  children: React.ReactNode
  userTier: SubscriptionTier
  requiredTier: 'basic' | 'pro'
  /** Short label shown on the lock badge, e.g. "Detail IDR" */
  featureLabel: string
  /** Benefit shown below label, e.g. "Cek berapa yang kurang dibayar" */
  benefit: string
  /** Optional: preview lines to render as masked (Rp ██.███) inside the blur zone */
  maskedLines?: string[]
}

const TIER_RANK: Record<SubscriptionTier, number> = {
  free: 0,
  basic: 1,
  pro: 2,
}

export function PremiumGate({
  children,
  userTier,
  requiredTier,
  featureLabel,
  benefit,
  maskedLines,
}: PremiumGateProps) {
  const hasAccess = TIER_RANK[userTier] >= TIER_RANK[requiredTier]

  if (hasAccess) {
    return <>{children}</>
  }

  return (
    <div className="relative rounded-xl border border-amber-200 bg-amber-50/50 overflow-hidden">
      {/* Partial blur zone — shows blurred table/rows, masked amounts */}
      <div className="filter blur-[3px] pointer-events-none select-none opacity-60 p-4">
        {maskedLines ? (
          <div className="space-y-2">
            {maskedLines.map((line, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="h-4 flex-1 rounded bg-amber-200" style={{ width: `${60 + (i * 17) % 30}%` }} />
                <span className="font-mono text-amber-700">Rp ██.███</span>
              </div>
            ))}
          </div>
        ) : (
          children
        )}
      </div>

      {/* Gate overlay — centered, does NOT cover full height */}
      <div className="absolute inset-x-0 bottom-0 flex items-end justify-center pb-4 px-4">
        <div className="flex flex-col items-center gap-2 rounded-xl border border-amber-200 bg-white/95 p-4 text-center shadow-sm backdrop-blur-sm">
          <div className="rounded-full bg-amber-100 p-2">
            <Lock className="h-4 w-4 text-amber-600" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">{featureLabel}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">{benefit}</p>
          </div>
          <Button
            size="sm"
            className="mt-1 bg-emerald-600 hover:bg-emerald-700 gap-1.5"
            onClick={() => (window.location.href = '/upgrade')}
          >
            {COPY.ui.upgradeBtn}
            <ArrowRight className="h-3 w-3" />
          </Button>
          <p className="text-xs text-muted-foreground">{UPGRADE_COPY.cancelAnytime}</p>
        </div>
      </div>
    </div>
  )
}
