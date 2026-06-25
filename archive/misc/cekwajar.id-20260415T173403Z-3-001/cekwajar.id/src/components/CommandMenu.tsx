'use client'

import * as React from 'react'
import { useRouter } from 'next/navigation'
import { Command } from 'cmdk'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  X,
  Moon,
  Sun,
  Monitor,
  LayoutDashboard,
  TrendingUp,
  Calculator,
  MapPin,
  Globe,
  Sparkles,
  ArrowRight,
} from 'lucide-react'

// ─── Navigation pages ───────────────────────────────────────────────────────
const NAV_ITEMS = [
  { name: 'Dashboard', path: '/dashboard', description: 'Ringkasan akun & langganan', icon: LayoutDashboard },
  { name: 'Wajar Gaji', path: '/wajar-gaji', description: 'Benchmark gaji berdasarkan provinsi', icon: TrendingUp },
  { name: 'Wajar Slip', path: '/wajar-slip', description: 'Audit slip gaji PPh21 & BPJS', icon: Calculator },
  { name: 'Wajar Tanah', path: '/wajar-tanah', description: 'Analisis harga tanah & properti', icon: MapPin },
  { name: 'Wajar Hidup', path: '/wajar-hidup', description: 'Hitung standar hidup per kota', icon: Globe },
  { name: 'Wajar Kabur', path: '/wajar-kabur', description: 'Perbandingan 20+ negara', icon: Sparkles },
  { name: 'Upgrade', path: '/upgrade', description: 'Upgrade paket langganan', icon: ArrowRight },
  { name: 'Pricing', path: '/pricing', description: 'Lihat semua paket & harga', icon: ArrowRight },
]

// ─── Theme ─────────────────────────────────────────────────────────────────
type Theme = 'light' | 'dark' | 'system'

const THEME_ITEMS: { value: Theme; label: string; icon: React.ReactNode }[] = [
  { value: 'light', label: 'Light', icon: <Sun className="h-4 w-4" /> },
  { value: 'dark', label: 'Dark', icon: <Moon className="h-4 w-4" /> },
  { value: 'system', label: 'System', icon: <Monitor className="h-4 w-4" /> },
]

