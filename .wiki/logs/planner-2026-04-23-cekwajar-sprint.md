---
title: Planner 2026 04 23 Cekwajar Sprint
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Plan: cekwajar.id Exhaustive Improvement Sprint
Date: 2026-04-23
Type: FEATURE
Context gathered:
- 47 issues across 8 dimensions identified in exploration
- Project is Next.js 14 App Router with TypeScript, Tailwind, shadcn/ui
- Test file `__tests__/audit.test.ts` imports non-existent `@/lib/slip/audit` (should be `calculateSlip` from `@/lib/pph21-ter`)
- No ESLint config exists
- Dead code: `useDarkMode` (no UI toggle), `usePayment` (references `/api/payment/create-transaction` that doesn't exist), `useAudit` (slip page uses local useState instead)
- `NEXT_PUBLIC_JP_CAP_2026_VERIFIED` in VerdictCard is dead (hardcoded to `false` now that cap is verified)
- `CurrencyInput` clear button is 24px (WCAG requires ≥44px)
- Missing: sitemap.xml, robots.txt, manifest.json
- Privacy policy has grammar error ("Kami encourages Anda")
- Share text uses "gue" instead of national "saya"
- 4 placeholder tool cards on landing page link to `#`
- Unused deps: `@react-pdf/renderer`, `groq-sdk`, `openai`, `axios`
- next.config.mjs is empty (no compression, no security headers)
- app/icon.svg has "cj" text that should be "cw" or removed

Risk assessment:
- Editing the test file requires creating stub `auditSlip` OR removing test cases that test `auditSlip` (since `auditSlip` doesn't exist in the codebase)
- Removing unused deps could break things if they're actually imported somewhere
- Accessibility fixes (aria attributes) are low-risk HTML changes
- Privacy policy grammar fix is straightforward

Approach:
- Batch 1 (Critical): Fix test import + ESLint config (parallel)
- Batch 2 (Critical): Remove dead code (useDarkMode wiring OR removal, NEXT_PUBLIC_JP_CAP_2026_VERIFIED, dead links)
- Batch 3 (Major): Touch target fix + SEO files (parallel)
- Batch 4 (Major): Dead hooks removal (usePayment, useAudit wiring or removal)
- Batch 5 (Accessibility): aria-live, aria-expanded, aria-current, aria-describedby, aria-errormessage
- Batch 6 (Mobile): Collapsible VerdictCard sections, responsive font scaling, PTKP grid fix, overflow-x-auto
- Batch 7 (Copy/UX): Grammar fix, emoji consistency, success message, FAQ, how-it-works
- Batch 8 (Psychology): Testimonials, trust logos, live counter, viral mechanics, email capture
- Batch 9 (Technical): Bundle analyzer, Core Web Vitals, OG image, next.config optimizations, rate limiting, test coverage, icon.svg, useReducedMotion, stale types, loading skeleton, bundle optimization

Total contracts: 47 issues → ~40 contracts (some grouped)