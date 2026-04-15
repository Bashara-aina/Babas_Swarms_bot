'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — PremiumGate
// Blurs content and shows upgrade CTA when user tier is insufficient
// ══════════════════════════════════════════════════════════════════════════════

import { Lock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { SubscriptionTier } from '@/types'

interface PremiumGateProps {
  children: React.ReactNode
  userTier: SubscriptionTier
  requiredTier: 'basic' | 'pro'
  featureLabel: string
}

const TIER_RANK: Record<SubscriptionTier, number> = {
  free: 0,
  basic: 1,
  pro: 2,
}

export function PremiumGate({ children, userTier, requiredTier, featureLabel }: PremiumGateProps) {
  const hasAccess = TIER_RANK[userTier] >= TIER_RANK[requiredTier]

  if (hasAccess) {
    return <>{children}</>
  }

  return (
    <div className="relative">
      {/* Blurred content */}
      <div className="filter blur-sm pointer-events-none select-none opacity-50">
        {children}
      </div>

      {/* Gate overlay */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3 rounded-xl border bg-white p-6 text-center shadow-lg">
          <div className="rounded-full bg-amber-100 p-3">
            <Lock className="h-5 w-5 text-amber-600" />
          </div>
          <div>
            <p className="font-semibold text-slate-800">Fitur Premium</p>
            <p className="mt-1 text-sm text-slate-500">{featureLabel}</p>
            <p className="mt-1 text-xs text-slate-400">
              Upgrade ke Basic atau Pro untuk akses penuh.
            </p>
          </div>
          <Button
            size="sm"
            className="bg-emerald-600 hover:bg-emerald-700"
            onClick={() => window.location.href = '/upgrade'}
          >
            Upgrade Sekarang
          </Button>
        </div>
      </div>
    </div>
  )
}
