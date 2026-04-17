// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — ShareVerdictButton
// Share audit result to clipboard or social
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useState } from 'react'
import { Share2, Check, Copy } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ShareVerdictButtonProps {
  verdict: 'SESUAI' | 'ADA_PELANGGARAN'
  violationCount: number
  city: string
  grossSalary: number
  className?: string
}

function formatIDR(n: number) {
  return `Rp ${n.toLocaleString('id-ID')}`
}

export function ShareVerdictButton({
  verdict,
  violationCount,
  city,
  grossSalary,
  className,
}: ShareVerdictButtonProps) {
  const [copied, setCopied] = useState(false)

  const text = verdict === 'SESUAI'
    ? `✅ Slip gaji saya di ${city} (${formatIDR(grossSalary)}/bulan) sudah sesuai regulasi! Cek juga di cekwajar.id — gratis!`
    : `⚠️ Ada ${violationCount} pelanggaran di slip gaji saya di ${city}. Potensi kerugian Rp juta-an/tahun. Cek juga di cekwajar.id — gratis!`

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // fallback — select text
    }
  }

  return (
    <div className={className}>
      <Button
        variant="outline"
        size="sm"
        onClick={handleCopy}
        className="gap-2"
      >
        {copied ? (
          <>
            <Check className="h-4 w-4 text-emerald-600" />
            <span className="text-emerald-700">Disalin!</span>
          </>
        ) : (
          <>
            <Share2 className="h-4 w-4" />
            Bagikan Hasil
          </>
        )}
      </Button>

      {/* Hidden text for accessibility + copy fallback */}
      <span className="sr-only">{text}</span>
    </div>
  )
}