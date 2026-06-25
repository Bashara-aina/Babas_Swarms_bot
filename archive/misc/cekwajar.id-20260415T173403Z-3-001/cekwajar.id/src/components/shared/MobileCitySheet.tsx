// cekwajar.id — MobileCitySheet (spec 06)
// Bottom-sheet city picker for mobile with search + popular cities

'use client'

import { useState } from 'react'
import { Search, Check, ChevronDown } from 'lucide-react'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { CityOption } from '@/components/shared/CityCommandSelect'

const TOP_CITIES = [
  'Jakarta Pusat', 'Jakarta Selatan', 'Jakarta Utara', 'Jakarta Barat', 'Jakarta Timur',
  'Bekasi', 'Tangerang', 'Tangerang Selatan', 'Depok', 'Bogor',
  'Surabaya', 'Bandung', 'Medan', 'Semarang', 'Makassar', 'Palembang',
]

interface MobileCitySheetProps {
  cities: Array<string | CityOption>
  value: string
  onValueChange: (city: string) => void
  placeholder?: string
}

export function MobileCitySheet({
  cities,
  value,
  onValueChange,
  placeholder = 'Pilih kota kerja',
}: MobileCitySheetProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')

  const normalizeCity = (city: string | CityOption): string =>
    typeof city === 'string' ? city : (city.city ?? city.label ?? '')

  const topInList = cities.filter((city) => TOP_CITIES.includes(normalizeCity(city)))
  const others = cities.filter(c => !TOP_CITIES.includes(normalizeCity(c)))

  const filtered = search
    ? cities.filter(c => normalizeCity(c).toLowerCase().includes(search.toLowerCase())).slice(0, 50)
    : null

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <button
          type="button"
          className={cn(
            'w-full h-14 flex items-center justify-between px-4 rounded-xl border bg-background',
            'text-left text-sm transition-colors',
            'hover:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-1',
            !value && 'text-muted-foreground'
          )}
        >
          <span>{value || placeholder}</span>
          <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        </button>
      </SheetTrigger>

      <SheetContent side="bottom" className="h-[85vh] px-0 pb-0">
        <SheetHeader className="px-4 pb-3 border-b">
          <SheetTitle className="text-base">Pilih Kota Kerja</SheetTitle>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Cari kota..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="pl-9 h-11"
              autoFocus
            />
          </div>
        </SheetHeader>

        <div className="overflow-y-auto flex-1 h-full pb-safe">
          {filtered ? (
            <div className="px-2 py-2">
              {filtered.length === 0 ? (
                <p className="text-center text-sm text-muted-foreground py-8">
                  Kota tidak ditemukan. Coba kata kunci lain.
                </p>
              ) : (
                filtered.map(city => {
                  const label = typeof city === 'string' ? city : (city.city ?? city.label ?? '')
                  const key = typeof city === 'string' ? city : (city.id ?? city.label ?? '')
                  return (
                    <CityItem
                      key={key}
                      city={label}
                      isSelected={value === label}
                      onSelect={() => { onValueChange(label); setOpen(false); setSearch('') }}
                    />
                  )
                })
              )}
            </div>
          ) : (
            <>
              <div className="px-4 pt-3 pb-1">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                  Kota Populer
                </p>
              </div>
              <div className="px-2">
                {topInList.map(city => {
                  const label = typeof city === 'string' ? city : (city.city ?? city.label ?? '')
                  const key = typeof city === 'string' ? city : (city.id ?? city.label ?? '')
                  return (
                    <CityItem
                      key={key}
                      city={label}
                      isSelected={value === label}
                      onSelect={() => { onValueChange(label); setOpen(false); setSearch('') }}
                    />
                  )
                })}
              </div>

              <div className="border-t mx-4 my-3" />

              <div className="px-4 pb-1">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                  Semua Kota
                </p>
              </div>
              <div className="px-2 pb-8">
                {others.map(city => {
                  const label = typeof city === 'string' ? city : (city.city ?? city.label ?? '')
                  const key = typeof city === 'string' ? city : (city.id ?? city.label ?? '')
                  return (
                    <CityItem
                      key={key}
                      city={label}
                      isSelected={value === label}
                      onSelect={() => { onValueChange(label); setOpen(false); setSearch('') }}
                    />
                  )
                })}
              </div>
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}

function CityItem({
  city,
  isSelected,
  onSelect,
}: {
  city: string
  isSelected: boolean
  onSelect: () => void
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        'w-full flex items-center justify-between px-4 py-3.5 rounded-xl text-sm text-left',
        'transition-colors active:scale-[0.98]',
        isSelected
          ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 font-medium'
          : 'hover:bg-muted/50 text-foreground'
      )}
    >
      {city}
      {isSelected && <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />}
    </button>
  )
}
