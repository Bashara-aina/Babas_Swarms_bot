// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — FormProgress Component
// 3-step wizard progress indicator
// Shows: Upload → Konfirmasi → Hasil
// ══════════════════════════════════════════════════════════════════════════════

import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Step {
  label: string
  description?: string
}

interface FormProgressProps {
  steps: Step[]
  currentStep: number // 0-based
  className?: string
}

export function FormProgress({ steps, currentStep, className }: FormProgressProps) {
  return (
    <div className={cn('w-full', className)}>
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep
          const isCurrent = index === currentStep
          const isPending = index > currentStep

          return (
            <div key={step.label} className="flex flex-1 items-center last:flex-none">
              {/* Step indicator */}
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'flex h-8 w-8 items-center justify-center rounded-full border-2 text-sm font-semibold transition-colors',
                    isCompleted && 'border-emerald-500 bg-emerald-500 text-white',
                    isCurrent && 'border-emerald-500 bg-white text-emerald-600',
                    isPending && 'border-border bg-white text-muted-foreground'
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <span>{index + 1}</span>
                  )}
                </div>
                <div className="mt-1.5 text-center">
                  <div
                    className={cn(
                      'text-xs font-medium',
                      isCurrent && 'text-emerald-600',
                      isCompleted && 'text-emerald-600',
                      isPending && 'text-muted-foreground'
                    )}
                  >
                    {step.label}
                  </div>
                  {step.description && (
                    <div className="text-xs text-muted-foreground mt-0.5 hidden sm:block">
                      {step.description}
                    </div>
                  )}
                </div>
              </div>

              {/* Connector line */}
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    'flex-1 mx-2 h-0.5 mb-6 transition-colors',
                    index < currentStep ? 'bg-emerald-500' : 'bg-muted'
                  )}
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
