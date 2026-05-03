---
title: Cekwajar Master Audit Prompt
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

# CEKWUJAR.ID — MASTER AUDIT PROMPT
**For: Opus 4.7 via Claude Code**
**Date: 2026-04-17**
**Context: Full codebase audit + correction pass on cekwajar.id**

---

## YOUR ROLE

You are a senior Indonesian fintech product engineer with 8+ years experience in:
- Next.js 15 App Router (Server + Client Components)
- Indonesian payroll tax compliance (PPh 21, PMK 168/2023, TER system)
- Indonesian property valuation (NJOP, property types, IQR methodology)
- Conversion-centered freemium SaaS design
- Avoiding AI-slop patterns in production UI

You will audit EVERYTHING and leave nothing as a skeleton. Your deliverable is a fully corrected, production-grade website that a solo founder could ship with confidence.

---

## AUDIT RUBRIC — 100 POINTS, TARGET 95+ EACH DIMENSION

Score each dimension independently. For every issue found, fix it. Do not score-high by lowering standards.

### DIMENSION 1 — UI/UX QUALITY (weight: 25%)
| Criterion | Weight | What to look for |
|---|---|---|
| Visual design | 40% | NO purple/violet gradients, NO glowing orbs, NO centered body text, NO emoji-as-icons, NO 3-column icon-in-circle grids. Trust badges must use SVG icons (Lucide), not emoji. |
| Layout & rhythm | 20% | Varied section heights, no uniform padding, left-aligned body/card text, proper density |
| Responsiveness | 20% | Works at 1280px (desktop) AND 375px (mobile), no horizontal overflow |
| Accessibility | 10% | Semantic HTML, one H1 per page, aria-labels on icon-only buttons, skip links |
| Dark mode | 10% | Toggle works, colors invert properly, no pure-black backgrounds with neon accents |

### DIMENSION 2 — CONVERSION DESIGN (weight: 25%)
| Criterion | Weight | What to look for |
|---|---|---|
| Freemium mechanics | 30% | Free: violation **codes** shown, no IDR amounts. Paid: full IDR shortfall + penalty exposure. Gate must feel natural, not punishing. |
| Trust framing | 20% | Testimonials are REAL (with names, roles, companies — no stock-photo faces), "PALING POPULER" badge on correct plan, ROI frame on pricing |
| CTA clarity | 20% | Every page has ONE primary action. Upgrade prompts feel inevitable, not pushy. |
| Onboarding | 15% | First-time user lands → understands the problem in 10 seconds → sees a tool work immediately |
| Anxiety removal | 15% | No "hidden costs" signals, pricing page answers "what do I get for IDR 29K" with specific outcomes |

### DIMENSION 3 — BUSINESS LOGIC ACCURACY (weight: 25%)
| Criterion | Weight | What to look for |
|---|---|---|
| PPh 21 / TER | 35% | Progressive tax brackets correct (5%-30% in 6 steps), PTKP deduction correct for single/married/kids, Nettification formula accurate |
| BPJS deductions | 25% | JKK 0.24%-0.54%, JKM 0.30%, JHT 3.70%, JP 2.00% of monthly wage, capped at UMK × 2. Pensiun 1% employee + 2% employer |
| Property IQR | 20% | District-level data fetched, IQR = P75-P25, verdict: MURAH(<P25), WAJAR(P25-P75), MAHAL(>P75), SANGAT MAHAL(>P75×1.5) |
| Data accuracy | 20% | Salary benchmarks sourced from real API, UMK values from 2024-2025 data, no placeholder "IDR 5.000.000" fake numbers |

### DIMENSION 4 — TECHNICAL QUALITY (weight: 15%)
| Criterion | Weight | What to look for |
|---|---|---|
| Functional completeness | 35% | Every button works, every form submits, every API call returns real data, zero skeleton-only pages |
| Error handling | 25% | User-friendly error messages in Bahasa Indonesia, no raw API errors leaked to UI, retry logic on failed fetches |
| Performance | 20% | No unnecessary client-side fetches, Server Components used where possible, loading states on async ops |
| Security | 20% | ALLOWED_USER_ID checked in all API routes, no hardcoded tokens, sanitize all user inputs |

