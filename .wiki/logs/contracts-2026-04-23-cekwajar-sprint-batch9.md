---
title: Contracts 2026 04 23 Cekwajar Sprint Batch9
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## BATCH 9 — TECHNICAL (Parallel: contracts 34-47)

### CONTRACT #34: Add bundle analyzer
WHAT: Add `@next/bundle-analyzer` to the project and configure it for bundle size analysis. Add a script "analyze" to package.json.

FILES:
  READ: package.json
  WRITE: package.json
  WRITE: next.config.mjs

DONE_WHEN:
  - `@next/bundle-analyzer` is in devDependencies
  - `next.config.mjs` has bundle analyzer configuration
  - `package.json` has `"analyze": "next build && npx @next/bundle-analyzer"`
  - Running `npm run analyze` produces a bundle report

PROOF_FORMAT:
  grep -n "bundle-analyzer\|analyze" package.json next.config.mjs

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #35: Add Core Web Vitals measurement
WHAT: Add a Web Vitals measurement component to `app/layout.tsx` using `next/web-vitals`. This will help track LCP, FID, CLS, FCP, TTFB in production.

FILES:
  READ: app/layout.tsx
  WRITE: app/layout.tsx

DONE_WHEN:
  - Layout imports from `next/web-vitals`
  - `reportWebVitals` function is defined and passed to `<body>`
  - Core Web Vitals are measured (no console.log in production, send to analytics)

PROOF_FORMAT:
  grep -n "web-vitals\|reportWebVitals" app/layout.tsx

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #36: Create OG image for social sharing
WHAT: Create a social sharing OG image for the app. Create `app/opengraph-image.tsx` (Next.js App Router OG image) that generates an OpenGraph image showing the Cek Wajar branding and tagline.

FILES:
  WRITE: app/opengraph-image.tsx

DONE_WHEN:
  - `app/opengraph-image.tsx` exists
  - Uses `next/og` ImageResponse to generate OG image
  - Shows app name and tagline

PROOF_FORMAT:
  ls app/opengraph-image.tsx && head -20 app/opengraph-image.tsx

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #37: Add next.config.mjs optimizations
WHAT: Enhance `next.config.mjs` with compression, security headers, and other optimizations.

FILES:
  READ: next.config.mjs
  WRITE: next.config.mjs

DONE_WHEN:
  - Compression enabled (should already be on by default in Next.js)
  - Security headers added: X-DNS-Prefetch-Control, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
  - `poweredByHeader: false` to remove "Next.js" header
  - File is valid ES module config

PROOF_FORMAT:
  cat next.config.mjs

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #38: Add rate limiting to API route
WHAT: Add rate limiting to `app/api/slip/audit/route.ts` using a simple in-memory rate limiter (e.g., using a Map with IP-based tracking). Limit to 10 requests per minute per IP.

FILES:
  READ: app/api/slip/audit/route.ts
  WRITE: app/api/slip/audit/route.ts

DONE_WHEN:
  - Rate limiting middleware exists in the API route
  - Returns 429 Too Many Requests when limit exceeded
  - Limit is 10 requests per minute per IP

PROOF_FORMAT:
  grep -n "rate\|429\|Too Many" app/api/slip/audit/route.ts | head -5

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #39: Add comprehensive test coverage for TER slabs and edge cases
WHAT: Expand `__tests__/audit.test.ts` with additional test cases for:
- TER slab boundary conditions (exact thresholds)
- PTKP K/I values (K/I/0, K/I/1, K/I/2, K/I/3)
- Edge cases: gross = 0, gross at exact cap values
- BPJS Kesehatan cap boundary

FILES:
  READ: __tests__/audit.test.ts
  WRITE: __tests__/audit.test.ts

DONE_WHEN:
  - Test file has at least 5 new test cases added
  - All new tests pass
  - Tests cover boundary values and K/I PTKP variants

PROOF_FORMAT:
  npx jest --testPathPattern="audit" --passWithNoTests 2>&1 | grep -E "Tests:|Test Suites:" | head -5

BLOCKER_IF:
  - None

DEPENDS_ON: 1

---

### CONTRACT #40: Fix app/icon.svg — change "cj" to "cw" or remove text
WHAT: The `app/icon.svg` contains "cj" text that should be "cw" (for CekWajar) or removed entirely. Fix the SVG.

FILES:
  READ: app/icon.svg
  WRITE: app/icon.svg

DONE_WHEN:
  - "cj" text is replaced with "cw" or removed from icon SVG
  - Icon is still visually clean and recognizable
  - SVG is valid

PROOF_FORMAT:
  grep -c "cj\|cw" app/icon.svg

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #41: Add useReducedMotion to more components
WHAT: `components/VerdictCard.tsx` already uses `useReducedMotion` from framer-motion. Check other components that use framer-motion animations and add `useReducedMotion` hooks where missing. Check: `app/slip/page.tsx`, `components/CurrencyInput.tsx`.

FILES:
  READ: app/slip/page.tsx
  READ: components/CurrencyInput.tsx
  READ: components/MonthPicker.tsx (if it exists)
  WRITE: app/slip/page.tsx

DONE_WHEN:
  - All framer-motion usages in slip page respect `prefersReducedMotion`
  - Animations are disabled or simplified when `useReducedMotion()` returns true

PROOF_FORMAT:
  grep -n "useReducedMotion" app/slip/page.tsx components/CurrencyInput.tsx

