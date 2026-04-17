// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — DashboardSkeleton
// Civora-style shimmer skeleton for the main dashboard page
// Mimics the layout: stats row → chart row → table row
// ══════════════════════════════════════════════════════════════════════════════

import * as React from 'react'
import { Skeleton } from '@/components/ui/skeleton'

function StatCardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
      {/* Card header */}
      <div className="flex items-center justify-between">
        <Skeleton shimmer className="h-4 w-28 rounded" />
        <Skeleton shimmer className="h-8 w-8 rounded-full" />
      </div>
      {/* Value */}
      <Skeleton shimmer className="mt-3 h-8 w-36 rounded" />
      {/* Trend */}
      <div className="mt-2 flex items-center gap-2">
        <Skeleton shimmer className="h-5 w-14 rounded-full" />
        <Skeleton shimmer className="h-3 w-20 rounded" />
      </div>
    </div>
  )
}

function ChartSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
      {/* Chart header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="space-y-1.5">
          <Skeleton shimmer className="h-5 w-40 rounded" />
          <Skeleton shimmer className="h-3 w-24 rounded" />
        </div>
        <Skeleton shimmer className="h-8 w-20 rounded-md" />
      </div>
      {/* Chart body — area placeholder */}
      <div className="relative h-48 overflow-hidden rounded-lg bg-muted">
        {/* Fake chart bars */}
        <div className="absolute inset-x-4 bottom-0 flex items-end justify-between gap-2">
          {[65, 45, 80, 55, 90, 70, 85, 60, 75, 50, 88, 72].map((h, i) => (
            <Skeleton key={i} shimmer className="rounded-t-sm" style={{ height: `${h}%`, width: '6%' }} />
          ))}
        </div>
      </div>
    </div>
  )
}

function TableSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-white shadow-sm">
      {/* Table header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <Skeleton shimmer className="h-5 w-32 rounded" />
        <Skeleton shimmer className="h-8 w-24 rounded-md" />
      </div>
      {/* Table rows */}
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex items-center gap-4 border-b border-border px-6 py-4 last:border-0">
          {/* Avatar + name */}
          <div className="flex items-center gap-3 flex-1">
            <Skeleton shimmer className="h-9 w-9 rounded-full" />
            <div className="space-y-1.5">
              <Skeleton shimmer className="h-4 w-32 rounded" />
              <Skeleton shimmer className="h-3 w-24 rounded" />
            </div>
          </div>
          {/* Badge */}
          <Skeleton shimmer className="h-5 w-20 rounded-full" />
          {/* Amount */}
          <Skeleton shimmer className="h-4 w-24 rounded" />
          {/* Arrow */}
          <Skeleton shimmer className="h-4 w-4 rounded" />
        </div>
      ))}
    </div>
  )
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Stats row — 4 cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
      </div>

      {/* Charts row — 2 charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <ChartSkeleton />
        <ChartSkeleton />
      </div>

      {/* Table row */}
      <TableSkeleton />
    </div>
  )
}
