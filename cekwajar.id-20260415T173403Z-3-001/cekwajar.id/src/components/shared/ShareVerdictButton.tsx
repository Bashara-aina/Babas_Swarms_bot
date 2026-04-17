// cekwajar.id — ShareVerdictButton (spec 07)
// WhatsApp share + native share for audit results

'use client'

import { Share2, MessageCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ShareVerdictButtonProps {
  verdict: 'SESUAI' | 'ADA_PELANGGARAN'
  violationCount: number
  city?: string
  grossSalary?: number
  className?: string
}

export function ShareVerdictButton({
  verdict,
  violationCount,
  city,
  grossSalary,
  className,
}: ShareVerdictButtonProps) {
  const isSesuai = verdict === 'SESUAI'

  const text = isSesuai
    ? `Slip gaji saya SESUAI regulasi ✅ — cek PPh21, BPJS, dan UMK otomatis di cekwajar.id`
    : `Slip gaji saya ada ${violationCount} pelanggaran ⚠️ — cek slip gajimu juga di cekwajar.id`

  const handleWhatsApp = () => {
    const encodedText = encodeURIComponent(text)
    window.open(`https://wa.me/?text=${encodedText}`, '_blank', 'noopener,noreferrer')
  }

  const handleNativeShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Hasil Audit Slip Gaji — cekwajar.id',
          text,
          url: 'https://cekwajar.id/wajar-slip',
        })
      } catch {
        // User cancelled
      }
    } else {
      handleWhatsApp()
    }
  }

  return (
    <div className={cn('flex gap-2 mt-4', className)}>
      <Button
        variant="outline"
        size="sm"
        className="gap-2 flex-1 border-green-200 text-green-700 hover:bg-green-50 dark:border-green-800 dark:text-green-400 dark:hover:bg-green-950/30"
        onClick={handleWhatsApp}
      >
        <MessageCircle className="w-4 h-4" />
        Bagikan ke WhatsApp
      </Button>

      {'share' in navigator && (
        <Button
          variant="outline"
          size="sm"
          className="gap-2 border-slate-200 hover:bg-slate-50 dark:border-slate-700"
          onClick={handleNativeShare}
          aria-label="Bagikan"
        >
          <Share2 className="w-4 h-4" />
        </Button>
      )}
    </div>
  )
}

function cn(...classes: (string | undefined | false)[]) {
  return classes.filter(Boolean).join(' ')
}
