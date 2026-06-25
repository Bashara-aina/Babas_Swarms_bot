// cekwajar.id — MobileBottomNav (spec 06)
// Persistent bottom nav bar with Home + 5 tool destinations

'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, FileText, TrendingUp, MapPin, Plane, BarChart3 } from 'lucide-react'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { href: '/', icon: Home, label: 'Home', exact: true },
  { href: '/wajar-slip', icon: FileText, label: 'Slip', color: 'text-amber-500' },
  { href: '/wajar-gaji', icon: TrendingUp, label: 'Gaji', color: 'text-blue-500' },
  { href: '/wajar-tanah', icon: MapPin, label: 'Tanah', color: 'text-stone-500' },
  { href: '/wajar-kabur', icon: Plane, label: 'Kabur', color: 'text-indigo-500' },
  { href: '/wajar-hidup', icon: BarChart3, label: 'Hidup', color: 'text-teal-500' },
]

export function MobileBottomNav() {
  const pathname = usePathname()
  if (pathname.startsWith('/auth')) return null

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-background/95 backdrop-blur-sm border-t border-border safe-area-pb"
      aria-label="Navigasi utama"
    >
      <div className="flex items-center justify-around px-1 py-1">
        {NAV_ITEMS.map(item => {
          const isActive = item.exact
            ? pathname === item.href
            : pathname.startsWith(item.href)
          const Icon = item.icon

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex flex-col items-center gap-0.5 px-2 py-2 rounded-xl min-w-0 flex-1 transition-all duration-150',
                'tap-highlight-transparent active:scale-95',
                isActive
                  ? 'bg-emerald-50 dark:bg-emerald-950/40'
                  : 'hover:bg-muted/50'
              )}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon
                className={cn(
                  'w-5 h-5 transition-colors',
                  isActive
                    ? (item.color ?? 'text-emerald-600 dark:text-emerald-400')
                    : 'text-muted-foreground'
                )}
              />
              <span
                className={cn(
                  'text-[10px] font-medium leading-none transition-colors',
                  isActive
                    ? 'text-emerald-700 dark:text-emerald-400'
                    : 'text-muted-foreground'
                )}
              >
                {item.label}
              </span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
