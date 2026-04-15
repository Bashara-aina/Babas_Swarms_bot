'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Global Navigation Bar
// Mobile-first sticky nav with auth-aware user menu
// ══════════════════════════════════════════════════════════════════════════════

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, useEffect } from 'react'
import { Menu, X, Calculator, User, LogOut, LayoutDashboard } from 'lucide-react'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { TOOLS } from '@/lib/constants'
import { cn } from '@/lib/utils'
import { createClient } from '@/lib/supabase/client'
import { signOut } from '@/app/auth/actions'
import { SubscriptionBadge } from '@/components/shared/SubscriptionBadge'
import type { SubscriptionTier } from '@/types'
import { useRouter } from 'next/navigation'

export function GlobalNav() {
  const pathname = usePathname()
  const router = useRouter()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [user, setUser] = useState<{
    id: string
    email?: string
    user_metadata?: { full_name?: string; avatar_url?: string }
  } | null>(null)
  const [tier, setTier] = useState<SubscriptionTier>('free')
  const [menuOpen, setMenuOpen] = useState(false)

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
    setMenuOpen(false)
    await signOut()
  }

  return (
    <header className="stick top-0 z-50 w-full border-b bg-white shadow-sm">
      <nav className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4 lg:h-16 lg:px-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <Calculator className="h-6 w-6 text-emerald-600" />
          <span className="text-lg font-bold text-emerald-700">cekwajar.id</span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden items-center gap-1 md:flex">
          {TOOLS.map((tool) => (
            <Link
              key={tool.id}
              href={tool.href}
              className={cn(
                'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                pathname === tool.href
                  ? 'bg-emerald-100 text-emerald-800'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              )}
            >
              {tool.emoji} {tool.name}
            </Link>
          ))}
        </div>

        {/* Desktop auth section */}
        <div className="hidden items-center gap-2 md:flex">
          {user ? (
            <div className="relative">
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="flex items-center gap-2 rounded-full p-1 hover:bg-slate-100"
              >
                <Avatar className="h-7 w-7">
                  <AvatarFallback className="bg-emerald-100 text-emerald-700 text-xs">
                    {getUserInitials(user.email)}
                  </AvatarFallback>
                </Avatar>
                <SubscriptionBadge tier={tier} />
              </button>

              {/* Dropdown menu */}
              {menuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setMenuOpen(false)}
                  />
                  <div className="absolute right-0 top-full z-20 mt-1 w-48 rounded-lg border bg-white py-1 shadow-lg">
                    <div className="border-b px-3 py-2">
                      <p className="text-sm font-medium truncate">{user.user_metadata?.full_name ?? user.email}</p>
                      <p className="text-xs text-slate-500 truncate">{user.email}</p>
                    </div>
                    <Link
                      href="/dashboard"
                      onClick={() => setMenuOpen(false)}
                      className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-slate-50"
                    >
                      <LayoutDashboard className="h-4 w-4" />
                      Dashboard
                    </Link>
                    <button
                      onClick={handleSignOut}
                      className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
                    >
                      <LogOut className="h-4 w-4" />
                      Keluar
                    </button>
                  </div>
                </>
              )}
            </div>
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
            <Button variant="ghost" size="icon" aria-label="Buka menu">
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-72">
            <div className="flex flex-col gap-4 pt-6">
              <div className="flex items-center gap-2 border-b pb-4">
                <Calculator className="h-5 w-5 text-emerald-600" />
                <span className="font-bold text-emerald-700">cekwajar.id</span>
              </div>

              {TOOLS.map((tool) => (
                <Link
                  key={tool.id}
                  href={tool.href}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-base font-medium transition-colors',
                    pathname === tool.href
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'text-slate-600 hover:bg-slate-50'
                  )}
                >
                  <span>{tool.emoji}</span>
                  {tool.name}
                </Link>
              ))}

              <div className="mt-4 flex flex-col gap-2 border-t pt-4">
                {user ? (
                  <>
                    <div className="flex items-center gap-2 px-3">
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className="bg-emerald-100 text-emerald-700 text-xs">
                          {getUserInitials(user.email)}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
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
                      className="w-full text-red-600 hover:bg-red-50"
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
