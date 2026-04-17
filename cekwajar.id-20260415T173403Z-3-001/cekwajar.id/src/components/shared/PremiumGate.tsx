'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — PremiumGate
// Partial-reveal paywall: blurred masked amounts + personalized upgrade CTA
// Supports compact inline mode and full partial-reveal mode
// ══════════════════════════════════════════════════════════════════════════════

import { Lock, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { SubscriptionTier } from '@/types'
import { COPY, UPGRADE_COPY } from '@/lib/copy'
import Link from 'next/link'
import { cn } from '@/lib/utils'

interface PremiumGateProps {
  children?: React.ReactNode
  userTier: SubscriptionTier
  requiredTier: 'basic' | 'pro'
  /** Short label shown on the lock badge, e.g. "Detail IDR" */
  featureLabel: string
  /** Benefit shown below label, e.g. "Cek berapa yang kurang dibayar" */
  benefit?: string
  /** Optional: preview lines to render as masked (Rp ██.███) inside the blur zone */
  maskedLines?: string[]
  /** Compact mode for inline gating (single line) */
  compact?: boolean
  /** Custom class */
  className?: string
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
  compact = false,
  className,
}: PremiumGateProps) {
  const hasAccess = TIER_RANK[userTier] >= TIER_RANK[requiredTier]

  if (hasAccess) {
    return <>{children}</>
  }

  // Compact inline mode — single line with lock + masked amount + upgrade link
  if (compact) {
    return (
      <div className={cn('flex items-center gap-2 text-xs text-muted-foreground py-2', className)}>
        <Lock className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
        <span className="blur-sm select-none pointer-events-none">Rp ██.███.███</span>
        <Link
          href="/upgrade"
          className="text-emerald-600 dark:text-emerald-400 font-semibold hover:underline flex-shrink-0"
        >
          Upgrade →
        </Link>
      </div>
    )
  }

  return (
    <div className={cn('relative rounded-xl overflow-hidden border-2 border-emerald-200 dark:border-emerald-800', className)}>
      {/* Partial preview — visible but blurred */}
      {(children || maskedLines) && (
        <div className="blur-sm select-none pointer-events-none opacity-60 p-4" aria-hidden="true">
          {maskedLines ? (
            <div className="space-y-2">
              {maskedLines.map((line, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="h-4 flex-1 rounded bg-amber-200" style={{ width: `${60 + (i * 17) % 30}%` }} />
                  <span className="font-mono text-amber-700">Rp ██.███</span>
                </div>
              ))}
            </div>
          ) : children}
        </div>
      )}

      {/* Overlay */}
      <div
        className={cn(
          'rounded-xl border-2 border-emerald-200 dark:border-emerald-800',
          'bg-gradient-to-b from-white/95 to-emerald-50/95 dark:from-slate-900/95 dark:to-emerald-950/95',
          'p-6 text-center',
          (children || maskedLines) ? 'absolute inset-0 flex flex-col items-center justify-center' : ''
        )}
      >
        {/* Lock icon */}
        <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900 rounded-full flex items-center justify-center mx-auto mb-3">
          <Lock className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
        </div>

        {/* Personalized message */}
        <h3 className="font-bold text-foreground text-base mb-1">
          {featureLabel}
        </h3>
        {benefit && (
          <p className="text-sm text-muted-foreground mb-4 max-w-xs mx-auto">
            {benefit}
          </p>
        )}

        {/* Price + CTA */}
        <Button asChild className="bg-emerald-600 hover:bg-emerald-700 text-white w-full max-w-xs gap-2">
          <Link href="/upgrade">
            {COPY.ui.upgradeBtn} — {UPGRADE_COPY.priceLabel}
          </Link>
        </Button>

        {/* Value framing */}
        <p className="text-xs text-muted-foreground mt-2">
          {UPGRADE_COPY.valueFrame}. {UPGRADE_COPY.cancelAnytime}.
        </p>
      </div>
    </div>
  )
}
