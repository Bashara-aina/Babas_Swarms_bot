---
title: rumahlabuh-com
type: project
status: active
tags: [indonesia, property, kost, booking, rental, nextjs, supabase, midtrans, business-rules]
created: 2026-04-13
updated: 2026-04-13
summary: "rumahlabuh.com is a Labuh Biru kost (boarding house) booking platform in Indonesia with Next.js + Supabase. Features open-ended and fixed-term contract management, automatic late fee enforcement (Aturan 3: Rp250K penalty for 4-15 days late), deposit refund logic (Aturan 17: ≥14 days notice = full refund), Midtrans payment integration, and atomic room assignment. Scored 100/100 in comprehensive logic audit (April 2026)."
wikilinks:
  - [[supabase]]
  - [[midtrans]]
  - [[cekwajar-id]]
confidence: high
source: implementation
project: rumahlabuh
---

# rumahlabuh.com — Labuh Biru Kost Booking System

## TL;DR

rumahlabuh.com is a kost (Indonesian boarding house) booking and rental management platform built with Next.js 15 + Supabase. It handles open-ended and fixed-term contracts with deterministic business rules: **Aturan 3** (late penalties: 3-day grace, Rp250K for days 4-15, contract termination if >15 days) and **Aturan 17** (deposit refunds: ≥14 days notice = full refund, <14 days = forfeited). Includes `/perpanjang` (extend booking) and `/perpanjang/pemberitahuan-pindah` (move-out notice) workflows, Midtrans Snap payments, and atomic room conflict prevention via `FOR UPDATE SKIP LOCKED`. Logic audit score: **100/100**.

---

## 1. Business Domain

**Product**: Labuh Biru kost — managed boarding house rental in Indonesia
**Problem solved**: Transparent booking workflow with enforceable contract rules, eliminating manual penalty/deposit tracking
**Target users**: Kost tenants (monthly rental), property manager

---

## 2. Core Business Rules

### Aturan 3 — Late Payment (Kontrak Fleksibel / Open-ended)

Applies to open-ended (monthly) contracts:

| Days Late | Consequence |
|-----------|-------------|
| 1–3 | Grace period, no penalty |
| 4–15 | Late fee: **Rp 250,000** |
| >15 | Contract terminated, deposit forfeited |

### Aturan 17 — Deposit Refund (Move-Out Notice)

Applies when tenant submits move-out notice (`/perpanjang/pemberitahuan-pindah`):

| Notice Timing | Deposit Outcome |
|---------------|-----------------|
| ≥14 days before move-out | **Full refund** |
| <14 days before move-out | **Forfeited** |

---

## 3. Contract Types

### Open-ended (Kontrak Fleksibel)
- Monthly billing cycle
- Payment due at **start of each monthly period**
- Grace period: 3 days after due date
- Late fee Rp 250K applied on days 4-15
- Contract termination if payment >15 days overdue
- `move_out_notice_deadline` = `end_date - 14 days`

### Fixed-term (Kontrak Tetap)
- Set check-in → check-out dates
- Cannot be extended month-by-month (converts to open-ended on extension)
- Extension creates a new booking period

### Type Conversion
- `perpanjang` on fixed-term → converts to open-ended
- Open-ended extension → always stays open-ended
- `booking_type` field tracks: `'open_ended'` | `'fixed_term'`

---

## 4. Key Workflows

### 4.1 Booking Extension (`/perpanjang`)

**Flow**: `checkExtensionAvailability` → `createExtensionPayment` → Midtrans Snap → webhook → `processExtensionPayment`

**Key constraints**:
- Cannot extend if `move_out_notice_date` is set
- Cannot extend if `daysLate > 15` (open-ended, Aturan 3)
- Cannot extend if room conflict exists (checks `confirmed`, `active`, `pending_payment` statuses)
- Past dates rejected — future dates only validated via `startOfDay()`
- Amount must be positive (validates before Midtrans call)

**Late fee calculation**:
```
if (isOpenEnded && daysLate > 3) {
  lateFee = 250000
  totalAmount = monthlyRate + lateFee
}
```

**Conflict detection**: Uses `getAvailableRoomIdsForRoomType()` which applies full overlap + open-ended logic (not simple room status check)

### 4.2 Move-Out Notice (`/perpanjang/pemberitahuan-pindah`)

**Flow**: `calculateMoveOutPayment` → (optional overstay payment) → `createMoveOutNotice` → email notification

**Key constraints**:
- Cannot submit if notice already exists
- Future dates only (past dates rejected)
- Positive amount validation on overstay payment

**Overstay payment** (if move-out after due date):
```
overstayDays = moveOutDate - dueDate
overstayAmount = overstayDays × dailyRate
```

**Deposit handling**:
- ≥14 days notice → refund: status = `'refunded'`
- <14 days notice → forfeit: status = `'forfeited'`
- Update `deposit_status`, `deposit_amount`, `move_out_notice_date`

### 4.3 Booking Creation (`/pesan`)

**Atomic room assignment** via `reserve_available_room` RPC:
```sql
-- FOR UPDATE SKIP LOCKED prevents race conditions
reserve_available_room(room_type_id, check_in, check_out)
```

**Duplicate check** includes `active` status (not just `confirmed`):
```sql
.in('status', ['confirmed', 'active'])
```

---

## 5. Database Schema

### Core Tables

