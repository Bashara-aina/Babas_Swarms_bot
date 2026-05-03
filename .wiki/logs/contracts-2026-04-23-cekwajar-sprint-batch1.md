---
title: Contracts 2026 04 23 Cekwajar Sprint Batch1
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Execution Order
Serial (must run in sequence): None — all batches are parallel within themselves
Parallel: Batches 1-9 run in parallel (independent files/symbols)
Final gate: Run `npx jest --testPathPattern="audit" --passWithNoTests` to confirm test suite passes after all changes

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Removing `@react-pdf/renderer` breaks a component | Medium | Medium | Grep all imports before removing; keep it if found |
| Dead link removal changes page layout | Low | Low | Landing page cards will just not be clickable |
| aria-live interferes with screen reader flow | Low | Low | Only announce on verdict change, not always |
| Bundle analyzer adds build time | Low | Low | Only run on demand, not part of every build |

---

## BATCH 1 — CRITICAL (Parallel: contracts 1-2)

### CONTRACT #1: Fix broken test import
WHAT: Fix `__tests__/audit.test.ts` — it imports `auditSlip` from `@/lib/slip/audit` which doesn't exist. Either remove the `auditSlip` test cases OR replace with `calculateSlip` from `@/lib/pph21-ter` since auditSlip doesn't exist in the codebase. The test file tests `auditSlip` (lines 379, 401, etc.) but this function doesn't exist in lib/slip/ — the codebase has `calculateSlip` in pph21-ter.ts instead.

FILES:
  READ: __tests__/audit.test.ts
  READ: lib/pph21-ter.ts
  WRITE: __tests__/audit.test.ts

DONE_WHEN:
  - `__tests__/audit.test.ts` no longer imports from non-existent `@/lib/slip/audit`
  - All `auditSlip({...})` calls replaced with equivalent `calculateSlip` calls
  - Test file still covers all 5 critical bug regressions (JP 2026 cap, K/I/0 TER category C, December JKK catch, December clean verdict, K/2 TER category B)
  - `npx jest --testPathPattern="audit" --passWithNoTests` passes with 0 failures

PROOF_FORMAT:
  npx jest --testPathPattern="audit" --passWithNoTests 2>&1 | tail -20

BLOCKER_IF:
  - `calculateSlip` function signature has changed since exploration (verify lib/pph21-ter.ts exports match what test needs)

DEPENDS_ON: none

---

### CONTRACT #2: Create ESLint config
WHAT: Create `.eslintrc.json` for the Next.js project (missing — no `.eslintrc*` files exist)

FILES:
  WRITE: .eslintrc.json

DONE_WHEN:
  - `.eslintrc.json` exists and extends `next/core-web-vitals`
  - `npx next lint` runs without errors on existing code (or only known/acceptable warnings)
  - File is valid JSON

PROOF_FORMAT:
  cat .eslintrc.json

BLOCKER_IF:
  - None (template config, won't break existing code)

DEPENDS_ON: none

---