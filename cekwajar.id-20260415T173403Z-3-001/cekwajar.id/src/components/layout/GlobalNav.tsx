'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Global Navigation Bar
// Mobile-first sticky nav with hamburger sheet menu
// ══════════════════════════════════════════════════════════════════════════════

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'
import { Menu, X, Calculator } from 'lucide-react'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { TOOLS } from '@/lib/constants'
import { cn } from '@/lib/utils'

export function GlobalNav() {
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)

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

        {/* Desktop CTA */}
        <div className="hidden items-center gap-2 md:flex">
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
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </nav>
    </header>
  )
}
