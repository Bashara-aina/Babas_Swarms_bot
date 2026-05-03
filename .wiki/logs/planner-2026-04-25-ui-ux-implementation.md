---
title: Planner 2026 04 25 Ui Ux Implementation
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Plan: UI/UX Deep Implementation for cekwajar.id
Date: 2026-04-25
Type: FEATURE

## Context Gathered
- **Project**: Next.js App Router Indonesian fintech wage fairness platform
- **Current State**:
  - System fonts (Arial/Helvetica) via body { font-family: Arial, Helvetica, sans-serif }
  - Geist fonts loaded in layout.tsx but not applied
  - Minimal globals.css with only background/foreground variables
  - No semantic color tokens (verdict colors, surface colors)
  - Only Badge component exists in components/ui/
  - Chinese characters present in kabur and gaji pages (bilingual pollution)
  - No skeleton loading states
  - PercentileBar has no aria labels
  - FreemiumGate uses blur overlay
  - Footer is minimal with just copyright text
  - Landing page uses plain Tailwind, no shadcn components

## Reference Sites
- shadcn/ui taxonomy: 112k stars, component patterns
- shadcn/taxonomy: saas starter reference
- ln-dev7/square-ui: premium UI reference

## Risk Assessment
1. **Font loading**: Plus Jakarta Sans via next/font/google should work
2. **Tailwind v4**: Uses @import "tailwindcss" syntax, CSS variables in @theme inline
3. **Component conflicts**: Badge already exists, need to ensure no conflicts
4. **Bilingual fix**: Need to remove Chinese text, not translate to Indonesian
5. **Accessibility**: Must add proper ARIA labels to PercentileBar

## Approach
Group 12 items into 6 contracts (~30 min each):
1. Foundation: Font + Color tokens + globals.css cleanup
2. shadcn/ui core components (Card, Button, Input, Label, Select, Skeleton, Toast, Sheet)
3. Fix bilingual pollution + Accessible PercentileBar
4. Empty state component + Form micro-interactions
5. FreemiumGate rework
6. Footer with trust signals + Landing page polish

## Dependencies
- No external API dependencies
- All work is local file modifications
- No breaking changes expected
