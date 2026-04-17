// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Skeleton Component (shadcn/ui style)
// Enhanced: Civora-style shimmer animation, multiple shape presets
// ══════════════════════════════════════════════════════════════════════════════

import * as React from 'react'
import { cn } from '@/lib/utils'

/*
 * Shimmer skeleton — Civora-style with gradient sweep
 * The shimmer gradient is defined in src/lib/animations.css as .bg-shimmer
 */
function Skeleton({
  className,
  shimmer = false,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { shimmer?: boolean }) {
  return (
    <div
      className={cn(
        'rounded-md bg-muted',
        shimmer && 'bg-shimmer',
        className
      )}
      {...props}
    />
  )
}

/* Preset skeleton shapes for reuse */
function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          shimmer
          className={cn(
            'h-4',
            // Last line is shorter (trailing "..." effect)
            i === lines - 1 ? 'w-3/4' : 'w-full'
          )}
        />
      ))}
    </div>
  )
}

function SkeletonAvatar({
  size = 'md',
  className,
}: {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}) {
  const sizeMap = { sm: 'h-8 w-8', md: 'h-10 w-10', lg: 'h-12 w-12' }
  return <Skeleton shimmer className={cn('rounded-full', sizeMap[size], className)} />
}

function SkeletonCard({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'rounded-xl border border-border bg-white p-6 space-y-4 shadow-sm',
        className
      )}
    >
      {/* Card header row */}
      <div className="flex items-center gap-3">
        <Skeleton shimmer className="h-10 w-10 rounded-full" />
        <div className="flex-1 space-y-1.5">
          <Skeleton shimmer className="h-4 w-1/3" />
          <Skeleton shimmer className="h-3 w-1/4" />
        </div>
      </div>
      {/* Card body lines */}
      <SkeletonText lines={3} />
      {/* Card footer */}
      <div className="flex gap-2 pt-2">
        <Skeleton shimmer className="h-8 w-20 rounded-full" />
        <Skeleton shimmer className="h-8 w-16 rounded-full" />
      </div>
    </div>
  )
}

export { Skeleton, SkeletonText, SkeletonAvatar, SkeletonCard }
