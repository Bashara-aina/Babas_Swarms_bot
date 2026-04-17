// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — MobileCitySheet
// Mobile: bottom sheet with CityCommandSelect
// Desktop: renders CityCommandSelect directly
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useState, useEffect } from 'react'
import { MapPin, Search, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { CityCommandSelect, CityOption } from './CityCommandSelect'
import { cn } from '@/lib/utils'

interface MobileCitySheetProps {
  value: string
  onChange: (city: string) => void
  cities: CityOption[]
  className?: string
  placeholder?: string
}

export function MobileCitySheet({
  value,
  onChange,
  cities,
  className,
  placeholder = 'Pilih kota...',
}: MobileCitySheetProps) {
  const [isMobile, setIsMobile] = useState(false)
  const [sheetOpen, setSheetOpen] = useState(false)

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])

  const selectedCity = cities.find((c) => c.city === value)

  if (!isMobile) {
    return (
      <CityCommandSelect
        value={value}
        onChange={onChange}
        cities={cities}
        className={className}
        placeholder={placeholder}
      />
    )
  }

  // Mobile: trigger button → opens bottom sheet with city search
  return (
    <>
      <button
        type="button"
        onClick={() => setSheetOpen(true)}
        className={cn(
          'flex h-10 w-full items-center justify-between rounded-lg border bg-white px-3 py-2 text-sm',
          'transition-colors hover:border-border focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-1',
          'text-left',
          !selectedCity && 'text-muted-foreground'
        )}
        style={{ borderColor: 'var(--border)' }}
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
      </button>

      {/* Mobile Bottom Sheet */}
      {sheetOpen && (
        <div className="fixed inset-0 z-50 flex flex-col justify-end">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setSheetOpen(false)}
          />

          {/* Sheet */}
          <div className="relative bg-white rounded-t-2xl max-h-[80vh] overflow-hidden flex flex-col">
            {/* Handle */}
            <div className="flex justify-center pt-3 pb-2">
              <div className="w-10 h-1 rounded-full bg-muted" />
            </div>

            {/* Header */}
            <div className="flex items-center justify-between px-4 pb-2 border-b border-border">
              <h2 className="text-base font-semibold text-foreground">Pilih Kota</h2>
              <button
                onClick={() => setSheetOpen(false)}
                className="rounded-full p-1 hover:bg-muted transition-colors"
                aria-label="Tutup"
              >
                <X className="h-5 w-5 text-muted-foreground" />
              </button>
            </div>

            {/* City list */}
            <div className="flex-1 overflow-y-auto">
              {/* Search */}
              <div className="sticky top-0 bg-white border-b border-border px-4 py-2">
                <div className="flex items-center gap-2 border rounded-lg px-3 py-2 bg-muted">
                  <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Cari kota atau provinsi..."
                    className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
                    autoFocus
                    id="city-sheet-search"
                  />
                </div>
              </div>

              <div className="py-2">
                {cities.map((city) => (
                  <button
                    key={`${city.city}-${city.province}`}
                    type="button"
                    onClick={() => {
                      onChange(city.city)
                      setSheetOpen(false)
                    }}
                    className={cn(
                      'flex w-full items-center justify-between px-4 py-3 text-sm transition-colors',
                      city.city === value && 'bg-emerald-50 text-emerald-700',
                      city.city !== value && 'hover:bg-muted'
                    )}
                  >
                    <span className="flex items-center gap-2 truncate">
                      <MapPin className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                      <span className="truncate">{city.city}</span>
                      <span className="text-muted-foreground text-xs truncate">{city.province}</span>
                    </span>
                    <span className="ml-2 shrink-0 text-xs font-medium text-muted-foreground">
                      UMK {city.umk >= 1_000_000 ? `${(city.umk / 1_000_000).toFixed(1)}jt` : `Rp ${city.umk.toLocaleString('id-ID')}`}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-border">
              <Button
                onClick={() => setSheetOpen(false)}
                variant="outline"
                className="w-full"
              >
                Batal
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
