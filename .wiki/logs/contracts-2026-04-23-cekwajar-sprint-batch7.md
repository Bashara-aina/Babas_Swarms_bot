---
title: Contracts 2026 04 23 Cekwajar Sprint Batch7
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## BATCH 7 — COPY & UX (Parallel: contracts 23-28)

### CONTRACT #23: Fix emoji inconsistency in UI
WHAT: Audit all emoji usage across the codebase and make them consistent. Some places use emoji as decorative icons (⚠️ 🚫 ✅), some places use text. Ensure emoji are either accompanied by text labels for accessibility OR are purely decorative with `aria-hidden="true"`. Check: VerdictCard (RowStatus), breakdown table headers, explanation cards.

FILES:
  READ: components/VerdictCard.tsx
  READ: app/slip/page.tsx
  RUN: grep -rn "🚫\|⚠️\|✅\|❌\|📋\|ℹ️\|⚠️" --include="*.tsx" --include="*.ts" . 2>/dev/null | grep -v node_modules | grep -v ".next" | head -30

DONE_WHEN:
  - All emoji-only status indicators have accompanying text labels
  - All decorative-only emoji have `aria-hidden="true"`
  - No status information conveyed by emoji alone without text

PROOF_FORMAT:
  grep -rn "🚫\|⚠️\|✅\|❌" --include="*.tsx" . 2>/dev/null | grep -v node_modules | grep -v ".next" | head -20

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #24: Fix grammar in privacy policy ("Kami encourages Anda")
WHAT: Fix the grammatical error in `app/privacy-policy/page.tsx` line 148: "Kami encourages Anda" should be "Kami mendorong Anda" or "Kami mendesak Anda". Also check line 106 "jika ada" should likely be "jika ada" (fine), and line 151 "stated berbeda" should be "dinyatakan berbeda".

FILES:
  READ: app/privacy-policy/page.tsx
  WRITE: app/privacy-policy/page.tsx

DONE_WHEN:
  - "Kami encourages" → "Kami mendorong"
  - "stated berbeda" → "dinyatakan berbeda"
  - No other obvious grammar errors in Indonesian text

PROOF_FORMAT:
  grep -n "encourages\|stated" app/privacy-policy/page.tsx  # should return nothing

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #25: Add success confirmation message after form submit
WHAT: Add a success confirmation message in `app/slip/page.tsx` after the audit form is successfully submitted. When the user submits the form and results appear, show a brief success toast or inline message like "Slip gaji berhasil dianalisis!"

FILES:
  READ: app/slip/page.tsx
  WRITE: app/slip/page.tsx

DONE_WHEN:
  - Success message appears after successful form submission
  - Message uses aria-live for screen reader announcement
  - Message auto-dismisses after 3 seconds

PROOF_FORMAT:
  grep -n "berhasil\|success\|toast" app/slip/page.tsx | head -5

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #26: Add FAQ section to landing page
WHAT: Add an FAQ section to `app/page.tsx` with 3-4 common questions about the service: "Apakah data slip saya disimpan?", "Bagaimana cara kerja TER?", "Apakah gratis?"

FILES:
  READ: app/page.tsx
  WRITE: app/page.tsx

DONE_WHEN:
  - FAQ section exists with at least 3 questions
  - Questions use proper semantic HTML (details/summary accordion)
  - Section is visually separated from other content

PROOF_FORMAT:
  grep -n "FAQ\|Pertanyaan" app/page.tsx

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #27: Add "how it works" section to landing page
WHAT: Add a "how it works" (Cara Kerja) section to `app/page.tsx` with 3 steps: 1) Masukkan data slip, 2) AI menganalisis, 3) Lihat hasilnya.

FILES:
  READ: app/page.tsx
  WRITE: app/page.tsx

DONE_WHEN:
  - "Cara Kerja" section exists with 3 numbered steps
  - Steps use icons and brief descriptions
  - Visually distinct from other sections

PROOF_FORMAT:
  grep -n "Cara Kerja\|Langkah\|Step" app/page.tsx

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #28: Replace "gue" with "saya" in share text
WHAT: Fix Indonesian informality issue in `components/VerdictCard.tsx` share text (lines 117, 141). The share text uses "gue" (Jakarta slang) which is not national. Replace with "saya" for broader national appeal. Also "lo" → "Anda", "punya lo" → "milik Anda".

FILES:
  READ: components/VerdictCard.tsx
  WRITE: components/VerdictCard.tsx

DONE_WHEN:
  - "gue" replaced with "saya" everywhere
  - "lo" replaced with "Anda" everywhere
  - Share text reads naturally for all Indonesian speakers

PROOF_FORMAT:
  grep -n "gue\|lo\b" components/VerdictCard.tsx  # should return nothing

BLOCKER_IF:
  - None

DEPENDS_ON: none

---