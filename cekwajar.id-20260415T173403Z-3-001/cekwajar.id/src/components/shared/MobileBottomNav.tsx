// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — MobileBottomNav
// Fixed bottom navigation for mobile web
// Shows 4 key destinations + active tool indicator
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, FileText, BarChart2, User } from 'lucide-react'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { href: '/', label: 'Beranda', icon: Home },
  { href: '/wajar-slip', label: 'Cek Slip', icon: FileText },
  { href: '/dashboard', label: 'Dashboard', icon: BarChart2 },
  { href: '/auth/login', label: 'Akun', icon: User },
]

export function MobileBottomNav({ className }: { className?: string }) {
  const pathname = usePathname()
  const [mounted, setMounted] = useState(false)

  useEffect(() => setMounted(true), [])

  if (!mounted) return null

  return (
    <nav
      className={cn(
        'fixed bottom-0 inset-x-0 z-40 border-t bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80 md:hidden',
        className
      )}
      aria-label="Navigasi utama"
    >
      <div className="flex items-center justify-around py-1.5 px-2">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || (href !== '/' && pathname.startsWith(href))
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex flex-col items-center gap-0.5 rounded-lg px-3 py-1.5 text-xs transition-colors',
                isActive
                  ? 'text-emerald-700'
                  : 'text-muted-foreground hover:text-foreground'
              )}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon className={cn('h-5 w-5', isActive ? 'text-emerald-600' : '')} />
              <span className={cn(isActive ? 'font-semibold' : '')}>{label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}