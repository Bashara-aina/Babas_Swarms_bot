---
title: Contracts 2026 04 23 Cekwajar Sprint Batch5
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## BATCH 5 — ACCESSIBILITY (Parallel: contracts 13-18)

### CONTRACT #13: Add aria-live region for dynamic verdict announcement
WHAT: Add an `aria-live="polite"` region in `components/VerdictCard.tsx` that announces the verdict result when it changes, for screen reader users. The verdict (WAJAR/PERLU_DICEK/TIDAK_WAJAR) is the key dynamic announcement.

FILES:
  READ: components/VerdictCard.tsx
  WRITE: components/VerdictCard.tsx

DONE_WHEN:
  - `aria-live="polite"` region exists in VerdictCard
  - It contains the verdict label (e.g., "WAJAR" or "TIDAK WAJAR")
  - Region is visually hidden but accessible

PROOF_FORMAT:
  grep -n "aria-live" components/VerdictCard.tsx

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #14: Add aria-expanded to details/summary accordion (Dasar Hukum)
WHAT: The "Dasar Hukum" section in `components/VerdictCard.tsx` uses a `<details>/<summary>` element (line 502-505). Add `aria-expanded` to the summary element or wrap in a button with proper aria attributes. WCAG requires interactive elements to communicate state.

FILES:
  READ: components/VerdictCard.tsx
  WRITE: components/VerdictCard.tsx

DONE_WHEN:
  - The `<details>` element has an `aria-expanded` attribute on its trigger
  - Or the summary is wrapped in a `<button>` with `aria-expanded` and `aria-controls`
  - Screen reader can determine open/closed state

PROOF_FORMAT:
  grep -n "aria-expanded\|details\|summary" components/VerdictCard.tsx | head -10

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #15: Add aria-current="page" on active nav link
WHAT: In `app/page.tsx` and other pages, the active navigation link should have `aria-current="page"` to indicate which page is currently active. The nav currently has a link to "/slip" — mark it with `aria-current="page"` when on that route.

FILES:
  READ: app/page.tsx
  READ: app/slip/page.tsx
  READ: app/privacy-policy/page.tsx
  WRITE: app/layout.tsx (or relevant nav components)

DONE_WHEN:
  - Navigation links have `aria-current="page"` on the active route
  - Next.js `usePathname()` is used to determine active route

PROOF_FORMAT:
  grep -n "aria-current" app/page.tsx app/slip/page.tsx app/privacy-policy/page.tsx app/layout.tsx 2>/dev/null

BLOCKER_IF:
  - No shared navigation component exists (each page has its own inline nav — add to each page)

DEPENDS_ON: none

---

### CONTRACT #16: Fix color contrast (WCAG 4.5:1 check)
WHAT: Audit and fix color contrast issues in the UI. The most likely issues are:
- Muted text on colored backgrounds may not meet 4.5:1
- Emoji-only status indicators may be problematic
Check Tailwind config and key components. Primary fixes needed in:
- `components/VerdictCard.tsx` — verdict emoji-only rows (✅ 🚫 ⚠️) need text labels for screen readers
- `app/page.tsx` — trust badge text contrast

FILES:
  READ: components/VerdictCard.tsx
  READ: app/globals.css (or tailwind config)
  WRITE: components/VerdictCard.tsx

DONE_WHEN:
  - All emoji status indicators (✅ ⚠️ 🚫) are accompanied by text or `aria-label`
  - `RowStatus` component has text label for each status (not just emoji)
  - `aria-label` or visible text exists for all status indicators

PROOF_FORMAT:
  grep -n "RowStatus\|emoji" components/VerdictCard.tsx | head -10

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #17: Add aria-describedby linking hints to inputs
WHAT: Add `aria-describedby` to all form inputs in `app/slip/page.tsx` and `components/CurrencyInput.tsx` linking them to hint text. WCAG requires form inputs to have associated hints.

FILES:
  READ: app/slip/page.tsx
  READ: components/CurrencyInput.tsx
  WRITE: app/slip/page.tsx
  WRITE: components/CurrencyInput.tsx

DONE_WHEN:
  - Each CurrencyInput with a `hint` prop also has `aria-describedby` linking to the hint element ID
  - The hint element has the corresponding `id` attribute
  - Form fields are properly associated with their help text

PROOF_FORMAT:
  grep -n "aria-describedby" app/slip/page.tsx components/CurrencyInput.tsx | head -10

BLOCKER_IF:
  - CurrencyInput component needs modification to accept and render aria-describedby (check component API)

DEPENDS_ON: none

---

### CONTRACT #18: Add aria-errormessage for form errors
WHAT: Add `aria-errormessage` and `aria-invalid` to form inputs with errors in the slip form. When a field has an error, it should have `aria-invalid="true"` and `aria-errormessage` pointing to the error message element ID.

FILES:
  READ: app/slip/page.tsx
  READ: components/CurrencyInput.tsx
  WRITE: app/slip/page.tsx
  WRITE: components/CurrencyInput.tsx

DONE_WHEN:
  - Inputs with errors have `aria-invalid="true"`
  - Error message elements have unique IDs
  - Inputs with errors have `aria-errormessage` pointing to the error element ID
  - CurrencyInput already has `aria-invalid` — add `aria-errormessage`

PROOF_FORMAT:
  grep -n "aria-errormessage\|aria-invalid" app/slip/page.tsx components/CurrencyInput.tsx | head -10

BLOCKER_IF:
  - CurrencyInput component API doesn't support aria-describedby/aria-errormessage (may need prop extension)

DEPENDS_ON: none

---