# Stage 3 — Authentication, User Dashboard & Subscription System
**cekwajar.id Vibe Coding Playbook**  
**Estimated time:** 3–4 hours  
**Prerequisites:** Stage 1 + 2 complete. All 19 migrations applied.  
**Goal:** Full auth flow (email + Google OAuth), user dashboard, subscription status display, freemium gate component.

---

## What You're Building

- Email + Google OAuth login/signup
- Protected dashboard at `/dashboard`
- Subscription status display
- `PremiumGate` component (blur overlay + upgrade CTA)
- Session middleware fully configured
- Auth callback route handling
- Logout flow

---

## New Dependencies This Stage

```bash
# These should already be installed from Stage 1:
# @supabase/supabase-js @supabase/ssr

# No new packages needed — Stage 1 covered them all
pnpm tsc --noEmit  # run this to confirm no errors before starting
```

---

## ═══════════════════════════════════════════════
## MASTER PROMPT — SEND THIS TO CLAUDE CODE
## (Stage 3 — Auth + Dashboard)
## ═══════════════════════════════════════════════

```
===START===
cekwajar.id — Stage 3: Authentication + User Dashboard

Context: Next.js 15 App Router, Supabase Auth, TypeScript, shadcn/ui.
Stage 1 (scaffold) and Stage 2 (database) are complete.
All tables exist including user_profiles with subscription_tier column.
The handle_new_user() trigger auto-creates a user_profiles row on signup.

YOUR TASK FOR STAGE 3:
Build complete auth system + user dashboard + freemium gate infrastructure.

════════════════════════════════════════════════════
PART A: AUTH CONFIGURATION
════════════════════════════════════════════════════

1. SUPABASE AUTH SETTINGS:
In Supabase Dashboard (supabase.com) → Authentication → URL Configuration:
  Site URL: http://localhost:3000 (dev) / https://cekwajar.id (prod)
  Redirect URLs: http://localhost:3000/auth/callback, https://cekwajar.id/auth/callback

In Supabase Dashboard → Authentication → Providers:
  Email: ENABLED (with email confirmation: DISABLED for better UX)
  Google: ENABLED (requires Google OAuth Client ID + Secret)
  
Google OAuth setup:
  console.cloud.google.com → cekwajar-ocr project → Credentials → Create OAuth 2.0 Client ID
  Application type: Web
  Authorized redirect URIs: https://[project-ref].supabase.co/auth/v1/callback
  Copy Client ID + Secret to Supabase Google provider config.

Add to .env.local:
  GOOGLE_OAUTH_CLIENT_ID=xxx.apps.googleusercontent.com (for reference, Supabase stores this)

2. UPDATE MIDDLEWARE (src/middleware.ts):
Full Supabase SSR middleware that:
- Refreshes session on every request
- Attaches session to request headers
- Does NOT redirect unauthenticated users (all pages public)
- Only one protected route: /dashboard (redirect to /auth/login if not authenticated)

import { createServerClient } from '@supabase/ssr'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })
  
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return request.cookies.getAll() },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )
  
  const { data: { user } } = await supabase.auth.getUser()
  
  // Protect /dashboard only
  if (!user && request.nextUrl.pathname.startsWith('/dashboard')) {
    const redirectUrl = new URL('/auth/login', request.url)
    redirectUrl.searchParams.set('redirectTo', request.nextUrl.pathname)
    return NextResponse.redirect(redirectUrl)
  }
  
  return supabaseResponse
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)'],
}

════════════════════════════════════════════════════
PART B: AUTH PAGES
════════════════════════════════════════════════════

3. LOGIN PAGE (src/app/auth/login/page.tsx):
Clean centered card layout.
Title: "Masuk ke cekwajar.id"
Subtitle: "Gratis selamanya untuk fitur dasar."

Google OAuth button (large, primary):
  onClick: supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: `${location.origin}/auth/callback` }
  })
  Text: "Masuk dengan Google"
  Icon: Google icon (use SVG inline)

Divider: "atau"

Email magic link form:
  Input: Email address (type=email, placeholder="email@kamu.com")
  Button: "Kirim Link Masuk"
  On submit: supabase.auth.signInWithOtp({ email, options: { emailRedirectTo: `${origin}/auth/callback` } })
  
Success state: "Cek inbox kamu! Link masuk dikirim ke [email]"
Error state: Show error message in red

Add at bottom: Privacy notice in small text:
  "Dengan masuk, kamu setuju dengan Kebijakan Privasi dan Syarat & Ketentuan kami."

4. AUTH CALLBACK ROUTE (src/app/auth/callback/route.ts):
Handle Supabase auth callback (code exchange):

import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const next = searchParams.get('next') ?? '/dashboard'
  
  if (code) {
    const cookieStore = await cookies()
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          getAll() { return cookieStore.getAll() },
          setAll(cookiesToSet) {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          },
        },
      }
    )
    const { error } = await supabase.auth.exchangeCodeForSession(code)
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`)
    }
  }
  
  return NextResponse.redirect(`${origin}/auth/login?error=auth_failed`)
}

