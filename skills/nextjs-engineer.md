# Next.js Engineer (App Router + Production Patterns)

Use this skill for building/reviewing Next.js apps with TypeScript strict mode and Supabase SSR auth.

## 1) Router choice: App vs Pages

| Scenario | Prefer | Why |
|---|---|---|
| New product | App Router | Server Components, layouts, nested routing |
| Legacy migration | Pages Router | Lower migration risk |
| Heavy streaming/suspense | App Router | Better async composition |

Default for new work: **App Router**.

## 2) Component boundary rules

- Server Component by default.
- Add `"use client"` only when using browser APIs/state/effects/event handlers.
- Never import server-only modules into client components.
- Keep data fetching in server layer when possible.

Common error: hydration mismatch.
Mitigation:
- avoid non-deterministic render output (`Date.now()`, random values) at SSR stage
- gate client-only values with effect

## 3) Data fetching strategy

- SSR (dynamic): user-specific dashboards, auth-dependent pages.
- SSG/ISR: mostly static docs/marketing pages.
- CSR: only for highly interactive, low-SEO content.

Decision table:
| Need | Strategy |
|---|---|
| per-request personalization | SSR |
| static with occasional updates | ISR |
| static forever | SSG |
| browser-only widgets | CSR |

## 4) API routes and validation

- Use Route Handlers under `app/api/.../route.ts`.
- Validate all input with Zod.
- Return normalized error shape `{ error: string, code?: string }`.
- Never trust client payload shape.

## 5) Supabase SSR auth pattern

Use server client (`createServerClient`) in server contexts.

Checklist:
- read/write auth cookies through Next request/response APIs
- validate session on server before protected render
- avoid exposing service role key to client

## 6) TypeScript strict mode

- `strict: true` mandatory.
- Avoid `any`; use inferred + explicit interfaces/types.
- Narrow unknown values from external APIs.
- Prefer discriminated unions for response states.

## 7) App Router conventions

- `loading.tsx`: lightweight skeleton state.
- `error.tsx`: route-level fallback with recovery action.
- `not-found.tsx`: explicit 404 UX.
- `layout.tsx`: shared shells and providers.

## 8) Middleware guidance

Use middleware for:
- auth gate on protected paths
- locale/routing rewrites
- lightweight edge checks

Do not put heavy DB logic in middleware.

## 9) Env variable safety

- `NEXT_PUBLIC_*`: browser-visible only.
- server-only secrets: no `NEXT_PUBLIC_` prefix.
- fail fast when required env is missing in server code.

## 10) Common pitfalls + fixes

1. Missing Suspense boundary
   - wrap async client boundaries with `<Suspense fallback=...>`.
2. Client/server import violation
   - move server code to action/route/server component.
3. Hydration mismatch
   - make initial render deterministic.
4. Over-fetching in nested components
   - centralize data loading in parent server component.
5. Overusing client components
   - keep majority server-side for perf.

## 11) Output standards for generated code

- Include exact file paths.
- Keep API contracts typed.
- Include error and loading states.
- Include one minimal test strategy note (unit + integration).
- Avoid introducing unnecessary UI libraries unless requested.
