---
title: Planner 2026 04 25 Cekwajar Improvements
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Plan: cekwajar.id Platform Improvements
Date: 2026-04-25
Type: FEATURE

Context gathered:
- PPh21 route.ts calls FastAPI at localhost:4000 (BROKEN, no FastAPI exists)
- calculators.ts: TER tables have only 8 rows per status — PMK 168/2023 Tabel A for TK/0 has 32+ rows
- violations.ts: V01-V07 detection functions exist but NOT connected to slip page API or UI
- salary-benchmark route: queries Supabase for gross_p50/p75/p90 but schema has p50_idr (field name mismatch)
- property route: queries land_prices correctly with price_per_m2
- gaji + tanah pages: API wired correctly but DB has no seed data
- FreemiumGate.tsx: Pure UI stub — button does nothing, no auth/tier checking
- ResultCard accepts violations prop with severity field matching violations.ts

Approach:
- Contract 1: Fix slip page — replace FastAPI call with local TypeScript calculation (calculators.ts + violations.ts) in route.ts
- Contract 2: Expand TER tables to full PMK 168/2023 (32-row Tabel A for TK/0 at minimum)
- Contract 3: Seed Supabase with realistic minimal data for gaji and tanah
- Contract 4: Make FreemiumGate functional with Supabase auth
- Contract 5: Fix salary-benchmark field name mismatch (gross_p50 vs p50_idr)

Risk assessment:
- Contract 1 (route rewrite): Risk of regression — old tests mock FastAPI response; new tests must call calculators.ts directly. Need to update test file.
- Contract 2 (TER expansion): Safe addition — existing 8-row tables are a subset; backward-compatible.
- Contract 3 (seed data): DB schema is already defined; safe to insert seed rows.
- Contract 4 (FreemiumGate): Requires Supabase client-side auth setup; could conflict with existing auth if any.
- Contract 5 (field names): Quick fix — salary-benchmark route uses wrong column names; needs update.

## Execution Order
Serial: Contract 1 → Contract 2 → Contract 5 → Contract 3 → Contract 4
Parallel: none (sequential dependencies)
Final gate: Contract 4 (FreemiumGate, most complex)

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| FastAPI removal breaks existing tests | H | H | Update route.test.ts to test calculators.ts directly |
| TER expansion changes existing calculation results | M | M | New rows are for higher salary ranges; existing tests should pass |
| Seed data SQL syntax errors | L | M | Test INSERTs in Supabase SQL editor first |
| FreemiumGate conflicts with existing auth | M | M | Check if any existing auth setup before implementing |
| Field name mismatch causes silent failures | H | H | Contract 5 is quick fix; verify with gitnexus_detect_changes after |
