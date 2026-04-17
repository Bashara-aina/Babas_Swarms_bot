'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — IDRInput Component
// Formats Indonesian Rupiah in real-time as user types
// Shows formatted value on display, raw number on focus/blur
// ══════════════════════════════════════════════════════════════════════════════

import { useState, useCallback, type InputHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

interface IDRInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange'> {
  value: number | ''
  onValueChange?: (rawValue: number | '') => void
  /** Show formatted value inline (before input focus). Default: true */
  showFormattedOnDisplay?: boolean
  placeholder?: string
}

function formatIDR(value: number): string {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

function stripFormatting(value: string): number {
  // Remove 'Rp', spaces, dots (thousand separators in IDR), and commas
  const cleaned = value.replace(/[Rp\s.]/g, '').replace(/,/g, '')
  return cleaned === '' ? NaN : parseInt(cleaned, 10)
}

export function IDRInput({
  value,
  onValueChange,
  showFormattedOnDisplay = true,
  placeholder = '0',
  className,
  id,
  ...props
}: IDRInputProps) {
  const [isFocused, setIsFocused] = useState(false)

  const handleFocus = useCallback(() => {
    setIsFocused(true)
  }, [])

  const handleBlur = useCallback(() => {
    setIsFocused(false)
    if (isNaN(value as number) || value === '') {
      onValueChange?.('')
    }
  }, [value])

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const raw = e.target.value
      // Allow empty or partial input while typing
      if (raw === '') {
        onValueChange?.('')
        return
      }
      const cleaned = raw.replace(/[Rp\s.]/g, '').replace(/,/g, '')
      const num = parseInt(cleaned, 10)
      if (!isNaN(num)) {
        onValueChange?.(num)
      }
    },
    [onValueChange]
  )

  const displayValue = (() => {
    if (isFocused) {
      // While focused: show raw input value for easy editing
      if (value === '') return ''
      return value.toString()
    }
    // While not focused: show formatted IDR
    if (value === '' || value === null) return ''
    return formatIDR(value)
  })()

  return (
    <div className="relative">
      <input
        type="text"
        inputMode="numeric"
        id={id}
        value={displayValue}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        placeholder={placeholder}
        className={cn(
          'w-full rounded-lg border border-border bg-background px-3 py-2 pr-7 text-sm font-medium text-foreground',
          'transition-all duration-150',
          'focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20',
          'hover:border-emerald-400',
          'placeholder:text-muted-foreground placeholder:font-normal',
          className
        )}
        {...props}
      />
      {/* IDR currency indicator */}
      <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs font-medium text-muted-foreground">
        IDR
      </span>
    </div>
  )
}
