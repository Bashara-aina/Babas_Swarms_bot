---
name: ui
description: "Skill for the Ui area of swarm-bot. 963 symbols across 328 files."
---

# Ui

963 symbols | 328 files | Cohesion: 91%

## When to Use

- Working with code in `shadboard-ref/`
- Understanding how cn, Nav, CalendarDateRangePicker work
- Modifying ui-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `shadboard-ref/starter-kit/src/components/ui/sidebar.tsx` | SidebarInset, SidebarInput, SidebarHeader, SidebarFooter, SidebarSeparator (+18) |
| `shadboard-ref/full-kit/src/components/ui/sidebar.tsx` | SidebarInset, SidebarInput, SidebarHeader, SidebarFooter, SidebarSeparator (+18) |
| `project/rumahlabuh/components/ui/sidebar.tsx` | SidebarInset, SidebarInput, SidebarHeader, SidebarFooter, SidebarSeparator (+14) |
| `project/rumahlabuh/components/ui/menubar.tsx` | Menubar, MenubarTrigger, MenubarContent, MenubarItem, MenubarCheckboxItem (+6) |
| `shadboard-ref/starter-kit/src/components/ui/menubar.tsx` | Menubar, MenubarTrigger, MenubarSubTrigger, MenubarSubContent, MenubarContent (+6) |
| `shadboard-ref/full-kit/src/components/ui/menubar.tsx` | Menubar, MenubarTrigger, MenubarSubTrigger, MenubarSubContent, MenubarContent (+6) |
| `project/rumahlabuh/components/ui/item.tsx` | ItemGroup, ItemSeparator, Item, ItemMedia, ItemContent (+5) |
| `project/rumahlabuh/components/ui/field.tsx` | FieldSet, FieldLegend, FieldGroup, Field, FieldContent (+5) |
| `shadboard-ref/starter-kit/src/components/ui/dropdown-menu.tsx` | DropdownMenuTrigger, DropdownMenuSubTrigger, DropdownMenuSubContent, DropdownMenuContent, DropdownMenuItem (+5) |
| `shadboard-ref/full-kit/src/components/ui/dropdown-menu.tsx` | DropdownMenuTrigger, DropdownMenuSubTrigger, DropdownMenuSubContent, DropdownMenuContent, DropdownMenuItem (+5) |

## Entry Points

Start here when exploring this area:

- **`cn`** (Function) — `nextjs-dashboard-ref/lib/utils.ts:3`
- **`Nav`** (Function) — `nextjs-dashboard-ref/components/nav.tsx:28`
- **`CalendarDateRangePicker`** (Function) — `nextjs-dashboard-ref/components/date-range-picker.tsx:14`
- **`DashboardNav`** (Function) — `nextjs-dashboard-ref/components/dashboard-nav.tsx:18`
- **`BreadCrumb`** (Function) — `nextjs-dashboard-ref/components/breadcrumb.tsx:14`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `cn` | Function | `nextjs-dashboard-ref/lib/utils.ts` | 3 |
| `Nav` | Function | `nextjs-dashboard-ref/components/nav.tsx` | 28 |
| `CalendarDateRangePicker` | Function | `nextjs-dashboard-ref/components/date-range-picker.tsx` | 14 |
| `DashboardNav` | Function | `nextjs-dashboard-ref/components/dashboard-nav.tsx` | 18 |
| `BreadCrumb` | Function | `nextjs-dashboard-ref/components/breadcrumb.tsx` | 14 |
| `RootLayout` | Function | `nextjs-dashboard-ref/app/layout.tsx` | 26 |
| `WordmarkLogo` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/WordmarkLogo.tsx` | 21 |
| `SparklesCore` | Function | `nextjs-dashboard-ref/components/ui/sparkles.tsx` | 20 |
| `CardContainer` | Function | `nextjs-dashboard-ref/components/ui/3d-card.tsx` | 17 |
| `CardBody` | Function | `nextjs-dashboard-ref/components/ui/3d-card.tsx` | 79 |
| `CardItem` | Function | `nextjs-dashboard-ref/components/ui/3d-card.tsx` | 98 |
| `Header` | Function | `nextjs-dashboard-ref/components/layout/header.tsx` | 34 |
| `isNonNegative` | Function | `shadboard-ref/full-kit/src/lib/utils.ts` | 268 |
| `getDiscountedPrice` | Function | `shadboard-ref/full-kit/src/lib/utils.ts` | 272 |
| `RootLayout` | Function | `shadboard-ref/starter-kit/src/app/layout.tsx` | 40 |
| `PricingPlans` | Function | `shadboard-ref/full-kit/src/components/pricing-plans.tsx` | 128 |
| `DateInput` | Function | `project/rumahlabuh/components/ui/date-input.tsx` | 21 |
| `StatusBadge` | Function | `project/rumahlabuh/components/labuh/status-badge.tsx` | 109 |
| `RoomPhotoGallery` | Function | `project/rumahlabuh/components/labuh/room-photo-gallery.tsx` | 17 |
| `LoadingSpinner` | Function | `project/rumahlabuh/components/labuh/loading-spinner.tsx` | 11 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `ManualBookingForm → Listener` | cross_community | 4 |
| `MoveOutTrackerClient → Listener` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Extension | 2 calls |

## How to Explore

1. `gitnexus_context({name: "cn"})` — see callers and callees
2. `gitnexus_query({query: "ui"})` — find related execution flows
3. Read key files listed above for implementation details
