// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — FieldTooltip Component
// Contextual help popover for form fields
// Shows definition + example when user hovers/focuses
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useState } from 'react'
import { HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { FIELD_TOOLTIPS } from '@/lib/field-tooltips'

interface FieldTooltipProps {
  content: string       // The explanatory text
  example?: string       // Optional "Contoh:" text shown in a callout
  className?: string
  iconSize?: number
}

export function FieldTooltip({ content, example, className, iconSize = 14 }: FieldTooltipProps) {
  const [open, setOpen] = useState(false)

  return (
    <div className={cn('relative inline-flex', className)}>
      <button
        type="button"
        aria-label="Bantuan"
        className="inline-flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors cursor-help"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
      >
        <HelpCircle className="text-muted-foreground" style={{ width: iconSize, height: iconSize }} />
      </button>

      {open && (
        <div
          role="tooltip"
          className="absolute left-full top-1/2 z-50 ml-2 w-64 rounded-lg border bg-popover p-3 shadow-lg text-sm"
          style={{ transform: 'translateY(-50%)' }}
        >
          <p className="text-foreground leading-relaxed">{content}</p>
          {example && (
            <div className="mt-2 rounded-md bg-muted px-2 py-1.5">
              <p className="text-xs text-muted-foreground">Contoh:</p>
              <p className="text-xs font-medium text-foreground mt-0.5">{example}</p>
            </div>
          )}
          {/* Arrow */}
          <div className="absolute left-0 top-1/2 -translate-x-full -translate-y-1/2 border-6 border-transparent border-r-popover" />
        </div>
      )}
    </div>
  )
}

// ─── Pre-built tooltip content map for wajar-slip fields ───────────────────

export const SLIP_TOOLTIPS: Record<string, { content: string; example?: string }> = {
  grossSalary: {
    content: FIELD_TOOLTIPS.gapok,
    example: 'Rp 8.500.000',
  },
  takeHome: {
    content: FIELD_TOOLTIPS.take_home,
    example: 'Rp 6.800.000',
  },
  ptkpStatus: {
    content: FIELD_TOOLTIPS.ptkp,
    example: 'TK/0 = Tidak Kawin, 0 tanggungan',
  },
  city: {
    content: FIELD_TOOLTIPS.kota,
    example: 'Jakarta',
  },
  reportedPph21: {
    content: FIELD_TOOLTIPS.pph21,
    example: 'Rp 425.000',
  },
  reportedJht: {
    content: FIELD_TOOLTIPS.jht_karyawan,
    example: 'Rp 170.000',
  },
  reportedJp: {
    content: FIELD_TOOLTIPS.jp_karyawan,
    example: 'Rp 85.000',
  },
  reportedKesehatan: {
    content: FIELD_TOOLTIPS.bpjs_kes_karyawan,
    example: 'Rp 150.000',
  },
  hasNPWP: {
    content: FIELD_TOOLTIPS.npwp,
  },
}
