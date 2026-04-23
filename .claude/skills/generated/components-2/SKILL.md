---
name: components-2
description: "Skill for the Components area of swarm-bot. 54 symbols across 12 files."
---

# Components

54 symbols | 12 files | Cohesion: 100%

## When to Use

- Working with code in `cekwajar.id-20260415T173403Z-3-001/`
- Understanding how setupMockFetch, MockProvider, ThemeProvider work
- Modifying components-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/combined.js` | fmtIDR, fmtIDRShort, SalaryRangeBar, ViolationItem, WajarTanahPage (+11) |
| `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/wajar-hidup.jsx` | fmtIDR, fmtIDRShort, WajarHidupPage, handleSubmit, ResultSkeleton (+1) |
| `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/components/providers.tsx` | getResolvedTheme, applyTheme, ThemeProvider, handler, useAppTheme |
| `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/wajar-tanah.jsx` | fmtIDR, fmtIDRShort, WajarTanahPage, ResultSkeleton, bar |
| `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/wajar-kabur.jsx` | fmtIDR, fmtIDRShort, WajarKaburPage, ResultSkeleton, bar |
| `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/wajar-slip.jsx` | parseIDR, idrInput, WajarSlipPage, runCalculation |
| `halolight-ref/src/lib/mock-fetch.ts` | getUrlPathname, findMockHandler, setupMockFetch |
| `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/home.jsx` | fmtIDR, fmtIDRShort, SalaryRangeBar |
| `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/components/ConfettiEffect.tsx` | ConfettiEffect, loadAndFire, fire |
| `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/pages.jsx` | PricingPage, fmtP |

## Entry Points

Start here when exploring this area:

- **`setupMockFetch`** (Function) — `halolight-ref/src/lib/mock-fetch.ts:65`
- **`MockProvider`** (Function) — `halolight-ref/src/components/mock-provider.tsx:4`
- **`ThemeProvider`** (Function) — `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/components/providers.tsx:38`
- **`handler`** (Function) — `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/components/providers.tsx:55`
- **`ConfettiEffect`** (Function) — `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/components/ConfettiEffect.tsx:20`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `setupMockFetch` | Function | `halolight-ref/src/lib/mock-fetch.ts` | 65 |
| `MockProvider` | Function | `halolight-ref/src/components/mock-provider.tsx` | 4 |
| `ThemeProvider` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/components/providers.tsx` | 38 |
| `handler` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/components/providers.tsx` | 55 |
| `ConfettiEffect` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/components/ConfettiEffect.tsx` | 20 |
| `loadAndFire` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/components/ConfettiEffect.tsx` | 27 |
| `fire` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/components/ConfettiEffect.tsx` | 37 |
| `useAppTheme` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/components/providers.tsx` | 20 |
| `GlobalNav` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/components/layout/GlobalNav.tsx` | 29 |
| `fmtIDR` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/combined.js` | 217 |
| `fmtIDRShort` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/combined.js` | 221 |
| `SalaryRangeBar` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/combined.js` | 338 |
| `ViolationItem` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/combined.js` | 811 |
| `WajarTanahPage` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/combined.js` | 1281 |
| `handleSubmit` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/combined.js` | 1308 |
| `WajarKaburPage` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/combined.js` | 1593 |
| `WajarHidupPage` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/combined.js` | 1931 |
| `getUrlPathname` | Function | `halolight-ref/src/lib/mock-fetch.ts` | 9 |
| `findMockHandler` | Function | `halolight-ref/src/lib/mock-fetch.ts` | 29 |
| `parseIDR` | Function | `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/wajar-slip.jsx` | 9 |

## How to Explore

1. `gitnexus_context({name: "setupMockFetch"})` — see callers and callees
2. `gitnexus_query({query: "components"})` — find related execution flows
3. Read key files listed above for implementation details
