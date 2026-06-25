// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Error Card
// Error state for tool pages
// ══════════════════════════════════════════════════════════════════════════════

import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ErrorCardProps {
  title?: string
  message?: string
  onRetry?: () => void
}

export function ErrorCard({
  title = 'Terjadi Kesalahan',
  message = 'Silakan coba lagi.',
  onRetry,
}: ErrorCardProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-red-100 bg-red-50 p-6 text-center">
      <div className="rounded-full bg-red-100 p-2">
        <AlertCircle className="h-5 w-5 text-red-600" />
      </div>
      <div>
        <p className="font-semibold text-red-800">{title}</p>
        <p className="mt-1 text-sm text-red-600">{message}</p>
      </div>
      {onRetry && (
        <Button
          size="sm"
          variant="outline"
          className="border-red-200 text-red-700 hover:bg-red-100"
          onClick={onRetry}
        >
          <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          Coba Lagi
        </Button>
      )}
    </div>
  )
}
