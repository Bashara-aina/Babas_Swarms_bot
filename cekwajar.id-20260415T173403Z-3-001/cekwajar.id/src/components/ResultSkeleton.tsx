// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — ResultSkeleton Component
// Loading skeleton for wajar-slip result state
// Matches actual ViolationItem and Card heights for smooth transition
// ══════════════════════════════════════════════════════════════════════════════

import { Skeleton } from '@/components/ui/skeleton'

export function ResultSkeleton({ className }: { className?: string }) {
  return (
    <div className={className}>
      {/* Verdict header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Skeleton shimmer className="h-10 w-10 rounded-full" />
          <div className="space-y-1.5">
            <Skeleton shimmer className="h-5 w-32" />
            <Skeleton shimmer className="h-3 w-24" />
          </div>
        </div>
        <Skeleton shimmer className="h-6 w-16 rounded-full" />
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="rounded-lg border border-border bg-white p-3 space-y-1.5">
          <Skeleton shimmer className="h-3 w-16" />
          <Skeleton shimmer className="h-5 w-20" />
        </div>
        <div className="rounded-lg border border-border bg-white p-3 space-y-1.5">
          <Skeleton shimmer className="h-3 w-16" />
          <Skeleton shimmer className="h-5 w-20" />
        </div>
        <div className="rounded-lg border border-border bg-white p-3 space-y-1.5">
          <Skeleton shimmer className="h-3 w-16" />
          <Skeleton shimmer className="h-5 w-20" />
        </div>
      </div>

      {/* Violations */}
      <div className="space-y-2.5 mb-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg border border-border bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2">
                <Skeleton shimmer className="h-5 w-5 rounded-full" />
                <Skeleton shimmer className="h-4 w-40" />
              </div>
              <Skeleton shimmer className="h-5 w-24" />
            </div>
            <div className="mt-2 flex items-center gap-2">
              <Skeleton shimmer className="h-3 w-20" />
              <Skeleton shimmer className="h-3 w-16" />
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Skeleton shimmer className="h-10 flex-1 rounded-lg" />
        <Skeleton shimmer className="h-10 flex-1 rounded-lg" />
      </div>
    </div>
  )
}
