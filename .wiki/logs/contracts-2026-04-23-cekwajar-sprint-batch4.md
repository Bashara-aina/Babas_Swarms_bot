---
title: Contracts 2026 04 23 Cekwajar Sprint Batch4
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## BATCH 4 — MAJOR (Parallel: contracts 9-12)

### CONTRACT #9: Remove dead usePayment hook
WHAT: `hooks/usePayment.ts` references `/api/payment/create-transaction` which doesn't exist. The hook is not imported anywhere in the codebase. Remove the file entirely.

FILES:
  READ: hooks/usePayment.ts
  WRITE: (delete hooks/usePayment.ts)

DONE_WHEN:
  - `hooks/usePayment.ts` is deleted
  - No imports of `usePayment` remain in any file: `grep -r "usePayment" --include="*.ts" --include="*.tsx" . | grep -v node_modules | grep -v ".next"`

PROOF_FORMAT:
  ls hooks/usePayment.ts 2>&1  # should output "No such file or directory"
  grep -r "usePayment" --include="*.ts" --include="*.tsx" . 2>/dev/null | grep -v node_modules | grep -v ".next" | wc -l  # should be 0

BLOCKER_IF:
  - `usePayment` is imported somewhere — verify before deleting

DEPENDS_ON: none

---

### CONTRACT #10: Remove dead NEXT_PUBLIC_MIDTRANS_CLIENT_KEY usage
WHAT: `NEXT_PUBLIC_MIDTRANS_CLIENT_KEY` is referenced in `hooks/usePayment.ts` (which is being deleted) but also referenced elsewhere. After removing usePayment, verify no other files reference this env var. If not referenced anywhere, remove the env var reference note from documentation. Also check if the app uses it anywhere else.

FILES:
  READ: hooks/usePayment.ts
  READ: app/slip/page.tsx
  RUN: grep -r "MIDTRANS" --include="*.ts" --include="*.tsx" . 2>/dev/null | grep -v node_modules | grep -v ".next"

DONE_WHEN:
  - No file references `MIDTRANS_CLIENT_KEY` or `MIDTRANS_SANDBOX` (after usePayment removal)
  - No dead env var references remain

PROOF_FORMAT:
  grep -r "MIDTRANS" --include="*.ts" --include="*.tsx" . 2>/dev/null | grep -v node_modules | grep -v ".next" | wc -l  # should be 0

BLOCKER_IF:
  - MIDTRANS is referenced elsewhere — investigate before proceeding

DEPENDS_ON: 9

---

### CONTRACT #11: Wire or remove useAudit hook — wire it to slip page
WHAT: `hooks/useAudit.ts` has `activeTab` and `ocrDraft` state but `app/slip/page.tsx` uses local `useState` instead of this hook. Wire the slip page to use `useAudit` hook so there's a single source of truth for the audit state.

FILES:
  READ: hooks/useAudit.ts
  READ: app/slip/page.tsx
  WRITE: app/slip/page.tsx

DONE_WHEN:
  - `app/slip/page.tsx` imports and uses `useAudit` from `@/hooks/useAudit`
  - `activeTab` and `ocrDraft` from the hook are used in the page (or confirmed not needed and removed from hook)
  - No duplicate state management for audit data in the page

PROOF_FORMAT:
  grep -n "useAudit" app/slip/page.tsx

BLOCKER_IF:
  - `useAudit` hook API doesn't match what slip page needs (verify hook exports match page requirements)

DEPENDS_ON: none

---

### CONTRACT #12: Create manifest.json for PWA
WHAT: Create `app/manifest.ts` (Next.js App Router PWA manifest) to enable PWA installation.

FILES:
  WRITE: app/manifest.ts

DONE_WHEN:
  - `app/manifest.ts` exports a valid PWA manifest
  - Manifest includes name "Cek Wajar", short_name "CekWajar", theme_color, icons
  - File is valid TypeScript

PROOF_FORMAT:
  ls app/manifest.ts && head -30 app/manifest.ts

BLOCKER_IF:
  - None

DEPENDS_ON: none

---