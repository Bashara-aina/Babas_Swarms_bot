---
name: hooks
description: "Skill for the Hooks area of swarm-bot. 118 symbols across 43 files."
---

# Hooks

118 symbols | 43 files | Cohesion: 89%

## When to Use

- Working with code in `halolight-ref/`
- Understanding how useSettings, relocalizePathname, ThemeProvider work
- Modifying hooks-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `shadboard-ref/starter-kit/src/hooks/use-toast.ts` | genId, addToRemoveQueue, reducer, dispatch, toast (+3) |
| `shadboard-ref/full-kit/src/hooks/use-toast.ts` | genId, addToRemoveQueue, reducer, dispatch, toast (+3) |
| `halolight-ref/src/hooks/use-dashboard-data.ts` | fetcher, useDashboardVisits, useDashboardPie, useDashboardTasks, useDashboardNotifications (+2) |
| `halolight-ref/src/components/dashboard/configurable-dashboard.tsx` | LineChartWidget, PieChartWidget, NotificationsWidget, TasksWidget, CalendarWidget (+2) |
| `halolight-ref/src/lib/api/mock-api.ts` | getRoles, getMessages, getEvents, getUser, getRole (+2) |
| `halolight-ref/src/hooks/use-users.ts` | useUsers, useRoles, useCreateUser, useDeleteUser, useBatchDeleteUsers (+1) |
| `halolight-ref/src/hooks/use-teams.ts` | useRolesDetail, useTeams, useCreateTeam, useUpdateTeam, useDeleteTeam (+1) |
| `halolight-ref/src/hooks/use-documents.ts` | useCreateDocument, useUpdateDocument, useDeleteDocument, useBatchDeleteDocuments, useDocuments (+1) |
| `halolight-ref/src/hooks/use-calendar.ts` | useCreateCalendarEvent, useUpdateCalendarEvent, useDeleteCalendarEvent, useBatchDeleteCalendarEvents, useCalendarEvents (+1) |
| `halolight-ref/src/hooks/use-action-mutation.ts` | useActionMutation, createActionMutationHook, useActionMutationVoid, useOptimisticListUpdate, useBatchActionMutation |

## Entry Points

Start here when exploring this area:

- **`useSettings`** (Function) — `shadboard-ref/starter-kit/src/hooks/use-settings.ts:6`
- **`relocalizePathname`** (Function) — `shadboard-ref/full-kit/src/lib/i18n.ts:28`
- **`ThemeProvider`** (Function) — `shadboard-ref/starter-kit/src/providers/theme-provider.tsx:8`
- **`useRadius`** (Function) — `shadboard-ref/starter-kit/src/hooks/use-radius.tsx:6`
- **`useIsVertical`** (Function) — `shadboard-ref/starter-kit/src/hooks/use-is-vertical.tsx:4`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `useSettings` | Function | `shadboard-ref/starter-kit/src/hooks/use-settings.ts` | 6 |
| `relocalizePathname` | Function | `shadboard-ref/full-kit/src/lib/i18n.ts` | 28 |
| `ThemeProvider` | Function | `shadboard-ref/starter-kit/src/providers/theme-provider.tsx` | 8 |
| `useRadius` | Function | `shadboard-ref/starter-kit/src/hooks/use-radius.tsx` | 6 |
| `useIsVertical` | Function | `shadboard-ref/starter-kit/src/hooks/use-is-vertical.tsx` | 4 |
| `ThemeProvider` | Function | `shadboard-ref/full-kit/src/providers/theme-provider.tsx` | 8 |
| `useRadius` | Function | `shadboard-ref/full-kit/src/hooks/use-radius.tsx` | 6 |
| `useIsDarkMode` | Function | `shadboard-ref/full-kit/src/hooks/use-mode.tsx` | 6 |
| `useIsVertical` | Function | `shadboard-ref/full-kit/src/hooks/use-is-vertical.tsx` | 4 |
| `ModeDropdown` | Function | `shadboard-ref/full-kit/src/components/mode-dropdown.tsx` | 29 |
| `LanguageDropdown` | Function | `shadboard-ref/full-kit/src/components/language-dropdown.tsx` | 26 |
| `Toaster` | Function | `shadboard-ref/starter-kit/src/components/ui/sonner.tsx` | 10 |
| `ModeDropdown` | Function | `shadboard-ref/starter-kit/src/components/layout/mode-dropdown.tsx` | 25 |
| `Layout` | Function | `shadboard-ref/starter-kit/src/components/layout/index.tsx` | 8 |
| `Toaster` | Function | `shadboard-ref/full-kit/src/components/ui/sonner.tsx` | 10 |
| `Layout` | Function | `shadboard-ref/full-kit/src/components/layout/index.tsx` | 10 |
| `Customizer` | Function | `shadboard-ref/full-kit/src/components/layout/customizer.tsx` | 36 |
| `DocsModeDropdown` | Function | `shadboard-ref/full-kit/src/app/(unlocalized)/docs/_components/docs-mode-dropdown.tsx` | 25 |
| `useDashboardVisits` | Function | `halolight-ref/src/hooks/use-dashboard-data.ts` | 54 |
| `useDashboardPie` | Function | `halolight-ref/src/hooks/use-dashboard-data.ts` | 70 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `RolesPage → UpdateMetaTag` | cross_community | 3 |
| `RolesPage → GetRoles` | cross_community | 3 |
| `TeamsPage → UpdateMetaTag` | cross_community | 3 |
| `UsersPage → GetUsers` | intra_community | 3 |
| `UsersPage → GetRoles` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ui | 4 calls |
| Dashboard | 2 calls |
| Layout | 1 calls |
| Providers | 1 calls |

## How to Explore

1. `gitnexus_context({name: "useSettings"})` — see callers and callees
2. `gitnexus_query({query: "hooks"})` — find related execution flows
3. Read key files listed above for implementation details