5. LOGOUT ACTION (src/app/auth/actions.ts):
'use server'
Create signOut server action:
  await supabase.auth.signOut()
  redirect('/')

════════════════════════════════════════════════════
PART C: USER DASHBOARD
════════════════════════════════════════════════════

6. DASHBOARD PAGE (src/app/dashboard/page.tsx):
This is a SERVER COMPONENT that reads session server-side.

Layout:
  - Welcome: "Halo, [name]!" 
  - Subscription card (see below)
  - Recent audits section (placeholder — "Riwayat audit akan muncul di sini")
  - Quick access cards for 5 tools

SUBSCRIPTION STATUS CARD:
Show based on tier:

FREE tier card:
  Title: "Paket Gratis"
  Features list: ✅ 3 audit/hari, ✅ Benchmark provinsi, ❌ Detail IDR, ❌ Riwayat
  CTA Button: "Upgrade ke Basic — Rp 29.000/bulan" → links to /upgrade

BASIC tier card (green):
  Title: "Paket Basic ✓"
  Renewal date: "Aktif hingga [date]"
  Features: ✅ Semua fitur Free + ✅ Detail IDR pelanggaran, ✅ P25-P75 kota, ✅ 20 negara Wajar Kabur
  CTA: "Upgrade ke Pro" → /upgrade

PRO tier card (purple/gold):
  Title: "Paket Pro ✓"
  Renewal date: "Aktif hingga [date]"
  All features checked
  No upsell

7. SUBSCRIPTION STATUS COMPONENT (src/components/shared/SubscriptionBadge.tsx):
Props: { tier: SubscriptionTier, showLabel?: boolean }
Small colored badge:
  free: gray background, "Gratis"
  basic: blue background, "Basic"  
  pro: purple background, "Pro"

════════════════════════════════════════════════════
PART D: PREMIUM GATE COMPONENT
════════════════════════════════════════════════════

8. PremiumGate (src/components/shared/PremiumGate.tsx):
This is the most important shared component — used on every tool.

Props:
  requiredTier: 'basic' | 'pro'
  featureLabel: string        // e.g., "Detail IDR pelanggaran"
  currentTier: SubscriptionTier
  children: React.ReactNode   // content to gate

Behavior:
  - If currentTier >= requiredTier: render children normally
  - If currentTier < requiredTier: render children with blur overlay

Gate overlay UI:
  Blurred background: CSS backdrop-filter: blur(8px) over children
  Center card on top:
    🔒 icon
    featureLabel text
    "Tersedia di paket [required tier]"
    Price: "Mulai Rp 29.000/bulan"
    Button: "Upgrade Sekarang" → links to /upgrade
    Link: "Pelajari fitur" → /pricing

TypeScript for tier comparison:
  const TIER_RANK: Record<SubscriptionTier, number> = { free: 0, basic: 1, pro: 2 }
  const isAllowed = TIER_RANK[currentTier] >= TIER_RANK[requiredTier]

