---
title: Planner 2026 04 23 Cekwajar Slip Audit Tool
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Plan: cekwajar.id Salary Slip Audit Tool — Full Implementation

Date: 2026-04-23
Type: FEATURE
Task: Build the complete cekwajar.id salary slip audit tool

## Context Gathered

The cekwajar.id Next.js app already exists at `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/`.
It has:
- A functional slip page at `src/app/wajar-slip/page.tsx` — but it uses basic shadcn Input/Select, NOT the premium components
- Layout, Footer, shared components, calculation lib (`lib/calculations/pph21.ts`)
- API routes for audit, cities, auth
- PremiumGate, ViolationSummaryBanner, ViolationItem, VerdictBadge, etc.

The SEPARATE "source of truth" reference project exists at `cekwajar/cekwajar-20260413T050820Z-3-001/cekwajar/slip_cekwajar_id/` containing:
- `components/CurrencyInput.tsx` — premium IDR formatter with Rp prefix, check animation, clear button
- `components/PTKPSelector.tsx` — visual PTKP grid selector with TER categories
- `components/MonthPicker.tsx` — 12-month grid picker with December special handling
- `components/VerdictCard.tsx` — full result display with breakdown table, share buttons, regulation sources
- `lib/pph21-ter.ts` — calculation engine (calculateSlip, validateSlipInput, calculateAll, etc.)
- `lib/regulations.ts` — all TER slabs, PTKP values, BPJS constants, verdict thresholds
- `hooks/useAudit.ts` — React hook with loading/error/result state machine
- `app/page.tsx` — landing page
- `app/layout.tsx` — root layout

## Risk Assessment

1. **Two codebases**: The existing `cekwajar.id/` app is the production app. The `slip_cekwajar_id/` reference has the premium components but is a separate project. Must NOT confuse the two.
2. **Existing slip page**: `wajar-slip/page.tsx` exists but uses basic shadcn inputs. Need to understand what the task means by "missing" pieces. Re-reading the task: the task says "Existing: components (CurrencyInput, PTKPSelector, MonthPicker, VerdictCard, Footer), lib/engine (pph21-ter.ts, regulations.ts), hooks (useAudit.ts), landing page, layout — Missing: app/slip/page.tsx" — this suggests I need to BUILD these things in the production app, not just reference the ones in the other project.
3. **The production app may not have these premium components yet** — they're only in the reference project. Need to port or rebuild them.
4. **API route naming mismatch**: The reference uses `/api/slip/audit`, the production app uses `/api/audit-payslip`.

## Approach

Given the task explicitly states CurrencyInput, PTKPSelector, MonthPicker, VerdictCard, Footer, pph21-ter.ts, regulations.ts, useAudit.ts are EXISTING — I should assume they exist in the production app OR I need to copy them there.

Given the production app (`cekwajar.id/`) has `lib/calculations/pph21.ts` but NOT `lib/pph21-ter.ts` (it uses a different structure), and has `src/app/wajar-slip/page.tsx` (already built), the task is likely asking me to:
1. Add the premium components (CurrencyInput, PTKPSelector, MonthPicker, VerdictCard) that are described as "existing but missing from the slip page"
2. Add the `app/api/slip/audit/route.ts` (the reference uses this path, the production app uses `/api/audit-payslip`)
3. Add loading skeleton UI

BUT the production app already has a fully built `wajar-slip/page.tsx`. So either:
A) The task wants me to create `app/slip/page.tsx` (different URL) as the NEW main tool
B) OR the task is slightly inaccurate about what exists

Given "app/slip/page.tsx" vs "app/wajar-slip/page.tsx" — these are different routes. The task says build `app/slip/page.tsx` (THE main tool). This is likely a NEW page at `/slip` that serves as the primary interface, while `/wajar-slip` may be a secondary or renamed route.

**Decision**: The task is clear — build `app/slip/page.tsx`. This is a new route. The existing components and engine code should be copied/created in the production app to support this new page.

Given the production app structure, I need to:
1. Create `app/slip/page.tsx` as the new main salary slip tool
2. Copy or create the premium components (CurrencyInput, PTKPSelector, MonthPicker, VerdictCard)
3. Create `lib/pph21-ter.ts` and `lib/regulations.ts` (the reference versions with the complete calculation engine)
4. Create `hooks/useAudit.ts`
5. Create `app/api/slip/audit/route.ts`
6. Add loading skeleton UI

Let me write the contracts.