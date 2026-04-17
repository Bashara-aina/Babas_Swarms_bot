import Link from 'next/link'
import { Home, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function NotFound() {
  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="text-8xl font-black text-emerald-600 dark:text-emerald-400 mb-4">
          404
        </div>
        <h1 className="text-2xl font-bold text-foreground mb-2">
          Halaman tidak ditemukan
        </h1>
        <p className="text-muted-foreground mb-8">
          Halaman yang kamu cari tidak ada atau sudah dipindahkan.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button asChild className="bg-emerald-600 hover:bg-emerald-700 gap-2">
            <Link href="/">
              <Home className="w-4 h-4" />
              Ke Beranda
            </Link>
          </Button>
          <Button asChild variant="outline" className="gap-2">
            <Link href="/wajar-slip">
              <ArrowLeft className="w-4 h-4" />
              Cek Slip Gaji
            </Link>
          </Button>
        </div>
      </div>
    </main>
  )
}