BLOCKER_IF:
  - Components don't use framer-motion animations (verify first)

DEPENDS_ON: none

---

### CONTRACT #42: Clean up stale types in types/slip.ts
WHAT: Check `types/slip.ts` (or wherever types are defined) for stale/outdated types. The `AuditInput`, `AuditResult`, `OcrExtractedData`, `SlipGajiInput` types in `hooks/useAudit.ts` are imported from `@/types/slip` but the file may not exist or may have stale definitions. Verify and clean up.

FILES:
  RUN: ls types/slip.ts 2>/dev/null || echo "NOT FOUND"
  READ: types/slip.ts (if exists)
  READ: hooks/useAudit.ts

DONE_WHEN:
  - All types imported in useAudit.ts exist in types/slip.ts
  - No stale/duplicate type definitions
  - Types are consistent with the SlipInput and SlipResult in lib/pph21-ter.ts

PROOF_FORMAT:
  grep -n "from \"@/types/slip\"" hooks/useAudit.ts && ls types/slip.ts 2>&1

BLOCKER_IF:
  - types/slip.ts doesn't exist — create it with required type exports

DEPENDS_ON: none

---

### CONTRACT #43: Add loading skeleton for initial page load
WHAT: Add a loading skeleton to `app/slip/page.tsx` for when the page first loads before the form is ready. Use `@/components/ui/skeleton` or a simple CSS skeleton. Show skeleton for the form fields.

FILES:
  READ: app/slip/page.tsx
  WRITE: app/slip/page.tsx

DONE_WHEN:
  - `app/slip/loading.tsx` exists with skeleton UI
  - Skeleton shows placeholder for form fields
  - Loading.tsx uses Next.js loading conventions

PROOF_FORMAT:
  ls app/slip/loading.tsx && head -20 app/slip/loading.tsx

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #44: Optimize bundle size — remove unused deps
WHAT: Remove unused dependencies from `package.json` that add bloat: `@react-pdf/renderer` (PDF generation, not used), `groq-sdk` (not used), `openai` (not used), `axios` (fetch is used instead). Verify each is unused before removal.

FILES:
  RUN: grep -r "@react-pdf/renderer\|groq-sdk\|openai\|axios" --include="*.ts" --include="*.tsx" . 2>/dev/null | grep -v node_modules | grep -v ".next"
  READ: package.json
  WRITE: package.json

DONE_WHEN:
  - `@react-pdf/renderer`, `groq-sdk`, `openai`, `axios` are removed from package.json dependencies
  - No import statements reference these packages in any .ts/.tsx file
  - `package-lock.json` is updated (or note added to NOT update — just remove from package.json)

PROOF_FORMAT:
  grep -r "@react-pdf/renderer\|groq-sdk\|openai\|axios" --include="*.ts" --include="*.tsx" . 2>/dev/null | grep -v node_modules | grep -v ".next" | wc -l  # should be 0

BLOCKER_IF:
  - Any of these packages are actually imported somewhere — verify with grep before removing

DEPENDS_ON: none

---

### CONTRACT #45: Verify PTKP K/I values in regulations.ts
WHAT: Verify that PTKP K/I values (K/I/0, K/I/1, K/I/2, K/I/3) in `lib/regulations.ts` match the official 2024/2025 PTKP table from DJP. The PTKP selector UI supports K/I status. Check if the values are correct and the TER category mapping for K/I is correct (should be TER C based on test case).

FILES:
  READ: lib/regulations.ts
  RUN: grep -n "PTKP\|K/I\|TER_CATEGORY\|ptkp_status" lib/regulations.ts | head -30

DONE_WHEN:
  - K/I/0, K/I/1, K/I/2, K/I/3 are defined in PTKP object
  - TER_CATEGORY maps K/I/* to "C" (or correct category)
  - Values match official DJP PTKP table

PROOF_FORMAT:
  grep -n "K/I" lib/regulations.ts | head -10

BLOCKER_IF:
  - PTKP values don't match official table — flag for user review

DEPENDS_ON: none

---

### CONTRACT #46: Set up privacy email note
WHAT: The privacy policy references `privacy@cekwajar.id` but it's not verified. Add a note to the privacy policy page (or a comment) indicating this is a placeholder email. Since no actual email is set up, add a note: "(email ini belum dikonfigurasi — hubungi pengembang)"

FILES:
  READ: app/privacy-policy/page.tsx
  WRITE: app/privacy-policy/page.tsx

DONE_WHEN:
  - Email in privacy policy has a clarifying note about configuration status
  - Or remove email from display and replace with a note

PROOF_FORMAT:
  grep -n "privacy@\|email" app/privacy-policy/page.tsx | head -5

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #47: Final test suite verification
WHAT: Run the full test suite after all changes to confirm nothing is broken.

FILES:
  RUN: npx jest --passWithNoTests 2>&1

DONE_WHEN:
  - All tests pass (0 failures)
  - No TypeScript errors (run `npx tsc --noEmit` first)
  - ESLint passes (run `npx next lint`)

PROOF_FORMAT:
  npx jest --passWithNoTests 2>&1 | tail -10
  npx tsc --noEmit 2>&1 | tail -10

BLOCKER_IF:
  - Test failures occur — investigate before completing

DEPENDS_ON: 1, 9, 39, 44

---