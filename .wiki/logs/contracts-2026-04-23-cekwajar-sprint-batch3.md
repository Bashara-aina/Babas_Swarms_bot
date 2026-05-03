---
title: Contracts 2026 04 23 Cekwajar Sprint Batch3
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## BATCH 3 — MAJOR (Parallel: contracts 6-8)

### CONTRACT #6: Fix CurrencyInput clear button touch target (WCAG 44px minimum)
WHAT: In `components/CurrencyInput.tsx` line 164, the clear button has `className="flex h-6 w-6 items-center justify-center rounded-full ..."` which is 24px × 24px. WCAG accessibility requires touch targets to be at least 44px × 44px. Change `h-6 w-6` to `h-11 w-11` (44px) and adjust padding accordingly.

FILES:
  READ: components/CurrencyInput.tsx
  WRITE: components/CurrencyInput.tsx

DONE_WHEN:
  - Clear button has `h-11 w-11` (not `h-6 w-6`)
  - Button is visually centered and properly styled
  - Aria-label "Hapus nilai" is preserved

PROOF_FORMAT:
  grep -n "h-11 w-11\|h-6 w-6" components/CurrencyInput.tsx

BLOCKER_IF:
  - None (clear improvement)

DEPENDS_ON: none

---

### CONTRACT #7: Create sitemap.xml for SEO
WHAT: Create `app/sitemap.ts` (Next.js App Router sitemap) to improve SEO crawling.

FILES:
  WRITE: app/sitemap.ts

DONE_WHEN:
  - `app/sitemap.ts` exports a `sitemap` object
  - Sitemap includes /slip, /privacy-policy routes
  - Sitemap is valid TypeScript

PROOF_FORMAT:
  ls app/sitemap.ts && head -20 app/sitemap.ts

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #8: Create robots.txt for SEO
WHAT: Create `app/robots.ts` (Next.js App Router robots.txt) to allow crawling of main routes.

FILES:
  WRITE: app/robots.ts

DONE_WHEN:
  - `app/robots.ts` exports a `robots` object
  - robots.txt allows all crawlers access to /slip and /privacy-policy
  - Disallows /api routes

PROOF_FORMAT:
  ls app/robots.ts && head -20 app/robots.ts

BLOCKER_IF:
  - None

DEPENDS_ON: none

---