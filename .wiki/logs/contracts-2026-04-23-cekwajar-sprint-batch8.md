---
title: Contracts 2026 04 23 Cekwajar Sprint Batch8
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## BATCH 8 — PSYCHOLOGY/CONVERSION (Parallel: contracts 29-33)

### CONTRACT #29: Add testimonials section to landing page
WHAT: Add a testimonials section to `app/page.tsx` with 2-3 placeholder testimonials from "anonymous workers" about how the tool helped them find salary discrepancies. Use realistic names and stories in Indonesian.

FILES:
  READ: app/page.tsx
  WRITE: app/page.tsx

DONE_WHEN:
  - Testimonials section exists with at least 2 testimonial cards
  - Each card has a name, job title, and quote
  - Section has appropriate heading

PROOF_FORMAT:
  grep -n "Testimoni\|testimonial" app/page.tsx

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #30: Add trust logos section to landing page
WHAT: Add a "Terverifikasi oleh" (Verified by) section to `app/page.tsx` showing logos or badges for:
- DJP (Direktorat Jenderal Pajak) reference
- BPJS Kesehatan
- PP 44/2015
Use text-based badges since we don't have real logo images.

FILES:
  READ: app/page.tsx
  WRITE: app/page.tsx

DONE_WHEN:
  - Trust badges section exists
  - At least 3 badges showing regulatory references
  - Badges use realistic regulatory references (PMK 168/2023, PP 44/2015, etc.)

PROOF_FORMAT:
  grep -n "Terverifikasi\|BPJS\|DJP\|PMK 168" app/page.tsx | head -10

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #31: Add live counter ("10,000+ slips analyzed") to landing page
WHAT: Add a social proof counter section to `app/page.tsx` showing "10.000+ slip gaji dianalisis" or "1.247 slip dianalisis hari ini". Use realistic numbers. This is a placeholder counter.

FILES:
  READ: app/page.tsx
  WRITE: app/page.tsx

DONE_WHEN:
  - Counter section exists with animated number display
  - Counter text is visible in the hero or trust section
  - Number uses Indonesian number formatting (10.000 not 10,000)

PROOF_FORMAT:
  grep -n "diperiksa\|dianalisis\|counter" app/page.tsx | head -5

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #32: Add viral mechanics explanation
WHAT: Add a brief "bagikan ke teman" (share with friends) section or callout in `app/page.tsx` explaining how sharing helps: "Setiap slip yang dicek = kesadaran yang lebih luas = gerakan #GajiAman". Encourage sharing without being spammy.

FILES:
  READ: app/page.tsx
  WRITE: app/page.tsx

DONE_WHEN:
  - Share call-to-action exists
  - Mentions the hashtag #GajiAman or #CekWajar
  - Explains the viral/awareness value of sharing

PROOF_FORMAT:
  grep -n "bagikan\|#GajiAman\|#CekWajar" app/page.tsx | head -5

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #33: Add email capture for premium features
WHAT: Add an email capture section to `app/page.tsx` for users to sign up for premium features (PDF export, detailed report, etc.). Use a simple email input with "Dapatkan laporan lengkap" CTA. Since there's no backend, create the UI and add a placeholder form handler.

FILES:
  READ: app/page.tsx
  WRITE: app/page.tsx

DONE_WHEN:
  - Email input with label exists in the landing page
  - CTA button says something like "Dapatkan PDF" or "Daftar Premium"
  - Form has proper input type="email" and aria-label
  - Submit shows a placeholder "Segera hadir!" message (no real backend needed)

PROOF_FORMAT:
  grep -n "email\|Dapatkan PDF\|premium" app/page.tsx | head -5

BLOCKER_IF:
  - None

DEPENDS_ON: none

---