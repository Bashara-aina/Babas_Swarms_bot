// cekwajar.id — CityCommandSelect (spec 06)
// Desktop searchable dropdown for city selection

'use client'

import { useState, useRef, useEffect } from 'react'
import { Search, Check, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface CityOption {
  id?: string
  label: string
  city?: string
  province?: string
  umk?: number
}

interface CityCommandSelectProps {
  cities: Array<string | CityOption>
  value: string
  onValueChange?: (city: string) => void
  onChange?: (city: string) => void
  placeholder?: string
  className?: string
}

export function CityCommandSelect({
  cities,
  value,
  onValueChange,
  onChange,
  placeholder = 'Pilih kota kerja',
  className,
}: CityCommandSelectProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 50)
  }, [open])

  const normalizedCities = cities
    .map((city) => {
      if (typeof city === 'string') return city
      return city.city ?? city.label ?? ''
    })
    .filter(Boolean)

  const filtered = search
    ? normalizedCities.filter((c) => c.toLowerCase().includes(search.toLowerCase())).slice(0, 50)
    : normalizedCities.slice(0, 50)

  const handleSelect = (city: string) => {
    onValueChange?.(city)
    onChange?.(city)
    setOpen(false)
    setSearch('')
  }

  return (
    <div ref={containerRef} className={cn('relative w-full', className)}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={cn(
          'w-full h-14 flex items-center justify-between px-4 rounded-xl border bg-background',
          'text-left text-sm transition-colors',
          'hover:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-1',
          open && 'ring-2 ring-emerald-500 ring-offset-1',
          !value && 'text-muted-foreground'
        )}
      >
        <span className="truncate">{value || placeholder}</span>
        <ChevronDown className={cn('w-4 h-4 text-muted-foreground flex-shrink-0 transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div className="absolute z-50 top-full left-0 right-0 mt-1 bg-background border border-border rounded-xl shadow-lg overflow-hidden">
          <div className="p-2 border-b">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                ref={inputRef}
                type="text"
                placeholder="Cari kota..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm bg-muted rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
            </div>
          </div>

          <div className="max-h-64 overflow-y-auto">
            {filtered.length === 0 ? (
              <p className="text-center text-sm text-muted-foreground py-6">
                Kota tidak ditemukan
              </p>
            ) : (
              filtered.map((city) => (
                <button
                  key={city}
                  type="button"
                  onClick={() => handleSelect(city)}
                  className={cn(
                    'w-full flex items-center justify-between px-4 py-2.5 text-sm text-left transition-colors',
                    value === city
                      ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 font-medium'
                      : 'hover:bg-muted/50 text-foreground'
                  )}
                >
                  {city}
                  {value === city && <Check className="w-4 h-4 text-emerald-600" />}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
