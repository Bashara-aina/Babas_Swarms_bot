// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — PageHeader
// Consistent page header: icon + title + description + optional CTA slot
// ══════════════════════════════════════════════════════════════════════════════

import { type ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface PageHeaderProps {
  /** Lucide icon component rendered in a styled badge */
  icon?: ReactNode
  /** Page title (h1) */
  title: string
  /** Optional subtitle / description */
  description?: string
  /** Right-side CTA slot (e.g. a Button or Badge) */
  action?: ReactNode
  className?: string
}

export function PageHeader({
  icon,
  title,
  description,
  action,
  className,
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        'flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between',
        'animate-fade-in-up',
        className
      )}
    >
      <div className="flex items-start gap-3">
        {/* Icon badge */}
        {icon && (
          <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-sm shadow-emerald-500/20">
            {icon}
          </div>
        )}
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {title}
          </h1>
          {description && (
            <p className="text-sm text-muted-foreground sm:text-base">{description}</p>
          )}
        </div>
      </div>

      {/* Action slot */}
      {action && <div className="shrink-0">{action}</div>}
    </div>
  )
}
