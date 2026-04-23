---
name: layout
description: "Skill for the Layout area of swarm-bot. 44 symbols across 19 files."
---

# Layout

44 symbols | 19 files | Cohesion: 82%

## When to Use

- Working with code in `halolight-ref/`
- Understanding how slugify, ToggleMobileSidebar, Sidebar work
- Modifying layout-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `halolight-ref/src/components/layout/tab-bar.tsx` | resolveTitle, resolveIcon, TabBar, scroll, handleTabClick (+4) |
| `project/rumahlabuh/components/ui/sidebar.tsx` | useSidebar, Sidebar, SidebarRail, SidebarMenuButton |
| `halolight-ref/src/components/layout/sidebar.tsx` | Sidebar, traverse, renderMenuItems, renderCollapsedFlyout |
| `shadboard-ref/full-kit/src/lib/utils.ts` | slugify, titleCaseToCamelCase, getDictionaryValue |
| `shadboard-ref/starter-kit/src/components/layout/sidebar.tsx` | Sidebar, renderMenuItem |
| `shadboard-ref/full-kit/src/app/(unlocalized)/docs/_components/docs-toc.tsx` | DocsToc, generateTree |
| `shadboard-ref/full-kit/src/components/layout/sidebar.tsx` | Sidebar, renderMenuItem |
| `shadboard-ref/full-kit/src/components/layout/command-menu.tsx` | CommandMenu, renderMenuItem |
| `shadboard-ref/full-kit/src/components/layout/horizontal-layout/top-bar-header-menubar.tsx` | TopBarHeaderMenubar, renderMenuItem |
| `halolight-ref/src/config/routes.ts` | getMenuPermission, findPermissionRule |

## Entry Points

Start here when exploring this area:

- **`slugify`** (Function) — `shadboard-ref/full-kit/src/lib/utils.ts:234`
- **`ToggleMobileSidebar`** (Function) — `shadboard-ref/starter-kit/src/components/layout/toggle-mobile-sidebar.tsx:7`
- **`Sidebar`** (Function) — `shadboard-ref/starter-kit/src/components/layout/sidebar.tsx:37`
- **`renderMenuItem`** (Function) — `shadboard-ref/starter-kit/src/components/layout/sidebar.tsx:47`
- **`ToggleMobileSidebar`** (Function) — `shadboard-ref/full-kit/src/components/layout/toggle-mobile-sidebar.tsx:7`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `slugify` | Function | `shadboard-ref/full-kit/src/lib/utils.ts` | 234 |
| `ToggleMobileSidebar` | Function | `shadboard-ref/starter-kit/src/components/layout/toggle-mobile-sidebar.tsx` | 7 |
| `Sidebar` | Function | `shadboard-ref/starter-kit/src/components/layout/sidebar.tsx` | 37 |
| `renderMenuItem` | Function | `shadboard-ref/starter-kit/src/components/layout/sidebar.tsx` | 47 |
| `ToggleMobileSidebar` | Function | `shadboard-ref/full-kit/src/components/layout/toggle-mobile-sidebar.tsx` | 7 |
| `DocsToc` | Function | `shadboard-ref/full-kit/src/app/(unlocalized)/docs/_components/docs-toc.tsx` | 17 |
| `DocsSidebar` | Function | `shadboard-ref/full-kit/src/app/(unlocalized)/docs/_components/docs-sidebar.tsx` | 27 |
| `LandingSidebar` | Function | `shadboard-ref/full-kit/src/app/[lang]/(plain-layout)/pages/landing/_components/layout/landing-sidebar.tsx` | 32 |
| `TabBar` | Function | `halolight-ref/src/components/layout/tab-bar.tsx` | 88 |
| `scroll` | Function | `halolight-ref/src/components/layout/tab-bar.tsx` | 170 |
| `handleTabClick` | Function | `halolight-ref/src/components/layout/tab-bar.tsx` | 181 |
| `handleCloseTab` | Function | `halolight-ref/src/components/layout/tab-bar.tsx` | 189 |
| `handleCloseOthers` | Function | `halolight-ref/src/components/layout/tab-bar.tsx` | 205 |
| `handleCloseRight` | Function | `halolight-ref/src/components/layout/tab-bar.tsx` | 215 |
| `runRefresh` | Function | `halolight-ref/src/components/layout/tab-bar.tsx` | 245 |
| `titleCaseToCamelCase` | Function | `shadboard-ref/full-kit/src/lib/utils.ts` | 226 |
| `getDictionaryValue` | Function | `shadboard-ref/full-kit/src/lib/utils.ts` | 328 |
| `Sidebar` | Function | `shadboard-ref/full-kit/src/components/layout/sidebar.tsx` | 48 |
| `renderMenuItem` | Function | `shadboard-ref/full-kit/src/components/layout/sidebar.tsx` | 62 |
| `CommandMenu` | Function | `shadboard-ref/full-kit/src/components/layout/command-menu.tsx` | 49 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `TabBar → Refresh` | cross_community | 3 |
| `Sidebar → IsPathnameMissingLocale` | cross_community | 3 |
| `Sidebar → EnsureWithPrefix` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ui | 11 calls |
| Auth | 5 calls |
| Hooks | 2 calls |
| [id] | 1 calls |
| Providers | 1 calls |

## How to Explore

1. `gitnexus_context({name: "slugify"})` — see callers and callees
2. `gitnexus_query({query: "layout"})` — find related execution flows
3. Read key files listed above for implementation details
