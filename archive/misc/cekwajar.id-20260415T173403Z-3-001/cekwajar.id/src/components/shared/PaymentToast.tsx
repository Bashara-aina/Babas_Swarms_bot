'use client'

// ==============================================================================
// cekwajar.id — Payment Result Toast
// Shows success/pending toast based on URL search params
// ==============================================================================

import { useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { CheckCircle, Clock } from 'lucide-react'
import { useToast } from '@/components/ui/toast'

export function PaymentToast() {
  const searchParams = useSearchParams()
  const { toast } = useToast()

  useEffect(() => {
    const upgraded = searchParams.get('upgraded')
    const payment = searchParams.get('payment')

    if (upgraded === 'true') {
      toast({
        title: 'Selamat!',
        description: 'Langganan kamu kini aktif. Selamat menggunakan fitur premium!',
        duration: 8000,
      })
    } else if (payment === 'pending') {
      toast({
        description: (
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 shrink-0" />
            <span>Pembayaran menunggu konfirmasi. Ini bisa memakan waktu 1-5 menit.</span>
          </div>
        ),
        duration: 10000,
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return null
}
