'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Bento Card Component
// Animated card for bento grid layout with hover effects
// ══════════════════════════════════════════════════════════════════════════════

import { motion, useReducedMotion } from 'framer-motion'
import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface BentoCardProps {
  title: string
  description: string
  icon: ReactNode
  iconBgClass?: string
  borderClass?: string
  featured?: boolean
  className?: string
  span?: string
}

export function BentoCard({
  title,
  description,
  icon,
  iconBgClass = 'bg-emerald-100',
  borderClass = 'hover:border-emerald-300',
  featured = false,
  className = '',
}: BentoCardProps) {
  const prefersReducedMotion = useReducedMotion()

  if (prefersReducedMotion) {
    return (
      <div
        className={cn(
          'relative flex flex-col rounded-2xl border border-border bg-background p-6 shadow-sm transition-all',
          borderClass,
          featured && 'ring-2 ring-emerald-400/50',
          className
        )}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={cn('rounded-xl p-3', iconBgClass)}>
              <div className="text-emerald-600">{icon}</div>
            </div>
            <div>
              <h3 className="font-semibold text-foreground dark:text-muted">
                {title}
              </h3>
            </div>
          </div>
        </div>
        <p className="mt-4 text-sm text-muted-foreground dark:text-muted">{description}</p>
        {featured && (
          <div className="mt-auto pt-4">
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">
              Populer
            </span>
          </div>
        )}
      </div>
    )
  }

  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        'relative flex h-full min-h-[140px] flex-col rounded-2xl border border-border bg-background p-6 shadow-sm transition-all duration-300',
        borderClass,
        featured && 'ring-2 ring-emerald-400/50',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={cn('rounded-xl p-3', iconBgClass)}>
            <div className="text-emerald-600">{icon}</div>
          </div>
          <div>
            <h3 className="font-semibold text-foreground dark:text-muted">
              {title}
            </h3>
          </div>
        </div>
      </div>

      <p className="mt-4 flex-1 text-sm text-muted-foreground dark:text-muted">{description}</p>

      {featured && (
        <div className="mt-auto pt-4">
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">
            Populer
          </span>
        </div>
      )}
    </motion.div>
  )
}
