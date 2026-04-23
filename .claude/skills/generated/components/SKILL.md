---
name: components
description: "Skill for the _components area of swarm-bot. 109 symbols across 75 files."
---

# _components

109 symbols | 75 files | Cohesion: 85%

## When to Use

- Working with code in `shadboard-ref/`
- Understanding how formatDateShort, useIsRtl, Editor work
- Modifying _components-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `shadboard-ref/full-kit/src/lib/utils.ts` | formatDateShort, formatDistance, formatUnreadCount, ensureWithSuffix, camelCaseToTitleCase (+2) |
| `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/apps/calendar/_components/calendar-header.tsx` | CalendarHeader, handleDateChange, handlePrev, handleNext, handleViewChange (+1) |
| `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/apps/calendar/_contexts/calendar-context.tsx` | handleAddEvent, handleUpdateEvent, handleDeleteEvent, handleSelectEvent, handleSelectCategory |
| `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/apps/calendar/_components/calendar-content.tsx` | parseEvent, handleEventDrop, handleEventResize, handleEventClick, CalendarContent |
| `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/apps/calendar/_components/event-sidebar.tsx` | onSubmit, EventSidebar, handleSidebarClose, handleOnDeleteEvent |
| `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/apps/kanban/_contexts/kanban-context.tsx` | handleUpdateColumn, handleDeleteColumn, handleSelectColumn |
| `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/apps/kanban/_components/kanban-sidebar/kanban-update-column-sidebar.tsx` | KanbanUpdateColumnSidebar, onSubmit, handleSidebarClose |
| `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/ecommerce/_components/sales-trend-chart.tsx` | SalesTrendChart, ModifiedChartTooltipContent |
| `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/ecommerce/_components/gender-distribution-chart.tsx` | getNormalizedSize, GenderDistributionChart |
| `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/ecommerce/_components/churn-rate-chart.tsx` | ChurnRateChart, ModifiedChartTooltipContent |

## Entry Points

Start here when exploring this area:

- **`formatDateShort`** (Function) — `shadboard-ref/full-kit/src/lib/utils.ts:142`
- **`useIsRtl`** (Function) — `shadboard-ref/starter-kit/src/hooks/use-is-rtl.tsx:4`
- **`Editor`** (Function) — `shadboard-ref/full-kit/src/components/ui/editor/index.tsx:31`
- **`SalesTrendSummary`** (Function) — `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/ecommerce/_components/sales-trend-summary.tsx:6`
- **`SalesTrendChart`** (Function) — `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/ecommerce/_components/sales-trend-chart.tsx:38`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `formatDateShort` | Function | `shadboard-ref/full-kit/src/lib/utils.ts` | 142 |
| `useIsRtl` | Function | `shadboard-ref/starter-kit/src/hooks/use-is-rtl.tsx` | 4 |
| `Editor` | Function | `shadboard-ref/full-kit/src/components/ui/editor/index.tsx` | 31 |
| `SalesTrendSummary` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/ecommerce/_components/sales-trend-summary.tsx` | 6 |
| `SalesTrendChart` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/ecommerce/_components/sales-trend-chart.tsx` | 38 |
| `RevenueBySourceChart` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/ecommerce/_components/revenue-by-source-chart.tsx` | 10 |
| `GenderDistributionChart` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/ecommerce/_components/gender-distribution-chart.tsx` | 45 |
| `ChurnRateChart` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/ecommerce/_components/churn-rate-chart.tsx` | 55 |
| `SalesTrendChart` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/crm/_components/sales-trend-chart.tsx` | 38 |
| `SalesByCountryChart` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/crm/_components/sales-by-country-chart.tsx` | 54 |
| `RevenueTrendChart` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/crm/_components/revenue-trend-chart.tsx` | 40 |
| `PerformanceOverTimeChart` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/analytics/_components/performance-over-time-chart.tsx` | 13 |
| `NewVsReturningVisitorsChart` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/analytics/_components/new-vs-returning-visitors-chart.tsx` | 10 |
| `ConversionFunnelChart` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/analytics/_components/conversion-funnel-chart.tsx` | 9 |
| `UniqueVisitorsChart` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/analytics/_components/overview/unique-visitors-chart.tsx` | 20 |
| `ConversionRateChart` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/analytics/_components/overview/conversion-rate-chart.tsx` | 39 |
| `BounceRateChart` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/analytics/_components/overview/bounce-rate-chart.tsx` | 39 |
| `AverageSessionDurationChart` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/dashboards/analytics/_components/overview/average-session-duration-chart.tsx` | 40 |
| `useEmailContext` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/apps/email/_hooks/use-email-context.tsx` | 6 |
| `EmailView` | Function | `shadboard-ref/full-kit/src/app/[lang]/(dashboard-layout)/apps/email/_components/email-view.tsx` | 11 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ui | 9 calls |
| Auth | 7 calls |
| Hooks | 4 calls |
| [id] | 1 calls |

## How to Explore

1. `gitnexus_context({name: "formatDateShort"})` — see callers and callees
2. `gitnexus_query({query: "_components"})` — find related execution flows
3. Read key files listed above for implementation details
