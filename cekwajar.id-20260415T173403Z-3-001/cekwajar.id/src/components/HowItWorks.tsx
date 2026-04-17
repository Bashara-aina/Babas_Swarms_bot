// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — HowItWorks Component
// 3-step onboarding section for all tool pages
// ══════════════════════════════════════════════════════════════════════════════

import { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Step {
  icon: LucideIcon
  title: string
  description: string
}

interface HowItWorksProps {
  steps: Step[]
  className?: string
}

export function HowItWorks({ steps, className }: HowItWorksProps) {
  return (
    <div className={cn('mb-8', className)}>
      <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider text-center mb-5">
        Cara kerjanya
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {steps.map((step, index) => {
          const Icon = step.icon
          return (
            <div
              key={index}
              className="flex sm:flex-col items-start sm:items-center gap-3 sm:gap-2 sm:text-center"
            >
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center">
                <Icon className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <p className="font-semibold text-sm text-foreground">{step.title}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{step.description}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
