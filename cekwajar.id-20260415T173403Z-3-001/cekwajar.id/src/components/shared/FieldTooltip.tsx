// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — FieldTooltip Component
// Contextual help popover for form fields
// Shows definition + example when user hovers/focuses
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useState } from 'react'
import { HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

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
    content: 'Gaji bruto adalah total penghasilan sebelum potonganeberapa. Jumlah ini biasanya tertera di slip gaji bagian atas.',
    example: 'Rp 8.500.000',
  },
  takeHome: {
    content: 'Take home pay adalah jumlah yang benar-benar kamu terima setelah semua potongan. Ini biasanya angka paling besar di slip.',
    example: 'Rp 6.800.000',
  },
  ptkpStatus: {
    content: 'PTKP (Penghasilan Tidak Kena Pajak) ditentukan oleh status pernikahan dan jumlah tanggungan. Ini mempengaruhi besar kecilnya PPh21.',
    example: 'TK/0 = Tidak Kawin, 0 tanggungan',
  },
  city: {
    content: 'Kota determines UMK (Upah Minimum Kabupaten/Kota) yang berlaku. Gaji di atas UMK belum tentu wajar jika cost of living tinggi.',
    example: 'Jakarta',
  },
  reportedPph21: {
    content: 'PPh21 adalah pajak penghasilan Pasal 21. Jika angka ini 0 atau tidak ada di slip, kemungkinan ada pelanggaran.',
    example: 'Rp 425.000',
  },
  reportedJht: {
    content: 'JHT (Jaminan Hari Tua) adalah iuran untuk tabungan hari tua. Wajib 2% dari gaji, dibayar bersama oleh perusahaan (3.7%) dan karyawan (2%).',
    example: 'Rp 170.000',
  },
  reportedJp: {
    content: 'JP (Jaminan Pensiun) adalah iuran untuk pensiun. Wajib 1% dari gaji, dibayar bersama oleh perusahaan (2%) dan karyawan (1%).',
    example: 'Rp 85.000',
  },
  reportedKesehatan: {
    content: 'BPJS Kesehatan mandatory untuk semua karyawan. Biasanya 1% dari gaji (gigi minimum Rp 80.000/bulan untuk TK-grade 1).',
    example: 'Rp 150.000',
  },
  hasNPWP: {
    content: 'NPWP (Nomor Pokok Wajib Pajak) diperlukan untuk pengurangan tarif PPh21. Tanpa NPWP, tarif 20% lebih tinggi.',
  },
}
