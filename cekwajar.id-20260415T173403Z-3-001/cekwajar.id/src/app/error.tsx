'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { AlertTriangle, ChevronLeft, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full text-center">
        <div className="mb-4">
          <AlertTriangle className="h-12 w-12 text-amber-500 mx-auto" />
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-foreground">
          Ada yang tidak beres
        </h1>
        <p className="mt-2 text-muted-foreground">
          Terjadi kesalahan saat memuat halaman ini. Tim kami sudah diberi tahu
          — silakan coba lagi.
        </p>
        {error.digest && (
          <p className="mt-2 text-xs text-muted-foreground font-mono">
            Ref: {error.digest}
          </p>
        )}
        <div className="mt-6 flex flex-col sm:flex-row gap-3 justify-center">
          <Button
            onClick={reset}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            <RefreshCw className="mr-2 h-4 w-4" /> Coba lagi
          </Button>
          <Button variant="outline" asChild>
            <Link href="/">
              <ChevronLeft className="mr-2 h-4 w-4" /> Kembali ke beranda
            </Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
