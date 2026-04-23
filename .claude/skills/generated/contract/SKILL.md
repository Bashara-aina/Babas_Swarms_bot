---
name: contract
description: "Skill for the Contract area of swarm-bot. 47 symbols across 35 files."
---

# Contract

47 symbols | 35 files | Cohesion: 57%

## When to Use

- Working with code in `project/`
- Understanding how makeInitialBookingOrderId, getAvailableCountByBranchFallback, sitemap work
- Modifying contract-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `project/rumahlabuh/lib/contract/upload-contract.ts` | ensureBucket, uploadContractPdf, getContractSignedUrl |
| `project/rumahlabuh/app/cek-booking/_actions.ts` | normalisePhone, lookupBooking |
| `project/rumahlabuh/app/perpanjang/pemberitahuan-pindah/_actions.ts` | normalisePhone, findMonthlyBookings |
| `project/rumahlabuh/app/admin/(protected)/_actions.ts` | getTenantActiveBookingCount, checkTenantCanBeDeleted |
| `project/rumahlabuh/app/api/admin/uploads/images/route.ts` | DELETE, PATCH |
| `project/rumahlabuh/app/admin/(protected)/penyewa/page.tsx` | PenyewaPage, filterHref |
| `project/rumahlabuh/app/admin/(protected)/move-out/page.tsx` | depositApplies, MoveOutTrackerPage |
| `project/rumahlabuh/lib/contract/format-contract-dates.ts` | formatIndonesianDateIso, formatIndonesianDateLong |
| `project/rumahlabuh/lib/contract/generate-pdf.tsx` | renderContractPdf, ContractDocument |
| `project/rumahlabuh/app/api/contract/sign/route.ts` | formatDateYYYYMMDD, POST |

## Entry Points

Start here when exploring this area:

- **`makeInitialBookingOrderId`** (Function) — `project/rumahlabuh/lib/midtrans-order-id.ts:16`
- **`getAvailableCountByBranchFallback`** (Function) — `project/rumahlabuh/lib/availability.ts:310`
- **`sitemap`** (Function) — `project/rumahlabuh/app/sitemap.ts:9`
- **`Page`** (Function) — `project/rumahlabuh/app/page.tsx:71`
- **`createAdminClient`** (Function) — `project/rumahlabuh/lib/supabase/admin.ts:6`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `makeInitialBookingOrderId` | Function | `project/rumahlabuh/lib/midtrans-order-id.ts` | 16 |
| `getAvailableCountByBranchFallback` | Function | `project/rumahlabuh/lib/availability.ts` | 310 |
| `sitemap` | Function | `project/rumahlabuh/app/sitemap.ts` | 9 |
| `Page` | Function | `project/rumahlabuh/app/page.tsx` | 71 |
| `createAdminClient` | Function | `project/rumahlabuh/lib/supabase/admin.ts` | 6 |
| `uploadContractPdf` | Function | `project/rumahlabuh/lib/contract/upload-contract.ts` | 23 |
| `getContractSignedUrl` | Function | `project/rumahlabuh/lib/contract/upload-contract.ts` | 49 |
| `lookupBooking` | Function | `project/rumahlabuh/app/cek-booking/_actions.ts` | 10 |
| `renderExtensionInvoicePdf` | Function | `project/rumahlabuh/lib/invoice/extension-invoice-template.tsx` | 292 |
| `handleSubmit` | Function | `project/rumahlabuh/app/cek-booking/page.tsx` | 86 |
| `findMonthlyBookings` | Function | `project/rumahlabuh/app/perpanjang/pemberitahuan-pindah/_actions.ts` | 46 |
| `getTenantActiveBookingCount` | Function | `project/rumahlabuh/app/admin/(protected)/_actions.ts` | 376 |
| `checkTenantCanBeDeleted` | Function | `project/rumahlabuh/app/admin/(protected)/_actions.ts` | 389 |
| `handlePhoneSubmit` | Function | `project/rumahlabuh/app/perpanjang/pemberitahuan-pindah/_form.tsx` | 91 |
| `POST` | Function | `project/rumahlabuh/app/api/payment/create/route.ts` | 9 |
| `GET` | Function | `project/rumahlabuh/app/api/cron/expired-bookings/route.ts` | 12 |
| `GET` | Function | `project/rumahlabuh/app/api/contract/download/route.ts` | 7 |
| `runExpiredBookingsCleanup` | Function | `project/rumahlabuh/app/admin/(protected)/bookings/_expired-cleanup-action.ts` | 21 |
| `GET` | Function | `project/rumahlabuh/app/api/invoice/extension/[orderId]/route.ts` | 4 |
| `GET` | Function | `project/rumahlabuh/app/api/debug/booking/[bookingCode]/route.ts` | 3 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `POST → CreateAdminClient` | cross_community | 4 |
| `HandleSubmit → CreateAdminClient` | cross_community | 4 |
| `ManualBookingForm → CreateAdminClient` | cross_community | 4 |
| `MoveOutNoticeForm → CreateAdminClient` | cross_community | 4 |
| `RoomTypeDetailPage → CreateAdminClient` | cross_community | 3 |
| `RoomTypeDetailPage → CreateAdminClient` | cross_community | 3 |
| `LabuhBiruPage → CreateAdminClient` | cross_community | 3 |
| `LabuhBanyuPage → CreateAdminClient` | cross_community | 3 |
| `GET → FormatIndonesianDateIso` | intra_community | 3 |
| `GET → FormatIndonesianDateLong` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| [id] | 8 calls |

## How to Explore

1. `gitnexus_context({name: "makeInitialBookingOrderId"})` — see callers and callees
2. `gitnexus_query({query: "contract"})` — find related execution flows
3. Read key files listed above for implementation details
