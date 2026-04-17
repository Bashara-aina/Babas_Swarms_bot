'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Bento Grid Container
// Responsive CSS grid for bento layout
// ══════════════════════════════════════════════════════════════════════════════

import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface BentoGridProps {
  children: ReactNode
  className?: string
}

export function BentoGrid({ children, className }: BentoGridProps) {
  return (
    <div
      className={cn(
        'grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4',
        // Auto rows for varying heights
        'auto-rows-min',
        className
      )}
    >
      {children}
    </div>
  )
}
