// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Footer
// ══════════════════════════════════════════════════════════════════════════════

import Link from 'next/link'
import { WordmarkLogo } from '@/components/WordmarkLogo'

export function Footer() {
  return (
    <footer className="border-t bg-background">
      <div className="mx-auto max-w-5xl px-4 py-8 lg:px-6">
        <div className="grid gap-8 md:grid-cols-[1.5fr_1fr_1fr]">
          <div>
            <WordmarkLogo size="sm" />
            <p className="mt-3 max-w-xs text-xs leading-6 text-muted-foreground">
              Transparansi keuangan untuk semua orang Indonesia.
            </p>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Alat</p>
            <ul className="mt-2 space-y-1.5">
              <li><Link href="/wajar-slip" className="text-sm text-muted-foreground hover:text-emerald-600">Wajar Slip</Link></li>
              <li><Link href="/wajar-gaji" className="text-sm text-muted-foreground hover:text-emerald-600">Wajar Gaji</Link></li>
              <li><Link href="/wajar-tanah" className="text-sm text-muted-foreground hover:text-emerald-600">Wajar Tanah</Link></li>
              <li><Link href="/wajar-kabur" className="text-sm text-muted-foreground hover:text-emerald-600">Wajar Kabur</Link></li>
              <li><Link href="/wajar-hidup" className="text-sm text-muted-foreground hover:text-emerald-600">Wajar Hidup</Link></li>
            </ul>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Lainnya</p>
            <ul className="mt-2 space-y-1.5">
              <li><Link href="/pricing" className="text-sm text-muted-foreground hover:text-emerald-600">Pricing</Link></li>
              <li><Link href="/kontak" className="text-sm text-muted-foreground hover:text-emerald-600">Kontak</Link></li>
              <li><Link href="/privacy-policy" className="text-sm text-muted-foreground hover:text-emerald-600">Privacy</Link></li>
              <li><Link href="/terms" className="text-sm text-muted-foreground hover:text-emerald-600">Terms</Link></li>
            </ul>
          </div>
        </div>

        <div className="mt-8 flex flex-col gap-2 border-t border-border pt-4 md:flex-row md:items-center md:justify-between">
          <p className="text-xs font-mono text-muted-foreground">
            Data dari BPS · Kemnaker · BPN · Diperbarui setiap hari
          </p>
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} cekwajar.id
          </p>
        </div>
      </div>
    </footer>
  )
}
