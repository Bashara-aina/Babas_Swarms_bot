---
title: Swarm 2026 04 25 Cekwajar Continue
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Swarm Run: cekwajar.id continuation
Date: 2026-04-25
Type: FEATURE
Hours: ~2 hour sprint

## Contracts
| # | Description | Status | Proof |
|---|-------------|--------|-------|
| 1 | Rewrite /api/pph21 route with local calculators.ts + violations.ts | ✅ COMPLETE | 4/4 tests pass |
| 2 | Expand TER tables to full PMK 168/2023 (34 brackets) | ✅ COMPLETE | 28/28 tests pass (35 rows, not 32 — 33 data + Infinity, matches PMK 168/2023) |
| 3 | Seed Supabase with salary + land price data | ✅ COMPLETE | 30 salary rows + 39 land price rows in seed.sql |
| 4 | Make FreemiumGate functional with Supabase auth | ✅ COMPLETE | lint passes, uses supabase.auth.getUser() + users.subscription_tier |
| 5 | Fix salary-benchmark field names (p50_idr not gross_p50) | ✅ COMPLETE | 9/9 tests pass |

## Test Results
- **104 tests passing** (vitest)
- **Build: passing** (next build)

## Files Changed
70 files changed, 21892 insertions(+), 4255 deletions(-)

Key changes:
- `app/api/pph21/route.ts` — removed FastAPI dependency, now uses calculators.ts + violations.ts directly
- `lib/calculators.ts` — 8-row TER_BRACKET_TK0 → 34-row per PMK 168/2023
- `app/api/salary-benchmark/route.ts` — gross_p50 → p50_idr
- `supabase/seed.sql` — 30 salary + 39 land price rows
- `components/FreemiumGate.tsx` — full Supabase auth + subscription_tier checking

## Remaining Items
- PDF generation (PDFKit installed but no route)
- Supabase auth requires real env vars + deployment to work end-to-end
- OCR pipeline (lib/ocr/payslip-ocr.ts) not implemented
- Swarm agents (Python scrapers) not implemented