Full component:
  return isAllowed ? (
    <>{children}</>
  ) : (
    <div className="relative">
      <div className="pointer-events-none select-none" style={{ filter: 'blur(8px)' }}>
        {children}
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="bg-white rounded-xl p-6 shadow-xl border text-center max-w-xs">
          <div className="text-3xl mb-2">🔒</div>
          <h3 className="font-semibold mb-1">{featureLabel}</h3>
          <p className="text-sm text-gray-500 mb-4">Tersedia di paket {requiredTier}</p>
          <Button asChild className="w-full">
            <Link href="/upgrade">Upgrade Sekarang</Link>
          </Button>
          <Link href="/pricing" className="block mt-2 text-xs text-gray-400 hover:underline">
            Pelajari fitur
          </Link>
        </div>
      </div>
    </div>
  )

9. UPGRADE PAGE STUB (src/app/upgrade/page.tsx):
Simple placeholder showing pricing tiers.
Three columns: Gratis / Basic (Rp 29K/bulan) / Pro (Rp 79K/bulan)
Feature comparison table (text only, no real payment yet — that's Stage 9).
Each column has a "Pilih Paket" button (disabled with "Coming soon" for now).

10. PRICING PAGE (src/app/pricing/page.tsx):
Same as upgrade page but more detailed.

════════════════════════════════════════════════════
PART E: UPDATE GLOBAL NAV
════════════════════════════════════════════════════

11. UPDATE GlobalNav.tsx:
Now it should be a CLIENT COMPONENT that:
- Reads current user from Supabase browser client
- Shows: Login button if not authenticated
- Shows: Avatar + "Dashboard" link + Logout button if authenticated
- Shows subscription badge next to avatar

useEffect to get user:
  const [user, setUser] = useState(null)
  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setUser(data.user))
    const { data: listener } = supabase.auth.onAuthStateChange((_, session) => {
      setUser(session?.user ?? null)
    })
    return () => listener.subscription.unsubscribe()
  }, [])

Show avatar: use user.user_metadata.avatar_url (Google) or initials from email.

════════════════════════════════════════════════════
PART F: SERVER-SIDE USER HELPERS
════════════════════════════════════════════════════

12. Create src/lib/auth/getUser.ts:
Server-side helper used in all tool API routes:

import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function getCurrentUser() {
  const cookieStore = await cookies()
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          )
        },
      },
    }
  )
  
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return { user: null, tier: 'free' as const, supabase }
  
  const { data: profile } = await supabase
    .from('user_profiles')
    .select('subscription_tier')
    .eq('id', user.id)
    .single()
  
  return {
    user,
    tier: (profile?.subscription_tier ?? 'free') as SubscriptionTier,
    supabase,
  }
}

13. Create src/lib/auth/getServiceClient.ts:
Service role client for webhooks and Edge Functions:

import { createClient } from '@supabase/supabase-js'

export function getServiceClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    {
      auth: { persistSession: false }
    }
  )
}

════════════════════════════════════════════════════
VERIFICATION:
════════════════════════════════════════════════════

Test these flows:
1. Visit localhost:3000/auth/login → login page shows
2. Click "Masuk dengan Google" → Google OAuth popup/redirect
3. After login → redirect to /dashboard
4. Dashboard shows user name and "Paket Gratis" card
5. Visit localhost:3000/wajar-slip → no redirect (public)
6. Visit localhost:3000/dashboard without login → redirect to /auth/login
7. Nav shows Login when logged out, avatar when logged in
8. PremiumGate: render it with currentTier='free', requiredTier='basic' → blur overlay shows
9. PremiumGate: render with currentTier='basic', requiredTier='basic' → content shows normally
10. pnpm tsc --noEmit → zero errors
===END===
```

---

## Verification Checklist for Stage 3

```bash
# Auth working
# 1. Open http://localhost:3000/auth/login in browser
# 2. Test Google OAuth login (requires actual Google OAuth app setup)
# 3. Test magic link email
# 4. Visit /dashboard — check session is read server-side

# Redirect working
curl -I localhost:3000/dashboard
# Expected: 307 redirect to /auth/login

# TypeScript clean
pnpm tsc --noEmit

# New user profile created after signup
# Check in Supabase Studio:
# SELECT * FROM user_profiles ORDER BY created_at DESC LIMIT 5;
```

**Next:** Stage 4 — Wajar Slip Calculation Engine