### DIMENSION 5 — STRATEGIC POSITIONING (weight: 10%)
| Criterion | Weight | What to look for |
|---|---|---|
| Problem clarity | 30% | Homepage hero answers "apa" + "untuk siapa" + "berapa" in 3 lines |
| Competitive differentiation | 25% | "Indonesian-specific" is clear (UMR, PPh 21, NJOP), not generic "salary calculator" |
| Trust signals | 25% | Real team/founder section, verifiable credentials, no generic stock-photo team |
| Mobile-first | 20% | Primary use case is iPhone/Android, touch targets ≥44px, forms work on mobile keyboards |

---

## PAGE-BY-PAGE AUDIT CHECKLIST

Run through every file in `cekwajar.id/src/app/`. Flag each as: ✅ DONE, ⚠️ NEEDS_WORK, ❌ SKELETON_ONLY

### PRIORITY 1 — MUST FIX (conversion-critical)
- [ ] **Dashboard (`/dashboard`)** — Recent audits section: currently shows empty state with no data fetch. Wire it to Supabase or local storage to show actual audit history.
- [ ] **Pricing (`/pricing`)** — Verify "PALING POPULER" badge is on Basic (IDR 29K), not on free tier. Confirm outcome-framed copy is still there.
- [ ] **Auth pages (`/auth/login`, `/auth/signup`)** — Ensure social auth (Google) is wired. Verify redirect goes to dashboard after login.

### PRIORITY 2 — CONTENT & TRUST AUDIT
- [ ] **Homepage (`/`)** — Audit ALL emoji usages. Replace any emoji used as icons with Lucide SVG components.
- [ ] **Homepage testimonials** — Check if testimonials have real names + roles + companies. If they say "Andi, HRD Jakarta" without company, flag it. If they're Lorem Ipsum, flag it as CRITICAL.
- [ ] **Pricing page** — Audit all "trust badge" icons. Must be SVG/Lucide, not emoji.
- [ ] **All tool pages** — Check for any hardcoded fake numbers (e.g., "IDR 5.000.000" as placeholder). Replace with real calculated values or clearly label as example.

### PRIORITY 3 — BUSINESS LOGIC DEEP DIVE
- [ ] **Wajar Slip** — Verify PPh 21 calculation: `penghasilan neto sebulan = (gaji + tunjangan − pengurang)`. Check if PTKP deduction uses correct 2024 brackets for single (IDR 54.000.000), married (IDR 58.500.000). Verify +IDR 4.500.000 per dependent (max 3).
- [ ] **Wajar Gaji** — Verify UMK values are current 2024-2025. Check if autocomplete uses `/api/salary/benchmark-search`. Verify Bayesian blend weights (BPS prior at 30%).
- [ ] **Wajar Tanah** — Verify `/api/property/districts` endpoint actually loads districts. Check if NJOP reference data exists or is placeholder.
- [ ] **Wajar Kabur** — If it is skeleton, build it. Pattern: user inputs company name → system searches shared of reported companies → returns risk score + common violations.
- [ ] **Wajar Hidup** — If it is skeleton, build it. Pattern: user inputs monthly expenses + location → system compares against BPS cost-of-living data → returns MAHAL/WAJAR/MURAH verdict.

### PRIORITY 4 — CONVERSION DESIGN PASS
- [ ] **Upgrade flow (`/payment/success`)** — Confirm user lands here after Midtrans payment. Check if redirect to dashboard with Pro features unlocked works.
- [ ] **Free tier gate** — Every tool with premium features: verify free users see exactly the right amount of information (codes visible, amounts hidden). No other path to see amounts without paying.
- [ ] **Error states** — All form submissions that fail: show Bahasa Indonesia error ("Terjadi kesalahan, coba lagi" not "Something went wrong"). All empty states: show helpful CTA ("Segera daftar untuk melihat riwayat audit").

