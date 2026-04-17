// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — CityCommandSelect Component
// Searchable command-palette city selector
// Replaces standard dropdown with keyboard-navigable search
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { MapPin, Search, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

export interface CityOption {
  city: string
  province: string
  umk: number
}

interface CityCommandSelectProps {
  value: string
  onChange: (city: string) => void
  cities: CityOption[]
  className?: string
  placeholder?: string
}

function formatUMK(umk: number): string {
  if (umk >= 1_000_000) {
    return `Rp ${(umk / 1_000_000).toFixed(1)}jt`
  }
  return `Rp ${umk.toLocaleString('id-ID')}`
}

export function CityCommandSelect({
  value,
  onChange,
  cities,
  className,
  placeholder = 'Pilih kota...',
}: CityCommandSelectProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const [highlightedIndex, setHighlightedIndex] = useState(0)

  const selectedCity = cities.find((c) => c.city === value)

  const filtered = query.trim()
    ? cities.filter(
        (c) =>
          c.city.toLowerCase().includes(query.toLowerCase()) ||
          c.province.toLowerCase().includes(query.toLowerCase())
      )
    : cities.slice(0, 20) // Show top 20 by default

  useEffect(() => {
    if (open) {
      setQuery('')
      setHighlightedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [open])

  useEffect(() => {
    setHighlightedIndex(0)
  }, [query])

  const handleSelect = (cityName: string) => {
    onChange(cityName)
    setOpen(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open) {
      if (e.key === 'Enter' || e.key === ' ') {
        setOpen(true)
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex((i) => Math.min(i + 1, filtered.length - 1))
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex((i) => Math.max(i - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        if (filtered[highlightedIndex]) {
          handleSelect(filtered[highlightedIndex].city)
        }
        break
      case 'Escape':
        setOpen(false)
        break
    }
  }

  return (
    <div className={cn('relative', className)} onKeyDown={handleKeyDown}>
      {/* Trigger button */}
      <button
        type="button"
        aria-label="Pilih kota"
        aria-expanded={open}
        aria-haspopup="listbox"
        onClick={() => setOpen(!open)}
        className={cn(
          'flex h-10 w-full items-center justify-between rounded-lg border bg-white px-3 py-2 text-sm',
          'transition-colors hover:border-border focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-1',
          open && 'border-emerald-500 ring-2 ring-emerald-500',
          !selectedCity && 'text-muted-foreground'
        )}
        style={{ borderColor: open ? 'var(--ring)' : undefined }}
      >
        <span className="flex items-center gap-2 truncate">
          {selectedCity ? (
            <>
              <MapPin className="h-4 w-4 shrink-0 text-emerald-600" />
              <span>{selectedCity.city}</span>
              <span className="text-muted-foreground text-xs">{selectedCity.province}</span>
            </>
          ) : (
            <span>{placeholder}</span>
          )}
        </span>
        {selectedCity && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              onChange('')
            }}
            className="ml-1 rounded-full p-0.5 hover:bg-muted"
            aria-label="Hapus pilihan kota"
          >
            <X className="h-3 w-3 text-muted-foreground" />
          </button>
        )}
      </button>

      {/* Dropdown panel */}
      {open && (
        <div className="absolute z-50 mt-1 w-full rounded-xl border bg-popover shadow-lg overflow-hidden">
          {/* Search input */}
          <div className="flex items-center gap-2 border-b px-3 py-2">
            <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Cari kota atau provinsi..."
              className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
              aria-label="Cari kota"
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery('')}
                className="rounded-full p-0.5 hover:bg-muted"
                aria-label="Hapus pencarian"
              >
                <X className="h-3 w-3 text-muted-foreground" />
              </button>
            )}
          </div>

          {/* City list */}
          <div ref={listRef} role="listbox" className="max-h-64 overflow-y-auto py-1">
            {filtered.length === 0 ? (
              <div className="px-3 py-6 text-center text-sm text-muted-foreground">
                Kota tidak ditemukan
              </div>
            ) : (
              filtered.map((city, index) => (
                <button
                  key={`${city.city}-${city.province}`}
                  type="button"
                  role="option"
                  aria-selected={city.city === value}
                  onClick={() => handleSelect(city.city)}
                  className={cn(
                    'flex w-full items-center justify-between px-3 py-2 text-sm transition-colors',
                    index === highlightedIndex && 'bg-muted',
                    city.city === value && 'bg-emerald-50 text-emerald-700'
                  )}
                >
                  <span className="flex items-center gap-2 truncate">
                    <MapPin className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                    <span className="truncate">{city.city}</span>
                    <span className="text-muted-foreground text-xs truncate">{city.province}</span>
                  </span>
                  <span className="ml-2 shrink-0 text-xs font-medium text-muted-foreground">
                    UMK {formatUMK(city.umk)}
                  </span>
                </button>
              ))
            )}
          </div>

          {/* Footer hint */}
          {filtered.length > 0 && (
            <div className="border-t px-3 py-1.5 text-xs text-muted-foreground flex gap-3">
              <span>↑↓ Navigasi</span>
              <span>Enter Pilih</span>
              <span>Esc Tutup</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