// ─── Component ──────────────────────────────────────────────────────────────
export function CommandMenu() {
  const [open, setOpen] = React.useState(false)
  const [search, setSearch] = React.useState('')
  const router = useRouter()

  // Keyboard shortcut
  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  // Focus input when opened
  const inputRef = React.useRef<HTMLInputElement>(null)
  React.useEffect(() => {
    if (open) {
      // Small delay to ensure animation starts first
      const t = setTimeout(() => inputRef.current?.focus(), 50)
      return () => clearTimeout(t)
    }
  }, [open])

  const handleNavigate = React.useCallback((path: string) => {
    router.push(path)
    setOpen(false)
    setSearch('')
  }, [router])

  const handleThemeChange = React.useCallback((theme: Theme) => {
    const root = document.documentElement
    root.classList.remove('light', 'dark', 'system')
    if (theme === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      root.classList.add(prefersDark ? 'dark' : 'light')
    } else {
      root.classList.add(theme)
    }
    setOpen(false)
    setSearch('')
  }, [])

  // Close on Escape
  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  // Trigger button — hidden on mobile (overlay mode instead)
  if (!open) {
    return (
      <>
        {/* Desktop trigger */}
        <button
          onClick={() => setOpen(true)}
          className="hidden md:flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground border border-border rounded-lg hover:bg-muted transition-colors cursor-pointer"
          aria-label="Open command menu"
        >
          <Search className="h-4 w-4" />
          <span className="text-xs">Search...</span>
          <kbd className="pointer-events-none hidden h-5 select-none items-center gap-1 rounded border border-border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
            ⌘K
          </kbd>
        </button>

        {/* Mobile FAB — always visible */}
        <button
          onClick={() => setOpen(true)}
          className="md:hidden fixed bottom-4 right-4 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-600 text-white shadow-lg hover:bg-emerald-700 transition-colors cursor-pointer"
          aria-label="Open command menu"
        >
          <Search className="h-5 w-5" />
        </button>
      </>
    )
  }

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
            onClick={() => { setOpen(false); setSearch('') }}
          />

          {/* Dialog */}
          <motion.div
            key="dialog"
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className="fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2"
            onClick={(e) => e.stopPropagation()}
          >
            <Command
              className="overflow-hidden rounded-xl border border-border bg-white shadow-2xl dark:border-border dark:bg-background"
              loop
            >
              {/* Search header */}
              <div className="border-b border-border px-3 py-2 dark:border-border">
                <Search className="mr-2 h-4 w-4 shrink-0 text-muted-foreground dark:text-muted-foreground" />
                <Command.Input
                  ref={inputRef}
                  value={search}
                  onValueChange={setSearch}
                  placeholder="Ketik perintah atau navigasi..."
                  className="flex h-12 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground dark:placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
                  autoFocus
                />
                <button
                  onClick={() => { setOpen(false); setSearch('') }}
                  className="p-1 hover:bg-muted dark:hover:bg-muted rounded cursor-pointer"
                  aria-label="Close"
                >
                  <X className="h-4 w-4 text-muted-foreground" />
                </button>
              </div>

              <Command.List className="max-h-[320px] overflow-y-auto overflow-x-hidden p-2 scrollbar-hide">
                <Command.Empty className="py-6 text-center text-sm text-muted-foreground dark:text-muted-foreground">
                  Tidak ada hasil.
                </Command.Empty>

                {/* Navigation group */}
                <Command.Group
                  heading="Navigasi"
                  className="px-2 py-2 text-xs font-medium text-muted-foreground dark:text-muted-foreground"
                >
                  {NAV_ITEMS.map((item) => {
                    const Icon = item.icon
                    return (
                      <Command.Item
                        key={item.path}
                        value={`${item.name} ${item.description}`}
                        onSelect={() => handleNavigate(item.path)}
                        className="flex cursor-pointer items-center gap-3 rounded-lg px-2 py-2.5 text-sm text-foreground outline-none transition-colors hover:bg-muted hover:text-foreground dark:text-foreground dark:hover:bg-muted data-[selected=true]:bg-muted dark:data-[selected=true]:bg-muted"
                      >
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted dark:bg-muted">
                          <Icon className="h-4 w-4 text-muted-foreground dark:text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium">{item.name}</p>
                          <p className="text-xs text-muted-foreground dark:text-muted-foreground line-clamp-1">
                            {item.description}
                          </p>
                        </div>
                      </Command.Item>
                    )
                  })}
                </Command.Group>

                {/* Theme group */}
                <Command.Group
                  heading="Tema"
                  className="px-2 py-2 text-xs font-medium text-muted-foreground dark:text-muted-foreground"
                >
                  {THEME_ITEMS.map((item) => (
                    <Command.Item
                      key={item.value}
                      value={`theme ${item.label}`}
                      onSelect={() => handleThemeChange(item.value)}
                      className="flex cursor-pointer items-center gap-3 rounded-lg px-2 py-2.5 text-sm text-foreground outline-none transition-colors hover:bg-muted hover:text-foreground dark:text-foreground dark:hover:bg-muted data-[selected=true]:bg-muted dark:data-[selected=true]:bg-muted"
                    >
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted dark:bg-muted">
                        {item.icon}
                      </div>
                      <span className="capitalize">{item.label}</span>
                    </Command.Item>
                  ))}
                </Command.Group>
              </Command.List>

              {/* Footer hint */}
              <div className="border-t border-border px-3 py-2 dark:border-border">
                <div className="flex items-center gap-4 text-xs text-muted-foreground dark:text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <kbd className="rounded border border-border bg-muted px-1 py-0.5 font-mono dark:border-border dark:bg-muted">↑↓</kbd>
                    navigasi
                  </span>
                  <span className="flex items-center gap-1">
                    <kbd className="rounded border border-border bg-muted px-1 py-0.5 font-mono dark:border-border dark:bg-muted">↵</kbd>
                    pilih
                  </span>
                  <span className="flex items-center gap-1">
                    <kbd className="rounded border border-border bg-muted px-1 py-0.5 font-mono dark:border-border dark:bg-muted">esc</kbd>
                    tutup
                  </span>
                </div>
              </div>
            </Command>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