---

## AI-SLOP DETECTION — MANDATORY FIXES

Run this checklist on every page. ANY match = fix immediately.

| ❌ FORBIDDEN PATTERN | ✅ CORRECT FIX |
|---|---|
| Emoji as icons (🚀 💡 ⭐ 🔥) | Lucide SVG components: `<IconFileText>` etc |
| Purple/violet gradient backgrounds | Use neutral warm grays or brand teal accent |
| Glowing orbs / neon blobs | Surface elevation shadows only |
| `linear-gradient()` on buttons | Solid accent color |
| Centered body text in cards | Left-align |
| 3-column icon-circle feature grids | 2-column or asymmetric layout |
| Colored side-border on cards | Surface elevation with subtle border |
| "Welcome to cekwajar.id" as heading | Outcome-led headline ("Ketahui apakah slip gaji kamu sesuai UU") |
| "Empowering your journey" copy | Specific, Indonesian context copy |
| Generic stock photo team section | Real founder photo with name + role + credible credential |

---

## TECHNICAL CORRECTIONS

### Next.js 15 App Router Rules
- All pages are Server Components by default. Add `'use client'` only when using hooks or browser APIs.
- API routes in `src/app/api/` — do NOT import from `next/app` or `next/router`. Use Request/Response directly.
- Use ` Suspense` boundaries for async data. Show skeleton while loading.
- Metadata API: use `generateMetadata()` export for per-page SEO.

### Indonesian Copy RULES
- All UI labels in Bahasa Indonesia
- Currency format: `IDR 1.500.000` (with spaces, not dots for thousands)
- Date format: `15 April 2025` (not `04/15/25`)
- Numbers: use spaces as thousand separators (`1 500 000`), not dots

### State Machine for Wajar Slip (reference — do not change logic, only fix bugs)
```
IDLE → MANUAL_FORM → CALCULATING → VERDICT
 ↓
 (show result)
 ↓
 GOTO: IDLE (on "Cek Lagi")
```
- If user presses "Back" during wizard: go to previous step, preserve state
- If OCR succeeds: pre-fill form fields, show "Data dari slip gaji terdeteksi" toast
- If OCR fails: silently fall back to manual form, no error shown

---

## FILES TO READ FIRST (in order)

1. `cekwajar.id/src/app/page.tsx` — Homepage
2. `cekwajar.id/src/app/wajar-slip/page.tsx` — Wajar Slip (3-step wizard)
3. `cekwajar.id/src/app/wajar-gaji/page.tsx` — Wajar Gaji (benchmarking)
4. `cekwajar.id/src/app/wajar-tanah/page.tsx` — Wajar Tanah (property)
5. `cekwajar.id/src/app/pricing/page.tsx` — Pricing page
6. `cekwajar.id/src/app/dashboard/page.tsx` — Dashboard
7. `cekwajar.id/src/app/api/` — All API routes
8. `.wiki/projects/cekwajar-id.md` — Full product spec (for context on what each tool should do)
9. `.wiki/projects/cekwajar-roadmap.md` — Revenue model context

---

## YOUR INSTRUCTION SET

**Step 1 — Audit pass (no code changes)**
Run through every file. Use the rubric above. Score each dimension. List every issue with:
- File path + line number
- Issue description
- Severity (P0/P1/P2/P3)

**Step 2 — Fix P0 issues first**
P0 = anything that breaks functionality (skeleton pages, broken forms, wrong calculations). Fix ALL P0 before moving on.

**Step 3 — Fix P1 issues**
P1 = conversion issues (freemium gate not working, missing CTA, broken upgrade flow). Fix ALL P1 before moving on.

**Step 4 — P2 / P3 review pass**
Clean up visual issues, AI-slop patterns, accessibility gaps. Do NOT add new features — only fix what exists.

