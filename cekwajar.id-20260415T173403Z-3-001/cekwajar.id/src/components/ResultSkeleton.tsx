// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — ResultSkeleton Component
// Skeleton loading state for tool result sections
// Used wherever isCalculating / isLoading is true
// ══════════════════════════════════════════════════════════════════════════════

import { Skeleton } from '@/components/ui/skeleton'

export function ResultSkeleton() {
  return (
    <div className="space-y-4 mt-8" aria-label="Memuat hasil..." aria-busy="true">
      {/* Verdict badge skeleton */}
      <Skeleton className="h-16 w-full rounded-xl" />

      {/* Violation cards skeleton */}
      <Skeleton className="h-24 w-full rounded-lg" />
      <Skeleton className="h-24 w-full rounded-lg" />

      {/* Calculation table skeleton */}
      <Skeleton className="h-40 w-full rounded-lg" />
    </div>
  )
}
