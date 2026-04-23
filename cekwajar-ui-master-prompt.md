# CLAUDE.md — Cekwajar.id UI/UX Transformation Master Prompt

## Project Identity
**Cekwajar.id** — Indonesian payroll/BPJS compliance application
- **Stack**: Next.js 16 + React 19 + Tailwind CSS 4 + shadcn/ui + TypeScript
- **Goal**: Transform from generic website → premium enterprise product
- **Reference repos** (cloned locally):
  - `/home/newadmin/swarm-bot/shadboard-ref/` — Next.js 15 + Shadcn/UI + theme customizer
  - `/home/newadmin/swarm-bot/nextjs-dashboard-ref/` — Framer Motion + 3 theme configs
  - `/home/newadmin/swarm-bot/civora-ref/` — Bento grid + shimmer skeletons
  - `/home/newadmin/swarm-bot/halolight-ref/` — Drag-drop dashboard + ⌘K command palette + 11 themes

## Mission
**Phase 1: UI/UX Overhaul**
Transform every page to feel like a premium enterprise SaaS product — not a generic website.

## UI/UX Reference Sources (extract patterns from these)

### shadboard-ref — Theme System & Layout
- **What to steal**: Theme customizer component, dark/light mode toggle, sidebar layout system
- **Files to study**:
  - `src/components/layout/` — sidebar, header, admin layout patterns
  - `src/lib/theme.ts` or equivalent — theme configuration
  - Any theme provider setup

### halolight-ref — Drag-Drop & ⌘K Command Menu
- **What to steal**: Dashboard with react-grid-layout, command palette pattern
- **Critical for BPJS**: A command menu (⌘K) lets users jump to different wajar-* modules fast
- **Files to study**:
  - `src/components/dashboard/` — ConfigurableDashboard, widget components
  - `src/components/layout/CommandMenu.tsx` — ⌘K pattern
  - `src/stores/` — Zustand dashboard layout state

### civora-ref — Bento Grid & Shimmer Loading
- **What to steal**: Bento grid layout, shimmer skeleton loading states, RTL/Persian elegance
- **Why bento**: BPJS modules (wajar-slip, wajar-tanah, wajar-gaji, wajar-kabur, wajar-hidup) each have multiple data cards — bento grid is perfect
- **Files to study**:
  - `src/components/ui/` — shimmer/skeleton components
  - `src/app/` — page layouts with bento-style grids
  - `tailwind.config.ts` — custom color/spacing for the premium feel

### nextjs-dashboard-ref — Framer Motion Animations
- **What to steal**: Page transitions, hover micro-interactions, scroll animations
- **Key principle**: Motion should guide attention, not distract
- **Files to study**:
  - `src/components/ui/` — motion-enhanced components
  - `src/app/layout.tsx` — page transition wrappers
  - Any `framer-motion` usage patterns

## Priority Improvements

### P1 — Loading States (Quick Win)
Replace all spinner-based loading with **shimmer skeletons** from civora-ref.
- Look at: `src/components/ui/skeleton.tsx` or custom shimmer components
- Pattern: gray animated gradient overlay on cards/tables
- Impact: instantly feels more premium

### P2 — Command Menu (⌘K)
Add a global command palette (from halolight-ref) that lets users:
- Jump to any wajar-* module
- Search employees
- Access recent payslips
- Trigger BPJS calculations

### P3 — Bento Grid Dashboard Layout
Migrate the existing multi-card layouts to a bento grid system:
- wajar-tanah page — property cards
- wajar-gaji page — salary component cards
- Each card should have hover states, smooth transitions

### P4 — Theme System
Implement a proper dark/light mode with next-themes:
- Zero-flash theme switching
- Custom color scheme for Indonesian enterprise (deep blues, warm golds for tax/BPJS indicators)
- Persisted in localStorage

### P5 — Motion & Micro-interactions
Add framer-motion to:
- Page transitions (fade + slide)
- Table row hover highlights
- Button press feedback
- Dialog open/close animations

## Design Principles

1. **Enterprise, not playful** — avoid excessive rounded corners, keep it sharp
2. **Data-forward** — payroll is data-heavy, tables and charts must be first-class
3. **Indonesian enterprise aesthetic** — blues, greens, with gold/amber accents for:
   - Tax indicators
   - BPJS compliance badges
   - Gaji (salary) highlights
4. **Motion serves function** — every animation should guide attention or confirm action
5. **Accessibility always** — all interactions keyboard-navigable, proper ARIA labels

## BPJS Module Reference (what we're improving)
- `src/app/wajar-tanah/page.tsx` — tanah (land) allowance
- `src/app/wajar-gaji/page.tsx` — gaji (salary) components
- `src/app/wajar-kabur/page.tsx` — kabur (running/absent) tracking
- `src/app/wajar-hidup/page.tsx` — hidup (living) allowance
- `src/app/wajar-slip/page.tsx` — slip (payslip) generation

## Technical Notes

### shadcn/ui Components to Add
```bash
cd cekwajar.id-20260415T173403Z-3-001/cekwajar.id
npx shadcn@latest add card dialog skeleton table command chart
```

### next-themes Setup
```bash
npm install next-themes
```
Then wrap app in `ThemeProvider` from `next-themes`

### Key Files to Modify
- `src/app/layout.tsx` — add providers, command menu wrapper
- `src/app/globals.css` — extend Tailwind with custom colors/spacing
- Tailwind config — add Indonesian enterprise color palette

## Commands

```bash
# Start development
cd cekwajar.id-20260415T173403Z-3-001/cekwajar.id && npm run dev

# Add shadcn components
npx shadcn@latest add [component-name]

# Study reference repo (example)
cat shadboard-ref/src/components/layout/sidebar.tsx
```

## What "Done" Looks Like
- [ ] All pages have shimmer loading, not spinners
- [ ] ⌘K opens command palette from anywhere
- [ ] Dashboard uses bento grid layout
- [ ] Dark/light mode works with zero flash
- [ ] Page transitions are smooth (framer-motion)
- [ ] Tables have hover states and are sortable
- [ ] BPJS compliance badges use gold/amber accent colors
- [ ] No generic-looking pages remain