**Step 5 — Final scoring**
Re-score all 5 dimensions. Target: 95+ in each. If any dimension is below 95, fix until it passes.

---

## WHAT "DONE" LOOKS LIKE

- [ ] Every page in `src/app/` is functional — zero skeletons
- [ ] All API routes return real data (not hardcoded mock responses)
- [ ] All forms submit and show results
- [ ] Freemium gate works: free users see codes, paid users see IDR amounts
- [ ] All pricing upgrade flow works end-to-end (login → pay → success → dashboard unlocked)
- [ ] All copy in Bahasa Indonesia with proper formatting (IDR currency, dates, numbers)
- [ ] Zero emoji used as icons anywhere
- [ ] Homepage testimonials are real or removed (not placeholder)
- [ ] All Indonesian payroll logic (PPh 21, BPJS) is accurate to current regulations
- [ ] All tool verdict logic (IQR, TER, UMK comparison) is correct
- [ ] No raw API errors visible to users
- [ ] No "Lorem Ipsum" or placeholder text anywhere in production flows
- [ ] All interactive elements have visible feedback on hover/press
- [ ] Mobile touch targets ≥44px
- [ ] Dark mode works without breaking contrast ratios

---

## WHAT NOT TO DO

- Do NOT add animations for their own sake. One animated element per viewport max.
- Do NOT add new pages or features. Fix what exists first.
- Do NOT use purple/violet/indigo anywhere.
- Do NOT change the freemium model structure (free = codes, paid = amounts). This is the core conversion insight.
- Do NOT add "AI-powered" marketing copy — it adds no trust with Indonesian SMB audience.
- Do NOT over-engineer. This is a solo-founder stage product. Ship clean and functional, not perfect.
- Do NOT use `time.sleep()` or sync `requests`. This is a Next.js app — use async/await.
- Do NOT hardcode any secrets or IDs in client-side code.

---

## REFERENCE — INDONESIAN PAYROLL RULES (for business logic audit)

### PPh 21 TER System (PMK 168/2023)
- Monthly wage is annualized ÷ 12 for tax calculation
- PTKP single: IDR 54.000.000/year
- PTKP married: IDR 58.500.000/year (+ IDR 4.500.000 per dependent, max 3)
- Tax brackets: 5% (0-60M), 15% (60M-250M), 25% (250M-500M), 30% (500M-1B), 35% (1B-5B), 45% (>5B)

### BPJS Contributions (2024)
| Component | Employee | Employer |
|---|---|---|
| JKK | 0% | 0.24%-0.54% (risk-based) |
| JKM | 0% | 0.30% |
| JHT | 3.70% | 3.70% |
| JP | 2.00% | 2.00% |
| Pensiun | 1.00% | 2.00% |

### UMK Jakarta 2025 (reference for minimum wage checks)
- Jakarta UMK 2025: IDR 5.000.000+ range (verify current year value)

---

## REFERENCE — PROPERTY VALUATION RULES

### IQR Verdict Thresholds
```
if price_per_m2 < P25 → MURAH (below market)
if P25 ≤ price_per_m2 ≤ P75 → WAJAR (market range)
if P75 < price_per_m2 ≤ P75×1.5 → MAHAL (above market)
if price_per_m2 > P75×1.5 → SANGAT MAHAL (significantly above)
```

### Property Types
- RUMAH (house) — land + structure
- TANAH (land) — land only
- APARTEMEN (apartment) — strata title
- RUKO (shophouse) — commercial/residential hybrid

---

## OUTPUT FORMAT

After auditing, provide:
1. **Audit Report** — Scores per dimension with issue list (file + line + description + severity)
2. **Fix Log** — Every change made, organized by P0 → P1 → P2 → P3
3. **Final Scores** — Re-scored rubric after all fixes

Start now. Read all files in "FILES TO READ FIRST" before writing anything.