| Table | Purpose |
|-------|---------|
| `bookings` | Primary booking records |
| `booking_extensions` | Extension payment records |
| `rooms` | Room inventory with `room_type_id`, `status` |
| `room_types` | Room type definitions (monthly rate, etc.) |
| `room_type_pricing` | Rate overrides per room type |

### Key Booking Fields

```sql
bookings (
  -- Core
  id UUID PRIMARY KEY,
  room_id UUID REFERENCES rooms(id),
  check_in_date DATE,
  check_out_date DATE,          -- placeholder '2099-12-31' for open-ended
  booking_type TEXT,             -- 'open_ended' | 'fixed_term'
  status TEXT,                   -- 'confirmed' | 'active' | 'pending_payment'
  monthly_rate BIGINT,

  -- Deposit
  deposit_amount BIGINT,
  deposit_status TEXT,           -- 'held' | 'refunded' | 'forfeited'

  -- Move-out
  move_out_notice_date DATE,
  move_out_notice_deadline DATE, -- end_date - 14 days

  -- Timestamps
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
)
```

### Room Status Values

| Status | Meaning |
|--------|---------|
| `available` | Ready for booking |
| `occupied_short_term` | Fixed-term booking |
| `occupied_long_term` | Monthly/biweekly booking |
| `maintenance` | Excluded from availability |

---

## 6. Fixes Applied (April 2026 Audit)

17 fixes across critical/high/medium/low priority:

### Critical (C1–C4)
- **C1**: Open-ended extension lookup now includes `.or('check_out_date.gte.${today},booking_type.eq.open_ended')`
- **C2**: Extension webhook idempotency — checks `payment_status === 'paid'` before processing
- **C3**: Atomic room assignment via `reserve_available_room` RPC (`FOR UPDATE SKIP LOCKED`)
- **C4**: Duplicate booking check includes `active` status: `.in('status', ['confirmed', 'active'])`

### High (H1–H7)
- **H1**: `booking_type` added to PDF contract generation
- **H2**: Extension conflict check statuses: `['confirmed', 'active', 'pending_payment']`
- **H3**: Alternate room logic uses `getAvailableRoomIdsForRoomType()` (full overlap + open-ended logic)
- **H4**: Admin bookings UI includes `active` status filter with green badge
- **H6**: Availability queries optimized with open-ended predicate
- **H7**: Biweekly duration label added: `'2 Mingguan'`

### Medium (M1–M6)
- **M1**: `createExtensionPayment` uses `pricing` object from `calculateExtensionPrice` (no duplicate late fee calc)
- **M2**: `move_out_notice_deadline` updated on extension payment
- **M3**: New room status on extension: `occupied_long_term` for monthly/biweekly
- **M4**: Maintenance rooms excluded from availability
- **M6**: Admin date range filter uses OR logic for active bookings

### Low (L1–L3, L6)
- **L1**: Checkout date formatted in Indonesian: `"D Mon YYYY"`
- **L3**: Phone validation: 10–14 digits, normalized to `0xxx` format
- **L6**: `active` bookings show green badge (same as `confirmed`)

---

## 7. Webhook Handler

Payment webhook at `app/api/payment/webhook/route.ts`:

1. **Idempotency guard**: Skips if `booking_extensions.payment_status === 'paid'`
2. **Room status update**: `occupied_long_term` for monthly/biweekly, `occupied_short_term` otherwise
3. **Booking dates**: Updates `check_out_date` for open-ended extensions
4. **Email notification**: Sends confirmation email after payment
5. **Overstay handling**: If move-out after due date, calculates overstay payment

---

## 8. Technical Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15 (App Router) |
| Database | Supabase PostgreSQL + RLS |
| Payments | Midtrans Snap |
| Validation | date-fns (`startOfDay`, `isBefore`) |
| Deployment | Vercel |

### Key Files

| File | Purpose |
|------|---------|
| `app/perpanjang/_actions.ts` | Extension availability + payment creation |
| `app/pesan/_actions.ts` | Booking creation with atomic room |
| `app/api/payment/webhook/route.ts` | Midtrans webhook handler |
| `lib/availability.ts` | Availability queries (3 functions) |
| `lib/format.ts` | Date/currency formatting |

---

## 9. Logic Audit Result

**Score: 100/100** (April 8, 2026)

All business rules correctly implemented:
- Aturan 3 late fee calculation: ✅
- Aturan 17 deposit refund: ✅
- Open-ended vs fixed-term handling: ✅
- Webhook idempotency: ✅
- Atomic room assignment: ✅
- Date validation (future dates only): ✅
- Amount validation (positive only): ✅
- Phone validation (10-14 digits): ✅
- Move-out notice blocking on extensions: ✅
- Timezone-safe date comparisons: ✅

---

## 10. Current Status

As of 2026-04-13:
- ✅ Extension workflow complete
- ✅ Move-out notice workflow complete
- ✅ Late fee enforcement active
- ✅ Deposit refund rules enforced
- ✅ Webhook handler with email notifications
- ✅ 100/100 logic audit passed
- ✅ All 17 audit fixes applied

**Post-deployment remaining**:
- Email worker setup (Resend/SendGrid)
- Load testing (optional)
- Admin cancel move-out UI (P3)

---

## Related Articles

- [[supabase]] — Database provider
- [[cekwajar-id]] — Related project (Indonesian salary/property data platform)
- [[cekwajar-tech-stack]] — cekwajar tech stack reference (similar Next.js + Supabase pattern)
