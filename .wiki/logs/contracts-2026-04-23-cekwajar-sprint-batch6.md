---
title: Contracts 2026 04 23 Cekwajar Sprint Batch6
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## BATCH 6 — MOBILE (Parallel: contracts 19-22)

### CONTRACT #19: Make VerdictCard sections collapsible on mobile
WHAT: In `components/VerdictCard.tsx`, the breakdown table and Dasar Hukum sections should be collapsible on mobile to reduce scrolling. Add a "show more/less" toggle for mobile (≤640px) for the breakdown table and the regulation sources.

FILES:
  READ: components/VerdictCard.tsx
  WRITE: components/VerdictCard.tsx

DONE_WHEN:
  - Breakdown table has a mobile-only collapse toggle
  - "Rincian Komponen" section is collapsed by default on mobile
  - Smooth expand/collapse animation
  - `overflow-hidden` properly hides collapsed content

PROOF_FORMAT:
  grep -n "collaps\|mobile\|sm:" components/VerdictCard.tsx | head -10

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #20: Add responsive font scaling for mobile
WHAT: Add responsive font sizing utilities. Check if Tailwind config already has responsive text sizes — if not, ensure text elements in `app/page.tsx`, `components/VerdictCard.tsx` use `text-base sm:text-lg` patterns for better mobile readability.

FILES:
  READ: app/globals.css
  READ: tailwind.config.js (or tailwind.config.ts if it exists)
  WRITE: tailwind.config.js

DONE_WHEN:
  - Heading fonts scale appropriately on mobile vs desktop
  - No text is too small on mobile (minimum 14px for body text)
  - Check: grep -n "text-xs\|text-sm" in components | check if any are not responsive

PROOF_FORMAT:
  ls tailwind.config.* && head -30 tailwind.config.*

BLOCKER_IF:
  - No tailwind config found (use default)

DEPENDS_ON: none

---

### CONTRACT #21: Fix PTKP grid on mobile (8 items = 4 rows of tall cards)
WHAT: In `components/PTKPSelector.tsx`, the 8 PTKP status options (TK/0-3, K/0-3, K/I/0-3) are displayed in a grid. On mobile, each card may be too tall. Make the grid responsive — 1 column on mobile, 2 on tablet, 4 on desktop. Also reduce card height.

FILES:
  READ: components/PTKPSelector.tsx
  WRITE: components/PTKPSelector.tsx

DONE_WHEN:
  - PTKP grid uses `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`
  - Cards are not excessively tall on mobile
  - Horizontal scroll is avoided

PROOF_FORMAT:
  grep -n "grid-cols\|grid-cols-1\|grid-cols-2" components/PTKPSelector.tsx

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #22: Add overflow-x-auto to breakdown table
WHAT: In `components/VerdictCard.tsx`, the breakdown table (`role="table"`) may overflow horizontally on small screens. Add `overflow-x-auto` to prevent horizontal scroll on the page while allowing the table itself to scroll.

FILES:
  READ: components/VerdictCard.tsx
  WRITE: components/VerdictCard.tsx

DONE_WHEN:
  - The breakdown table container has `overflow-x-auto`
  - Table doesn't cause page-level horizontal scroll

PROOF_FORMAT:
  grep -n "overflow-x-auto\|overflow-x" components/VerdictCard.tsx

BLOCKER_IF:
  - None

DEPENDS_ON: none

---