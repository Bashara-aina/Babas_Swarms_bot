---
title: Planner 2026 04 25 Cekwajar Impl
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Plan: cekwajar.id Full Implementation
Date: 2026-04-25
Type: FEATURE
Context gathered: 
- Read all 10 reference files (00_audit_fixes.md through 10_data_visualization.md)
- Reviewed codebase structure: app/ (Next.js App Router), components/, lib/
- Verified current state: FreemiumGate exists, TrustBadges exists, button default uses bg-primary not slate-900
- Verified project does NOT use src/ prefix — app files are directly under /app/
- Tailwind v4 with @import "tailwindcss" — theme variables in globals.css via @theme inline
- No tailwind.config.ts exists

Risk assessment:
- HUGE scope (22 fixes + 10 clusters + multiple new components)
- Breaking up into batches is required
- Project already builds (verified in task description)
- Need to be careful about /privacy vs /privacy-policy link fixes
- button.tsx uses bg-primary (emerald) already — NOT slate-900

Approach:
- Execute contracts in dependency order
- First: P0 audit fixes (critical for brand/trust)
- Second: Tool page updates (add tints, TrustBadges, HowItWorks, CrossToolSuggestion)
- Third: Mobile components (BottomNav, CitySheet, useIsMobile hook)
- Fourth: New components (ViolationSummaryBanner, SampleResultTeaser, FounderSection, etc.)
- Fifth: Data visualization components
- Sixth: Remaining audit fixes + copy library
- Seventh: Final build + lint + test + push

---

## Execution Order

### Batch 1 (Serial - must run in sequence):
1. CONTRACT #[1] — Tool tints + globals.css tool vars
2. CONTRACT #[2] — TrustBadges + HowItWorksTool + CrossToolSuggestion on all tool pages
3. CONTRACT #[3] — Mobile components (MobileBottomNav + MobileCitySheet + useIsMobile)
4. CONTRACT #[4] — Footer with WordmarkLogo + Pricing page

### Batch 2 (Serial - depends on batch 1):
5. CONTRACT #[5] — New components (ViolationSummaryBanner + SampleResultTeaser + SamplePaidResultModal + FounderSection)
6. CONTRACT #[6] — Data visualization components (PercentileBar + PropertyPriceBar + COLComparisonChart + PPPBasketComparison + PayslipDiagram)
7. CONTRACT #[7] — Copy library + remaining P1/P2 audit fixes

### Final (Must run last):
8. CONTRACT #[8] — Final build + lint + test + git push

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Build fails due to TypeScript errors in new components | M | H | Run build after each contract, fix errors immediately |
| MobileBottomNav conflicts with existing navigation | M | M | Check pathname and auth page detection before rendering |
| Recharts not installed or wrong version | L | H | Check package.json before creating chart components |
| Tool page structure differs from reference (no outer container) | M | M | Read each tool page first, adapt tint application accordingly |
| Pricing page already exists at different path | L | L | Check before creating, adapt if needed |
| Button default variant is already emerald (not slate) | L | L | Task says already fixed — verify before fixing |
| Privacy link fix not needed (none found) | L | L | Verify with grep before making changes |
| copy.ts already exists with different content | M | L | Check existing content, merge or overwrite per requirements |
| Confetti library (canvas-confetti) not installed | L | M | Check package.json, install if missing before contract #[7] |

---

## Contracts Summary

| # | Task | Type | Dep |
|---|------|------|-----|
| 1 | Tool tints + globals.css vars | WRITE | none |
| 2 | TrustBadges + HowItWorksTool + CrossToolSuggestion | WRITE | 1 |
| 3 | MobileBottomNav + MobileCitySheet + useIsMobile | WRITE | none |
| 4 | Footer WordmarkLogo + Pricing page | WRITE | 1,2 |
| 5 | ViolationSummaryBanner + SampleResultTeaser + FounderSection | WRITE | 4 |
| 6 | 5 Data visualization components | WRITE | 5 |
| 7 | copy.ts library + P1/P2 audit fixes | WRITE | 6 |
| 8 | Final build + lint + test + git push | VERIFY | all |