---
title: Contracts 2026 04 25 Cekwajar Batch1
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

### CONTRACT #[2]: TrustBadges + HowItWorksTool + CrossToolSuggestion on All 5 Tool Pages

WHAT:
Import and render TrustBadges, HowItWorksTool (with tool-specific steps), and CrossToolSuggestion (with fromTool prop) on all 5 tool pages. TrustBadges above form, HowItWorksTool above TrustBadges, CrossToolSuggestion below result section.

FILES:
READ:
  - /home/newadmin/swarm-bot/cekwajar.id/components/TrustBadges.tsx
  - /home/newadmin/swarm-bot/cekwajar.id/components/HowItWorksTool.tsx
  - /home/newadmin/swarm-bot/cekwajar.id/components/CrossToolSuggestion.tsx
  - /home/newadmin/swarm-bot/cekwajar.id/app/(wajar)/slip/page.tsx
  - /home/newadmin/swwajar.id/app/(wajar)/gaji/page.tsx
  - /home/newadmin/swarm-bot/cekwajar.id/app/(wajar)/tanah/page.tsx
  - /home/newadmin/swarm-bot/cekwajar.id/app/(wajar)/kabur/page.tsx
  - /home/newadmin/swarm-bot/cekwajar.id/app/(wajar)/hidup/page.tsx

WRITE:
  Modify each tool page to add the three components.

RUN:
  - grep -c "TrustBadges" /home/newadmin/swarm-bot/cekwajar.id/app/\(wajar\)/slip/page.tsx 2>/dev/null || echo "0"

DONE_WHEN:
  - slip page: HowItWorksTool (Upload/Brain/ShieldCheck steps) above TrustBadges above form; CrossToolSuggestion with fromTool="slip" below result section
  - gaji page: HowItWorksTool (Search/BarChart2/Users steps) above TrustBadges; CrossToolSuggestion with fromTool="gaji" below result
  - tanah page: HowItWorksTool (MapPin/TrendingUp/FileCheck steps) above TrustBadges; CrossToolSuggestion with fromTool="tanah" below result
  - kabur page: HowItWorksTool (Globe/Calculator/DollarSign steps) above TrustBadges; CrossToolSuggestion with fromTool="kabur" below result
  - hidup page: HowItWorksTool (Home/ArrowLeftRight/PieChart steps) above TrustBadges; CrossToolSuggestion with fromTool="hidup" below result
  - npm run build passes

PROOF_FORMAT:
  - CODE: `grep -n "TrustBadges\|HowItWorksTool\|CrossToolSuggestion" /home/newadmin/swarm-bot/cekwajar.id/app/\(wajar\)/slip/page.tsx` → paste output
  - CODE: `grep -n "TrustBadges\|HowItWorksTool\|CrossToolSuggestion" /home/newadmin/swarm-bot/cekwajar.id/app/\(wajar\)/gaji/page.tsx` → paste output
  - CODE: `npm run build --prefix /home/newadmin/swarm-bot/cekwajar.id 2>&1 | tail -5` → paste output

BLOCKER_IF:
  - One of the components (TrustBadges, HowItWorksTool, CrossToolSuggestion) doesn't exist at expected path — check and report

DEPENDS_ON: #[1]