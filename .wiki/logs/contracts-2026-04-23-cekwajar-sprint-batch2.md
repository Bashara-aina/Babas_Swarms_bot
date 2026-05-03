---
title: Contracts 2026 04 23 Cekwajar Sprint Batch2
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## BATCH 2 — CRITICAL (Parallel: contracts 3-5)

### CONTRACT #3: Wire or remove useDarkMode hook
WHAT: `useDarkMode` hook exists (hooks/useDarkMode.ts) but has no toggle in the UI — no dark mode button in header or anywhere. Either add a dark mode toggle to the Header component in `app/page.tsx` OR remove the hook file if dark mode isn't part of the design. Decision: Add a minimal sun/moon toggle to the Header nav.

FILES:
  READ: hooks/useDarkMode.ts
  READ: app/page.tsx
  WRITE: app/page.tsx

DONE_WHEN:
  - Header has a dark mode toggle button (sun/moon icon)
  - Toggling updates localStorage and document class
  - No dead code warnings for useDarkMode

PROOF_FORMAT:
  grep -n "dark" app/page.tsx | head -5

BLOCKER_IF:
  - Dark mode is already implemented via a different mechanism (verify first)

DEPENDS_ON: none

---

### CONTRACT #4: Fix dead link cards on landing page
WHAT: The 4 placeholder tool cards (Wajar Gaji, Wajar Tanah, Wajar Kabur, Wajar Hidup) in `app/page.tsx` link to `#` with "Segera hadir" text. Either remove the section OR create stub pages at those routes with "coming soon" content. Decision: Remove the section entirely to reduce confusion — the page currently shows 4 non-functional cards.

FILES:
  READ: app/page.tsx
  WRITE: app/page.tsx

DONE_WHEN:
  - The "Juga tersedia" section with 4 placeholder cards is removed
  - Page still renders without errors
  - No dead `#` links remain in the page

PROOF_FORMAT:
  grep -c 'href="#"' app/page.tsx  # should output 0

BLOCKER_IF:
  - These links are tracked for future implementation (in which case, add a note instead)

DEPENDS_ON: none

---

### CONTRACT #5: Remove NEXT_PUBLIC_JP_CAP_2026_VERIFIED dead code from VerdictCard
WHAT: In `components/VerdictCard.tsx` line 532, there's a conditional block that only renders when `process.env.NEXT_PUBLIC_JP_CAP_2026_VERIFIED !== "true"`. But looking at the code, the cap is now verified (`jp_cap_unverified = false` hardcoded in pph21-ter.ts:310). The conditional render block (lines 532-551) renders an amber warning banner about the 2026 cap being "unverified" — which is now outdated. Remove this conditional block since the cap IS verified per SE BPJS B/1226/022026.

FILES:
  READ: components/VerdictCard.tsx
  WRITE: components/VerdictCard.tsx

DONE_WHEN:
  - The `process.env.NEXT_PUBLIC_JP_CAP_2026_VERIFIED` conditional block (lines 532-551) is removed entirely
  - VerdictCard no longer references `NEXT_PUBLIC_JP_CAP_2026_VERIFIED`
  - Component renders the same as before but without the stale warning

PROOF_FORMAT:
  grep -c "NEXT_PUBLIC_JP_CAP_2026_VERIFIED" components/VerdictCard.tsx  # should output 0

BLOCKER_IF:
  - `jp_cap_unverified` in pph21-ter.ts is still `true` (meaning the cap is NOT verified — verify first)

DEPENDS_ON: none

---