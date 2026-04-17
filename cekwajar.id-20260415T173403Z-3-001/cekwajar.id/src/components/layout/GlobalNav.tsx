'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Global Navigation Bar
// Mobile-first sticky nav with auth-aware user menu
// ══════════════════════════════════════════════════════════════════════════════

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, useEffect } from 'react'
import { Menu, X, Calculator, User, LogOut, LayoutDashboard, Sun, Moon } from 'lucide-react'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { TOOLS } from '@/lib/constants'
import { cn } from '@/lib/utils'
import { createClient } from '@/lib/supabase/client'
import { signOut } from '@/app/auth/actions'
import { SubscriptionBadge } from '@/components/shared/SubscriptionBadge'
import type { SubscriptionTier } from '@/types'
import { useRouter } from 'next/navigation'
import { useAppTheme } from '@/components/providers'
import { WordmarkLogo } from '@/components/WordmarkLogo'

// Tool accent colors — dot indicator per tool
const TOOL_ACCENT: Record<string, string> = {
  'wajar-slip': 'bg-amber-500',
  'wajar-gaji': 'bg-blue-500',
  'wajar-tanah': 'bg-amber-500',
  'wajar-kabur': 'bg-indigo-500',
  'wajar-hidup': 'bg-rose-500',
}

export function GlobalNav() {
  const pathname = usePathname()
  const router = useRouter()
  const { resolvedTheme, toggleTheme } = useAppTheme()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [user, setUser] = useState<{
    id: string
    email?: string
    user_metadata?: { full_name?: string; avatar_url?: string }
  } | null>(null)
  const [tier, setTier] = useState<SubscriptionTier>('free')

  useEffect(() => {
    const supabase = createClient()

    // Get initial user
    supabase.auth.getUser().then(({ data }) => {
      setUser(data.user as typeof user)
      if (data.user) {
        // Fetch tier from profile
        supabase
          .from('user_profiles')
          .select('subscription_tier')
          .eq('id', data.user.id)
          .single()
          .then(({ data: profile }) => {
            if (profile) {
              setTier(profile.subscription_tier as SubscriptionTier)
            }
          })
      }
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (_, session) => {
      const u = session?.user as typeof user | null
      setUser(u)
      if (u) {
        const { data: profile } = await supabase
          .from('user_profiles')
          .select('subscription_tier')
          .eq('id', u.id)
          .single()
        setTier((profile?.subscription_tier as SubscriptionTier) ?? 'free')
      } else {
        setTier('free')
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  function getUserInitials(email?: string): string {
    if (!email) return 'U'
    const name = email.split('@')[0]
    return name.slice(0, 2).toUpperCase()
  }

  async function handleSignOut() {
    await signOut()
  }

  return (
    <header className="stick top-0 z-50 w-full border-b shadow-sm" style={{ backgroundColor: 'var(--nav-bg)', borderColor: 'var(--nav-border)' }}>
      <nav className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4 lg:h-16 lg:px-6">
        {/* Logo */}
        <WordmarkLogo size="md" />

        {/* Desktop nav */}
        <div className="hidden items-center gap-1 md:flex">
          {TOOLS.map((tool) => (
            <Link
              key={tool.id}
              href={tool.href}
              className={cn(
                'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                pathname === tool.href
                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                  : 'hover:bg-[var(--nav-hover-bg)]'
              )}
              style={{ color: pathname === tool.href ? undefined : 'var(--nav-text-muted)' }}
            >
              <span
                className={cn('mr-1.5 inline-block h-1.5 w-1.5 rounded-full', TOOL_ACCENT[tool.id] ?? 'bg-emerald-500')}
                aria-hidden="true"
              />
              <tool.Icon className="mr-1 h-4 w-4 inline-block" />
              {tool.name}
            </Link>
          ))}
        </div>

        {/* Desktop auth + theme section */}
        <div className="hidden items-center gap-2 md:flex">
          {/* Theme toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            aria-label={resolvedTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            className="text-[var(--nav-text-muted)] hover:bg-[var(--nav-hover-bg)]"
          >
            {resolvedTheme === 'dark' ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </Button>

          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  aria-label="Menu pengguna"
                  className="flex items-center gap-2 rounded-full p-1 hover:bg-[var(--nav-hover-bg)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
                >
                  <Avatar className="h-7 w-7">
                    <AvatarFallback className="bg-emerald-100 text-emerald-700 text-xs">
                      {getUserInitials(user.email)}
                    </AvatarFallback>
                  </Avatar>
                  <SubscriptionBadge tier={tier} />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
                <div className="px-3 py-2 border-b" style={{ borderColor: 'var(--border)' }}>
                  <p className="text-sm font-medium truncate" style={{ color: 'var(--card-foreground)' }}>{user.user_metadata?.full_name ?? user.email}</p>
                  <p className="text-xs truncate" style={{ color: 'var(--muted-foreground)' }}>{user.email}</p>
                </div>
                <DropdownMenuSeparator style={{ backgroundColor: 'var(--border)' }} />
                <DropdownMenuItem asChild>
                  <Link href="/dashboard" className="flex items-center gap-2 cursor-pointer" style={{ color: 'var(--card-foreground)' }}>
                    <LayoutDashboard className="h-4 w-4" />
                    Dashboard
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator style={{ backgroundColor: 'var(--border)' }} />
                <DropdownMenuItem
                  onClick={handleSignOut}
                  className="text-red-600 cursor-pointer focus:text-red-600"
                  style={{ color: 'var(--destructive)' }}
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  Keluar
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <>
              <Link href="/auth/login">
                <Button variant="outline" size="sm" className="border-emerald-600 text-emerald-700 hover:bg-emerald-50">
                  Masuk
                </Button>
              </Link>
              <Link href="/wajar-slip">
                <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700">
                  Cek Gratis
                </Button>
              </Link>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger asChild className="md:hidden">
            <Button variant="ghost" size="icon" aria-label="Buka menu navigasi">
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-72" style={{ backgroundColor: 'var(--card)', color: 'var(--card-foreground)' }}>
            <div className="flex flex-col gap-4 pt-6">
              <div className="flex items-center justify-between border-b pb-4" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center gap-2">
                  <WordmarkLogo size="sm" />
                </div>
                {/* Theme toggle in mobile */}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={toggleTheme}
                  aria-label={resolvedTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
                >
                  {resolvedTheme === 'dark' ? (
                    <Sun className="h-5 w-5" />
                  ) : (
                    <Moon className="h-5 w-5" />
                  )}
                </Button>
              </div>

              {TOOLS.map((tool) => (
                <Link
                  key={tool.id}
                  href={tool.href}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-base font-medium transition-colors',
                    pathname === tool.href
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                      : ''
                  )}
                  style={{ color: pathname === tool.href ? undefined : 'var(--muted-foreground)' }}
                >
                  <tool.Icon className="h-5 w-5" />
                  {tool.name}
                </Link>
              ))}

              <div className="mt-4 flex flex-col gap-2 border-t pt-4" style={{ borderColor: 'var(--border)' }}>
                {user ? (
                  <>
                    <div className="flex items-center gap-2 px-3">
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className="bg-emerald-100 text-emerald-700 text-xs">
                          {getUserInitials(user.email)}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate" style={{ color: 'var(--card-foreground)' }}>
                          {user.user_metadata?.full_name ?? user.email}
                        </p>
                        <SubscriptionBadge tier={tier} />
                      </div>
                    </div>
                    <Link href="/dashboard" onClick={() => setMobileOpen(false)}>
                      <Button variant="outline" className="w-full border-emerald-600 text-emerald-700">
                        <LayoutDashboard className="mr-2 h-4 w-4" />
                        Dashboard
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      onClick={handleSignOut}
                      className="w-full"
                      style={{ color: 'var(--destructive)' }}
                    >
                      <LogOut className="mr-2 h-4 w-4" />
                      Keluar
                    </Button>
                  </>
                ) : (
                  <>
                    <Link href="/auth/login" onClick={() => setMobileOpen(false)}>
                      <Button variant="outline" className="w-full border-emerald-600 text-emerald-700">
                        Masuk
                      </Button>
                    </Link>
                    <Link href="/wajar-slip" onClick={() => setMobileOpen(false)}>
                      <Button className="w-full bg-emerald-600 hover:bg-emerald-700">
                        Cek Gratis
                      </Button>
                    </Link>
                  </>
                )}
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </nav>
    </header>
  )
}
