---
name: id
description: "Skill for the [id] area of swarm-bot. 102 symbols across 64 files."
---

# [id]

102 symbols | 64 files | Cohesion: 70%

## When to Use

- Working with code in `project/`
- Understanding how refreshDashboardData, refresh, handleRefresh work
- Modifying [id]-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `project/rumahlabuh/app/admin/(protected)/bookings/[id]/_booking-actions.tsx` | handleConfirm, handleCancel, handleOpenEndedExtend, handleFixedTermExtend, handleSaveNotes (+5) |
| `project/rumahlabuh/app/admin/(protected)/_actions.ts` | confirmPayment, cancelBooking, markBookingExpired, updateAdminNotes, updateDepositDecision (+3) |
| `project/rumahlabuh/lib/date.ts` | formatDateInWIB, formatDateTimeWIB, formatDateTimeWIBShortMonth, formatDateShortInWIB |
| `nextjs-dashboard-ref/components/ui/use-toast.ts` | genId, toast, useToast |
| `project/rumahlabuh/lib/utils/require-admin.ts` | getAdminEmailList, requireAdmin, getAdminUser |
| `project/rumahlabuh/app/perpanjang/_actions.ts` | validateFutureDate, extendOpenEndedBooking, manualExtendBooking |
| `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/app/api/col/compare/route.ts` | buildVerdictMessage, calculateCOLAdjustment, GET |
| `nextjs-dashboard-ref/components/refresh-button.tsx` | handleRefresh, RefreshButton |
| `project/rumahlabuh/app/admin/(protected)/bookings/create/_actions.ts` | listEligibleRoomsForManualBooking, createManualBooking |
| `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/app/api/ocr/quota/route.ts` | GET, getCurrentMonthKey |

## Entry Points

Start here when exploring this area:

- **`refreshDashboardData`** (Function) — `nextjs-dashboard-ref/lib/actions.ts:349`
- **`refresh`** (Function) — `halolight-ref/src/hooks/use-dashboard-data.ts:116`
- **`handleRefresh`** (Function) — `nextjs-dashboard-ref/components/refresh-button.tsx:12`
- **`requireAdmin`** (Function) — `project/rumahlabuh/lib/utils/require-admin.ts:21`
- **`getAdminUser`** (Function) — `project/rumahlabuh/lib/utils/require-admin.ts:54`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `refreshDashboardData` | Function | `nextjs-dashboard-ref/lib/actions.ts` | 349 |
| `refresh` | Function | `halolight-ref/src/hooks/use-dashboard-data.ts` | 116 |
| `handleRefresh` | Function | `nextjs-dashboard-ref/components/refresh-button.tsx` | 12 |
| `requireAdmin` | Function | `project/rumahlabuh/lib/utils/require-admin.ts` | 21 |
| `getAdminUser` | Function | `project/rumahlabuh/lib/utils/require-admin.ts` | 54 |
| `logAdminAction` | Function | `project/rumahlabuh/lib/utils/audit-log.ts` | 6 |
| `createClient` | Function | `project/rumahlabuh/lib/supabase/server.ts` | 3 |
| `extendOpenEndedBooking` | Function | `project/rumahlabuh/app/perpanjang/_actions.ts` | 533 |
| `manualExtendBooking` | Function | `project/rumahlabuh/app/perpanjang/_actions.ts` | 645 |
| `handleLogout` | Function | `project/rumahlabuh/components/labuh/admin-sidebar-v2.tsx` | 140 |
| `BookingConfirmationEmail` | Function | `project/rumahlabuh/lib/email/templates/booking-confirmation.ts` | 0 |
| `confirmPayment` | Function | `project/rumahlabuh/app/admin/(protected)/_actions.ts` | 12 |
| `cancelBooking` | Function | `project/rumahlabuh/app/admin/(protected)/_actions.ts` | 106 |
| `markBookingExpired` | Function | `project/rumahlabuh/app/admin/(protected)/_actions.ts` | 144 |
| `updateAdminNotes` | Function | `project/rumahlabuh/app/admin/(protected)/_actions.ts` | 200 |
| `updateDepositDecision` | Function | `project/rumahlabuh/app/admin/(protected)/_actions.ts` | 225 |
| `adminSetMoveOutDate` | Function | `project/rumahlabuh/app/admin/(protected)/_actions.ts` | 260 |
| `changeRoomStatus` | Function | `project/rumahlabuh/app/admin/(protected)/_actions.ts` | 327 |
| `updateTenant` | Function | `project/rumahlabuh/app/admin/(protected)/_actions.ts` | 431 |
| `UserDropdown` | Function | `shadboard-ref/full-kit/src/components/layout/user-dropdown.tsx` | 24 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `ManualBookingForm → Listener` | cross_community | 4 |
| `ManualBookingForm → CreateClient` | cross_community | 4 |
| `ManualBookingForm → GetAdminEmailList` | cross_community | 4 |
| `ManualBookingForm → ToDateString` | cross_community | 4 |
| `ManualBookingForm → CreateAdminClient` | cross_community | 4 |
| `MoveOutTrackerClient → Listener` | cross_community | 4 |
| `POST → CreateClient` | cross_community | 3 |
| `POST → GetAdminEmailList` | cross_community | 3 |
| `POST → CreateClient` | cross_community | 3 |
| `POST → CreateClient` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Contract | 22 calls |
| Labuh | 4 calls |
| Ui | 3 calls |
| Email | 3 calls |
| Kamar | 2 calls |
| Move-out | 2 calls |
| Cekwajar.id | 1 calls |
| Login | 1 calls |

## How to Explore

1. `gitnexus_context({name: "refreshDashboardData"})` — see callers and callees
2. `gitnexus_query({query: "[id]"})` — find related execution flows
3. Read key files listed above for implementation details
