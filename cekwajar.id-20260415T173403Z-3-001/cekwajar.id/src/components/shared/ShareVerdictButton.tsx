// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — ShareVerdictButton
// Share audit / benchmark result via clipboard (works on any tool)
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useState } from 'react'
import { Share2, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'

type SlipVerdictProps = {
  verdict: 'SESUAI' | 'ADA_PELANGGARAN'
  violationCount: number
  city: string
  grossSalary: number
  text?: never
  className?: string
}

type CustomTextProps = {
  text: string
  verdict?: never
  violationCount?: never
  city?: never
  grossSalary?: never
  className?: string
}

type ShareVerdictButtonProps = SlipVerdictProps | CustomTextProps

function formatIDR(n: number) {
  return `Rp ${n.toLocaleString('id-ID')}`
}

function buildSlipText(
  verdict: 'SESUAI' | 'ADA_PELANGGARAN',
  violationCount: number,
  city: string,
  grossSalary: number,
) {
  return verdict === 'SESUAI'
    ? `✅ Slip gaji saya di ${city} (${formatIDR(grossSalary)}/bulan) sudah sesuai regulasi! Cek juga di cekwajar.id — gratis!`
    : `⚠️ Ada ${violationCount} pelanggaran di slip gaji saya di ${city}. Potensi kerugian Rp juta-an/tahun. Cek juga di cekwajar.id — gratis!`
}

export function ShareVerdictButton(props: ShareVerdictButtonProps) {
  const [copied, setCopied] = useState(false)

  const text =
    'text' in props && props.text
      ? props.text
      : buildSlipText(
          (props as SlipVerdictProps).verdict,
          (props as SlipVerdictProps).violationCount,
          (props as SlipVerdictProps).city,
          (props as SlipVerdictProps).grossSalary,
        )

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // fallback — select text
    }
  }

  const handleWhatsApp = () => {
    const url = `https://wa.me/?text=${encodeURIComponent(text)}`
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  return (
    <div className={props.className}>
      <div className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleWhatsApp}
          className="gap-2"
          aria-label="Bagikan hasil ke WhatsApp"
        >
          <Share2 className="h-4 w-4" />
          Bagikan ke WhatsApp
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleCopy}
          className="gap-2"
          aria-label="Salin hasil"
        >
          {copied ? (
            <>
              <Check className="h-4 w-4 text-emerald-600" />
              <span className="text-emerald-700">Disalin!</span>
            </>
          ) : (
            <>
              <Share2 className="h-4 w-4" />
              Salin
            </>
          )}
        </Button>
      </div>
      <span className="sr-only">{text}</span>
    </div>
  )
}
