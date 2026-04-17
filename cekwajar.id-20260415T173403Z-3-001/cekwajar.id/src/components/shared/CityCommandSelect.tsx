'use client'

// cekwajar.id — CityCommandSelect (spec 11)
// Enhanced: keyboard nav, scroll-to-highlight, recent cities, clear button

import { useState, useRef, useEffect, useCallback } from 'react'
import { Search, Check, ChevronDown, X, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'

const TOP_CITIES = [
  'Jakarta Pusat',
  'Jakarta Selatan',
  'Jakarta Utara',
  'Jakarta Barat',
  'Jakarta Timur',
  'Bekasi',
  'Tangerang',
  'Tangerang Selatan',
  'Depok',
  'Bogor',
  'Surabaya',
  'Bandung',
  'Medan',
  'Semarang',
  'Makassar',
]

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

// --- Session-storage recent cities (survive soft nav, not hard refresh) ---
const RECENT_KEY = 'ckj_recent_cities'
const MAX_RECENT = 5

function getRecentCities(): string[] {
  try {
    return JSON.parse(sessionStorage.getItem(RECENT_KEY) ?? '[]')
  } catch {
    return []
  }
}

function addRecentCity(city: string) {
  try {
    const recent = getRecentCities().filter((c) => c !== city)
    sessionStorage.setItem(RECENT_KEY, JSON.stringify([city, ...recent].slice(0, MAX_RECENT)))
  } catch {
    // sessionStorage unavailable
  }
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
  const [highlightedIdx, setHighlightedIdx] = useState(-1)
  const [recentCities, setRecentCities] = useState<string[]>([])

  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const itemRefs = useRef<Map<number, HTMLButtonElement>>(new Map())

  // Load recent cities on mount
  useEffect(() => {
    setRecentCities(getRecentCities())
  }, [])

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
        setSearch('')
        setHighlightedIdx(-1)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // Focus input when dropdown opens
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50)
    } else {
      setHighlightedIdx(-1)
    }
  }, [open])

  // Scroll highlighted item into view
  useEffect(() => {
    if (highlightedIdx < 0) return
    const el = itemRefs.current.get(highlightedIdx)
    el?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [highlightedIdx])

  const normalizedCities = cities.map((city) => {
    if (typeof city === 'string') return city
    return city.city ?? city.label ?? ''
  }).filter(Boolean)

  const uniqueCities = Array.from(new Set(normalizedCities))
  const topCities = TOP_CITIES.filter((c) => uniqueCities.includes(c))
  const otherCities = uniqueCities.filter((c) => !TOP_CITIES.includes(c))
  const keyword = search.toLowerCase()

  const filteredTop = search
    ? topCities.filter((c) => c.toLowerCase().includes(keyword))
    : topCities
  const filteredOther = search
    ? otherCities.filter((c) => c.toLowerCase().includes(keyword))
    : otherCities
  const filteredRecent = !search
    ? recentCities.filter((c) => uniqueCities.includes(c) && c !== value)
    : []

  // Build flat option list for keyboard nav
  type Section = { label?: string; cities: string[] }
  const sections: Section[] = []
  if (filteredRecent.length > 0 && !search) sections.push({ label: 'Terbaru', cities: filteredRecent })
  if (filteredTop.length > 0) sections.push({ label: 'Kota Populer', cities: filteredTop })
  if (filteredOther.length > 0) sections.push({ label: undefined, cities: filteredOther })

  const flatOptions = sections.flatMap((s) => s.cities)

  const handleSelect = useCallback((city: string) => {
    onValueChange?.(city)
    onChange?.(city)
    addRecentCity(city)
    setRecentCities(getRecentCities())
    setOpen(false)
    setSearch('')
    setHighlightedIdx(-1)
  }, [onValueChange, onChange])

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open) return
    switch (e.key) {
      case 'ArrowDown': {
        e.preventDefault()
        setHighlightedIdx((i) => Math.min(i + 1, flatOptions.length - 1))
        break
      }
      case 'ArrowUp': {
        e.preventDefault()
        setHighlightedIdx((i) => Math.max(i - 1, 0))
        break
      }
      case 'Enter': {
        e.preventDefault()
        if (highlightedIdx >= 0 && highlightedIdx < flatOptions.length) {
          handleSelect(flatOptions[highlightedIdx])
        }
        break
      }
      case 'Escape': {
        e.preventDefault()
        setOpen(false)
        setSearch('')
        setHighlightedIdx(-1)
        break
      }
    }
  }, [open, flatOptions, highlightedIdx, handleSelect])

  const showClear = Boolean(value && !open)
  const totalVisible = filteredRecent.length + filteredTop.length + filteredOther.length

  return (
    <div ref={containerRef} className={cn('relative w-full', className)}>
      {/* Trigger */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={value ? `Kota dipilih: ${value}` : placeholder}
        className={cn(
          'w-full h-14 flex items-center justify-between px-4 rounded-xl border bg-background',
          'text-left text-sm transition-colors',
          'hover:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-1',
          open && 'ring-2 ring-emerald-500 ring-offset-1',
          !value && 'text-muted-foreground'
        )}
      >
        <span className="truncate">{value || placeholder}</span>
        <span className="flex items-center gap-1 flex-shrink-0">
          {showClear && (
            <span
              role="button"
              tabIndex={0}
              aria-label="Hapus pilihan kota"
              onClick={(e) => {
                e.stopPropagation()
                onValueChange?.('')
                onChange?.('')
                setRecentCities(getRecentCities())
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.stopPropagation()
                  e.preventDefault()
                  onValueChange?.('')
                  onChange?.('')
                }
              }}
              className="p-1 rounded hover:bg-muted transition-colors"
            >
              <X className="w-3.5 h-3.5 text-muted-foreground" />
            </span>
          )}
          <ChevronDown className={cn('w-4 h-4 text-muted-foreground transition-transform', open && 'rotate-180')} />
        </span>
      </button>

      {/* Dropdown */}
      {open && (
        <div
          role="dialog"
          aria-label="Pilih kota"
          className="absolute z-50 top-full left-0 right-0 mt-1 bg-background border border-border rounded-xl shadow-lg overflow-hidden"
        >
          {/* Search */}
          <div className="p-2 border-b">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
              <input
                ref={inputRef}
                type="text"
                placeholder="Cari kota..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  setHighlightedIdx(-1)
                }}
                onKeyDown={handleKeyDown}
                aria-label="Cari kota"
                aria-controls="city-listbox"
                aria-activedescendant={highlightedIdx >= 0 ? `city-option-${highlightedIdx}` : undefined}
                className="w-full pl-9 pr-3 py-2.5 text-sm bg-muted rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          {/* List */}
          <div
            id="city-listbox"
            ref={listRef}
            role="listbox"
            aria-label="Daftar kota"
            className="max-h-72 overflow-y-auto oversc-contain"
          >
            {totalVisible === 0 ? (
              <p className="text-center text-sm text-muted-foreground py-8">
                Kota tidak ditemukan
              </p>
            ) : (
              <>
                {sections.map((section, si) => {
                  const startIdx = sections.slice(0, si).reduce((acc, s) => acc + s.cities.length, 0)
                  return (
                    <div key={section.label ?? `section-${si}`}>
                      {section.label && (
                        <p className="px-4 pt-2 pb-1 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                          {section.label === 'Terbaru' && <Clock className="inline w-3 h-3 mr-1 mb-0.5" />}
                          {section.label}
                        </p>
                      )}
                      {section.cities.map((city) => {
                        const flatIdx = startIdx + section.cities.indexOf(city)
                        const isHighlighted = highlightedIdx === flatIdx
                        const isSelected = value === city

                        return (
                          <button
                            key={city}
                            id={`city-option-${flatIdx}`}
                            ref={(el) => {
                              if (el) itemRefs.current.set(flatIdx, el)
                              else itemRefs.current.delete(flatIdx)
                            }}
                            role="option"
                            aria-selected={isSelected}
                            type="button"
                            onClick={() => handleSelect(city)}
                            onMouseEnter={() => setHighlightedIdx(flatIdx)}
                            className={cn(
                              'w-full flex items-center justify-between px-4 py-2.5 text-sm text-left transition-colors',
                              isHighlighted && 'bg-muted/70',
                              isSelected
                                ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 font-medium'
                                : 'hover:bg-muted/50 text-foreground'
                            )}
                          >
                            {city}
                            {isSelected && <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />}
                          </button>
                        )
                      })}
                    </div>
                  )
                })}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
